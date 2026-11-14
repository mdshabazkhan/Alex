"""
Matrix Ledger & Memory Store (SQLite WAL)
Provides persistent storage for task lifecycles, steps, token costs, bugs, and checkpoints.
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

LEDGER_PATH = os.path.join("storage", "data", "ledger.db")
MEMORY_PATH = os.path.join("storage", "data", "memory.db")


def get_connection(db_path: str = LEDGER_PATH) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 30000;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection(LEDGER_PATH)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            created_at TEXT,
            finished_at TEXT,
            request_redacted TEXT,
            intent TEXT,
            executor TEXT,
            kind TEXT,
            profile TEXT,
            status TEXT,
            progress_pct REAL DEFAULT 0.0,
            current_step TEXT,
            total_steps INTEGER DEFAULT 1,
            step_number INTEGER DEFAULT 0,
            verified INTEGER DEFAULT 0,
            evidence TEXT,
            needs_network INTEGER DEFAULT 1,
            offline_capable INTEGER DEFAULT 0,
            interrupted INTEGER DEFAULT 0,
            resumed INTEGER DEFAULT 0,
            retries INTEGER DEFAULT 0,
            artifacts_json TEXT DEFAULT '[]',
            policy_version TEXT DEFAULT '1',
            budget_tokens INTEGER DEFAULT 120000,
            pinned_gateway TEXT,
            pinned_model TEXT
        );

        CREATE TABLE IF NOT EXISTS steps (
            task_id TEXT,
            step_no INTEGER,
            attempt INTEGER,
            tool TEXT,
            idempotency_key TEXT,
            started_at TEXT,
            finished_at TEXT,
            duration_ms INTEGER,
            status TEXT,
            verified INTEGER DEFAULT 0,
            evidence TEXT,
            rule_id TEXT,
            error_class TEXT,
            error_message TEXT,
            PRIMARY KEY (task_id, step_no, attempt)
        );

        CREATE TABLE IF NOT EXISTS model_calls (
            call_id TEXT PRIMARY KEY,
            task_id TEXT,
            at TEXT,
            profile TEXT,
            gateway TEXT,
            provider TEXT,
            model TEXT,
            tokens_in INTEGER DEFAULT 0,
            tokens_out INTEGER DEFAULT 0,
            latency_ms INTEGER DEFAULT 0,
            cost_usd REAL DEFAULT 0.0,
            outcome TEXT,
            redactions INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS bugs (
            bug_id TEXT PRIMARY KEY,
            fingerprint TEXT UNIQUE,
            component TEXT,
            error_class TEXT,
            first_seen TEXT,
            last_seen TEXT,
            occurrences INTEGER DEFAULT 1,
            sample_message TEXT,
            example_tasks TEXT,
            diagnosis TEXT,
            status TEXT DEFAULT 'open',
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT,
            at TEXT,
            source TEXT,
            type TEXT,
            payload_redacted TEXT
        );

        CREATE TABLE IF NOT EXISTS checkpoints (
            task_id TEXT,
            seq INTEGER,
            at TEXT,
            reason TEXT,
            hermes_run_id TEXT,
            hermes_session_id TEXT,
            verified_steps_json TEXT,
            next_step TEXT,
            artifacts_json TEXT,
            idempotency_keys_json TEXT,
            tokens_so_far INTEGER,
            PRIMARY KEY (task_id, seq)
        );
        """)
    conn.close()


def create_task(task_data: Dict[str, Any]) -> str:
    conn = get_connection()
    with conn:
        conn.execute("""
            INSERT OR REPLACE INTO tasks (
                task_id, created_at, request_redacted, intent, executor, kind,
                profile, status, progress_pct, current_step, total_steps, step_number,
                needs_network, offline_capable, budget_tokens, pinned_gateway, pinned_model
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_data["task_id"],
            task_data.get("created_at", datetime.now().isoformat()),
            task_data.get("request_redacted", ""),
            task_data.get("intent", "general"),
            task_data.get("executor", "hermes"),
            task_data.get("kind", "complex"),
            task_data.get("profile", "agent"),
            task_data.get("status", "running"),
            task_data.get("progress_pct", 0.0),
            task_data.get("current_step", "Initializing"),
            task_data.get("total_steps", 1),
            task_data.get("step_number", 0),
            task_data.get("needs_network", 1),
            task_data.get("offline_capable", 0),
            task_data.get("budget_tokens", 120000),
            task_data.get("pinned_gateway", ""),
            task_data.get("pinned_model", "")
        ))
    conn.close()
    return task_data["task_id"]


def update_task_progress(task_id: str, step_no: int, total_steps: int, current_step: str, status: Optional[str] = None):
    conn = get_connection()
    cur = conn.cursor()
    progress_pct = round((step_no / max(1, total_steps)) * 100.0, 1)
    if status:
        cur.execute("""
            UPDATE tasks
            SET step_number = ?, total_steps = ?, current_step = ?, progress_pct = ?, status = ?
            WHERE task_id = ?
        """, (step_no, total_steps, current_step, progress_pct, status, task_id))
    else:
        cur.execute("""
            UPDATE tasks
            SET step_number = ?, total_steps = ?, current_step = ?, progress_pct = ?
            WHERE task_id = ?
        """, (step_no, total_steps, current_step, progress_pct, task_id))
    conn.commit()
    conn.close()


def complete_task(task_id: str, verified: bool = True, evidence: str = "", status: str = "done"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE tasks
        SET finished_at = ?, status = ?, progress_pct = 100.0, verified = ?, evidence = ?
        WHERE task_id = ?
    """, (datetime.now().isoformat(), status, 1 if verified else 0, evidence, task_id))
    conn.commit()
    conn.close()


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_recent_tasks(limit: int = 15) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT task_id, created_at, finished_at, request_redacted, intent,
               executor, kind, status, progress_pct, current_step,
               step_number, total_steps, verified
        FROM tasks
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def record_model_call(call_data: Dict[str, Any]):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO model_calls (
            call_id, task_id, at, profile, gateway, provider, model,
            tokens_in, tokens_out, latency_ms, cost_usd, outcome, redactions
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        call_data["call_id"],
        call_data.get("task_id", ""),
        datetime.now().isoformat(),
        call_data.get("profile", ""),
        call_data.get("gateway", ""),
        call_data.get("provider", ""),
        call_data.get("model", ""),
        call_data.get("tokens_in", 0),
        call_data.get("tokens_out", 0),
        call_data.get("latency_ms", 0),
        call_data.get("cost_usd", 0.0),
        call_data.get("outcome", "success"),
        call_data.get("redactions", 0)
    ))
    conn.commit()
    conn.close()


def get_task_token_usage(task_id: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT SUM(tokens_in + tokens_out) as total FROM model_calls WHERE task_id = ?", (task_id,))
    row = cur.fetchone()
    conn.close()
    return row["total"] if row and row["total"] else 0


def clear_all_tasks():
    """Clear all logged tasks, steps, model calls, and traces from the database."""
    conn = get_connection()
    with conn:
        try:
            conn.execute("DELETE FROM steps;")
        except Exception:
            pass
        try:
            conn.execute("DELETE FROM tasks;")
        except Exception:
            pass
        try:
            conn.execute("DELETE FROM model_calls;")
        except Exception:
            pass
        try:
            conn.execute("DELETE FROM traces;")
        except Exception:
            pass
    conn.close()


# Initialize on import
init_db()
