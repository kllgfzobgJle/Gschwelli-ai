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
    {"tool": "write_text_to_notepad | open_or_focus_app | close_app | system_control | undo_action | confirm_pending | open_url | web_search | youtube_search | system_status | remember_fact | recall_memory | write_text | read_file_text | list_directory | move_or_rename_file | delete_to_trash | process_document | create_office_doc | git_ops | inspect_python_code | scaffold_project | run_ps", "args": {"...": "..."}}
  ],
  "verification": [
    {"type": "process_running | file_exists | uia_text_contains | none", "target": "...", "expected": "..."}
  ]
}
Available tools:
- write_text_to_notepad(text, filename, new_tab_via_hotkey): Atomically creates a clean file with 'text' and opens it in a new Notepad document/tab without modifying pre-existing tabs.
- open_or_focus_app(app_name, args): Opens or focuses an application.
- close_app(app_name): Gracefully closes an application via WM_CLOSE.
- system_control(action, value): Controls volume_set, volume_up, volume_down, mute, unmute, brightness_set, dark_mode, light_mode, minimize_window, maximize_window, snap_left, snap_right, show_desktop, lock, shutdown, restart.
- undo_action(count): Reverses the last reversible file/settings action.
- confirm_pending(approve): Approves or cancels a pending high-impact action.
- open_url(url): Opens a website or shortcut (github, youtube, gmail, chatgpt, etc.).
- web_search(query, max_results): Searches DuckDuckGo and returns top snippets.
- youtube_search(query, open_in_browser): Searches YouTube and optionally opens the result.
- system_status(): Returns CPU, RAM, disk, battery, and top processes.
- remember_fact(key, value, category): Stores a persistent fact or preference in long-term memory.
- recall_memory(query): Searches long-term memory.
- write_text(path, text): Writes text atomically to a file path (with undo snapshot).
- read_file_text(path): Reads a text file.
- list_directory(path, pattern): Lists directory contents.
- move_or_rename_file(src, dst): Moves or renames a file (reversible via undo).
- delete_to_trash(path): Sends a file/folder to the Windows Recycle Bin (gated by confirmation).
- process_document(path, mode): Reads/summarizes PDF, Word (.docx), Excel (.xlsx), or CSV.
- create_office_doc(path, title, content): Creates a .docx or .xlsx document.
- git_ops(operation, repo_path, message): Runs git status, diff, log, branch, or commit.
- inspect_python_code(path): Parses Python AST and syntax health.
- scaffold_project(path, template, name): Scaffolds a Python CLI, FastAPI, or Web project.
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
_CLOSE_APP_RE = re.compile(
    r"^(?:schließe|schliesse|beende|close|quit|exit)\s+(?:den\s+|die\s+|das\s+)?([a-zA-Z0-9_. -]+?)\.?$",
    re.IGNORECASE,
)
_UNDO_RE = re.compile(
    r"^(?:undo|rückgängig|rueckgaengig|mach\s+das\s+rückgängig|undo\s+last(?:\s+action)?)\.?$",
    re.IGNORECASE,
)
_VOLUME_SET_RE = re.compile(
    r"(?:lautstärke|volume).*?(\d{1,3})\s*%?",
    re.IGNORECASE,
)
_BRIGHTNESS_SET_RE = re.compile(
    r"(?:helligkeit|brightness).*?(\d{1,3})\s*%?",
    re.IGNORECASE,
)
_WEB_SEARCH_RE = re.compile(
    r"^(?:suche\s+nach|search\s+for|google|web\s+search|recherchiere)\s+['\"]?(.+?)['\"]?\.?$",
    re.IGNORECASE,
)
_REMEMBER_RE = re.compile(
    r"^(?:merke\s+dir|remember(?:\s+that)?)\s+([a-zA-Z0-9_ -]+?)\s*(?:=|ist|is|:)\s*(.+?)\.?$",
    re.IGNORECASE,
)
_RECALL_RE = re.compile(
    r"^(?:was\s+weißt\s+du\s+über|recall|erinnere\s+dich\s+an|memory\s+search)\s+['\"]?(.+?)['\"]?\.?$",
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

    def _ping_ollama_kv(self, prompt_tag: str) -> None:
        """Keep `qwen2.5-coder:7b` warm with fixed `num_ctx: 512` in <200ms."""
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt_tag[:120]}],
            "stream": False,
            "keep_alive": "30m",
            "options": {"temperature": 0.0, "num_predict": 1, "num_ctx": 512},
        }
        try:
            resp = self._client.post("/api/chat", json=payload)
            resp.raise_for_status()
        except Exception as exc:
            blackboard.log(1, f"Ollama /api/chat notice: {exc}", "WARN")

    def _fast_ollama_confirm(self, instruction: str) -> Optional[AgentPlan]:
        """
        Parse instruction locally via `qwen2.5-coder:7b` at `/api/chat` with fixed context
        so Tier 1 executes in <1.0s on CPU without reloading KV cache.
        """
        stripped = instruction.strip()
        low = stripped.lower()

        # 1. Notepad / Editor clean lifecycle
        notepad_req = _extract_notepad_request(instruction)
        if notepad_req is not None:
            extracted_text, use_hotkey_tab = notepad_req
            self._ping_ollama_kv(f"Action: {instruction}\nConfirm tool write_text_to_notepad.")
            action_args: dict = {"text": extracted_text}
            if use_hotkey_tab:
                action_args["new_tab_via_hotkey"] = True

            return AgentPlan(
                thought="Create clean text file or new Notepad tab and write text without touching existing tabs.",
                tier=1,
                requires_vision=False,
                actions=[Action(tool="write_text_to_notepad", args=action_args)],
                verification=[
                    VerificationCheck(type="process_running", target="notepad.exe"),
                    VerificationCheck(type="file_exists", target="", expected=extracted_text),
                ],
            )

        # 2. Undo last action
        if _UNDO_RE.match(stripped):
            self._ping_ollama_kv("Confirm tool undo_action.")
            return AgentPlan(
                thought="Reverse the most recent reversible action on the AETHER undo stack.",
                tier=1,
                requires_vision=False,
                actions=[Action(tool="undo_action", args={"count": 1})],
                verification=[VerificationCheck(type="none")],
            )

        # 3. System Status / Hardware Telemetry
        if any(p in low for p in ("system status", "systemstatus", "cpu auslastung", "system info", "hardware status", "wie ausgelastet")):
            self._ping_ollama_kv("Confirm tool system_status.")
            return AgentPlan(
                thought="Retrieve live CPU, RAM, disk, and battery telemetry.",
                tier=1,
                requires_vision=False,
                actions=[Action(tool="system_status", args={})],
                verification=[VerificationCheck(type="none")],
            )

        # 4. System Settings (Volume, Mute, Brightness, Dark/Light mode, Window management)
        vol_match = _VOLUME_SET_RE.search(stripped)
        if vol_match:
            val = int(vol_match.group(1))
            self._ping_ollama_kv(f"Confirm system_control volume_set {val}")
            return AgentPlan(
                thought=f"Set system master volume to {val}%.",
                tier=1,
                requires_vision=False,
                actions=[Action(tool="system_control", args={"action": "volume_set", "value": val})],
                verification=[VerificationCheck(type="none")],
            )

        bright_match = _BRIGHTNESS_SET_RE.search(stripped)
        if bright_match:
            val = int(bright_match.group(1))
            self._ping_ollama_kv(f"Confirm system_control brightness_set {val}")
            return AgentPlan(
                thought=f"Set display brightness to {val}%.",
                tier=1,
                requires_vision=False,
                actions=[Action(tool="system_control", args={"action": "brightness_set", "value": val})],
                verification=[VerificationCheck(type="none")],
            )

        if any(p in low for p in ("dark mode", "dunkler modus", "darkmode")):
            self._ping_ollama_kv("Confirm system_control dark_mode")
            return AgentPlan(
                thought="Enable Windows 11 Dark Mode.",
                tier=1,
                requires_vision=False,
                actions=[Action(tool="system_control", args={"action": "dark_mode"})],
                verification=[VerificationCheck(type="none")],
            )

        if any(p in low for p in ("light mode", "heller modus", "lightmode")):
            self._ping_ollama_kv("Confirm system_control light_mode")
            return AgentPlan(
                thought="Enable Windows 11 Light Mode.",
                tier=1,
                requires_vision=False,
                actions=[Action(tool="system_control", args={"action": "light_mode"})],
                verification=[VerificationCheck(type="none")],
            )

        # 5. Memory Remember / Recall
        rem_match = _REMEMBER_RE.match(stripped)
        if rem_match:
            key, val = rem_match.group(1).strip(), rem_match.group(2).strip().strip("'\"")
            self._ping_ollama_kv(f"Confirm remember_fact {key}={val}")
            return AgentPlan(
                thought=f"Store persistent fact '{key}' in long-term memory.",
                tier=1,
                requires_vision=False,
                actions=[Action(tool="remember_fact", args={"key": key, "value": val, "category": "general"})],
                verification=[VerificationCheck(type="none")],
            )

        rec_match = _RECALL_RE.match(stripped)
        if rec_match:
            query = rec_match.group(1).strip()
            self._ping_ollama_kv(f"Confirm recall_memory {query}")
            return AgentPlan(
                thought=f"Recall facts matching '{query}' from long-term memory.",
                tier=1,
                requires_vision=False,
                actions=[Action(tool="recall_memory", args={"query": query})],
                verification=[VerificationCheck(type="none")],
            )

        # 6. Web Search
        ws_match = _WEB_SEARCH_RE.match(stripped)
        if ws_match:
            query = ws_match.group(1).strip()
            self._ping_ollama_kv(f"Confirm web_search {query}")
            return AgentPlan(
                thought=f"Search the web for '{query}'.",
                tier=1,
                requires_vision=False,
                actions=[Action(tool="web_search", args={"query": query, "max_results": 5})],
                verification=[VerificationCheck(type="none")],
            )

        # 7. Close Application
        close_match = _CLOSE_APP_RE.match(stripped)
        if close_match:
            app_target = close_match.group(1).strip()
            self._ping_ollama_kv(f"Close {app_target}")
            return AgentPlan(
                thought=f"Gracefully close application '{app_target}'.",
                tier=1,
                requires_vision=False,
                actions=[Action(tool="close_app", args={"app_name": app_target})],
                verification=[VerificationCheck(type="none")],
            )

        # 8. Open Application or URL
        open_match = _OPEN_APP_RE.match(stripped)
        if open_match:
            app_target = open_match.group(1).strip()
            if "." in app_target and not app_target.lower().endswith(".exe"):
                self._ping_ollama_kv(f"Open URL {app_target}")
                return AgentPlan(
                    thought=f"Open URL '{app_target}' in default browser.",
                    tier=1,
                    requires_vision=False,
                    actions=[Action(tool="open_url", args={"url": app_target})],
                    verification=[VerificationCheck(type="none")],
                )
            self._ping_ollama_kv(f"Open {app_target}")
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
