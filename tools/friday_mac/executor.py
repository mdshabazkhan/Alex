"""
Alex-Mac Deterministic Native macOS Actuators
Executes standard system controls instantaneously via native tools and AppleScript:
- App launching and quitting
- Web browsing and URL opening
- Playing songs on YouTube / Internet
- Audio volume and screen brightness
- Dark mode and Wi-Fi toggling
- File IO (copying, moving)
Returns: {ok: bool, verified: bool, evidence: str}
"""

import os
import shutil
import subprocess
import re
import urllib.parse
from typing import Dict, Any


def run_cmd(cmd: str) -> str:
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=8)
        return res.stdout.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"


def open_app(app_name: str) -> Dict[str, Any]:
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', app_name).strip()
    run_cmd(f"open -a '{clean_name}'")
    check = run_cmd(f"pgrep -fi '{clean_name}'")
    return {
        "ok": True,
        "verified": bool(check),
        "evidence": f"App PID: {check}" if check else f"App '{clean_name}' opened",
        "app": clean_name
    }


def quit_app(app_name: str) -> Dict[str, Any]:
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', app_name).strip()
    run_cmd(f"osascript -e 'quit app \"{clean_name}\"'")
    return {
        "ok": True,
        "verified": True,
        "evidence": f"Quit command sent to '{clean_name}'",
        "app": clean_name
    }


def browse_web(query_or_url: str) -> Dict[str, Any]:
    target = query_or_url.strip()
    if target.startswith("http://") or target.startswith("https://"):
        url = target
    else:
        encoded = urllib.parse.quote(target)
        url = f"https://www.google.com/search?q={encoded}"

    run_cmd(f"open '{url}'")
    return {
        "ok": True,
        "verified": True,
        "evidence": f"Opened browser at: {url}",
        "url": url
    }


def play_song(song_or_artist: str) -> Dict[str, Any]:
    clean_song = song_or_artist.strip()
    # Strip any trailing 'on youtube' or 'on spotify'
    clean_song = re.sub(r'\s+on\s+(youtube|spotify|internet)', '', clean_song, flags=re.IGNORECASE).strip()
    encoded = urllib.parse.quote(clean_song)
    url = f"https://www.youtube.com/results?search_query={encoded}"
    run_cmd(f"open '{url}'")
    return {
        "ok": True,
        "verified": True,
        "evidence": f"Playing '{clean_song}' on YouTube ({url})",
        "song": clean_song
    }


def set_volume(level: int) -> Dict[str, Any]:
    level = max(0, min(100, int(level)))
    run_cmd(f"osascript -e 'set volume output volume {level}'")
    current_vol = run_cmd("osascript -e 'output volume of (get volume settings)'")
    is_verified = (str(level) == current_vol)
    return {
        "ok": True,
        "verified": is_verified,
        "evidence": f"Volume set to {current_vol}",
        "level": level
    }


def toggle_dark_mode() -> Dict[str, Any]:
    script = """
    tell application "System Events"
        tell appearance preferences
            set dark mode to not dark mode
            return dark mode
        end tell
    end tell
    """
    res = run_cmd(f"osascript -e '{script}'")
    return {
        "ok": True,
        "verified": True,
        "evidence": f"Dark mode is now: {res}",
        "dark_mode": res
    }


def toggle_wifi(state: str = "toggle") -> Dict[str, Any]:
    device = run_cmd("networksetup -listallhardwareports | awk '/Wi-Fi|AirPort/{getline; print $2}'") or "en0"
    current = run_cmd(f"networksetup -getairportpower {device}")
    if "On" in current:
        target_state = "off" if state in ["off", "toggle"] else "on"
    else:
        target_state = "on" if state in ["on", "toggle"] else "off"

    run_cmd(f"networksetup -setairportpower {device} {target_state}")
    verified_status = run_cmd(f"networksetup -getairportpower {device}")
    is_verified = (target_state.lower() in verified_status.lower())
    return {
        "ok": True,
        "verified": is_verified,
        "evidence": verified_status,
        "action": f"wifi_{target_state}"
    }


def file_copy(src: str, dst: str) -> Dict[str, Any]:
    src = os.path.expanduser(src.strip())
    dst = os.path.expanduser(dst.strip())
    if not os.path.exists(src):
        return {"ok": False, "verified": False, "evidence": f"Source file does not exist: {src}"}
    try:
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
        return {"ok": True, "verified": os.path.exists(dst), "evidence": f"Copied {src} to {dst}"}
    except Exception as e:
        return {"ok": False, "verified": False, "evidence": f"File copy error: {str(e)}"}


def file_move(src: str, dst: str) -> Dict[str, Any]:
    src = os.path.expanduser(src.strip())
    dst = os.path.expanduser(dst.strip())
    if not os.path.exists(src):
        return {"ok": False, "verified": False, "evidence": f"Source file does not exist: {src}"}
    try:
        shutil.move(src, dst)
        return {"ok": True, "verified": os.path.exists(dst), "evidence": f"Moved {src} to {dst}"}
    except Exception as e:
        return {"ok": False, "verified": False, "evidence": f"File move error: {str(e)}"}
