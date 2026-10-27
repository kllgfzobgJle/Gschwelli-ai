"""Tier 3 Selective Cloud Vision Fallback Engine using `gemini-3.8-flash` via `google-genai` on `v1beta`."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types as gtypes

from core.blackboard import blackboard
from core.schemas import AgentPlan


def _resolve_gemini_api_key() -> str:
    """Resolve Gemini API key from environment or local config files."""
    for env_var in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        val = os.environ.get(env_var, "").strip()
        if val:
            return val

    base = Path(__file__).resolve().parent.parent
    candidates = [
        base / "config" / "api_keys.json",
        base / "Inspirations" / "Mark-LVI-main" / "config" / "api_keys.json",
    ]
    for path in candidates:
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                key = str(data.get("gemini_api_key") or "").strip()
                if key:
                    return key
            except Exception:
                continue
    return ""


def strip_thought_parts(response: Any) -> str:
    """
    Crucial Tier 3 requirement:
    Strip all `thought` and `thought_signature` parts from Gemini response candidates
    before extracting the JSON string for parsing.
    """
    clean_chunks: List[str] = []
    candidates = getattr(response, "candidates", None) or []
    for cand in candidates:
        content = getattr(cand, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            # Skip any part flagged as a thought or carrying only a thought_signature
            is_thought = bool(getattr(part, "thought", False))
            if is_thought:
                continue
            # Clear thought_signature attribute if present on the part object
            if hasattr(part, "thought_signature"):
                try:
                    setattr(part, "thought_signature", None)
                except Exception:
                    pass
            text = getattr(part, "text", None)
            if isinstance(text, str) and text.strip():
                clean_chunks.append(text)

    if clean_chunks:
        return "\n".join(clean_chunks).strip()

    # Fallback if candidates structure is mocked or non-standard
    raw_text = getattr(response, "text", "") or ""
    return str(raw_text).strip()


class GeminiVisionEngine:
    """
    Tier 3 Cloud Vision Engine:
    - Model: `gemini-3.8-flash`
    - API version: `v1beta`
    - `max_output_tokens=8192`, `temperature=0.0`
    - `timeout=25.0s`, `max_retries=1`
    """

    MODEL_NAME = "gemini-3.8-flash"
    API_VERSION = "v1beta"
    MAX_OUTPUT_TOKENS = 8192
    TEMPERATURE = 0.0
    TIMEOUT_SECONDS = 25.0
    MAX_RETRIES = 1

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key or _resolve_gemini_api_key()

    def _build_client(self) -> genai.Client:
        if not self._api_key:
            raise RuntimeError("No GEMINI_API_KEY configured for Tier 3 Cloud Vision fallback.")

        # google-genai HttpOptions timeout is specified in milliseconds (25.0s -> 25000ms)
        http_opts = gtypes.HttpOptions(
            api_version=self.API_VERSION,
            timeout=int(self.TIMEOUT_SECONDS * 1000),
        )
        return genai.Client(api_key=self._api_key, http_options=http_opts)

    def generate_vision_plan(
        self,
        instruction: str,
        som_jpeg_bytes: bytes,
        som_elements: List[Dict[str, Any]],
    ) -> Optional[AgentPlan]:
        """Query `gemini-3.8-flash` on `v1beta` with SoM image + mark index and parse into `AgentPlan`."""
        marks_summary = "\n".join(
            f"[{m['mark']}] {m.get('control_type', 'Control')}: {m.get('name', '')!r} at {m.get('screen_center')}"
            for m in som_elements
        )
        prompt = (
            "You are AETHER Tier 3 Vision Planner. Analyze the active window screenshot with Set-of-Marks (SoM) tags.\n"
            f"User instruction: {instruction}\n\n"
            f"Detected Set-of-Marks interactive elements:\n{marks_summary or '(none detected)'}\n\n"
            "Return ONLY a JSON object with keys: thought, actions ([{\"tool\": \"...\", \"args\": {...}}]), "
            "and verification ([{\"type\": \"...\", \"target\": \"...\"}]). "
            "Never click inside a terminal/console window."
        )

        config = gtypes.GenerateContentConfig(
            temperature=self.TEMPERATURE,
            max_output_tokens=self.MAX_OUTPUT_TOKENS,
            response_mime_type="application/json",
        )

        attempts = 0
        max_attempts = 1 + self.MAX_RETRIES  # 1 initial + max_retries (1)
        last_err: Optional[Exception] = None

        while attempts < max_attempts:
            attempts += 1
            try:
                client = self._build_client()
                response = client.models.generate_content(
                    model=self.MODEL_NAME,
                    contents=[
                        gtypes.Part.from_bytes(data=som_jpeg_bytes, mime_type="image/jpeg"),
                        prompt,
                    ],
                    config=config,
                )
                clean_json_text = strip_thought_parts(response)
                plan = AgentPlan.model_validate(clean_json_text)
                plan.tier = 3
                return plan
            except Exception as exc:
                last_err = exc
                blackboard.log(3, f"Gemini Vision attempt {attempts}/{max_attempts} failed: {exc}", "WARN")

        blackboard.log(3, f"Gemini Vision exhausted retries: {last_err}", "ERROR")
        return None


gemini_engine = GeminiVisionEngine()
