"""
Jarvis Client for Matrix Supervisor
Communicates with Matrix on 127.0.0.1:8700 for task submission, progress updates, and telemetry.
"""

import httpx
from typing import Dict, Any, List, Optional


class MatrixClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8700"):
        self.base_url = base_url.rstrip("/")

    async def submit_task(self, request_text: str, intent: str = "general", executor: str = "hermes", total_steps: int = 1) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/tasks",
                json={
                    "request": request_text,
                    "intent": intent,
                    "executor": executor,
                    "total_steps": total_steps
                }
            )
            resp.raise_for_status()
            return resp.json()

    async def get_task_progress(self, task_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{self.base_url}/api/tasks/{task_id}/progress")
            resp.raise_for_status()
            return resp.json()

    async def get_recent_tasks(self, limit: int = 15) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{self.base_url}/api/tasks/recent", params={"limit": limit})
            resp.raise_for_status()
            data = resp.json()
            return data.get("tasks", [])

    async def update_progress(self, task_id: str, step_no: int, total_steps: int, current_step: str, status: str = "running") -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/tasks/{task_id}/update_progress",
                json={
                    "step_number": step_no,
                    "total_steps": total_steps,
                    "current_step": current_step,
                    "status": status
                }
            )
            resp.raise_for_status()
            return resp.json()

    async def complete_task(self, task_id: str, verified: bool = True, evidence: str = "") -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/tasks/{task_id}/complete",
                json={
                    "verified": verified,
                    "evidence": evidence,
                    "status": "done"
                }
            )
            resp.raise_for_status()
            return resp.json()

    async def check_health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url}/api/status")
                return resp.status_code == 200
        except Exception:
            return False


client = MatrixClient()
