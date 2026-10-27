"""Safety guards for AETHER: process tree protection, terminal click prevention, and PS validation."""

from __future__ import annotations

import os
import re
import sys
from typing import Set

import psutil

# Terminal/console process names and window classes that must NEVER be targets for blind/OCR clicks
_TERMINAL_PROCESS_STEMS = frozenset({
    "windowsterminal",
    "wt",
    "powershell",
    "pwsh",
    "cmd",
    "conhost",
    "openconsole",
    "python",
    "pythonw",
    "code",  # VS Code host terminal
})

_TERMINAL_WINDOW_CLASSES = frozenset({
    "CASCADIA_HOSTING_WINDOW_CLASS",
    "ConsoleWindowClass",
    "VirtualConsoleClass",
})

# Destructive PowerShell patterns blocked by default
_DESTRUCTIVE_PS_RE = re.compile(
    r"\b(Remove-Item\s+.*-Recurse.*-Force|Format-Volume|Stop-Computer|Restart-Computer|Clear-Disk|rd\s+/s\s+/q)\b",
    re.IGNORECASE,
)


def own_process_chain_pids() -> Set[int]:
    """Return PIDs of this process, all children, and all ancestors (ported from Mark-LVI appidentity.py)."""
    pids: Set[int] = {os.getpid()}
    try:
        me = psutil.Process(os.getpid())
        for child in me.children(recursive=True):
            pids.add(child.pid)
        parent = me.parent()
        seen: Set[int] = set()
        while parent is not None and parent.pid not in seen and parent.pid > 1:
            seen.add(parent.pid)
            pids.add(parent.pid)
            try:
                parent = parent.parent()
            except Exception:
                break
    except Exception:
        pass
    return pids


def is_terminal_window(hwnd: int) -> bool:
    """Return True if hwnd belongs to the terminal/console or our own process chain."""
    if not hwnd:
        return False
    try:
        import win32gui
        import win32process

        if not win32gui.IsWindow(hwnd):
            return False

        cls_name = win32gui.GetClassName(hwnd) or ""
        if cls_name in _TERMINAL_WINDOW_CLASSES:
            return True

        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if pid in own_process_chain_pids():
            return True

        try:
            proc = psutil.Process(pid)
            stem = os.path.splitext(proc.name() or "")[0].lower()
            if stem in _TERMINAL_PROCESS_STEMS:
                # Allow VS Code or general apps only if explicitly targeted, but never console hosts
                if stem in {"windowsterminal", "wt", "powershell", "pwsh", "cmd", "conhost", "openconsole"}:
                    return True
        except Exception:
            pass
    except Exception:
        pass
    return False


def is_safe_powershell_command(command: str) -> tuple[bool, str]:
    """Validate that a PowerShell command does not execute destructive system wipe operations."""
    if not command or not command.strip():
        return False, "Empty PowerShell command"
    match = _DESTRUCTIVE_PS_RE.search(command)
    if match:
        return False, f"Blocked destructive PowerShell pattern: {match.group(0)}"
    return True, "OK"
