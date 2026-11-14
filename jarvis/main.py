"""
Jarvis Voice & Command Console (Alex Face)
Fast-path instant reflexes (<50ms), conversational greetings, real spoken audio (Daniel),
and active task tracking so commands NEVER hang.
"""

import asyncio
import sys
import time
from datetime import datetime
from jarvis.reflex import reflex_engine
from jarvis.matrix_client import client as matrix_client
from jarvis.voice_filter import notifier
from matrix.store import create_task, complete_task

GREETINGS = {"hi", "hello", "hey", "good morning", "good evening", "howdy", "sup", "alex", "jarvis"}
TIME_QUERIES = {"what time is it", "what's the time", "time", "current time", "what is the time"}
DATE_QUERIES = {"what's the date", "what is the date", "date", "today's date"}


async def handle_user_command(utterance: str):
    utterance = utterance.strip()
    if not utterance:
        return

    clean = utterance.lower()

    # 1. Instant Conversational Greetings (<50ms, 0 tokens)
    if clean in GREETINGS:
        reply = "Hello sir! I am online, listening, and ready for your commands."
        print(f"\n[JARVIS]: {reply}")
        notifier.speak("conversation", reply)
        return

    # 2. Instant Time & Date Queries (<50ms)
    if clean in TIME_QUERIES:
        now_str = datetime.now().strftime("%I:%M %p")
        reply = f"It is currently {now_str}, sir."
        print(f"\n[JARVIS]: {reply}")
        notifier.speak("conversation", reply)
        return

    if clean in DATE_QUERIES:
        today_str = datetime.now().strftime("%A, %B %d, %Y")
        reply = f"Today is {today_str}, sir."
        print(f"\n[JARVIS]: {reply}")
        notifier.speak("conversation", reply)
        return

    # 3. Deterministic Fast-Path Reflex (Wi-Fi, Volume, Dark mode, App launch)
    fast_result = reflex_engine.try_execute(utterance)
    if fast_result is not None:
        evidence = fast_result.get("evidence", "Command executed")
        print(f"[JARVIS FAST-PATH]: {evidence}")
        notifier.speak("task_completed", f"Done, sir. {evidence}")
        return

    # 4. Complex Task -> Delegate to Matrix & Hermes with Active Progress Tracking
    print(f"\n[JARVIS INTAKE]: \"{utterance}\"")
    notifier.speak("task_started", "On it, sir.")

    try:
        task_info = await matrix_client.submit_task(
            request_text=utterance,
            intent="agent_task",
            executor="hermes",
            total_steps=3
        )
        task_id = task_info["task_id"]
        print(f"[JARVIS DELEGATION]: Dispatched to Matrix. Task ID: {task_id}")

        # Active progress polling with 20s timeout so commands NEVER hang
        start_poll = time.time()
        last_pct = -1.0

        while (time.time() - start_poll) < 25.0:
            status_data = await matrix_client.get_task_progress(task_id)
            pct = status_data.get("progress_pct", 0.0)
            status = status_data.get("status", "running")
            step = status_data.get("current_step", "Processing")

            if pct != last_pct:
                bar = status_data.get("progress_bar", f"[{pct}%]")
                print(f"[JARVIS PROGRESS]: {bar} | {step}")
                last_pct = pct

            if status in ["done", "failed"]:
                evidence = status_data.get("evidence", "Task finished")
                if status == "done":
                    print(f"\n[JARVIS RESULT]: {evidence}\n")
                    # Voice reads out the outcome
                    speech_msg = evidence if len(evidence) < 140 else f"Task completed: {evidence[:100]}..."
                    notifier.speak("task_completed", f"Done, sir. {speech_msg}")
                else:
                    print(f"\n[JARVIS FAILED]: {evidence}\n")
                    notifier.speak("task_failed", f"Task encountered an issue, sir.")
                return

            await asyncio.sleep(0.4)

        print("[JARVIS WARNING]: Task taking longer in background. Check http://localhost:8000/ui for live updates.")

    except Exception as e:
        print(f"[JARVIS ERROR]: Failed to dispatch to Matrix: {e}")
        notifier.speak("task_failed", "Failed to start task, sir.")


async def cli_loop():
    print("==========================================================")
    print("           ALEX — JARVIS ACTIVE VOICE ASSISTANT           ")
    print("  Status: Connected to Matrix & Hermes                    ")
    print("  Audio Output: Native Mac Synthesizer (Daniel)           ")
    print("  Web Dashboard: http://localhost:8000/ui                 ")
    print("  Try: 'hi', 'what time is it', 'set volume 40', or tasks ")
    print("==========================================================")

    while True:
        try:
            prompt = await asyncio.get_event_loop().run_in_executor(None, input, "\nAlex > ")
            prompt = prompt.strip()
            if prompt.lower() in ["exit", "quit", "q"]:
                break
            await handle_user_command(prompt)
        except (KeyboardInterrupt, EOFError):
            break

    print("\nJarvis stopped.")


if __name__ == "__main__":
    asyncio.run(cli_loop())
