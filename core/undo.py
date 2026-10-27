"""Shared thread-safe undo stack for reversible AETHER operations (adapted from Mark-LVI core/undo.py)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import threading
import time
from typing import Callable, Dict, List

from core.blackboard import blackboard

MAX_DEPTH = 20


@dataclass
class _Entry:
    label: str
    undo: Callable[[], str]
    category: str = "general"
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))
    at: float = field(default_factory=time.monotonic)


_stack: List[_Entry] = []
_lock = threading.Lock()


def push_undo(label: str, undo_fn: Callable[[], str], category: str = "general") -> None:
    """Record that `label` just happened and `undo_fn()` reverses it."""
    if not callable(undo_fn):
        return
    try:
        with _lock:
            _stack.append(_Entry(label=str(label)[:120], undo=undo_fn, category=category))
            while len(_stack) > MAX_DEPTH:
                _stack.pop(0)
    except Exception as exc:
        blackboard.log(1, f"Undo push warning: {exc}", "WARN")


def can_undo() -> bool:
    with _lock:
        return bool(_stack)


def peek() -> str:
    """Label of the operation that `undo_last()` would reverse, or ''."""
    with _lock:
        return _stack[-1].label if _stack else ""


def history(limit: int = 20) -> List[Dict[str, str]]:
    """Most recent first — used by the UI panel and the `undo_action` tool's list mode."""
    with _lock:
        items = list(reversed(_stack))[: max(1, limit)]
        return [
            {
                "label": e.label,
                "category": e.category,
                "timestamp": e.timestamp,
            }
            for e in items
        ]


def undo_last(count: int = 1) -> str:
    """Reverse the most recent `count` reversible operations."""
    undone_labels: List[str] = []
    details: List[str] = []
    for _ in range(max(1, int(count))):
        with _lock:
            entry = _stack.pop() if _stack else None
        if entry is None:
            break
        try:
            detail = entry.undo() or ""
            undone_labels.append(entry.label)
            if detail:
                details.append(detail)
        except Exception as exc:
            return f"status=failed action=undo_last reason=\"Could not undo '{entry.label}': {exc}\""

    if not undone_labels:
        return "status=done action=undo_last detail=\"Nothing to undo\""

    return (
        f"status=done action=undo_last undone=\"{'; '.join(undone_labels)}\" "
        f"detail=\"{'; '.join(details)}\""
    )


def clear() -> None:
    with _lock:
        _stack.clear()
