"""
Jarvis Dashboard Web Application (Port 8000)
A full interactive chat & voice desktop web application for Project Alex.
Features:
- Live Chat Feed with instant assistant replies
- Browser Voice Recognition (Microphone button for hands-free speech input)
- Voice Audio Speech Synthesis (Spoken audio responses)
- Real-time Active Task Progress Bars
- Recent Tasks History
"""

import os
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Alex — Jarvis Application", version="3.0.0")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "jarvis"}

MATRIX_URL = os.getenv("MATRIX_URL", "http://matrix:8700").rstrip("/")


class TaskSubmit(BaseModel):
    request: str
    intent: Optional[str] = "agent_task"
    executor: Optional[str] = "hermes"
    total_steps: Optional[int] = 3


@app.get("/", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
async def ui_page():
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ALEX — AI Operating Companion</title>
    <style>
        :root {{
            --bg: #090d16;
            --card: #111827;
            --border: #1f293d;
            --cyan: #38bdf8;
            --blue: #6366f1;
            --green: #22c55e;
            --yellow: #eab308;
            --red: #ef4444;
            --text: #f8fafc;
            --dim: #94a3b8;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        header {{
            background: #0f172a;
            border-bottom: 1px solid var(--border);
            padding: 14px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .brand {{ display: flex; align-items: center; gap: 12px; }}
        .brand h1 {{ font-size: 18px; font-weight: 700; color: var(--cyan); letter-spacing: 0.05em; }}
        .brand span {{ font-size: 12px; color: var(--dim); }}
        .status-pill {{
            display: inline-flex; align-items: center; gap: 6px;
            font-size: 11px; padding: 4px 10px; border-radius: 9999px;
            background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); color: var(--green);
            font-weight: 600;
        }}
        .status-dot {{ width: 6px; height: 6px; border-radius: 50%; background: var(--green); }}

        .layout {{
            display: flex;
            flex: 1;
            height: calc(100vh - 65px);
            overflow: hidden;
        }}

        /* Left: Chat & Voice Interface */
        .chat-pane {{
            flex: 1.2;
            display: flex;
            flex-direction: column;
            border-right: 1px solid var(--border);
            background: #0c121e;
        }}
        .chat-messages {{
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }}
        .message {{
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 14px;
            line-height: 1.5;
            word-break: break-word;
        }}
        .message.user {{
            align-self: flex-end;
            background: linear-gradient(135deg, #2563eb, #4f46e5);
            color: #fff;
            border-bottom-right-radius: 2px;
        }}
        .message.alex {{
            align-self: flex-start;
            background: var(--card);
            border: 1px solid var(--border);
            border-bottom-left-radius: 2px;
        }}
        .message .sender {{
            font-size: 10px; font-weight: 700; text-transform: uppercase;
            color: var(--cyan); margin-bottom: 4px;
        }}

        .chat-input-bar {{
            padding: 16px 20px;
            background: #0f172a;
            border-top: 1px solid var(--border);
            display: flex;
            gap: 10px;
            align-items: center;
        }}
        .chat-input {{
            flex: 1;
            background: #1e293b;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px 16px;
            color: #fff;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }}
        .chat-input:focus {{ border-color: var(--cyan); }}
        
        .btn {{
            background: var(--cyan);
            color: #090d16;
            font-weight: 700;
            padding: 12px 18px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            transition: opacity 0.2s;
        }}
        .btn:hover {{ opacity: 0.9; }}
        .btn-mic {{
            background: #1e293b;
            color: var(--text);
            border: 1px solid var(--border);
            padding: 12px 16px;
            font-size: 16px;
        }}
        .btn-mic.listening {{
            background: rgba(239, 68, 68, 0.2);
            border-color: var(--red);
            color: var(--red);
            animation: pulse 1.2s infinite;
        }}
        @keyframes pulse {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
            100% {{ transform: scale(1); }}
        }}

        /* Right: Active Dashboard & Monitor */
        .dash-pane {{
            flex: 1;
            background: var(--bg);
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        .section-header {{
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--dim);
            margin-bottom: 10px;
        }}
        .task-card {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 14px;
            margin-bottom: 10px;
        }}
        .task-card-header {{
            display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;
        }}
        .task-title {{ font-size: 13px; font-weight: 700; color: #fff; }}
        .badge-status {{
            font-size: 10px; font-weight: 700; text-transform: uppercase;
            padding: 2px 8px; border-radius: 4px;
        }}
        .status-running {{ background: rgba(234, 179, 8, 0.15); color: var(--yellow); }}
        .status-done {{ background: rgba(34, 197, 94, 0.15); color: var(--green); }}
        .status-failed {{ background: rgba(239, 68, 68, 0.15); color: var(--red); }}
        
        .progress-track {{
            background: #1e293b;
            height: 8px;
            border-radius: 9999px;
            overflow: hidden;
            margin: 8px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #38bdf8, #818cf8);
            transition: width 0.4s ease;
        }}
        .task-footer {{
            display: flex; justify-content: space-between; font-size: 11px; color: var(--dim);
        }}

        table {{
            width: 100%; border-collapse: collapse; background: var(--card);
            border-radius: 8px; overflow: hidden; border: 1px solid var(--border); font-size: 12px;
        }}
        th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--border); }}
        th {{ background: #0f172a; color: var(--dim); font-size: 11px; text-transform: uppercase; }}
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <h1>ALEX</h1>
            <span>Jarvis Face &bull; Matrix Supervisor &bull; Hermes Autonomous Worker</span>
        </div>
        <div style="display: flex; gap: 10px; align-items: center;">
            <a href="http://127.0.0.1:9119" target="_blank" class="btn" style="background:#7c3aed; color:#fff; padding:5px 12px; font-size:11px; text-decoration:none; display:inline-flex; align-items:center; gap:6px;">⚡ Hermes Agent (:9119)</a>
            <a href="http://127.0.0.1:8700/api/tasks/export.csv" target="_blank" class="btn" style="background:#0284c7; color:#fff; padding:5px 12px; font-size:11px; text-decoration:none;">📊 Export CSV</a>
            <div class="status-pill"><div class="status-dot"></div> Matrix Operational</div>
            <button class="btn" style="background:#1e293b; color:#fff; border:1px solid var(--border); padding:5px 10px; font-size:11px;" onclick="clearHistory()">Clear History</button>
        </div>
    </header>

    <div class="layout">
        <!-- Left: Interactive Chat & Voice Feed -->
        <div class="chat-pane">
            <div class="chat-messages" id="chat-messages">
                <div class="message alex">
                    <div class="sender">Alex Assistant</div>
                    Hello sir! I am online, listening, and ready for your commands. You can type or click the microphone to speak.
                </div>
            </div>

            <div id="voice-indicator" style="font-size: 11px; color: var(--dim); padding: 6px 20px; background: #070b14; border-top: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center;">
                <span>🎙️ <b>Live Conversation Mode</b> &bull; Auto-mic active &bull; 5s silence auto-answers &bull; Say <b>'alex reply'</b> to send now &bull; Say <b>'listen'</b> to interrupt</span>
                <span id="silence-countdown" style="font-weight: 600; color: var(--cyan);"></span>
            </div>

            <div class="chat-input-bar">
                <button class="btn btn-mic" id="mic-btn" onclick="toggleVoice()" title="Microphone Active (Continuous Conversation)">🎙️</button>
                <input type="text" class="chat-input" id="chat-input" placeholder="Speak freely into microphone or type here..." />
                <button class="btn" onclick="sendChatMessage()">Send</button>
            </div>
        </div>

        <!-- Right: Active Monitoring & Progress Bars -->
        <div class="dash-pane">
            <div>
                <div class="section-header">Active Tasks & Progress</div>
                <div id="active-tasks-list">
                    <div style="font-size: 13px; color: var(--dim);">No active tasks running.</div>
                </div>
            </div>

            <div>
                <div class="section-header">Recent Tasks History</div>
                <table>
                    <thead>
                        <tr>
                            <th>Task</th>
                            <th>Status</th>
                            <th>Progress</th>
                            <th>Time</th>
                        </tr>
                    </thead>
                    <tbody id="recent-tasks-body">
                        <tr><td colspan="4" style="color:var(--dim); text-align:center;">No recent tasks</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        // Continuous Voice Conversation Engine
        let recognition = null;
        let isListening = false;
        let isSpeaking = false;
        let autoMicEnabled = true;
        let silenceTimer = null;
        let countdownInterval = null;
        let secondsRemaining = 5;
        let currentTranscript = "";

        function initSpeech() {{
            if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {{
                console.warn('Speech recognition is not supported in this browser.');
                const indicator = document.getElementById('voice-indicator');
                if (indicator) indicator.innerHTML = '<span style="color:var(--yellow)">Microphone: Please use Google Chrome or Safari for continuous voice input.</span>';
                return;
            }}

            const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRec();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'en-US';

            recognition.onstart = () => {{
                isListening = true;
                const micBtn = document.getElementById('mic-btn');
                if (micBtn) micBtn.classList.add('listening');
            }};

            recognition.onend = () => {{
                isListening = false;
                const micBtn = document.getElementById('mic-btn');
                if (micBtn) micBtn.classList.remove('listening');
                if (autoMicEnabled) {{
                    setTimeout(() => {{
                        try {{ recognition.start(); }} catch(e) {{}}
                    }}, 250);
                }}
            }};

            recognition.onresult = (e) => {{
                let interim = '';
                let final = '';

                for (let i = e.resultIndex; i < e.results.length; ++i) {{
                    if (e.results[i].isFinal) {{
                        final += e.results[i][0].transcript;
                    }} else {{
                        interim += e.results[i][0].transcript;
                    }}
                }}

                const spoken = (final || interim).trim();
                const lower = spoken.toLowerCase();

                // BARGE-IN INTERRUPTION: If user says "listen", stop speaking immediately
                if (lower === 'listen' || lower.startsWith('listen ') || lower.endsWith(' listen')) {{
                    stopAllSpeech();
                    clearSilenceCountdown();
                    currentTranscript = "";
                    document.getElementById('chat-input').value = "";
                    const indicator = document.getElementById('silence-countdown');
                    if (indicator) indicator.textContent = 'Listening...';
                    return;
                }}

                if (spoken) {{
                    currentTranscript = spoken;
                    document.getElementById('chat-input').value = spoken;

                    // STOPWORD CUE: "alex reply" responds immediately
                    if (lower.includes('alex reply')) {{
                        clearSilenceCountdown();
                        const cleanSpoken = spoken.replace(/alex reply/gi, '').trim();
                        if (cleanSpoken) {{
                            commitTranscriptAndSend(cleanSpoken);
                        }}
                        return;
                    }}

                    // 5-SECOND SILENCE DETECTION
                    startSilenceCountdown();
                }}
            }};

            try {{
                recognition.start();
            }} catch(err) {{
                console.warn('Auto-mic start deferred until user interaction:', err);
            }}
        }}

        function startSilenceCountdown() {{
            clearSilenceCountdown();
            secondsRemaining = 5;
            const indicator = document.getElementById('silence-countdown');
            if (indicator) indicator.textContent = `Replying in ${{secondsRemaining}}s...`;

            countdownInterval = setInterval(() => {{
                secondsRemaining--;
                if (secondsRemaining > 0) {{
                    if (indicator) indicator.textContent = `Replying in ${{secondsRemaining}}s...`;
                }} else {{
                    clearSilenceCountdown();
                    if (currentTranscript.trim()) {{
                        commitTranscriptAndSend(currentTranscript.trim());
                    }}
                }}
            }}, 1000);
        }}

        function clearSilenceCountdown() {{
            if (countdownInterval) {{
                clearInterval(countdownInterval);
                countdownInterval = null;
            }}
            const indicator = document.getElementById('silence-countdown');
            if (indicator) indicator.textContent = '';
        }}

        function commitTranscriptAndSend(text) {{
            clearSilenceCountdown();
            currentTranscript = "";
            document.getElementById('chat-input').value = "";
            sendChatMessageWithText(text);
        }}

        function toggleVoice() {{
            if (!recognition) {{
                initSpeech();
                return;
            }}
            if (isListening) {{
                autoMicEnabled = false;
                recognition.stop();
            }} else {{
                autoMicEnabled = true;
                try {{ recognition.start(); }} catch(e) {{}}
            }}
        }}

        function stopAllSpeech() {{
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel();
            }}
            isSpeaking = false;
            fetch('/proxy/alex/stop_speaking', {{ method: 'POST' }}).catch(() => {{}});
        }}

        function speakAloud(text) {{
            stopAllSpeech();
            if ('speechSynthesis' in window) {{
                const utter = new SpeechSynthesisUtterance(text);
                utter.rate = 1.05;
                const voices = window.speechSynthesis.getVoices();
                const samantha = voices.find(v => v.name && v.name.includes('Samantha'));
                if (samantha) utter.voice = samantha;

                isSpeaking = true;
                utter.onstart = () => {{ isSpeaking = true; }};
                utter.onend = () => {{
                    isSpeaking = false;
                    if (autoMicEnabled && !isListening) {{
                        try {{ recognition.start(); }} catch(e) {{}}
                    }}
                }};
                utter.onerror = () => {{ isSpeaking = false; }};
                window.speechSynthesis.speak(utter);
            }}
        }}

        function appendMessage(sender, text, isUser = false) {{
            const container = document.getElementById('chat-messages');
            const div = document.createElement('div');
            div.className = `message ${{isUser ? 'user' : 'alex'}}`;
            div.innerHTML = `<div class="sender">${{sender}}</div>${{text}}`;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }}

        async function sendChatMessageWithText(text) {{
            if (!text) return;
            appendMessage('You', text, true);

            try {{
                const res = await fetch('/proxy/alex/chat', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ utterance: text, session_id: 'default' }})
                }});
                const data = await res.json();
                const reply = data.reply || "Understood, sir.";
                appendMessage('Alex', reply);
                speakAloud(reply);
                fetchDashboard();
            }} catch (err) {{
                appendMessage('Alex', `Error connecting to Matrix: ${{err.message}}`);
            }}
        }}

        async function sendChatMessage() {{
            const input = document.getElementById('chat-input');
            const text = input.value.trim();
            if (!text) return;
            input.value = '';
            clearSilenceCountdown();
            currentTranscript = "";
            sendChatMessageWithText(text);
        }}

        async function pollTask(taskId) {{
            let attempts = 0;
            const timer = setInterval(async () => {{
                attempts++;
                try {{
                    const res = await fetch(`/proxy/tasks/progress/${{taskId}}`);
                    const data = await res.json();
                    
                    if (data.status === 'done' || data.status === 'failed') {{
                        clearInterval(timer);
                        const resultText = data.evidence || (data.status === 'done' ? 'Task completed successfully.' : 'Task failed.');
                        appendMessage('Alex', resultText);
                        speakAloud(resultText);
                        fetchDashboard();
                    }}
                }} catch (e) {{}}

                if (attempts > 30) clearInterval(timer);
            }}, 500);
        }}

        async function fetchDashboard() {{
            try {{
                const res = await fetch('/proxy/tasks/recent?limit=10');
                const data = await res.json();
                const tasks = data.tasks || [];

                const active = tasks.filter(t => t.status === 'running' || t.status === 'pending_approval' || t.status === 'paused');
                const recent = tasks.filter(t => t.status === 'done' || t.status === 'failed' || t.status === 'stopped');

                const activeContainer = document.getElementById('active-tasks-list');
                if (active.length === 0) {{
                    activeContainer.innerHTML = '<div style="font-size: 13px; color: var(--dim);">No active tasks running.</div>';
                }} else {{
                    activeContainer.innerHTML = active.map(t => `
                        <div class="task-card">
                            <div class="task-card-header">
                                <span class="task-title">${{t.task_id}}</span>
                                <span class="badge-status status-${{t.status}}">${{t.status}}</span>
                            </div>
                            <div style="font-size: 12px; margin-bottom: 4px;">${{t.request_redacted}}</div>
                            <div class="progress-track">
                                <div class="progress-fill" style="width: ${{t.progress_pct}}%"></div>
                            </div>
                            <div class="task-footer">
                                <span>${{t.current_step || 'Processing...'}}</span>
                                <span>${{t.progress_pct}}%</span>
                            </div>
                        </div>
                    `).join('');
                }}

                const tbody = document.getElementById('recent-tasks-body');
                if (recent.length === 0) {{
                    tbody.innerHTML = '<tr><td colspan="4" style="color:var(--dim); text-align:center;">No recent tasks</td></tr>';
                }} else {{
                    tbody.innerHTML = recent.map(t => `
                        <tr>
                            <td><strong>${{t.task_id}}</strong><br><span style="color:var(--dim);">${{t.request_redacted.substring(0, 30)}}</span></td>
                            <td><span class="badge-status status-${{t.status}}">${{t.status}}</span></td>
                            <td>${{t.progress_pct}}%</td>
                            <td style="color:var(--dim);">${{(t.finished_at || t.created_at || '').substring(11, 19)}}</td>
                        </tr>
                    `).join('');
                }}
            }} catch (err) {{}}
        }}

        async function clearHistory() {{
            await fetch('/proxy/tasks/clear', {{ method: 'POST' }});
            fetchDashboard();
        }}

        document.getElementById('chat-input').addEventListener('keydown', (e) => {{
            if (e.key === 'Enter') sendChatMessage();
        }});

        fetchDashboard();
        setInterval(fetchDashboard, 1500);

        // Auto-start continuous conversation microphone on launch
        window.addEventListener('DOMContentLoaded', initSpeech);
        window.addEventListener('load', initSpeech);
        document.body.addEventListener('click', () => {{
            if (!isListening) initSpeech();
        }}, {{ once: true }});
        setTimeout(initSpeech, 800);
    </script>
</body>
</html>"""


@app.get("/proxy/tasks/recent")
async def proxy_recent_tasks(limit: int = 15):
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{MATRIX_URL}/api/tasks/recent", params={"limit": limit})
        return resp.json()


@app.get("/proxy/tasks/progress/{task_id}")
async def proxy_task_progress(task_id: str):
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{MATRIX_URL}/api/tasks/{task_id}/progress")
        return resp.json()


@app.post("/proxy/tasks")
async def proxy_submit_task(req: TaskSubmit):
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(f"{MATRIX_URL}/api/tasks", json=req.dict())
        return resp.json()


@app.post("/proxy/alex/chat")
async def proxy_alex_chat(req: Request):
    body = await req.json()
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{MATRIX_URL}/api/alex/chat", json=body)
        return resp.json()


@app.post("/proxy/alex/stop_speaking")
async def proxy_stop_speaking():
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(f"{MATRIX_URL}/api/alex/stop_speaking")
        return resp.json()


@app.post("/proxy/tasks/clear")
@app.delete("/proxy/tasks/clear")
async def proxy_clear_tasks():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(f"{MATRIX_URL}/api/tasks/clear")
            return resp.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("jarvis.web:app", host="0.0.0.0", port=8000)
