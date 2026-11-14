"""
AppleKit Native macOS PC Controller for Alex.
Uses AppleKit / AppleScript / Apple Events (via osascript) as the PRIMARY mechanism to control macOS,
with deterministic Python scripts and system CLI tools as resilient BACKUP.
"""

import os
import subprocess
import shutil
import re
import urllib.parse
from typing import Dict, Any, Optional

def run_applescript(script: str) -> Dict[str, Any]:
    """Execute an AppleScript snippet via osascript. Returns {ok, output, error}."""
    try:
        res = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=10
        )
        if res.returncode == 0:
            return {"ok": True, "output": res.stdout.strip(), "error": None}
        return {"ok": False, "output": res.stdout.strip(), "error": res.stderr.strip()}
    except Exception as e:
        return {"ok": False, "output": "", "error": str(e)}

def open_app(app_name: str) -> Dict[str, Any]:
    """Open or activate an application using AppleScript, with Python open fallback."""
    clean_name = re.sub(r'[^a-zA-Z0-9\s\-_]', '', app_name).strip()
    # 1. Primary: AppleKit / AppleScript
    as_res = run_applescript(f'tell application "{clean_name}" to activate')
    if as_res["ok"]:
        return {"ok": True, "method": "applekit", "app": clean_name, "detail": f"Activated {clean_name} via AppleKit"}

    # 2. Backup: Python subprocess 'open -a'
    try:
        py_res = subprocess.run(["open", "-a", clean_name], capture_output=True, text=True, timeout=8)
        if py_res.returncode == 0:
            return {"ok": True, "method": "python_backup", "app": clean_name, "detail": f"Launched {clean_name} via Python fallback"}
    except Exception as e:
        pass

    return {"ok": False, "app": clean_name, "error": as_res.get("error") or "Failed to open app"}

def quit_app(app_name: str) -> Dict[str, Any]:
    """Quit an application using AppleScript, with Python pkill fallback."""
    clean_name = re.sub(r'[^a-zA-Z0-9\s\-_]', '', app_name).strip()
    # 1. Primary: AppleKit / AppleScript
    as_res = run_applescript(f'tell application "{clean_name}" to quit')
    if as_res["ok"]:
        return {"ok": True, "method": "applekit", "app": clean_name, "detail": f"Closed {clean_name} via AppleKit"}

    # 2. Backup: Python subprocess pkill
    try:
        py_res = subprocess.run(["pkill", "-f", clean_name], capture_output=True, text=True)
        return {"ok": True, "method": "python_backup", "app": clean_name, "detail": f"Terminated {clean_name} via Python pkill"}
    except Exception as e:
        return {"ok": False, "app": clean_name, "error": str(e)}

def set_system_volume(level: int) -> Dict[str, Any]:
    """Set system audio volume (0-100) via AppleScript."""
    level = max(0, min(100, int(level)))
    as_res = run_applescript(f"set volume output volume {level}")
    check = run_applescript("output volume of (get volume settings)")
    return {
        "ok": as_res["ok"],
        "method": "applekit",
        "volume": check.get("output", str(level)),
        "detail": f"Volume set to {level}%"
    }

def get_system_volume() -> Dict[str, Any]:
    """Get current system volume via AppleScript."""
    check = run_applescript("output volume of (get volume settings)")
    return {"ok": check["ok"], "volume": check.get("output", "50")}

def set_dark_mode(enable: Optional[bool] = None) -> Dict[str, Any]:
    """Toggle or set Dark Mode via AppleScript."""
    if enable is True:
        script = 'tell application "System Events" to tell appearance preferences to set dark mode to true'
    elif enable is False:
        script = 'tell application "System Events" to tell appearance preferences to set dark mode to false'
    else:
        script = 'tell application "System Events" to tell appearance preferences to set dark mode to not dark mode'
    res = run_applescript(script)
    status = run_applescript('tell application "System Events" to tell appearance preferences to get dark mode')
    return {
        "ok": res["ok"],
        "method": "applekit",
        "dark_mode": status.get("output", "unknown"),
        "detail": f"Dark mode state: {status.get('output')}"
    }

def sleep_display_or_pc() -> Dict[str, Any]:
    """Sleep computer via AppleScript."""
    res = run_applescript('tell application "System Events" to sleep')
    if not res["ok"]:
        subprocess.run(["pmset", "displaysleepnow"], capture_output=True)
    return {"ok": True, "method": "applekit", "detail": "Display/System entering sleep"}

def lock_screen() -> Dict[str, Any]:
    """Lock macOS screen via AppleScript keystroke."""
    res = run_applescript('tell application "System Events" to keystroke "q" using {control down, command down}')
    if not res["ok"]:
        subprocess.run(["/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession", "-suspend"], capture_output=True)
    return {"ok": True, "method": "applekit", "detail": "Screen locked"}

def show_notification(title: str, message: str) -> Dict[str, Any]:
    """Show native macOS notification via AppleScript."""
    clean_t = title.replace('"', '\\"')
    clean_m = message.replace('"', '\\"')
    res = run_applescript(f'display notification "{clean_m}" with title "{clean_t}"')
    return {"ok": res["ok"], "method": "applekit"}

def media_control(action: str = "playpause", app: str = "Music") -> Dict[str, Any]:
    """Control media playback (playpause, next, previous) via AppleScript."""
    valid_apps = ["Music", "Spotify"]
    target_app = app if app in valid_apps else "Music"
    if action in ["play", "pause", "playpause"]:
        script = f'tell application "{target_app}" to playpause'
    elif action in ["next", "next track"]:
        script = f'tell application "{target_app}" to next track'
    elif action in ["previous", "prev track"]:
        script = f'tell application "{target_app}" to previous track'
    else:
        script = f'tell application "{target_app}" to playpause'
    res = run_applescript(script)
    return {"ok": res["ok"], "method": "applekit", "action": action, "app": target_app}

def bluetooth_control(power: Optional[bool] = None) -> Dict[str, Any]:
    """Control Bluetooth via blueutil (macOS tool)."""
    if power is True:
        res = subprocess.run(["/opt/homebrew/bin/blueutil", "--power", "1"], capture_output=True, text=True)
        return {"ok": res.returncode == 0, "state": "on", "detail": "Bluetooth enabled"}
    elif power is False:
        res = subprocess.run(["/opt/homebrew/bin/blueutil", "--power", "0"], capture_output=True, text=True)
        return {"ok": res.returncode == 0, "state": "off", "detail": "Bluetooth disabled"}
    else:
        res = subprocess.run(["/opt/homebrew/bin/blueutil", "--power"], capture_output=True, text=True)
        state = "on" if "1" in res.stdout else "off"
        return {"ok": True, "state": state, "detail": f"Bluetooth is {state}"}

def wifi_control(power: Optional[bool] = None) -> Dict[str, Any]:
    """Control Wi-Fi via networksetup (macOS native tool)."""
    device = "en0"
    if power is True:
        subprocess.run(["networksetup", "-setairportpower", device, "on"], capture_output=True)
        return {"ok": True, "state": "on", "detail": "Wi-Fi enabled"}
    elif power is False:
        subprocess.run(["networksetup", "-setairportpower", device, "off"], capture_output=True)
        return {"ok": True, "state": "off", "detail": "Wi-Fi disabled"}
    else:
        res = subprocess.run(["networksetup", "-getairportpower", device], capture_output=True, text=True)
        return {"ok": True, "detail": res.stdout.strip()}
