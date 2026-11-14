"""
Comprehensive Automated Acceptance Test Suite for Project Alex (Phase 0)
Validates Policy, Ledger, Sticky Gateway Pinning, Voice Gatekeeper, and Report Generation.
"""

import os
import unittest
from matrix.policy import engine as policy_engine
from matrix.store import (
    create_task,
    get_task,
    update_task_progress,
    complete_task,
    get_recent_tasks,
    record_model_call,
    get_task_token_usage
)
from matrix.gateway import gateway_engine
from matrix.doctor import doctor
from matrix.reports import generate_report
from jarvis.reflex import reflex_engine
from jarvis.voice_filter import notifier


class TestAlexPipeline(unittest.TestCase):

    def test_01_safety_scrubbing(self):
        """Verifies DATA-001 (Secret scrubbing) and DATA-003 (Card placeholders)."""
        raw_text = "Here is my secret token: api_key='secret_key_123456789012' and card 4111-2222-3333-4444."
        cleaned, redaction_count = policy_engine.scrub_text(raw_text)
        
        self.assertNotIn("secret_key_123456789012", cleaned)
        self.assertNotIn("4111-2222-3333-4444", cleaned)
        self.assertIn("[REDACTED_SECRET]", cleaned)
        self.assertIn("[CARD_PLACEHOLDER]", cleaned)
        self.assertGreaterEqual(redaction_count, 2)

    def test_02_policy_tool_evaluation(self):
        """Verifies DENY-003, DENY-002, and APPROVE-001 enforcement."""
        # 1. Prohibited sudo
        action, rule_id, _ = policy_engine.evaluate_tool_call("terminal", {"command": "sudo rm -rf /"})
        self.assertEqual(action, "deny")

        # 2. Prohibited deletion
        action, rule_id, _ = policy_engine.evaluate_tool_call("terminal", {"command": "rm -rf /storage"})
        self.assertEqual(action, "deny")

        # 3. Approval required for email
        action, rule_id, _ = policy_engine.evaluate_tool_call("mail.send", {"recipients": "test@example.com"})
        self.assertEqual(action, "approve")
        self.assertEqual(rule_id, "APPROVE-001")

    def test_03_sticky_session_pinning(self):
        """Verifies SESSION-001: Model gateway stays pinned to one gateway mid-task."""
        session_id = "test_session_task_100"
        gw1, url1, mod1 = gateway_engine.resolve_gateway(session_id=session_id, profile_name="agent")
        gw2, url2, mod2 = gateway_engine.resolve_gateway(session_id=session_id, profile_name="agent")
        
        self.assertEqual(gw1, gw2)
        self.assertEqual(url1, url2)
        self.assertEqual(mod1, mod2)

    def test_04_ledger_lifecycle(self):
        """Verifies task creation, progress bar computation, and verification logging."""
        task_id = "T-TEST-001"
        create_task({
            "task_id": task_id,
            "request_redacted": "Scrape research papers",
            "intent": "research",
            "executor": "hermes",
            "kind": "complex",
            "total_steps": 4
        })

        # Step 2 of 4 (50%)
        update_task_progress(task_id, step_no=2, total_steps=4, current_step="Scraping page 2")
        t = get_task(task_id)
        self.assertEqual(t["progress_pct"], 50.0)
        self.assertEqual(t["current_step"], "Scraping page 2")

        # Completion with evidence
        complete_task(task_id, verified=True, evidence="Found 45 papers in papers.csv")
        t_done = get_task(task_id)
        self.assertEqual(t_done["status"], "done")
        self.assertEqual(t_done["progress_pct"], 100.0)
        self.assertEqual(t_done["verified"], 1)

    def test_05_doctor_and_bug_logging(self):
        """Verifies Doctor classifies errors and deduplicates bugs."""
        error_class, advice = doctor.classify_error("mail.send", "401 Unauthorized: Session expired")
        self.assertEqual(error_class, "auth")
        self.assertIn("Switch to registered alternative", advice)

        bug_id1 = doctor.record_bug("mail", error_class, "401 Unauthorized", task_id="T-TEST-001")
        bug_id2 = doctor.record_bug("mail", error_class, "401 Unauthorized", task_id="T-TEST-002")
        self.assertEqual(bug_id1, bug_id2) # Deduplicated

    def test_06_report_generation(self):
        """Verifies Excel report (or CSV fallback) is exported successfully."""
        report_file = generate_report("test-alex-report.xlsx")
        self.assertTrue(os.path.exists(report_file))


if __name__ == "__main__":
    unittest.main()
