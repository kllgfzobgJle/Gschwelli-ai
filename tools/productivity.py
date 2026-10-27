"""Productivity, Document Processing (PDF/Word/Excel/CSV), Reminders & System Diagnostics (ported from Mark-LVI file_processor.py, reminder.py, system_monitor.py)."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import threading
import time
from typing import Any, Dict, List, Optional

import psutil

from core.blackboard import blackboard
from tools.file_ops import resolve_user_path
from tools.registry import action

_REMINDERS_FILE = Path(__file__).resolve().parent.parent / "memory" / "reminders.json"
_rem_lock = threading.Lock()


@action(
    name="process_document",
    description="Extract text, metadata, or convert PDF, Word (.docx), Excel (.xlsx), CSV, or image files.",
    parameters={"path": "str", "operation": "Optional[str]"},
)
def process_document(path: str = "", operation: str = "extract_text") -> str:
    target = resolve_user_path(path)
    if not target.is_file():
        return f"status=failed action=process_document reason=\"File not found: {target}\""

    ext = target.suffix.lower().lstrip(".")
    op = (operation or "extract_text").strip().lower()

    try:
        if ext == "pdf":
            text = ""
            try:
                import pdfplumber

                with pdfplumber.open(target) as pdf:
                    pages = len(pdf.pages)
                    for page in pdf.pages[:20]:
                        text += (page.extract_text() or "") + "\n"
            except Exception:
                import PyPDF2

                with open(target, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    pages = len(reader.pages)
                    for page in reader.pages[:20]:
                        text += (page.extract_text() or "") + "\n"

            if op == "to_word":
                from docx import Document

                doc = Document()
                doc.add_heading(target.stem, 0)
                for para in text.split("\n\n"):
                    if para.strip():
                        doc.add_paragraph(para.strip())
                out_path = target.with_name(f"{target.stem}_converted.docx")
                doc.save(out_path)
                return f"status=done action=process_document type=pdf op=to_word output=\"{out_path}\""

            preview = text.strip()[:1500].replace("\n", " ")
            return f"status=done action=process_document type=pdf pages={pages} chars={len(text)} preview={preview!r}"

        if ext in ("docx", "doc"):
            from docx import Document

            doc = Document(target)
            paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            full_text = "\n".join(paras)
            return (
                f"status=done action=process_document type=docx paragraphs={len(paras)} "
                f"chars={len(full_text)} preview={full_text[:1500]!r}"
            )

        if ext in ("xlsx", "xls"):
            import openpyxl

            wb = openpyxl.load_workbook(target, data_only=True)
            sheet = wb.active
            rows = []
            for row in list(sheet.iter_rows(values_only=True))[:15]:
                rows.append([str(c) if c is not None else "" for c in row])
            return (
                f"status=done action=process_document type=xlsx sheets={wb.sheetnames!r} "
                f"sample_rows={rows[:5]!r}"
            )

        # Fallback plain text / CSV / JSON / code
        content = target.read_text(encoding="utf-8", errors="replace")
        return f"status=done action=process_document type={ext or 'text'} chars={len(content)} preview={content[:1500]!r}"
    except Exception as exc:
        return f"status=failed action=process_document reason=\"{exc}\""


@action(
    name="create_office_doc",
    description="Create a new Word (.docx) or Excel (.xlsx) document with the given content.",
    parameters={"path": "str", "title": "Optional[str]", "content": "str"},
)
def create_office_doc(path: str = "", title: str = "AETHER Document", content: str = "") -> str:
    target = resolve_user_path(path)
    ext = target.suffix.lower()
    target.parent.mkdir(parents=True, exist_ok=True)

    try:
        if ext == ".xlsx":
            import openpyxl

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = (title or "Sheet1")[:31]
            for line in (content or "").splitlines():
                ws.append([cell.strip() for cell in line.split(",")])
            wb.save(target)
            return f"status=done action=create_office_doc type=xlsx path=\"{target}\""

        if ext != ".docx":
            target = target.with_suffix(".docx")
        from docx import Document

        doc = Document()
        if title:
            doc.add_heading(title, 0)
        for para in (content or "").split("\n"):
            doc.add_paragraph(para)
        doc.save(target)
        return f"status=done action=create_office_doc type=docx path=\"{target}\""
    except Exception as exc:
        return f"status=failed action=create_office_doc reason=\"{exc}\""


@action(
    name="system_status",
    description="Return real-time CPU, RAM, disk, and battery diagnostics via psutil.",
    parameters={},
)
def system_status() -> str:
    cpu = psutil.cpu_percent(interval=0.05)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\")
    bat = psutil.sensors_battery()
    bat_str = f"{bat.percent:.0f}% ({'charging' if bat.power_plugged else 'discharging'})" if bat else "AC"
    return (
        f"status=done action=system_status cpu=\"{cpu:.1f}%\" "
        f"ram=\"{mem.percent:.1f}% ({mem.used // (1024**3)}/{mem.total // (1024**3)} GB)\" "
        f"disk_c=\"{disk.percent:.1f}%\" battery=\"{bat_str}\""
    )


@action(
    name="set_reminder",
    description="Set a timed reminder or note that triggers after `seconds` (or stores a persistent reminder).",
    parameters={"message": "str", "seconds": "Optional[int]"},
)
def set_reminder(message: str = "", seconds: int = 60) -> str:
    msg = (message or "").strip()
    if not msg:
        return "status=failed action=set_reminder reason=\"Empty reminder message\""
    delay = max(1, int(seconds or 60))
    due_at = time.time() + delay

    with _rem_lock:
        _REMINDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        existing: List[Dict[str, Any]] = []
        if _REMINDERS_FILE.exists():
            try:
                existing = json.loads(_REMINDERS_FILE.read_text(encoding="utf-8"))
            except Exception:
                existing = []
        entry = {
            "message": msg,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "due_timestamp": due_at,
            "seconds": delay,
        }
        existing.append(entry)
        _REMINDERS_FILE.write_text(json.dumps(existing[-50:], indent=2, ensure_ascii=False), encoding="utf-8")

    def _timer_cb() -> None:
        blackboard.log(1, f"REMINDER DUE: {msg}", "WARN")
        blackboard.set("last_triggered_reminder", msg)

    t = threading.Timer(delay, _timer_cb)
    t.daemon = True
    t.start()
    return f"status=done action=set_reminder message=\"{msg}\" in_seconds={delay}"
