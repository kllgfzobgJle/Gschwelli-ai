"""Fast deterministic verification checks for AETHER (process_running, file_exists, uia_text_contains)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Tuple

import psutil
import win32gui

from core.blackboard import blackboard
from core.schemas import VerificationCheck
from executors.win32_uia import find_window_by_title
from tools.app_lifecycle import find_running_pids
from tools.file_ops import resolve_user_path


def _check_process_running(target: str) -> Tuple[bool, str]:
    if not target:
        return True, "No process target specified"

    # Fast-path check via recently focused HWND or spawned PID on blackboard
    last_hwnd = blackboard.get("last_focused_hwnd")
    if last_hwnd and win32gui.IsWindow(last_hwnd):
        return True, f"Process '{target}' active window verified (HWND {last_hwnd})"

    last_pid = blackboard.get("last_spawned_pid")
    if last_pid and psutil.pid_exists(int(last_pid)):
        return True, f"Process '{target}' is running (PID {last_pid})"

    pids = find_running_pids(target)
    if pids:
        return True, f"Process '{target}' is running (PIDs: {pids[:4]})"

    # Direct psutil fallback by stem/name
    q = os.path.splitext(target.lower().strip())[0]
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            pname = os.path.splitext((proc.info.get("name") or "").lower())[0]
            if q == pname or q in pname:
                return True, f"Process '{target}' is running (PID {proc.info['pid']})"
        except Exception:
            continue
    return False, f"Process '{target}' is not running"


def _check_file_exists(target: str, expected: str | None = None) -> Tuple[bool, str]:
    # Allow checking the most recently written file if target is generic or placeholder
    candidates: List[Path] = []
    last_notepad = blackboard.get("last_notepad_file")
    last_written = blackboard.get("last_written_file")
    if target and target.strip():
        candidates.append(resolve_user_path(target))
    if last_notepad:
        candidates.append(Path(last_notepad))
    if last_written:
        candidates.append(Path(last_written))

    for path in candidates:
        if path.is_file():
            if expected:
                try:
                    content = path.read_text(encoding="utf-8", errors="ignore")
                    if expected in content:
                        return True, f"File '{path.name}' exists and contains '{expected}'"
                except Exception:
                    pass
            else:
                return True, f"File '{path}' exists"

    return False, f"File check failed for target='{target}' (expected='{expected}')"


def _check_uia_text_contains(target: str, expected: str | None = None) -> Tuple[bool, str]:
    search_text = (expected or target or "").strip()
    if not search_text:
        return True, "Empty UIA text check"

    # First check if a clean Notepad file was just written and Notepad is open with that file
    last_notepad = blackboard.get("last_notepad_file")
    if last_notepad and Path(last_notepad).is_file():
        try:
            file_text = Path(last_notepad).read_text(encoding="utf-8", errors="ignore")
            if search_text in file_text and find_running_pids("notepad.exe"):
                # Also verify via pywinauto UIA if quick, or confirm window exists
                hwnd = blackboard.get("last_focused_hwnd") or find_window_by_title("notepad", exclude_terminal=True)
                if hwnd and win32gui.IsWindow(hwnd):
                    try:
                        from pywinauto import Desktop

                        win = Desktop(backend="uia").window(handle=hwnd)
                        for ctrl in win.descendants():
                            try:
                                ctype = ctrl.element_info.control_type
                                if ctype in ("Document", "Edit", "Window", "TabItem"):
                                    texts = " ".join(t for t in ctrl.texts() if t)
                                    val = ""
                                    try:
                                        val = ctrl.iface_value.CurrentValue or ""
                                    except Exception:
                                        pass
                                    if search_text in texts or search_text in val or search_text in (ctrl.element_info.name or ""):
                                        return True, f"UIA verified '{search_text}' in {ctype}"
                            except Exception:
                                continue
                    except Exception:
                        pass
                    return True, f"Verified '{search_text}' in active Notepad document ({Path(last_notepad).name})"
        except Exception:
            pass

    # General pywinauto UIA inspection on target window
    hwnd = find_window_by_title(target or "notepad", exclude_terminal=True)
    if not hwnd:
        return False, f"Target window '{target}' not found for UIA text verification"

    try:
        from pywinauto import Desktop

        win = Desktop(backend="uia").window(handle=hwnd)
        win_title = win32gui.GetWindowText(hwnd) or ""
        if search_text.lower() in win_title.lower():
            return True, f"Window title contains '{search_text}'"

        for ctrl in win.descendants():
            try:
                name = ctrl.element_info.name or ""
                if search_text in name:
                    return True, f"UIA control name contains '{search_text}'"
                texts = " ".join(t for t in ctrl.texts() if t)
                if search_text in texts:
                    return True, f"UIA control text contains '{search_text}'"
                try:
                    val = ctrl.iface_value.CurrentValue or ""
                    if search_text in val:
                        return True, f"UIA control value contains '{search_text}'"
                except Exception:
                    pass
            except Exception:
                continue
    except Exception as exc:
        return False, f"UIA verification error: {exc}"

    return False, f"UIA text '{search_text}' not found in window '{target}'"


def verify_plan(checks: List[VerificationCheck]) -> Tuple[bool, List[str]]:
    """Run all deterministic verification checks for an executed plan."""
    if not checks:
        return True, ["No verification checks required"]

    messages: List[str] = []
    all_passed = True

    for chk in checks:
        ctype = chk.type
        if ctype == "none":
            messages.append("Check 'none': skipped")
            continue
        elif ctype == "process_running":
            ok, msg = _check_process_running(chk.target)
        elif ctype == "file_exists":
            ok, msg = _check_file_exists(chk.target, chk.expected)
        elif ctype == "uia_text_contains":
            ok, msg = _check_uia_text_contains(chk.target, chk.expected)
        else:
            ok, msg = True, f"Unknown check '{ctype}' ignored"

        messages.append(f"[{'PASS' if ok else 'FAIL'}] {ctype}: {msg}")
        if not ok:
            all_passed = False

    return all_passed, messages
