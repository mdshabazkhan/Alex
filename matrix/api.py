"""
Matrix API Service (Port 8700)
Unified supervisory API and model gateway for Alex:
Alex (Face & Quick Hands) × Matrix (Observer & Supervisor) × Hermes (Complex Worker).
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, Request, Header, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from matrix.store import (
    create_task,
    get_task,
    get_recent_tasks,
    update_task_progress,
    complete_task
)
from matrix.gateway import gateway_engine
from matrix.policy import engine as policy_engine
from matrix.reports import export_tasks_csv, generate_report
from matrix.worker import execute_task_background

app = FastAPI(title="Alex Matrix Supervision & Model Gateway", version="3.0.0")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "matrix"}


class TaskCreateRequest(BaseModel):
    request: str
    intent: Optional[str] = "general"
    executor: Optional[str] = "hermes"
    kind: Optional[str] = "complex"
    total_steps: Optional[int] = 3
    budget_tokens: Optional[int] = 120000


class ProgressUpdateRequest(BaseModel):
    step_number: int
    total_steps: int
    current_step: str
    status: Optional[str] = "running"


class CompleteTaskRequest(BaseModel):
    verified: bool = True
    evidence: str = ""
    status: Optional[str] = "done"


def render_progress_bar(pct: float, length: int = 24) -> str:
    filled = int(round(length * (pct / 100.0)))
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {pct:.1f}%"


# ==============================================================================
# Model Gateway Endpoints (/v1/*)
# ==============================================================================

@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {"id": "friday-agent", "object": "model", "owned_by": "matrix"},
            {"id": "friday-fast", "object": "model", "owned_by": "matrix"},
            {"id": "friday-coding", "object": "model", "owned_by": "matrix"},
            {"id": "auto", "object": "model", "owned_by": "matrix"}
        ]
    }


@app.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    x_friday_session: Optional[str] = Header(None, alias="X-Friday-Session")
):
    try:
        body = await request.json()
        session_id = x_friday_session or body.get("session_id") or "openjarvis_app"
        messages = body.get("messages", [])
        stream = body.get("stream", False)

        # Extract last user message
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user" and m.get("content"):
                last_user_msg = m.get("content").strip()
                break

        # Check if this is an internal backend model call (e.g. from Hermes or tool eval)
        is_internal = any("hermes" in str(m.get("content", "")).lower() for m in messages if m.get("role") == "system")

        if last_user_msg and not is_internal:
            from matrix.alex_dialogue import process_utterance
            alex_res = await process_utterance(last_user_msg, session_id=session_id)
            reply_text = alex_res.get("reply", "Understood, sir.")

            if stream:
                from fastapi.responses import StreamingResponse
                import json
                import time
                async def stream_generator():
                    chunk_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
                    chunk = {
                        "id": chunk_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": "friday-agent",
                        "choices": [{"index": 0, "delta": {"role": "assistant", "content": reply_text}, "finish_reason": None}]
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                    stop_chunk = {
                        "id": chunk_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": "friday-agent",
                        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
                    }
                    yield f"data: {json.dumps(stop_chunk)}\n\n"
                    yield "data: [DONE]\n\n"

                return StreamingResponse(stream_generator(), media_type="text/event-stream")

            import time
            return {
                "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "friday-agent",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": reply_text
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": len(last_user_msg.split()),
                    "completion_tokens": len(reply_text.split()),
                    "total_tokens": len(last_user_msg.split()) + len(reply_text.split())
                }
            }

        task_id = body.get("task_id")
        result = await gateway_engine.chat_completions(body, session_id=session_id, task_id=task_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class AlexChatRequest(BaseModel):
    utterance: str
    session_id: Optional[str] = "default"


@app.post("/api/alex/chat")
async def alex_chat_endpoint(req: AlexChatRequest):
    try:
        from matrix.alex_dialogue import process_utterance
        result = await process_utterance(req.utterance, session_id=req.session_id)
        return result
    except Exception as e:
        return {"reply": f"Understood, sir: {req.utterance}", "error": str(e)}


@app.post("/api/alex/stop_speaking")
async def stop_speaking_endpoint():
    try:
        import subprocess
        subprocess.run(["pkill", "say"], capture_output=True)
    except Exception:
        pass
    return {"status": "silenced"}


# ==============================================================================
# Task Management & UI Endpoints (/api/tasks/*)
# ==============================================================================

@app.post("/api/tasks")
async def api_create_task(req: TaskCreateRequest):
    cleaned_request, _ = policy_engine.scrub_text(req.request)
    task_id = f"T-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    gw_name, _, model = gateway_engine.resolve_gateway(session_id=task_id, profile_name="agent")

    create_task({
        "task_id": task_id,
        "request_redacted": cleaned_request,
        "intent": req.intent,
        "executor": req.executor,
        "kind": req.kind,
        "status": "running",
        "progress_pct": 0.0,
        "current_step": "Task Accepted",
        "total_steps": req.total_steps,
        "step_number": 0,
        "budget_tokens": req.budget_tokens,
        "pinned_gateway": gw_name,
        "pinned_model": model
    })

    # Execute in background via Matrix worker
    import asyncio
    asyncio.create_task(execute_task_background(task_id, cleaned_request, req.intent))

    return {
        "task_id": task_id,
        "status": "running",
        "progress_bar": render_progress_bar(0.0),
        "pinned_gateway": gw_name,
        "pinned_model": model
    }


@app.get("/api/tasks/recent")
async def api_get_recent_tasks(limit: int = 15):
    tasks = get_recent_tasks(limit=limit)
    for t in tasks:
        pct = float(t.get("progress_pct") or 0.0)
        t["progress_bar"] = render_progress_bar(pct)
    return {"tasks": tasks}


@app.get("/api/tasks/{task_id}/progress")
async def api_get_task_progress(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    pct = float(task.get("progress_pct") or 0.0)
    return {
        "task_id": task_id,
        "status": task.get("status", "running"),
        "step_number": task.get("step_number", 0),
        "total_steps": task.get("total_steps", 1),
        "current_step": task.get("current_step", ""),
        "progress_pct": pct,
        "progress_bar": render_progress_bar(pct),
        "pinned_gateway": task.get("pinned_gateway", ""),
        "pinned_model": task.get("pinned_model", "")
    }


# ==============================================================================
# CSV Export Endpoints (User Requested)
# ==============================================================================

@app.get("/api/tasks/export.csv")
@app.get("/api/tasks/export/csv")
async def api_export_csv():
    csv_data = export_tasks_csv()
    filename = f"alex_tasks_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Cache-Control": "no-cache"
        }
    )


@app.post("/api/tasks/clear")
@app.delete("/api/tasks/clear")
async def api_clear_tasks():
    from store import clear_all_tasks
    clear_all_tasks()
    return {"ok": True, "message": "All Matrix tasks and activity logs have been cleared."}


# ==============================================================================
# Alex Interactive Console & Web UI (Port 8700)
# ==============================================================================

@app.get("/", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
async def api_ui():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alex — Voice & Command Companion</title>
    <style>
        :root {
            --bg: #090d16;
            --surface: #111827;
            --surface-hover: #1f2937;
            --border: #374151;
            --primary: #3b82f6;
            --accent: #ec4899;
            --text: #f9fafb;
            --text-dim: #9ca3af;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: var(--bg); color: var(--text); padding: 24px; min-height: 100vh; }
        .container { max-width: 960px; margin: 0 auto; }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 18px; margin-bottom: 24px; }
        .title-group h1 { font-size: 22px; font-weight: 700; letter-spacing: 0.5px; }
        .title-group p { font-size: 13px; color: var(--text-dim); margin-top: 4px; }
        .badges { display: flex; gap: 8px; align-items: center; }
        .badge { font-size: 11px; padding: 4px 10px; border-radius: 9999px; font-weight: 600; text-transform: uppercase; }
        .badge-green { background: rgba(16, 185, 129, 0.2); color: var(--success); border: 1px solid rgba(16, 185, 129, 0.3); }
        .badge-pink { background: rgba(236, 72, 153, 0.2); color: var(--accent); border: 1px solid rgba(236, 72, 153, 0.3); }
        .btn-export { background: #1e293b; color: #38bdf8; border: 1px solid #0284c7; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600; text-decoration: none; display: inline-flex; align-items: center; gap: 6px; }
        .btn-export:hover { background: #0369a1; color: #fff; }
        .chat-section { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 18px; margin-bottom: 24px; }
        .chat-box { height: 260px; overflow-y: auto; background: #06090f; border: 1px solid var(--border); border-radius: 8px; padding: 14px; margin-bottom: 14px; display: flex; flex-direction: column; gap: 10px; }
        .chat-msg { padding: 10px 14px; border-radius: 8px; font-size: 14px; max-width: 80%; line-height: 1.4; }
        .msg-user { background: #1e3a8a; color: #fff; align-self: flex-end; }
        .msg-alex { background: #1e293b; color: #e2e8f0; border-left: 3px solid var(--accent); align-self: flex-start; }
        .input-bar { display: flex; gap: 10px; }
        .input-bar input { flex: 1; background: #06090f; border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px; color: var(--text); font-size: 14px; outline: none; }
        .input-bar input:focus { border-color: var(--primary); }
        .btn { padding: 10px 18px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; }
        .btn-mic { background: #374151; color: #fff; font-size: 16px; width: 44px; display: flex; align-items: center; justify-content: center; }
        .btn-mic.listening { background: var(--accent); animation: pulse 1s infinite alternate; }
        @keyframes pulse { from { opacity: 0.7; } to { opacity: 1; } }
        .btn-send { background: var(--primary); color: #fff; }
        .task-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px; margin-bottom: 12px; }
        .task-header { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 8px; }
        .task-id { font-family: monospace; color: #38bdf8; }
        .progress-container { background: #06090f; border-radius: 4px; height: 8px; overflow: hidden; margin: 8px 0; }
        .progress-bar { background: var(--primary); height: 100%; transition: width 0.3s ease; }
        .task-meta { display: flex; justify-content: space-between; font-size: 11px; color: var(--text-dim); }
        .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .section-title { font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; color: var(--text-dim); }
        table { width: 100%; border-collapse: collapse; background: var(--surface); border-radius: 8px; overflow: hidden; font-size: 13px; }
        th, td { padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--border); }
        th { background: #0f172a; color: var(--text-dim); font-size: 11px; text-transform: uppercase; }
        .status-done { color: var(--success); font-weight: 600; }
        .status-running { color: #38bdf8; font-weight: 600; }
        .status-failed { color: var(--error); font-weight: 600; }
        .status-paused { color: var(--warning); font-weight: 600; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title-group">
                <h1>ALEX — VOICE & COMMAND CONSOLE</h1>
                <p>Alex (Voice & Hands) &bull; Matrix (Observer & Supervisor) &bull; Hermes (Autonomous Worker)</p>
            </div>
            <div class="badges">
                <span class="badge badge-pink">Voice: Samantha (Female)</span>
                <span class="badge badge-green" id="matrix-status">Matrix: Connected</span>
                <a href="/api/tasks/export.csv" class="btn-export">📥 Export CSV</a>
            </div>
        </div>

        <div class="chat-section">
            <div class="chat-box" id="chat-stream">
                <div class="chat-msg msg-alex">Hello! I am Alex. I am online, listening, and ready for your commands. You can click the 🎙️ mic button or type a task below.</div>
            </div>
            <div class="input-bar">
                <button class="btn btn-mic" id="mic-btn" title="Click to speak (Voice Recognition)">🎙️</button>
                <input type="text" id="chat-input" placeholder="Give Alex a command (e.g. 'open Spotify', 'play bohemian rhapsody', 'research competitors and take screenshot')..." autofocus>
                <button class="btn btn-send" id="send-btn">Dispatch</button>
            </div>
        </div>

        <div class="section-header">
            <div class="section-title">Active Running Tasks</div>
        </div>
        <div id="active-tasks-list">
            <div style="color: var(--text-dim); font-size: 13px; margin-bottom: 20px;">No active tasks running.</div>
        </div>

        <div class="section-header" style="margin-top: 24px;">
            <div class="section-title">Task History & Ledger</div>
            <a href="/api/tasks/export.csv" style="color: #38bdf8; font-size: 12px; text-decoration: none;">Download CSV Record &rarr;</a>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Task ID</th>
                    <th>Task Request</th>
                    <th>Status</th>
                    <th>Executor</th>
                    <th>Progress</th>
                    <th>Time</th>
                </tr>
            </thead>
            <tbody id="recent-tasks-body">
                <tr><td colspan="6" style="text-align: center; color: var(--text-dim);">Loading ledger...</td></tr>
            </tbody>
        </table>
    </div>

    <script>
        const chatStream = document.getElementById('chat-stream');
        const chatInput = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-btn');
        const micBtn = document.getElementById('mic-btn');

        function appendMessage(role, text) {
            const div = document.createElement('div');
            div.className = `chat-msg ${role === 'user' ? 'msg-user' : 'msg-alex'}`;
            div.textContent = text;
            chatStream.appendChild(div);
            chatStream.scrollTop = chatStream.scrollHeight;
        }

        // Native Browser Voice Synthesis with Female Voice Fallback
        function speakBrowser(text) {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                const utter = new SpeechSynthesisUtterance(text);
                const voices = window.speechSynthesis.getVoices();
                const femaleVoice = voices.find(v => v.name.includes('Samantha') || v.name.includes('Victoria') || v.name.includes('Karen') || v.name.includes('Female'));
                if (femaleVoice) utter.voice = femaleVoice;
                utter.rate = 1.05;
                window.speechSynthesis.speak(utter);
            }
        }

        async function submitTask(text) {
            const val = text || chatInput.value.trim();
            if (!val) return;
            chatInput.value = '';
            appendMessage('user', val);

            try {
                const res = await fetch('/api/tasks', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        request: val,
                        intent: 'command',
                        executor: 'hermes',
                        total_steps: 3
                    })
                });
                const data = await res.json();
                fetchStatus();
            } catch (err) {
                appendMessage('alex', 'Error dispatching task: ' + err.message);
            }
        }

        sendBtn.addEventListener('click', () => submitTask());
        chatInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') submitTask(); });

        // Speech Recognition (Microphone)
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';

            recognition.onstart = () => { micBtn.classList.add('listening'); };
            recognition.onend = () => { micBtn.classList.remove('listening'); };
            recognition.onresult = (e) => {
                const transcript = e.results[0][0].transcript;
                submitTask(transcript);
            };
            micBtn.addEventListener('click', () => {
                try { recognition.start(); } catch (e) { recognition.stop(); }
            });
        } else {
            micBtn.style.display = 'none';
        }

        // Live Status Polling
        let lastTaskStatus = {};
        async function fetchStatus() {
            try {
                const res = await fetch('/api/tasks/recent?limit=15');
                const data = await res.json();
                const tasks = data.tasks || [];

                const active = tasks.filter(t => t.status === 'running' || t.status === 'paused');
                const recent = tasks.filter(t => t.status === 'done' || t.status === 'failed');

                // Check for newly completed tasks to show reply in chat
                tasks.forEach(t => {
                    if (lastTaskStatus[t.task_id] === 'running' && t.status === 'done') {
                        if (t.evidence) {
                            appendMessage('alex', t.evidence);
                            speakBrowser(t.evidence);
                        }
                    }
                    lastTaskStatus[t.task_id] = t.status;
                });

                // Active Tasks List
                const activeContainer = document.getElementById('active-tasks-list');
                if (active.length === 0) {
                    activeContainer.innerHTML = '<div style="color: var(--text-dim); font-size: 13px; margin-bottom: 16px;">No active tasks running.</div>';
                } else {
                    activeContainer.innerHTML = active.map(t => `
                        <div class="task-card">
                            <div class="task-header">
                                <span class="task-id">${t.task_id} &bull; ${t.intent}</span>
                                <span class="status-${t.status}">${t.status.toUpperCase()}</span>
                            </div>
                            <div style="font-size: 13px; margin-bottom: 6px;">${t.request_redacted}</div>
                            <div class="progress-container">
                                <div class="progress-bar" style="width: ${t.progress_pct}%"></div>
                            </div>
                            <div class="task-meta">
                                <span><strong>Step:</strong> ${t.current_step || 'Processing...'}</span>
                                <span>${t.progress_pct}% (${t.step_number || 0}/${t.total_steps || 1})</span>
                            </div>
                        </div>
                    `).join('');
                }

                // Recent Table
                const tbody = document.getElementById('recent-tasks-body');
                if (recent.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-dim);">No prior tasks completed yet.</td></tr>';
                } else {
                    tbody.innerHTML = recent.map(t => `
                        <tr>
                            <td><strong style="color: #38bdf8;">${t.task_id}</strong></td>
                            <td>${(t.request_redacted || '').substring(0, 45)}</td>
                            <td><span class="status-${t.status}">${t.status}</span></td>
                            <td style="text-transform: capitalize;">${t.executor || 'alex'}</td>
                            <td>${t.progress_pct}%</td>
                            <td style="color: var(--text-dim);">${(t.finished_at || t.created_at || '').substring(11, 19)}</td>
                        </tr>
                    `).join('');
                }
            } catch (err) {
                document.getElementById('matrix-status').textContent = 'Matrix: Disconnected';
            }
        }

        fetchStatus();
        setInterval(fetchStatus, 1000);
    </script>
</body>
</html>"""


@app.post("/api/reports/generate")
async def api_generate_report():
    report_file = generate_report()
    return {"status": "success", "report_path": report_file}


@app.get("/api/status")
async def api_status():
    recent = get_recent_tasks(limit=5)
    return {
        "system": "Alex (Face & UI × Matrix × Hermes)",
        "matrix_status": "operational",
        "voice": "Samantha (Female)",
        "gateways": list(gateway_engine.gateways.keys()),
        "active_sticky_sessions": len(gateway_engine.session_pins),
        "recent_tasks_count": len(recent)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("matrix.api:app", host="127.0.0.1", port=8700, reload=False)
