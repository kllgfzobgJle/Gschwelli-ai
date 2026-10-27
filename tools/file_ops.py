"""Atomic file operations and path resolution (adapted from Mark-LVI file_controller.py)."""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path
from typing import Optional

from core.blackboard import blackboard
from tools.registry import action


def resolve_user_path(raw: str) -> Path:
    """Resolve user path or shortcut ('desktop', 'documents', etc.) to an absolute Path."""
    shortcuts = {
        "desktop": Path.home() / "Desktop",
        "documents": Path.home() / "Documents",
        "downloads": Path.home() / "Downloads",
        "home": Path.home(),
    }
    cleaned = (raw or "").strip().strip('"').strip("'")
    if not cleaned:
        base_dir = Path(__file__).resolve().parent.parent / "workspace" / "notes"
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir / f"aether_note_{int(time.time() * 1000)}.txt"

    lower = cleaned.lower()
    if lower in shortcuts:
        return shortcuts[lower]

    head, sep, rest = cleaned.replace("\\", "/").partition("/")
    if sep and head.lower() in shortcuts:
        return shortcuts[head.lower()] / rest.strip("/")

    p = Path(cleaned).expanduser()
    if not p.is_absolute():
        p = (Path(__file__).resolve().parent.parent / p).resolve()
    return p


def atomic_write_text(target_path: Path, text: str) -> Path:
    """Atomically write UTF-8 text to target_path via a temporary file in the same directory."""
    target_path = target_path.resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{target_path.stem}_",
        suffix=".tmp",
        dir=str(target_path.parent),
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, target_path)
    except Exception:
        if os.path.exists(tmp_name):
            try:
                os.unlink(tmp_name)
            except Exception:
                pass
        raise

    blackboard.set("last_written_file", str(target_path))
    return target_path


@action(
    name="write_text",
    description="Atomically write text content to a local file path.",
    parameters={"path": "str", "text": "str"},
)
def write_text(path: str = "", text: str = "") -> str:
    """Write text atomically to a file and record the path on the blackboard."""
    target = resolve_user_path(path)
    if target.is_dir():
        target = target / f"aether_doc_{int(time.time() * 1000)}.txt"
    written = atomic_write_text(target, text)
    return f"status=done action=write_text path=\"{written}\" bytes={len(text.encode('utf-8'))}"
