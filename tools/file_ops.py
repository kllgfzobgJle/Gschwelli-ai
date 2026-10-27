"""Atomic file operations, directory management, and undoable file tools (ported from Mark-LVI file_controller.py)."""

from __future__ import annotations

import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Optional

from core.blackboard import blackboard
from core.undo import push_undo
from tools.registry import action

_UNDO_CONTENT_LIMIT = 1_000_000


def resolve_user_path(raw: str) -> Path:
    """Resolve user path or shortcut ('desktop', 'documents', 'downloads', 'home') to an absolute Path."""
    shortcuts = {
        "desktop": Path.home() / "Desktop",
        "documents": Path.home() / "Documents",
        "downloads": Path.home() / "Downloads",
        "pictures": Path.home() / "Pictures",
        "music": Path.home() / "Music",
        "videos": Path.home() / "Videos",
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


def _format_size(b: int) -> str:
    val = float(b)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if val < 1024.0:
            return f"{val:.1f} {unit}"
        val /= 1024.0
    return f"{val:.1f} TB"


def atomic_write_text(target_path: Path, text: str, register_undo: bool = True) -> Path:
    """Atomically write UTF-8 text to target_path via a temporary file in the same directory."""
    target_path = target_path.resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    existed = target_path.exists()
    previous: Optional[str] = None
    if existed and register_undo:
        try:
            if target_path.stat().st_size <= _UNDO_CONTENT_LIMIT:
                previous = target_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            previous = None

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

    if register_undo:
        if existed and previous is not None:
            old_content = previous
            push_undo(
                f"overwrote {target_path.name}",
                lambda p=target_path, c=old_content: (
                    p.write_text(c, encoding="utf-8"),
                    f"Restored previous contents of {p.name}",
                )[1],
            )
        elif not existed:
            push_undo(
                f"created {target_path.name}",
                lambda p=target_path: (
                    p.unlink(missing_ok=True),
                    f"Removed created file {p.name}",
                )[1],
            )

    blackboard.set("last_written_file", str(target_path))
    return target_path


@action(
    name="write_text",
    description="Atomically write text content to a local file path (reversible via undo).",
    parameters={"path": "str", "text": "str"},
)
def write_text(path: str = "", text: str = "") -> str:
    """Write text atomically to a file and record the path on the blackboard."""
    target = resolve_user_path(path)
    if target.is_dir():
        target = target / f"aether_doc_{int(time.time() * 1000)}.txt"
    written = atomic_write_text(target, text)
    return f"status=done action=write_text path=\"{written}\" bytes={len(text.encode('utf-8'))}"


@action(
    name="read_file_text",
    description="Read UTF-8 text content from a local file path.",
    parameters={"path": "str", "max_chars": "Optional[int]"},
)
def read_file_text(path: str = "", max_chars: int = 4000) -> str:
    target = resolve_user_path(path)
    if not target.is_file():
        return f"status=failed action=read_file_text reason=\"File not found: {target}\""
    try:
        content = target.read_text(encoding="utf-8", errors="replace")[: int(max_chars)]
        return f"status=done action=read_file_text path=\"{target}\" content={content!r}"
    except Exception as exc:
        return f"status=failed action=read_file_text reason=\"{exc}\""


@action(
    name="list_directory",
    description="List files and folders inside a directory or shortcut ('desktop', 'downloads', 'documents').",
    parameters={"path": "Optional[str]"},
)
def list_directory(path: str = "desktop") -> str:
    target = resolve_user_path(path or "desktop")
    if not target.exists() or not target.is_dir():
        return f"status=failed action=list_directory reason=\"Directory not found: {target}\""
    items = []
    for item in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))[:60]:
        if item.name.startswith("."):
            continue
        if item.is_dir():
            items.append(f"[DIR] {item.name}/")
        else:
            items.append(f"[FILE] {item.name} ({_format_size(item.stat().st_size)})")
    return f"status=done action=list_directory path=\"{target}\" count={len(items)} items=\"{', '.join(items)}\""


@action(
    name="move_or_rename_file",
    description="Move or rename a file or folder (reversible via undo).",
    parameters={"src": "str", "dst": "str"},
)
def move_or_rename_file(src: str = "", dst: str = "") -> str:
    if not src or not dst:
        return "status=failed action=move_or_rename_file reason=\"Both src and dst are required\""
    src_path = resolve_user_path(src)
    dst_path = resolve_user_path(dst)
    if not src_path.exists():
        return f"status=failed action=move_or_rename_file reason=\"Source not found: {src_path}\""
    if dst_path.is_dir():
        dst_path = dst_path / src_path.name
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    origin = src_path.resolve()
    dest = dst_path.resolve()
    shutil.move(str(origin), str(dest))
    push_undo(
        f"moved {origin.name} -> {dest}",
        lambda s=origin, d=dest: (shutil.move(str(d), str(s)), f"Moved {d.name} back to {s}")[1],
    )
    return f"status=done action=move_or_rename_file src=\"{origin}\" dst=\"{dest}\""


@action(
    name="delete_to_trash",
    description="Safely move a file or folder to the Windows Recycle Bin (reversible).",
    parameters={"path": "str"},
)
def delete_to_trash(path: str = "") -> str:
    if not path:
        return "status=failed action=delete_to_trash reason=\"No path provided\""
    target = resolve_user_path(path)
    if not target.exists():
        return f"status=failed action=delete_to_trash reason=\"File not found: {target}\""
    protected = {
        Path.home().resolve(),
        (Path.home() / "Desktop").resolve(),
        (Path.home() / "Documents").resolve(),
        (Path.home() / "Downloads").resolve(),
    }
    if target.resolve() in protected:
        return f"status=failed action=delete_to_trash reason=\"Protected directory: {target.name}\""
    try:
        import send2trash

        send2trash.send2trash(str(target.resolve()))
        return f"status=done action=delete_to_trash target=\"{target.name}\" recycle_bin=true"
    except Exception as exc:
        return f"status=failed action=delete_to_trash reason=\"{exc}\""
