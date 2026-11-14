"""
Jarvis Deterministic Reflex Matcher
Evaluates incoming speech/text against config/reflexes.yaml.
Executes instant actions (<1s, 0 tokens) and skips complex LLM inference.
"""

import os
import re
import yaml
from typing import Optional, Dict, Any
from tools.friday_mac import executor as mac_tools

REFLEXES_PATH = os.path.join("config", "reflexes.yaml")


class ReflexMatcher:
    def __init__(self, config_path: str = REFLEXES_PATH):
        self.config_path = config_path
        self.guards = []
        self.reflexes = []
        self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_path):
            return
        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            self.guards = [re.compile(g, re.IGNORECASE) for g in data.get("guards", [])]
            self.reflexes = data.get("reflexes", [])

    def match(self, utterance: str) -> Optional[Dict[str, Any]]:
        """Matches utterance against reflexes without executing hardware changes."""
        text = utterance.strip().lower()

        # Guard check: If compound or conditional, pass to Matrix
        for guard in self.guards:
            if guard.search(text):
                return None

        # Check reflexes
        for reflex in self.reflexes:
            m = re.match(reflex["match"], text, re.IGNORECASE)
            if m:
                return {
                    "id": reflex.get("id"),
                    "action": reflex.get("action"),
                    "args": m.groupdict()
                }

        return None

    def try_execute(self, utterance: str, execute: bool = True) -> Optional[Dict[str, Any]]:
        matched = self.match(utterance)
        if not matched:
            return None

        if not execute:
            return {"ok": True, "action": matched["action"], "args": matched["args"], "simulated": True}

        action = matched["action"]
        args = matched["args"]

        if action == "set_volume":
            level = args.get("level", 50)
            return mac_tools.set_volume(int(level))

        elif action == "toggle_wifi":
            return mac_tools.toggle_wifi()

        elif action == "toggle_dark_mode":
            return mac_tools.toggle_dark_mode()

        elif action == "open_app":
            app_name = args.get("app", "")
            return mac_tools.open_app(app_name)

        elif action == "quit_app":
            app_name = args.get("app", "")
            return mac_tools.quit_app(app_name)

        return {"ok": True, "action": action}


reflex_engine = ReflexMatcher()
