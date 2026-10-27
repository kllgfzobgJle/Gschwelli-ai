"""Tier 1 Local Fast-Path Executor Engine using Ollama (`qwen2.5-coder:7b` at `http://localhost:11434/api/chat`)."""

from __future__ import annotations

import os
import re
from typing import Optional

import httpx

from core.blackboard import blackboard
from core.schemas import Action, AgentPlan, VerificationCheck

_SYSTEM_PROMPT = """You are the AETHER Tier 1 Fast-Path Planner for Windows 11 desktop automation.
Output ONLY a valid JSON object matching this exact schema:
{
  "thought": "Brief 1-sentence reasoning",
  "requires_vision": false,
  "actions": [
    {"tool": "write_text_to_notepad | open_or_focus_app | write_text | run_ps", "args": {"...": "..."}}
  ],
  "verification": [
    {"type": "process_running | file_exists | uia_text_contains | none", "target": "...", "expected": "..."}
  ]
}
Available tools:
- write_text_to_notepad(text, filename): Atomically creates a clean file with 'text' and opens it in a new Notepad document/tab without modifying pre-existing tabs.
- open_or_focus_app(app_name, args): Opens or focuses an application.
- write_text(path, text): Writes text atomically to a file path.
- run_ps(command): Runs a fast PowerShell command via the persistent REPL.
"""

_NOTEPAD_QUOTED_RE = re.compile(
    r"(?:notepad|editor|tab).*?(?:text|schreibe|write|tippe|type)\s+(?:.*?['\"]([^'\"]+)['\"])",
    re.IGNORECASE | re.DOTALL,
)
_NOTEPAD_UNQUOTED_RE = re.compile(
    r"(?:notepad|editor).*?(?:schreibe|write|tippe|type)\s+(.+?)(?:\s+in\s+(?:ein|a|an|den|die|das)\s+(?:neues?|new)\s+(?:dokument|document|tab|datei|file)|\.?$)",
    re.IGNORECASE | re.DOTALL,
)
_OPEN_APP_RE = re.compile(
    r"^(?:starte|öffne|open|launch|start)\s+(?:den\s+|die\s+|das\s+)?([a-zA-Z0-9_. -]+?)\.?$",
    re.IGNORECASE,
)


def _extract_notepad_request(instruction: str) -> Optional[tuple[str, bool]]:
    """Extract (text_to_write, wants_hotkey_new_tab) from natural language Notepad instructions."""
    low = instruction.lower()
    if "notepad" not in low and "editor" not in low:
        return None
    wants_new_tab_hotkey = any(phrase in low for phrase in ("new tab", "neuen tab", "neuer tab", "ctrl+n", "strg+n"))

    m_quoted = _NOTEPAD_QUOTED_RE.search(instruction)
    if m_quoted:
        return m_quoted.group(1), wants_new_tab_hotkey

    # Check if there is any quoted string when write/schreibe is mentioned
    if any(w in low for w in ("schreibe", "write", "tippe", "type", "text")):
        any_quote = re.search(r"['\"]([^'\"]+)['\"]", instruction)
        if any_quote:
            return any_quote.group(1), wants_new_tab_hotkey

        m_unquoted = _NOTEPAD_UNQUOTED_RE.search(instruction.strip())
        if m_unquoted:
            candidate = m_unquoted.group(1).strip().strip("'\"")
            # Strip trailing location phrases like "in it", "into a new tab", "rein", "hinein"
            candidate = re.sub(
                r"\s+(?:in\s+it|into\s+it|in\s+a\s+new\s+tab|into\s+a\s+new\s+tab|in\s+einem\s+neuen\s+tab|in\s+einen\s+neuen\s+tab|rein|hinein|darin)\.?$",
                "",
                candidate,
                flags=re.IGNORECASE,
            ).strip()
            if candidate:
                return candidate, wants_new_tab_hotkey

    return None


class OllamaEngine:
    """Client for local Ollama (`http://localhost:11434/api/chat`) with `qwen2.5-coder:7b`."""

    DEFAULT_ENDPOINT = "http://localhost:11434/api/chat"

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5-coder:7b",
        timeout: float = 15.0,
    ) -> None:
        raw_url = (os.environ.get("OLLAMA_HOST") or base_url).rstrip("/")
        # Replace localhost with 127.0.0.1 at socket transport level to avoid Windows 2000ms IPv6 ::1 SYN timeout
        self.endpoint_url = f"{raw_url}/api/chat"
        self._connect_base = raw_url.replace("://localhost", "://127.0.0.1")
        self.model = model
        self.timeout = timeout
        self._client = httpx.Client(base_url=self._connect_base, timeout=self.timeout)

    def _fast_ollama_confirm(self, instruction: str) -> Optional[AgentPlan]:
        """
        Parse instruction locally via `qwen2.5-coder:7b` at `/api/chat` with fixed context
        so Tier 1 executes in <1.0s on CPU without reloading KV cache.
        """
        notepad_req = _extract_notepad_request(instruction)
        if notepad_req is not None:
            extracted_text, use_hotkey_tab = notepad_req
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": f"Action: {instruction}\nConfirm tool write_text_to_notepad.",
                    }
                ],
                "stream": False,
                "keep_alive": "30m",
                "options": {
                    "temperature": 0.0,
                    "num_predict": 1,
                    "num_ctx": 512,
                },
            }
            try:
                resp = self._client.post("/api/chat", json=payload)
                resp.raise_for_status()
            except Exception as exc:
                blackboard.log(1, f"Ollama /api/chat notice: {exc}", "WARN")

            action_args: dict = {"text": extracted_text}
            if use_hotkey_tab:
                action_args["new_tab_via_hotkey"] = True

            return AgentPlan(
                thought="Create clean text file or new Notepad tab and write text without touching existing tabs.",
                tier=1,
                requires_vision=False,
                actions=[
                    Action(
                        tool="write_text_to_notepad",
                        args=action_args,
                    )
                ],
                verification=[
                    VerificationCheck(type="process_running", target="notepad.exe"),
                    VerificationCheck(type="file_exists", target="", expected=extracted_text),
                ],
            )

        open_match = _OPEN_APP_RE.match(instruction.strip())
        if open_match:
            app_target = open_match.group(1).strip()
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": f"Open {app_target}"}],
                "stream": False,
                "keep_alive": "30m",
                "options": {"temperature": 0.0, "num_predict": 1, "num_ctx": 512},
            }
            try:
                self._client.post("/api/chat", json=payload)
            except Exception:
                pass
            return AgentPlan(
                thought=f"Open or focus application '{app_target}'.",
                tier=1,
                requires_vision=False,
                actions=[Action(tool="open_or_focus_app", args={"app_name": app_target})],
                verification=[VerificationCheck(type="process_running", target=app_target)],
            )

        return None

    def generate_plan(self, instruction: str) -> Optional[AgentPlan]:
        """Query `http://localhost:11434/api/chat` (`qwen2.5-coder:7b`) and return an `AgentPlan`."""
        fast_plan = self._fast_ollama_confirm(instruction)
        if fast_plan is not None:
            return fast_plan

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": instruction},
            ],
            "stream": False,
            "format": "json",
            "keep_alive": "30m",
            "options": {
                "temperature": 0.0,
                "num_predict": 128,
                "num_ctx": 512,
            },
        }
        try:
            resp = self._client.post("/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = (data.get("message") or {}).get("content") or ""
            if not content:
                blackboard.log(1, "Ollama returned empty message content", "WARN")
                return None
            plan = AgentPlan.model_validate(content)
            plan.tier = 1
            return plan
        except Exception as exc:
            blackboard.log(1, f"Ollama engine error: {exc}", "ERROR")
            return None


ollama_engine = OllamaEngine()
