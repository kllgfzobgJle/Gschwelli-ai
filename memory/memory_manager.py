"""Persistent user memory, session continuity, and lexical recall (ported from Mark-LVI memory_manager.py)."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
import sys
from threading import Lock
from typing import Any, Dict, List, Optional

from tools.registry import action


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = _base_dir()
MEMORY_PATH = BASE_DIR / "memory" / "long_term.json"
_lock = Lock()
MAX_VALUE_LENGTH = 400
MEMORY_MAX_CHARS = 200_000
PROMPT_CORE_CHARS = 900
PROMPT_INDEX_CHARS = 420
PROMPT_MAX_PER_CATEGORY = 6

_CATEGORIES = ("identity", "preferences", "projects", "relationships", "wishes", "notes")


def _empty_memory() -> Dict[str, Any]:
    return {cat: {} for cat in _CATEGORIES}


def load_memory() -> Dict[str, Any]:
    if not MEMORY_PATH.exists():
        return _empty_memory()
    with _lock:
        try:
            data = json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                base = _empty_memory()
                for k in base:
                    if k not in data or not isinstance(data[k], dict):
                        data[k] = {}
                return data
        except Exception:
            pass
    return _empty_memory()


def save_memory(memory: Dict[str, Any]) -> None:
    if not isinstance(memory, dict):
        return
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        MEMORY_PATH.write_text(
            json.dumps(memory, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def _entry_value(entry: Any) -> str:
    if isinstance(entry, dict):
        return str(entry.get("value", "") or "").strip()
    return str(entry or "").strip()


def remember_fact(key: str, value: str, category: str = "notes") -> str:
    cat = (category or "notes").strip().lower()
    if cat not in _CATEGORIES:
        cat = "notes"
    k = (key or "").strip().lower().replace(" ", "_")
    val = str(value or "").strip()[:MAX_VALUE_LENGTH]
    if not k or not val:
        return "status=failed action=remember_fact reason=\"Key and value are required\""

    mem = load_memory()
    mem.setdefault(cat, {})[k] = {
        "value": val,
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    save_memory(mem)
    return f"status=done action=remember_fact category=\"{cat}\" key=\"{k}\" value=\"{val}\""


def forget_fact(key: str, category: str = "notes") -> str:
    cat = (category or "notes").strip().lower()
    k = (key or "").strip().lower().replace(" ", "_")
    mem = load_memory()
    if cat in mem and k in mem[cat]:
        del mem[cat][k]
        save_memory(mem)
        return f"status=done action=forget_fact category=\"{cat}\" key=\"{k}\""
    # Also search across all categories if category wasn't exact
    for c in _CATEGORIES:
        if k in mem.get(c, {}):
            del mem[c][k]
            save_memory(mem)
            return f"status=done action=forget_fact category=\"{c}\" key=\"{k}\""
    return f"status=failed action=forget_fact reason=\"Key '{k}' not found\""


def search_memory(query: str = "", limit: int = 10) -> str:
    mem = load_memory()
    q_low = (query or "").strip().lower()
    words = [w for w in re.split(r"[^a-zA-Z0-9äöüß]+", q_low) if len(w) > 1]
    rows: List[tuple[int, str, str, str]] = []

    for cat in _CATEGORIES:
        items = mem.get(cat, {})
        if not isinstance(items, dict):
            continue
        for k, entry in items.items():
            val = _entry_value(entry)
            if not val:
                continue
            if not words and not q_low:
                score = 1
            else:
                score = 0
                raw_k = k.lower()
                hay_k = raw_k.replace("_", " ")
                hay_v = val.lower()
                if q_low and (q_low == raw_k or q_low == hay_k):
                    score += 20
                for w in words:
                    if w in (raw_k, hay_k):
                        score += 10
                    elif w in hay_k or w in raw_k:
                        score += 6
                    if w in hay_v:
                        score += 3
                    if w in cat:
                        score += 1
            if score > 0:
                rows.append((score, cat, k, val))

    if not rows:
        return f"status=done action=recall_memory count=0 detail=\"Nothing stored matching '{query}'\""

    rows.sort(key=lambda r: (-r[0], r[2]))
    matches = [f"{cat}/{k}: {val}" for _, cat, k, val in rows[: max(1, limit)]]
    return "status=done action=recall_memory results=\"" + " | ".join(matches) + "\""


def all_entries_for_ui() -> List[Dict[str, str]]:
    mem = load_memory()
    rows: List[Dict[str, str]] = []
    for cat in _CATEGORIES:
        items = mem.get(cat, {})
        if not isinstance(items, dict):
            continue
        for k, entry in items.items():
            val = _entry_value(entry)
            if not val:
                continue
            rows.append(
                {
                    "category": cat,
                    "key": k,
                    "value": val,
                    "updated": entry.get("updated", "") if isinstance(entry, dict) else "",
                }
            )
    rows.sort(key=lambda r: r.get("updated") or "0000-00-00", reverse=True)
    return rows


def save_session_summary(summary: str, instruction: str = "") -> None:
    text = (summary or "").strip()
    if not text:
        return
    mem = load_memory()
    sessions = mem.get("sessions", [])
    if not isinstance(sessions, list):
        sessions = []
    sessions.append(
        {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "instruction": instruction[:200],
            "summary": text[:300],
        }
    )
    mem["sessions"] = sessions[-25:]
    save_memory(mem)


@action(
    name="remember_fact",
    description="Store a persistent fact, preference, project, or note in AETHER long-term memory.",
    parameters={"key": "str", "value": "str", "category": "Optional[str]"},
)
def remember_tool(key: str = "", value: str = "", category: str = "notes") -> str:
    return remember_fact(key=key, value=value, category=category)


@action(
    name="recall_memory",
    description="Search long-term memory for stored facts, preferences, projects, or notes.",
    parameters={"query": "Optional[str]"},
)
def recall_tool(query: str = "") -> str:
    return search_memory(query=query)
