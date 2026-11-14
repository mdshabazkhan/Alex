"""
Jarvis Dashboard UI
Displays active running tasks with a live progress bar, percentage, and all recent tasks.
"""

import sys
import time
import asyncio
from typing import List, Dict, Any
from jarvis.matrix_client import client as matrix_client
from jarvis.voice_filter import notifier

# Terminal styling codes
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
CLEAR_SCREEN = "\033[2J\033[H"


def format_progress_bar(pct: float, length: int = 20) -> str:
    filled = int(round(length * (pct / 100.0)))
    bar = "█" * filled + "░" * (length - filled)
    if pct >= 100.0:
        color = GREEN
    elif pct >= 50.0:
        color = CYAN
    else:
        color = YELLOW
    return f"{color}[{bar}] {pct:5.1f}%{RESET}"


def render_dashboard(tasks: List[Dict[str, Any]], system_status: Dict[str, Any]):
    print(CLEAR_SCREEN, end="")
    print(f"{BOLD}{CYAN}══════════════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}{CYAN}                      ALEX — JARVIS ACTIVE DASHBOARD                                   {RESET}")
    print(f"{BOLD}{CYAN}══════════════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f" Matrix Status: {GREEN}Connected (127.0.0.1:8700){RESET} | Gateways: {YELLOW}Docker (FreeLLMAPI & OmniRoute){RESET}")
    print(f" Voice Policy : {DIM}Strict (Important Updates Only: Start, Milestone, Done, Error){RESET}")
    print(f" Storage Path : {DIM}storage/workspace | storage/data/ledger.db{RESET}")
    print(f"{CYAN}──────────────────────────────────────────────────────────────────────────────────────{RESET}")

    # Separate Active vs Completed
    active_tasks = [t for t in tasks if t.get("status") in ["running", "pending_approval", "paused"]]
    recent_done = [t for t in tasks if t.get("status") in ["done", "failed", "stopped"]]

    print(f"\n{BOLD}▶ ACTIVE TASKS ({len(active_tasks)}){RESET}")
    if not active_tasks:
        print(f"  {DIM}No active tasks currently running.{RESET}")
    else:
        for t in active_tasks:
            tid = t.get("task_id", "")
            pct = float(t.get("progress_pct") or 0.0)
            step = t.get("current_step", "Processing")
            req = t.get("request_redacted", "")[:35]
            bar = format_progress_bar(pct, length=20)
            status_col = YELLOW if t.get("status") == "running" else RED
            print(f"  • {BOLD}{tid}{RESET} | {bar} | {status_col}{t.get('status').upper()}{RESET}")
            print(f"    {DIM}Goal:{RESET} {req} | {DIM}Current Step:{RESET} {step}")

    print(f"\n{CYAN}──────────────────────────────────────────────────────────────────────────────────────{RESET}")
    print(f"{BOLD}▶ RECENT TASKS HISTORY ({len(recent_done)}){RESET}")
    print(f"  {'TASK ID':<22} {'INTENT':<16} {'STATUS':<12} {'PROGRESS':<28} {'FINISHED'}")
    print(f"  {'-'*20} {'-'*14} {'-'*10} {'-'*26} {'-'*12}")

    if not recent_done:
        print(f"  {DIM}No prior tasks found.{RESET}")
    else:
        for t in recent_done[:10]:
            tid = t.get("task_id", "")[:20]
            intent = t.get("intent", "general")[:14]
            status = t.get("status", "done").upper()
            pct = float(t.get("progress_pct") or 0.0)
            bar = format_progress_bar(pct, length=14)
            finished = (t.get("finished_at") or t.get("created_at") or "")[-8:]
            stat_color = GREEN if status == "DONE" else RED
            print(f"  {tid:<22} {intent:<16} {stat_color}{status:<12}{RESET} {bar:<36} {finished}")

    print(f"\n{CYAN}══════════════════════════════════════════════════════════════════════════════════════{RESET}")


async def main():
    while True:
        try:
            tasks = await matrix_client.get_recent_tasks(limit=15)
            status = {"connected": True}
            render_dashboard(tasks, status)
        except Exception as e:
            print(f"\n[Matrix Disconnected]: {e}. Retrying in 2 seconds...")
        await asyncio.sleep(1.0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting Jarvis Dashboard.")
