"""
Alex Voice Notification Gatekeeper
Speaks aloud on macOS using native high-quality female speech synthesizer (Samantha).
Non-blocking execution so speech never freezes the UI or execution loop.
"""

import subprocess
import shutil
from typing import Optional


class VoiceNotifier:
    def __init__(self, voice_name: str = "Samantha"):
        self.voice_name = voice_name
        self.has_say = shutil.which("say") is not None
        self.allowed_events = {
            "conversation",
            "task_started",
            "task_completed",
            "task_failed",
            "task_paused",
            "approval_needed"
        }

    def speak(self, event_type: str, message: str):
        if event_type not in self.allowed_events:
            return

        clean_text = message.replace('"', '').replace("'", "")
        print(f"\n[ALEX VOICE ({self.voice_name}) - {event_type.upper()}]: \"{clean_text}\"")

        # Non-blocking native macOS speech
        if self.has_say:
            try:
                subprocess.Popen(
                    ["say", "-v", self.voice_name, clean_text],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except Exception:
                try:
                    subprocess.Popen(["say", clean_text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    pass


notifier = VoiceNotifier()
