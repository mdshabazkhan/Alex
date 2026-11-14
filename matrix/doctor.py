"""
Matrix Doctor
Diagnoses tool and execution failures, logs deduplicated bugs, and steers Hermes to alternatives.
"""

import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any, Tuple
from matrix.store import get_connection


class Doctor:
    def __init__(self):
        pass

    def classify_error(self, tool: str, error_message: str) -> Tuple[str, str]:
        """
        Classifies error into standard categories and suggests steering advice.
        Returns: (error_class, advice)
        """
        msg = error_message.lower()

        if any(w in msg for w in ["401", "unauthorized", "login", "session expired", "auth"]):
            return "auth", "Service requires authentication. Switch to registered alternative route if available."

        if any(w in msg for w in ["429", "rate limit", "too many requests"]):
            return "rate_limit", "Rate limit exceeded. Back off and request gateway route rotation."

        if any(w in msg for w in ["connection refused", "timeout", "network unreachable", "no route to host"]):
            return "network", "Network error. Check internet connectivity or pause for offline takeover."

        if any(w in msg for w in ["element not found", "selector missing", "ui changed", "button not found"]):
            return "ui_drift", "UI elements shifted. Re-inspect DOM or Accessibility Tree to rediscover target."

        if any(w in msg for w in ["app not responding", "hung", "deadlock"]):
            return "app_hung", "Target application unresponsive. Suggest relaunching the app."

        return "tool_bug", "Unexpected tool exception. Capture stack trace and check input parameters."

    def record_bug(self, component: str, error_class: str, message: str, task_id: str = "") -> str:
        """Deduplicates and registers bugs by fingerprint."""
        raw_fp = f"{component}:{error_class}:{message[:120]}".lower()
        fingerprint = hashlib.sha256(raw_fp.encode("utf-8")).hexdigest()[:16]
        now = datetime.now().isoformat()

        conn = get_connection()
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT bug_id, occurrences FROM bugs WHERE fingerprint = ?", (fingerprint,))
            row = cur.fetchone()

            if row:
                bug_id = row["bug_id"]
                new_occ = row["occurrences"] + 1
                cur.execute("""
                    UPDATE bugs
                    SET occurrences = ?, last_seen = ?, sample_message = ?
                    WHERE bug_id = ?
                """, (new_occ, now, message[:300], bug_id))
            else:
                bug_id = f"BUG-{uuid.uuid4().hex[:6].upper()}"
                cur.execute("""
                    INSERT INTO bugs (
                        bug_id, fingerprint, component, error_class, first_seen,
                        last_seen, occurrences, sample_message, example_tasks, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (bug_id, fingerprint, component, error_class, now, now, 1, message[:300], task_id, "open"))

        conn.close()
        return bug_id


doctor = Doctor()
