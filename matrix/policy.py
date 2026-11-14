"""
Matrix Policy & Guardrails Engine
Enforces Alex_Safety_Guardrails.md and config/guardrails.yaml.
Strict precedence: deny > approve > notify > allow.
"""

import os
import re
import yaml
from typing import Dict, Any, Tuple, Optional

GUARDRAILS_PATH = os.path.join("config", "guardrails.yaml")

# Sensitive token patterns (DATA-001)
SECRET_PATTERNS = [
    (re.compile(r'(?i)(?:api_key|apikey|secret|token|bearer|auth|password)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{16,})["\']?'), '[REDACTED_SECRET]'),
    (re.compile(r'sk-[a-zA-Z0-9]{20,}'), '[REDACTED_KEY]'),
    (re.compile(r'ghp_[a-zA-Z0-9]{20,}'), '[REDACTED_GH_TOKEN]'),
    (re.compile(r'AKIA[0-9A-Z]{16}'), '[REDACTED_AWS_KEY]'),
    (re.compile(r'(?i)canary_test_secret_[a-zA-Z0-9]+'), '[REDACTED_CANARY]')
]

# Personal / Financial identifiers (DATA-003)
CARD_PATTERN = re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b')
SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')


class PolicyEngine:
    def __init__(self, config_path: str = GUARDRAILS_PATH):
        self.config_path = config_path
        self.rules = []
        self.default_action = "approve"
        self.load_rules()

    def load_rules(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Missing guardrails configuration: {self.config_path}")
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            self.rules = data.get("rules", [])
            self.default_action = data.get("default_action", "approve")

        # Baseline check (STOP-004)
        rule_ids = {r.get("id") for r in self.rules}
        if "DENY-001" not in rule_ids or "DATA-001" not in rule_ids:
            raise ValueError("Safety Baseline Error: DENY-001 and DATA-001 must be defined.")

    def scrub_text(self, text: str) -> Tuple[str, int]:
        """Scrubs secrets (DATA-001) and applies placeholders (DATA-003)."""
        redactions = 0
        cleaned = text

        for pattern, replacement in SECRET_PATTERNS:
            matches = pattern.findall(cleaned)
            if matches:
                redactions += len(matches)
                cleaned = pattern.sub(replacement, cleaned)

        # Placeholder replacement
        card_matches = CARD_PATTERN.findall(cleaned)
        if card_matches:
            redactions += len(card_matches)
            cleaned = CARD_PATTERN.sub("[CARD_PLACEHOLDER]", cleaned)

        ssn_matches = SSN_PATTERN.findall(cleaned)
        if ssn_matches:
            redactions += len(ssn_matches)
            cleaned = SSN_PATTERN.sub("[ID_PLACEHOLDER]", cleaned)

        return cleaned, redactions

    def scrub_messages(self, messages: list) -> Tuple[list, int]:
        """Scrubs outbound chat messages before they hit external model gateways."""
        total_redactions = 0
        scrubbed = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                cleaned, r_count = self.scrub_text(content)
                total_redactions += r_count
                scrubbed.append({**msg, "content": cleaned})
            else:
                scrubbed.append(msg)
        return scrubbed, total_redactions

    def _match_condition(self, condition: Dict[str, Any], tool_name: str, command: str, path: str) -> bool:
        if "command_matches" in condition and re.search(condition["command_matches"], command):
            return True
        if "path_matches" in condition:
            for p in condition["path_matches"]:
                if re.search(p, path):
                    return True
        if "tool" in condition:
            tools = condition["tool"] if isinstance(condition["tool"], list) else [condition["tool"]]
            if tool_name in tools:
                return True
        return False

    def evaluate_tool_call(self, tool_name: str, args: Dict[str, Any]) -> Tuple[str, str, Optional[str]]:
        """
        Evaluates tool calls against guardrail rules.
        Returns: (action, rule_id, prompt_message)
        """
        command = str(args.get("command", ""))
        path = str(args.get("path", "") or args.get("file", ""))

        # 1. Check Deny Rules
        for rule in self.rules:
            if rule.get("action") == "deny":
                when = rule.get("when", {})
                if "any" in when:
                    for cond in when["any"]:
                        if self._match_condition(cond, tool_name, command, path):
                            return "deny", rule["id"], f"Blocked by safety rule {rule['id']}: command prohibited."
                elif self._match_condition(when, tool_name, command, path):
                    return "deny", rule["id"], f"Blocked by safety rule {rule['id']}: command prohibited."

        # 2. Check Approve Rules
        for rule in self.rules:
            if rule.get("action") == "approve":
                when = rule.get("when", {})
                matched = False
                if "any" in when:
                    matched = any(self._match_condition(c, tool_name, command, path) for c in when["any"])
                else:
                    matched = self._match_condition(when, tool_name, command, path)

                if matched:
                    say_fmt = rule.get("say", f"Approval needed to execute {tool_name}")
                    try:
                        prompt = say_fmt.format(**args) if "{" in say_fmt else say_fmt
                    except KeyError:
                        # Fallback for missing format keys
                        prompt = say_fmt
                        for k, v in args.items():
                            prompt = prompt.replace(f"{{{k}}}", str(v))
                        # Clean any unreplaced placeholders
                        prompt = re.sub(r'\{[a-zA-Z0-9_]+\}', '...', prompt)
                    return "approve", rule["id"], prompt

        # 3. Default check
        return "allow", "ALLOW-DEFAULT", None


# Global policy instance
engine = PolicyEngine()
