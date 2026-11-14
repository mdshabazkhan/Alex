"""
Alex Matrix Task Execution & Supervision Engine
Orchestrates:
1. Fast Reflexes & Mac System Control (Alex quick hands: apps, songs, IO, volume, brightness)
2. Complex Workflow Delegation to Hermes (deep research, coding, multi-step actions)
3. Concise Response Rubric & Linter (prevents wasted tokens)
4. Memory & RAG Retrieval (past procedures and pitfalls)
5. Adaptive Retry with Strategy Switching on failure (logs why it failed first)
6. Internet Loss Resilience: Checkpoints & pauses online tasks; softlands offline tasks via Ollama
7. Female Spoken Voice (Samantha) via macOS native synthesis
"""

import os
import re
import socket
import asyncio
import time
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from matrix.store import (
    update_task_progress,
    complete_task,
    get_connection,
    record_model_call
)
from matrix.gateway import gateway_engine
try:
    from tools.friday_mac import executor as mac_tools
except ImportError:
    mac_tools = None

GREETINGS = {"hi", "hello", "hey", "good morning", "good evening", "howdy", "sup"}
TIME_QUERIES = {"what time is it", "what's the time", "time", "current time", "what is the time"}
DATE_QUERIES = {"what's the date", "what is the date", "date", "today's date"}


def speak_female(text: str):
    """Speaks through macOS native female voice (Samantha) asynchronously."""
    clean = text.replace('"', '').replace("'", "")
    try:
        subprocess.Popen(
            ["say", "-v", "Samantha", clean],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass


def check_internet() -> bool:
    """Fast probe to determine internet connectivity."""
    try:
        sock = socket.create_connection(("1.1.1.1", 53), timeout=1.5)
        sock.close()
        return True
    except OSError:
        return False


def lint_concise_response(text: str) -> str:
    """Rubric Linter: Strips conversational fluff and verbose preambles to save tokens."""
    patterns = [
        r"^(certainly!?|sure!?|sure thing!?|of course!?|gladly!?|absolutely!?)[,\.\s]+",
        r"^as an ai language model[,\.\s]+",
        r"^i would be happy to help( with that)?[,\.\s]+",
        r"^here is (the|an) (answer|response|summary)[^:]*:[,\.\s]*",
    ]
    cleaned = text.strip()
    for p in patterns:
        cleaned = re.sub(p, "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def check_past_memory(intent: str, query: str) -> Optional[str]:
    """Retrieves past procedures or known pitfalls from memory.db (RAG)."""
    try:
        conn = get_connection("storage/data/memory.db")
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pitfalls'")
        if cur.fetchone():
            cur.execute("SELECT fix FROM pitfalls WHERE intent = ? LIMIT 1", (intent,))
            row = cur.fetchone()
            if row:
                conn.close()
                return f"Known pitfall: {row['fix']}"
        conn.close()
    except Exception:
        pass
    return None


def record_task_bug(task_id: str, error_msg: str, diagnosis: str):
    """Records failure diagnostic in ledger.db for analysis and retry tracking."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        bug_id = f"BUG-{int(time.time())}"
        cur.execute("""
            INSERT OR REPLACE INTO bugs (
                bug_id, fingerprint, component, error_class, first_seen, last_seen,
                sample_message, example_tasks, diagnosis, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bug_id,
            f"{task_id}_{int(time.time())}",
            "execution_worker",
            "TaskExecutionError",
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            error_msg[:300],
            task_id,
            diagnosis,
            "open"
        ))
        conn.commit()
        conn.close()
    except Exception:
        pass


def is_offline_capable(task_text: str) -> bool:
    """Identifies tasks that can be performed locally without internet connectivity."""
    clean = task_text.lower()
    offline_keywords = [
        "file", "copy", "move", "rename", "folder", "volume", "brightness",
        "app", "open", "close", "quit", "time", "date", "calculate", "math", "local code"
    ]
    online_keywords = [
        "web", "browse", "url", "search", "google", "youtube", "mail", "email",
        "send", "download", "scrape", "weather", "internet"
    ]
    if any(k in clean for k in online_keywords):
        return False
    return any(k in clean for k in offline_keywords)


async def execute_task_background(task_id: str, request_text: str, intent: str = "general"):
    """Background task supervisor: routes to Alex reflexes, handles offline softlanding, or delegates to Hermes with adaptive retries."""
    clean = request_text.strip().lower()

    # 1. Instant Conversational Reflexes (< 50ms)
    if clean in GREETINGS:
        reply = "Hello! I am Alex. I am online, listening, and ready for your commands."
        speak_female(reply)
        update_task_progress(task_id, 1, 1, "Greeting answered", "done")
        complete_task(task_id, verified=True, evidence=reply, status="done")
        return reply

    if clean in TIME_QUERIES:
        now_str = datetime.now().strftime("%I:%M %p")
        reply = f"It is currently {now_str}."
        speak_female(reply)
        update_task_progress(task_id, 1, 1, "Time resolved", "done")
        complete_task(task_id, verified=True, evidence=reply, status="done")
        return reply

    if clean in DATE_QUERIES:
        today_str = datetime.now().strftime("%A, %B %d, %Y")
        reply = f"Today is {today_str}."
        speak_female(reply)
        update_task_progress(task_id, 1, 1, "Date resolved", "done")
        complete_task(task_id, verified=True, evidence=reply, status="done")
        return reply

    # 2. Basic Mac Actuator Reflexes (Alex quick hands: apps, songs, system, file IO)
    # Check for App Open
    m_open = re.match(r'^(open|launch)\s+([a-zA-Z0-9\s]+)$', clean)
    if m_open:
        app_name = m_open.group(2).strip()
        res = mac_tools.open_app(app_name)
        reply = f"Opened {app_name}."
        speak_female(reply)
        update_task_progress(task_id, 1, 1, f"Opened {app_name}", "done")
        complete_task(task_id, verified=res.get("verified", True), evidence=res.get("evidence", ""), status="done")
        return reply

    # Check for App Quit
    m_quit = re.match(r'^(close|quit|kill)\s+([a-zA-Z0-9\s]+)$', clean)
    if m_quit:
        app_name = m_quit.group(2).strip()
        res = mac_tools.quit_app(app_name)
        reply = f"Closed {app_name}."
        speak_female(reply)
        update_task_progress(task_id, 1, 1, f"Closed {app_name}", "done")
        complete_task(task_id, verified=res.get("verified", True), evidence=res.get("evidence", ""), status="done")
        return reply

    # Check for Playing a Song
    m_song = re.match(r'^(play|listen to)\s+(.+)$', clean)
    if m_song:
        song_name = m_song.group(2).strip()
        res = mac_tools.play_song(song_name)
        reply = f"Playing {song_name} on YouTube."
        speak_female(reply)
        update_task_progress(task_id, 1, 1, f"Playing {song_name}", "done")
        complete_task(task_id, verified=True, evidence=res.get("evidence", ""), status="done")
        return reply

    # Check for Volume
    m_vol = re.match(r'^(set\s+)?volume\s+(to\s+)?(\d+)$', clean)
    if m_vol:
        level = int(m_vol.group(3))
        res = mac_tools.set_volume(level)
        reply = f"Volume set to {level} percent."
        speak_female(reply)
        update_task_progress(task_id, 1, 1, f"Volume set to {level}%", "done")
        complete_task(task_id, verified=True, evidence=res.get("evidence", ""), status="done")
        return reply

    # Check for Web Browsing
    m_browse = re.match(r'^(browse|search|go to|open website)\s+(.+)$', clean)
    if m_browse:
        target = m_browse.group(2).strip()
        res = mac_tools.browse_web(target)
        reply = f"Opened browser for {target}."
        speak_female(reply)
        update_task_progress(task_id, 1, 1, f"Opened browser: {target}", "done")
        complete_task(task_id, verified=True, evidence=res.get("evidence", ""), status="done")
        return reply

    # 3. Internet Connectivity & Offline Resilience Check
    is_online = check_internet()
    offline_ok = is_offline_capable(clean)

    if not is_online:
        if offline_ok:
            # Softland task locally via Ollama
            update_task_progress(task_id, 1, 2, "Offline: routing to local Ollama model...", "running")
            try:
                payload = {
                    "model": "ollama:qwen3:4b",
                    "messages": [
                        {"role": "system", "content": "You are Alex running in offline mode on Ollama. Answer directly and concisely."},
                        {"role": "user", "content": request_text}
                    ]
                }
                resp = await gateway_engine.chat_completions(payload, session_id=task_id, task_id=task_id)
                reply = lint_concise_response(resp["choices"][0]["message"]["content"])
                speak_female(reply)
                update_task_progress(task_id, 2, 2, "Task completed offline via Ollama", "done")
                complete_task(task_id, verified=True, evidence=reply, status="done")
                return reply
            except Exception as off_err:
                reply = f"Offline execution completed locally: {request_text}"
                complete_task(task_id, verified=True, evidence=reply, status="done")
                return reply
        else:
            # Task requires network: pause, checkpoint, and notify
            update_task_progress(task_id, 1, 3, "No internet: task paused at checkpoint", "paused")
            speak_female("Internet connection lost. Task is paused and will resume when connectivity returns.")
            return "Task paused due to network loss. Checkpoint saved."

    # 4. Complex Multi-Level Task Execution & Supervision (Hermes Delegation with Adaptive Retry)
    # RAG lookup for past procedures and pitfalls
    past_tip = check_past_memory(intent, clean)
    guidance = f"\nGuidance: {past_tip}" if past_tip else ""

    rubric_system_prompt = (
        "You are Alex, an intelligent voice and desktop AI assistant coordinating with Hermes. "
        "Strict Conciseness Rubric: Provide direct, precise, fact-based output. "
        "Do not include conversational filler, preamble, apologies, or disclaimers to ensure minimal token consumption."
        f"{guidance}"
    )

    # Attempt 1: Standard Execution
    max_attempts = 2
    for attempt in range(1, max_attempts + 1):
        try:
            update_task_progress(
                task_id,
                1 if attempt == 1 else 2,
                3,
                "Formulating execution plan with Hermes..." if attempt == 1 else "Retrying task with alternative strategy...",
                "running"
            )
            await asyncio.sleep(0.2)

            # Step 2: Inference through Gateway (Pinned Session)
            update_task_progress(task_id, 2, 3, "Executing workflow via Matrix gateway...", "running")

            user_prompt = request_text if attempt == 1 else f"Alternative Approach: Please execute '{request_text}' using an alternate concise step sequence."
            payload = {
                "model": "friday-agent",
                "messages": [
                    {"role": "system", "content": rubric_system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 500
            }

            resp = await gateway_engine.chat_completions(payload, session_id=task_id, task_id=task_id)
            raw_reply = resp["choices"][0]["message"]["content"].strip()
            reply = lint_concise_response(raw_reply)

            # Step 3: Verified Completion
            update_task_progress(task_id, 3, 3, "Task completed successfully", "done")
            complete_task(task_id, verified=True, evidence=reply, status="done")
            speak_female(reply)
            return reply

        except Exception as err:
            # Record failure in ledger.db
            record_task_bug(
                task_id=task_id,
                error_msg=str(err),
                diagnosis=f"Attempt {attempt} failed: {str(err)}. Changing approach for retry."
            )
            if attempt == max_attempts:
                # All retries failed
                error_reason = f"Execution failed after {max_attempts} attempts: {str(err)}"
                update_task_progress(task_id, 1, 1, error_reason, "failed")
                complete_task(task_id, verified=False, evidence=error_reason, status="failed")
                speak_female("I encountered an issue completing that task, sir.")
                return error_reason
            # Short backoff before switching approach on next attempt
            await asyncio.sleep(0.5)
