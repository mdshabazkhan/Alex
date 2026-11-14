"""
Hermes Agent Daemon (Port 8642)
Autonomous execution daemon for Project Alex.
Receives tasks via /v1/runs, manages agent loops, and hooks into matrix_bridge.
"""

import os
import time
import uuid
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
from hermes.plugins.matrix_bridge import bridge

app = FastAPI(title="Hermes Agent Daemon", version="0.23.1")

MATRIX_GATEWAY_URL = os.getenv("MATRIX_GATEWAY_URL", "http://matrix:8700/v1")
active_runs: Dict[str, Dict[str, Any]] = {}


@app.get("/", response_class=HTMLResponse)
async def root_dashboard():
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Hermes Agent Daemon — Autonomous Worker</title>
    <style>
        :root {{
            --bg: #090d16;
            --card: #111827;
            --border: #1f293d;
            --purple: #a855f7;
            --green: #22c55e;
            --text: #f8fafc;
            --dim: #94a3b8;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            padding: 30px;
            display: flex;
            justify-content: center;
        }}
        .container {{
            max-width: 800px;
            width: 100%;
        }}
        .header {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .title h1 {{
            font-size: 22px;
            color: var(--purple);
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .title p {{
            font-size: 13px;
            color: var(--dim);
            margin-top: 4px;
        }}
        .status-pill {{
            background: rgba(34, 197, 94, 0.15);
            border: 1px solid rgba(34, 197, 94, 0.4);
            color: var(--green);
            padding: 6px 14px;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--green);
            box-shadow: 0 0 10px var(--green);
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}
        .metric-card {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px;
        }}
        .metric-label {{
            font-size: 11px;
            color: var(--dim);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .metric-val {{
            font-size: 16px;
            font-weight: 600;
            color: #fff;
            margin-top: 6px;
        }}
        .section {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
        }}
        .section h2 {{
            font-size: 15px;
            margin-bottom: 14px;
            color: var(--purple);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        th, td {{
            text-align: left;
            padding: 10px;
            border-bottom: 1px solid var(--border);
        }}
        th {{ color: var(--dim); font-size: 11px; text-transform: uppercase; }}
        code {{
            background: rgba(255, 255, 255, 0.08);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
            color: #38bdf8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">
                <h1>⚡ Hermes Agent Daemon</h1>
                <p>Autonomous Complex Execution Worker for Project Alex</p>
            </div>
            <div class="status-pill">
                <span class="dot"></span> LIVE & STANDBY
            </div>
        </div>

        <div class="grid">
            <div class="metric-card">
                <div class="metric-label">Supervisor Link</div>
                <div class="metric-val">{MATRIX_GATEWAY_URL}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Port & Protocol</div>
                <div class="metric-val">8642 (HTTP / REST API)</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Primary Role</div>
                <div class="metric-val">Multi-step coding, PDF generation, deep research</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Client Dispatch</div>
                <div class="metric-val">Silent backend; posts evidence to Matrix</div>
            </div>
        </div>

        <div class="section">
            <h2>API Endpoints & Status</h2>
            <table>
                <thead>
                    <tr>
                        <th>Method</th>
                        <th>Path</th>
                        <th>Description</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><code>GET</code></td>
                        <td><code>/health</code></td>
                        <td>Operational health check</td>
                        <td><span style="color:var(--green)">Ready</span></td>
                    </tr>
                    <tr>
                        <td><code>GET</code></td>
                        <td><code>/v1/runs</code></td>
                        <td>List active background jobs</td>
                        <td><span style="color:var(--green)">Ready</span></td>
                    </tr>
                    <tr>
                        <td><code>POST</code></td>
                        <td><code>/v1/runs</code></td>
                        <td>Dispatch new autonomous task</td>
                        <td><span style="color:var(--green)">Ready</span></td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>"""


class RunRequest(BaseModel):
    task_id: Optional[str] = None
    prompt: str
    model: Optional[str] = "friday-agent"


@app.get("/health")
async def health():
    return {"status": "operational", "agent": "hermes", "gateway_url": MATRIX_GATEWAY_URL}


@app.get("/v1/runs")
async def list_runs():
    return {"runs": list(active_runs.values())}


@app.post("/v1/runs")
async def create_run(req: RunRequest):
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    task_id = req.task_id or f"T-{int(time.time())}"

    active_runs[run_id] = {
        "run_id": run_id,
        "task_id": task_id,
        "prompt": req.prompt,
        "status": "running",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S")
    }

    # Simulate / execute tool execution with policy bridge check
    allowed, reason = await bridge.pre_tool_call("web.search", {"query": req.prompt[:30]}, task_id=task_id)
    if not allowed:
        active_runs[run_id]["status"] = "blocked"
        raise HTTPException(status_code=403, detail=f"Policy Block: {reason}")

    # Tool completed audit
    await bridge.post_tool_call("web.search", {"query": req.prompt[:30]}, "Result retrieved successfully", 45, task_id=task_id)
    active_runs[run_id]["status"] = "completed"

    return {
        "run_id": run_id,
        "task_id": task_id,
        "status": "completed",
        "result": f"Hermes completed execution for: {req.prompt[:50]}..."
    }


@app.post("/v1/runs/{run_id}/stop")
async def stop_run(run_id: str):
    if run_id in active_runs:
        active_runs[run_id]["status"] = "stopped"
        return {"status": "stopped", "run_id": run_id}
    raise HTTPException(status_code=404, detail="Run not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("hermes.daemon:app", host="0.0.0.0", port=8642)
