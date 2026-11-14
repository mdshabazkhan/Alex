#!/usr/bin/env python3
"""
Alex Wake-Word Listener Daemon.
Continuously listens on the default microphone for the wake phrase: "Wake up Alex".
When detected:
1. Speaks: "Good morning Master Khan, What can I do for you" with Samantha voice.
2. Launches OpenJarvis Desktop App (/Applications/OpenJarvis.app) and focuses it.
3. Automatically sleeps while OpenJarvis is running, then resumes listening when closed.
"""

import os
import sys
import time
import subprocess
import numpy as np

# Ensure dependencies are available
try:
    import sounddevice as sd
    from faster_whisper import WhisperModel
except ImportError:
    print("Missing sounddevice or faster_whisper in environment.", file=sys.stderr)
    sys.exit(1)

RATE = 16000
CHUNK_DURATION = 2.5  # seconds
CHUNK_SAMPLES = int(RATE * CHUNK_DURATION)
RMS_THRESHOLD = 0.015  # Voice activity threshold

def is_openjarvis_running():
    try:
        res = subprocess.run(["pgrep", "-f", "openjarvis-desktop"], capture_output=True)
        return res.returncode == 0
    except Exception:
        return False

def launch_alex():
    print("[WakeWord] Triggering Alex startup...")
    # 1. Speak greeting and wait until complete so mic does not record greeting
    try:
        subprocess.run(["say", "-v", "Samantha", "Good morning Master Khan, What can I do for you"])
    except Exception as e:
        print(f"Error speaking greeting: {e}", file=sys.stderr)

    # 2. Launch OpenJarvis application (mic starts in silence, ready for user)
    try:
        subprocess.run(["open", "-a", "/Applications/OpenJarvis.app"], check=False)
        time.sleep(0.3)
        subprocess.run(["osascript", "-e", 'tell application "OpenJarvis" to activate'], check=False)
    except Exception as e:
        print(f"Error launching OpenJarvis.app: {e}", file=sys.stderr)

def main():
    print("[WakeWord] Initializing Alex Wake-Word Listener...")
    # Load tiny English model
    model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
    print("[WakeWord] Model ready. Listening for 'Wake up Alex'...")

    buffer = []
    
    def audio_callback(indata, frames, time_info, status):
        if status:
            pass
        buffer.append(indata.copy())

    with sd.InputStream(samplerate=RATE, channels=1, dtype='float32', callback=audio_callback):
        while True:
            # If OpenJarvis is currently open and running in front, check less frequently
            if is_openjarvis_running():
                time.sleep(1.0)
                buffer.clear()
                continue

            time.sleep(0.5)
            
            # Check if we have accumulated enough audio
            total_samples = sum(len(c) for c in buffer)
            if total_samples < CHUNK_SAMPLES:
                continue

            # Concatenate collected chunks
            audio_data = np.concatenate(buffer, axis=0).flatten()
            buffer.clear()

            # Voice activity detection via RMS
            rms = np.sqrt(np.mean(audio_data ** 2))
            if rms < RMS_THRESHOLD:
                continue

            # Transcribe audio buffer
            try:
                segments, _ = model.transcribe(audio_data, language="en", beam_size=1)
                text = " ".join(seg.text for seg in segments).lower().strip()
                if not text:
                    continue

                print(f"[Heard]: {text}")
                wake_phrases = ["wake up alex", "alex wake up", "wake up, alex", "hey alex", "wake up"]
                if any(phrase in text for phrase in wake_phrases):
                    launch_alex()
                    # Wait 6 seconds for app to initialize before accepting new wake words
                    time.sleep(6.0)
                    buffer.clear()

            except Exception as e:
                print(f"[WakeWord Error]: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
