"""Pydantic v2 schemas and resilient JSON pre-validators for AETHER."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def _lowercase_keys_recursive(obj: Any, preserve_args: bool = False) -> Any:
    """Recursively lowercase dictionary keys to prevent case-mismatch errors."""
    if isinstance(obj, dict):
        out: Dict[str, Any] = {}
        for k, v in obj.items():
            key_lower = str(k).strip().lower()
            # Inside 'args' or 'parameters', lowercase parameter names too,
            # while keeping string values completely intact.
            out[key_lower] = _lowercase_keys_recursive(v, preserve_args=(key_lower in ("args", "parameters")))
        return out
    if isinstance(obj, list):
        return [_lowercase_keys_recursive(item, preserve_args=preserve_args) for item in obj]
    return obj


def extract_and_normalize_json(raw: Any) -> Dict[str, Any]:
    """Strip markdown code fences, extract outer {...} object, and lowercase keys."""
    if isinstance(raw, dict):
        return _lowercase_keys_recursive(raw)

    if not isinstance(raw, str):
        raise ValueError(f"Expected JSON string or dict, got {type(raw).__name__}")

    text = raw.strip()
    # 1. Strip markdown code fences if present
    fence_match = _FENCE_RE.search(text)
    if fence_match:
        text = fence_match.group(1).strip()

    # 2. Extract outer {...} object
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON payload: {exc}") from exc

    if not isinstance(parsed, dict):
        raise ValueError("Extracted JSON root must be an object/dict.")

    return _lowercase_keys_recursive(parsed)


class Action(BaseModel):
    """A single executable step in an AgentPlan."""

    tool: str = Field(..., description="Registered tool name or executor action")
    args: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")

    @model_validator(mode="before")
    @classmethod
    def _normalize_action(cls, data: Any) -> Any:
        if isinstance(data, str):
            data = extract_and_normalize_json(data)
        elif isinstance(data, dict):
            data = _lowercase_keys_recursive(data)
            # Support aliases like 'name'/'action' for 'tool' and 'parameters'/'params' for 'args'
            if "tool" not in data:
                for alias in ("name", "action", "function"):
                    if alias in data:
                        data["tool"] = data.pop(alias)
                        break
            if "args" not in data:
                for alias in ("parameters", "params", "arguments"):
                    if alias in data and isinstance(data[alias], dict):
                        data["args"] = data.pop(alias)
                        break
            # If tool arguments were placed flat at the top level alongside 'tool', collect them
            if "args" not in data:
                reserved = {"tool", "thought", "description"}
                flat_args = {k: v for k, v in data.items() if k not in reserved}
                if flat_args:
                    data["args"] = flat_args
        return data


class VerificationCheck(BaseModel):
    """A deterministic verification check executed after an AgentPlan runs."""

    type: Literal["process_running", "file_exists", "uia_text_contains", "none"] = Field(
        default="none",
        description="Type of deterministic check to run",
    )
    target: str = Field(
        default="",
        description="Process name, file path, or window title fragment",
    )
    expected: Optional[str] = Field(
        default=None,
        description="Expected substring for uia_text_contains or file content check",
    )

    @model_validator(mode="before")
    @classmethod
    def _normalize_check(cls, data: Any) -> Any:
        if isinstance(data, str):
            data = extract_and_normalize_json(data)
        elif isinstance(data, dict):
            data = _lowercase_keys_recursive(data)
            if "type" not in data and "check" in data:
                data["type"] = data.pop("check")
            if "target" not in data:
                for alias in ("process", "path", "file", "window", "app"):
                    if alias in data:
                        data["target"] = str(data.pop(alias))
                        break
            if "expected" not in data:
                for alias in ("text", "value", "contains"):
                    if alias in data:
                        data["expected"] = str(data.pop(alias))
                        break
        return data


class AgentPlan(BaseModel):
    """Structured execution plan emitted by Tier 1 (Ollama) or Tier 3 (Gemini Vision)."""

    thought: str = Field(default="", description="Brief reasoning behind the plan")
    tier: int = Field(default=1, description="Originating execution tier (0, 1, 2, or 3)")
    requires_vision: bool = Field(
        default=False,
        description="True if the task strictly requires Tier 2/3 GUI/Vision inspection",
    )
    actions: List[Action] = Field(default_factory=list, description="Ordered list of actions to run")
    verification: List[VerificationCheck] = Field(
        default_factory=list,
        description="Deterministic checks to confirm task completion",
    )

    @model_validator(mode="before")
    @classmethod
    def _pre_validate_plan(cls, data: Any) -> Any:
        parsed = extract_and_normalize_json(data)
        # Normalize single action or single verification check into lists
        if "actions" not in parsed and "action" in parsed:
            act = parsed.pop("action")
            parsed["actions"] = [act] if isinstance(act, dict) else act
        if isinstance(parsed.get("actions"), dict):
            parsed["actions"] = [parsed["actions"]]

        if "verification" not in parsed and "verify" in parsed:
             parsed["verification"] = parsed.pop("verify")
        if "verification" not in parsed and "checks" in parsed:
            parsed["verification"] = parsed.pop("checks")
        if isinstance(parsed.get("verification"), dict):
            parsed["verification"] = [parsed["verification"]]
        elif parsed.get("verification") is None:
            parsed["verification"] = []

        return parsed
