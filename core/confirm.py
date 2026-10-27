"""Non-forgeable human confirmation gate for irreversible actions (adapted from Mark-LVI core/confirm.py)."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

from core.blackboard import blackboard

TIMEOUT_SECONDS = 90.0


@dataclass
class PendingConfirmation:
    key: str
    title: str
    detail: str
    run: Callable[[], str]
    at: float


_pending: Optional[PendingConfirmation] = None
_lock = threading.Lock()

_show_cb: Optional[Callable[[str, str], None]] = None
_hide_cb: Optional[Callable[[], None]] = None


def bind(
    show: Optional[Callable[[str, str], None]],
    hide: Optional[Callable[[], None]] = None,
) -> None:
    """Wire confirmation gate callbacks to the active GUI/Overlay or CLI."""
    global _show_cb, _hide_cb
    _show_cb, _hide_cb = show, hide


def request_confirmation(key: str, title: str, detail: str, run: Callable[[], str]) -> str:
    """Park an irreversible action behind the human confirmation gate."""
    global _pending
    with _lock:
        _pending = PendingConfirmation(
            key=key,
            title=title,
            detail=detail,
            run=run,
            at=time.monotonic(),
        )

    blackboard.set("pending_confirmation", {"key": key, "title": title, "detail": detail})
    blackboard.log(1, f"Awaiting user confirmation for: {title} ({detail})", "WARN")

    if _show_cb is not None:
        try:
            _show_cb(title, detail)
        except Exception as exc:
            blackboard.log(1, f"Confirmation UI callback error: {exc}", "WARN")

    return (
        f"status=confirmation_pending action={key} title=\"{title}\" detail=\"{detail}\" "
        f"-- Awaiting human confirmation via UI or confirm_pending(accepted=True)."
    )


def get_pending() -> Optional[dict]:
    """Return metadata of the active pending confirmation, or None if expired/empty."""
    with _lock:
        if _pending is None:
            return None
        if time.monotonic() - _pending.at > TIMEOUT_SECONDS:
            return None
        return {
            "key": _pending.key,
            "title": _pending.title,
            "detail": _pending.detail,
            "age_seconds": round(time.monotonic() - _pending.at, 1),
        }


def resolve(accepted: bool) -> str:
    """Called by the UI or CLI when the user approves or cancels the pending action."""
    global _pending
    with _lock:
        p, _pending = _pending, None

    blackboard.set("pending_confirmation", None)
    if _hide_cb is not None:
        try:
            _hide_cb()
        except Exception:
            pass

    if p is None:
        return "status=failed action=resolve_confirmation reason=\"No pending confirmation\""

    if time.monotonic() - p.at > TIMEOUT_SECONDS:
        return f"status=failed action=resolve_confirmation reason=\"Confirmation expired for '{p.title}'\""

    if not accepted:
        blackboard.log(1, f"Cancelled pending action: {p.title}")
        return f"status=done action=resolve_confirmation cancelled=\"{p.title}\""

    try:
        res = p.run() or "Done."
        blackboard.log(1, f"Confirmed and executed: {p.title} -> {res}")
        return f"status=done action=resolve_confirmation executed=\"{p.title}\" result=\"{res}\""
    except Exception as exc:
        return f"status=failed action=resolve_confirmation reason=\"{exc}\""
