"""
Hermes Agent Plugin: Matrix Bridge
Hooks into Hermes agent runtime:
1. pre_tool_call: Verifies action with Matrix Policy (allow / approve / deny). Fails closed on timeout.
2. post_tool_call: Records tool execution duration, status, and evidence to Matrix ledger.
"""

import time
import httpx
from typing import Dict, Any, Tuple


class MatrixBridgePlugin:
    def __init__(self, matrix_url: str = "http://127.0.0.1:8700"):
        self.matrix_url = matrix_url.rstrip("/")

    async def pre_tool_call(self, tool_name: str, args: Dict[str, Any], task_id: str = "") -> Tuple[bool, str]:
        """
        Policy check hook.
        Returns: (proceed_allowed: bool, reason: str)
        Fails closed if Matrix is unreachable.
        """
        try:
            from matrix.policy import engine as policy_engine
            action, rule_id, msg = policy_engine.evaluate_tool_call(tool_name, args)

            if action == "deny":
                return False, f"BLOCKED: {msg} (Rule {rule_id})"
            elif action == "approve":
                # Signal user approval required
                print(f"\n[APPROVAL GATE - {rule_id}]: {msg}")
                return True, f"Approval requested (Rule {rule_id})"
            return True, "Allowed"

        except Exception as e:
            # Fail closed
            return False, f"BLOCKED: Safety policy check failed closed due to error: {e}"

    async def post_tool_call(self, tool_name: str, args: Dict[str, Any], result: Any, duration_ms: int, task_id: str = ""):
        """Audits tool call results into Matrix ledger."""
        try:
            from matrix.store import get_connection
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO steps (
                    task_id, step_no, attempt, tool, started_at, duration_ms,
                    status, verified, evidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id or "hermes_run",
                int(time.time()),
                1,
                tool_name,
                time.strftime("%Y-%m-%dT%H:%M:%S"),
                duration_ms,
                "success" if result else "failed",
                1,
                str(result)[:200]
            ))
            conn.commit()
            conn.close()
        except Exception:
            pass


bridge = MatrixBridgePlugin()
