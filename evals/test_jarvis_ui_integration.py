"""
Integration Test: Jarvis UI, Fast-Path Reflexes, and Matrix Supervision API
"""

import unittest
import asyncio
from fastapi.testclient import TestClient
from matrix.api import app
from matrix.store import get_recent_tasks, get_task
from jarvis.reflex import reflex_engine


class TestJarvisUIIntegration(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_01_matrix_health_and_status(self):
        resp = self.client.get("/api/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["matrix_status"], "operational")
        self.assertIn("freellmapi", data["gateways"])

    def test_02_task_submission_and_progress_bar(self):
        # 1. Submit complex task via API
        resp = self.client.post("/api/tasks", json={
            "request": "Analyze Apple Silicon M1 Pro memory usage",
            "intent": "analysis",
            "executor": "hermes",
            "total_steps": 5
        })
        self.assertEqual(resp.status_code, 200)
        t_data = resp.json()
        task_id = t_data["task_id"]
        self.assertIn("0.0%", t_data["progress_bar"])

        # 2. Update progress to step 3 (60%)
        upd = self.client.post(f"/api/tasks/{task_id}/update_progress", json={
            "step_number": 3,
            "total_steps": 5,
            "current_step": "Measuring swap memory pressure",
            "status": "running"
        })
        self.assertEqual(upd.status_code, 200)
        self.assertEqual(upd.json()["progress_pct"], 60.0)
        self.assertIn("60.0%", upd.json()["progress_bar"])

        # 3. Check /api/tasks/recent for Jarvis UI display
        rec = self.client.get("/api/tasks/recent?limit=5")
        self.assertEqual(rec.status_code, 200)
        tasks = rec.json()["tasks"]
        matching = [t for t in tasks if t["task_id"] == task_id]
        self.assertTrue(len(matching) > 0)
        self.assertEqual(matching[0]["progress_pct"], 60.0)

        # 4. Mark complete with PEVG evidence
        comp = self.client.post(f"/api/tasks/{task_id}/complete", json={
            "verified": True,
            "evidence": "Memory pressure green, 0 GB swap used",
            "status": "done"
        })
        self.assertEqual(comp.status_code, 200)
        self.assertEqual(comp.json()["verified"], True)
        self.assertIn("100.0%", comp.json()["progress_bar"])

    def test_03_reflex_fast_path_matching(self):
        """Verifies deterministic fast path matches pattern correctly without touching hardware."""
        res = reflex_engine.match("turn off wifi")
        self.assertIsNotNone(res)
        self.assertEqual(res.get("action"), "toggle_wifi")

        # Also verify execute=False simulation returns ok without touching hardware
        sim = reflex_engine.try_execute("turn off wifi", execute=False)
        self.assertTrue(sim.get("ok"))
        self.assertTrue(sim.get("simulated"))


if __name__ == "__main__":
    unittest.main()
