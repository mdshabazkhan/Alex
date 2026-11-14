"""
Matrix Telemetry & Reporting Engine
Generates:
1. Exact CSV Task Export (Task ID, Task, Status, Time Taken, Tokens Spent, Local or API, Executed By, Date, Time, Failure Reason)
2. Comprehensive Multi-Sheet Excel Report
"""

import os
import csv
import io
from datetime import datetime
from typing import Optional, List, Dict, Any
from matrix.store import get_connection

REPORTS_DIR = os.path.join("storage", "reports")


def export_tasks_csv() -> str:
    """
    Exports tasks to CSV with the exact columns requested:
    [task id, task, status, time taken, tokens spent, local or api, executed by, data, time, reason of failure if failed]
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            t.task_id,
            t.request_redacted,
            t.status,
            t.created_at,
            t.finished_at,
            t.executor,
            t.kind,
            t.pinned_gateway,
            t.evidence,
            COALESCE((SELECT SUM(m.tokens_in + m.tokens_out) FROM model_calls m WHERE m.task_id = t.task_id), 0) as tokens_spent,
            COALESCE((SELECT s.error_message FROM steps s WHERE s.task_id = t.task_id AND s.status = 'failed' ORDER BY s.step_no DESC LIMIT 1), '') as step_error
        FROM tasks t
        ORDER BY t.created_at DESC
    """)
    rows = cur.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    # User specified exact header columns:
    headers = [
        "task id",
        "task",
        "status",
        "time taken",
        "tokens spent",
        "local or api",
        "executed by",
        "data",
        "time",
        "reason of failure if failed"
    ]
    writer.writerow(headers)

    for r in rows:
        task_id = r["task_id"]
        task_text = r["request_redacted"] or ""
        status = r["status"] or "unknown"
        created_at_str = r["created_at"] or ""
        finished_at_str = r["finished_at"] or ""
        executor = r["executor"] or "alex"
        tokens_spent = int(r["tokens_spent"] or 0)
        gw = (r["pinned_gateway"] or "").lower()

        # Compute duration
        time_taken_str = "0.0s"
        if created_at_str and finished_at_str:
            try:
                t0 = datetime.fromisoformat(created_at_str)
                t1 = datetime.fromisoformat(finished_at_str)
                dur = max(0.0, (t1 - t0).total_seconds())
                time_taken_str = f"{dur:.1f}s"
            except Exception:
                time_taken_str = "0.5s"
        elif created_at_str and status in ["running", "paused"]:
            try:
                t0 = datetime.fromisoformat(created_at_str)
                dur = max(0.0, (datetime.now() - t0).total_seconds())
                time_taken_str = f"{dur:.1f}s (running)"
            except Exception:
                time_taken_str = "in progress"

        # Determine Local vs API
        if executor == "alex" and tokens_spent == 0:
            local_or_api = "local"
        elif "ollama" in gw or "local" in gw:
            local_or_api = "local"
        else:
            local_or_api = "api"

        # Parse date and time
        date_str = ""
        time_str = ""
        if created_at_str:
            try:
                dt = datetime.fromisoformat(created_at_str)
                date_str = dt.strftime("%Y-%m-%d")
                time_str = dt.strftime("%H:%M:%S")
            except Exception:
                date_str = created_at_str[:10]
                time_str = created_at_str[11:19]

        # Determine reason of failure if failed
        reason = ""
        if status == "failed":
            reason = r["step_error"] or r["evidence"] or "Execution failed"

        writer.writerow([
            task_id,
            task_text,
            status,
            time_taken_str,
            tokens_spent,
            local_or_api,
            executor,
            date_str,
            time_str,
            reason
        ])

    csv_content = output.getvalue()

    # Save to disk as well
    csv_file_path = os.path.join(REPORTS_DIR, "alex_tasks_export.csv")
    with open(csv_file_path, "w", encoding="utf-8") as f:
        f.write(csv_content)

    return csv_content


def generate_report(output_filename: Optional[str] = None) -> str:
    """Generates the comprehensive multi-sheet Excel / CSV workbook."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    if not output_filename:
        output_filename = f"alex-report-{date_str}.xlsx"

    target_path = os.path.join(REPORTS_DIR, output_filename)

    conn = get_connection()
    cur = conn.cursor()

    tasks = [dict(r) for r in cur.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()]
    steps = [dict(r) for r in cur.execute("SELECT * FROM steps ORDER BY started_at DESC").fetchall()]
    calls = [dict(r) for r in cur.execute("SELECT * FROM model_calls ORDER BY at DESC").fetchall()]
    bugs = [dict(r) for r in cur.execute("SELECT * FROM bugs ORDER BY last_seen DESC").fetchall()]

    total_tasks = len(tasks)
    verified_tasks = sum(1 for t in tasks if t.get("verified") == 1)
    total_tokens = sum((c.get("tokens_in", 0) + c.get("tokens_out", 0)) for c in calls)
    total_cost = sum(c.get("cost_usd", 0.0) for c in calls)

    summary_rows = [
        {"Metric": "Reporting Date", "Value": date_str},
        {"Metric": "Total Tasks Executed", "Value": total_tasks},
        {"Metric": "Verified Successful Tasks", "Value": verified_tasks},
        {"Metric": "Verification Rate", "Value": f"{(verified_tasks / max(1, total_tasks))*100:.1f}%"},
        {"Metric": "Total Tokens Consumed", "Value": total_tokens},
        {"Metric": "Total Estimated Cost ($)", "Value": f"${total_cost:.4f}"},
        {"Metric": "Active Open Bugs", "Value": sum(1 for b in bugs if b.get("status") == "open")}
    ]

    try:
        import openpyxl
        wb = openpyxl.Workbook()
        ws_sum = wb.active
        ws_sum.title = "Summary"
        ws_sum.append(["Metric", "Value"])
        for r in summary_rows:
            ws_sum.append([r["Metric"], r["Value"]])

        ws_jobs = wb.create_sheet(title="Jobs")
        if tasks:
            ws_jobs.append(list(tasks[0].keys()))
            for t in tasks:
                ws_jobs.append(list(t.values()))

        ws_steps = wb.create_sheet(title="Steps")
        if steps:
            ws_steps.append(list(steps[0].keys()))
            for s in steps:
                ws_steps.append(list(s.values()))

        ws_costs = wb.create_sheet(title="Costs")
        if calls:
            ws_costs.append(list(calls[0].keys()))
            for c in calls:
                ws_costs.append(list(c.values()))

        ws_bugs = wb.create_sheet(title="Bugs")
        if bugs:
            ws_bugs.append(list(bugs[0].keys()))
            for b in bugs:
                ws_bugs.append(list(b.values()))

        wb.save(target_path)
        conn.close()
        return target_path

    except ImportError:
        # Generate the requested task CSV as fallback
        export_tasks_csv()
        conn.close()
        return os.path.join(REPORTS_DIR, "alex_tasks_export.csv")
