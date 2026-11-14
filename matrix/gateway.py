"""
Matrix Model Gateway (:8700/v1)
Routes model inference requests to Docker API gateways (FreeLLMAPI & OmniRoute) or Groq / OpenRouter.
Enforces:
1. Strict Sticky Sessions: Keep session pinned during stable execution.
2. Gateway Failover: Auto-falls back to Groq / OpenRouter if primary gateway is unreachable.
3. Secret scrubbing & local placeholders (DATA-001 & DATA-003).
4. Token accounting and budget monitoring in ledger.db.
"""

import os
import time
import uuid
import httpx
import yaml
from typing import Dict, Any, Optional, Tuple, List
from matrix.policy import engine as policy_engine
from matrix.store import record_model_call, get_task_token_usage, get_task

PROFILES_PATH = os.path.join("config", "profiles.yaml")


class ModelGateway:
    def __init__(self, config_path: str = PROFILES_PATH):
        self.config_path = config_path
        self.gateways = {}
        self.profiles = {}
        self.budgets = {}
        self.session_pins: Dict[str, Dict[str, str]] = {}  # session_id -> {gateway, model}
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self.gateways = data.get("gateways", {})
                self.profiles = data.get("profiles", {})
                self.budgets = data.get("budgets", {})

    def get_candidate_gateways(self, profile_name: str = "agent") -> List[Tuple[str, str, str]]:
        profile = self.profiles.get(profile_name, self.profiles.get("agent", {}))
        chain = profile.get("chain", ["freellmapi:auto", "groq:llama-3.3-70b-versatile", "openrouter:auto"])
        candidates = []
        for entry in chain:
            parts = entry.split(":")
            gw_name = parts[0]
            model = parts[1] if len(parts) > 1 else "auto"
            gw_cfg = self.gateways.get(gw_name)
            if gw_cfg and gw_cfg.get("enabled", True):
                base_url = os.getenv(f"{gw_name.upper()}_URL", gw_cfg.get("base_url", ""))
                candidates.append((gw_name, base_url, model))
        return candidates

    def resolve_gateway(self, session_id: Optional[str], profile_name: str = "agent") -> Tuple[str, str, str]:
        if session_id and session_id in self.session_pins:
            pinned = self.session_pins[session_id]
            return pinned["gateway_name"], pinned["base_url"], pinned["model"]

        candidates = self.get_candidate_gateways(profile_name)
        if not candidates:
            return "freellmapi", os.getenv("FREELLMAPI_URL", "http://127.0.0.1:3001/v1"), "auto"

        chosen_gw, base_url, chosen_model = candidates[0]
        if session_id:
            self.session_pins[session_id] = {
                "gateway_name": chosen_gw,
                "base_url": base_url,
                "model": chosen_model
            }
        return chosen_gw, base_url, chosen_model

    async def chat_completions(self, request_payload: Dict[str, Any], session_id: Optional[str] = None, task_id: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()
        call_id = f"call_{uuid.uuid4().hex[:12]}"

        # 1. Budget check
        if task_id:
            tokens_used = get_task_token_usage(task_id)
            task_info = get_task(task_id)
            budget = task_info.get("budget_tokens", 120000) if task_info else 120000
            if tokens_used >= budget:
                raise ValueError(f"Task {task_id} exceeded token budget ({tokens_used}/{budget}). Approval required.")

        # 2. Scrub outbound messages (DATA-001 / DATA-003)
        raw_messages = request_payload.get("messages", [])
        scrubbed_messages, redaction_count = policy_engine.scrub_messages(raw_messages)
        payload = {**request_payload, "messages": scrubbed_messages}

        profile = request_payload.get("profile", "agent")
        candidates = self.get_candidate_gateways(profile)
        if not candidates:
            candidates = [("freellmapi", os.getenv("FREELLMAPI_URL", "http://127.0.0.1:3001/v1"), "auto")]

        last_error = None
        for gw_name, base_url, target_model in candidates:
            req_payload = dict(payload)
            # Map model name per provider
            raw_model = req_payload.get("model")
            if raw_model in [None, "friday-agent", "friday-fast", "auto", "default", "qwen3.5:2b", ""]:
                if gw_name == "freellmapi":
                    req_payload["model"] = "auto"
                elif gw_name == "groq":
                    req_payload["model"] = target_model if target_model != "auto" else "llama-3.3-70b-versatile"
                elif gw_name == "openrouter":
                    req_payload["model"] = target_model if target_model != "auto" else "meta-llama/llama-3.3-70b-instruct:free"
                else:
                    req_payload["model"] = target_model
            else:
                if gw_name == "freellmapi" and raw_model in ["tool-capable", "coding"]:
                    req_payload["model"] = "auto"

            endpoint = f"{base_url.rstrip('/')}/chat/completions"
            headers = {"Content-Type": "application/json"}
            key_env = self.gateways.get(gw_name, {}).get("key_env")
            api_key = os.getenv(key_env) if key_env else None
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            try:
                async with httpx.AsyncClient(timeout=45.0) as client:
                    resp = await client.post(endpoint, json=req_payload, headers=headers)
                    resp.raise_for_status()
                    response_data = resp.json()

                # Success - log and return
                latency_ms = int((time.time() - start_time) * 1000)
                usage = response_data.get("usage", {})
                record_model_call({
                    "call_id": call_id,
                    "task_id": task_id or session_id or "",
                    "profile": profile,
                    "gateway": gw_name,
                    "provider": gw_name,
                    "model": req_payload.get("model", ""),
                    "tokens_in": usage.get("prompt_tokens", 0),
                    "tokens_out": usage.get("completion_tokens", 0),
                    "latency_ms": latency_ms,
                    "cost_usd": 0.0,
                    "outcome": "success",
                    "redactions": redaction_count
                })
                return response_data

            except Exception as e:
                last_error = e
                # Fall through to next gateway in candidate chain
                continue

        # If all candidates failed:
        latency_ms = int((time.time() - start_time) * 1000)
        record_model_call({
            "call_id": call_id,
            "task_id": task_id or session_id or "",
            "profile": profile,
            "gateway": "failed",
            "provider": "none",
            "model": payload.get("model", ""),
            "tokens_in": 0,
            "tokens_out": 0,
            "latency_ms": latency_ms,
            "cost_usd": 0.0,
            "outcome": f"error: {str(last_error)}",
            "redactions": redaction_count
        })
        raise last_error


gateway_engine = ModelGateway()
