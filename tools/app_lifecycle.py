"""Application launching, focus management, and Clean Window Lifecycle (ported from Mark-LVI open_app.py & appidentity.py)."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import time
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional

import psutil
import win32gui
import win32process

from core.blackboard import blackboard
from core.safety import own_process_chain_pids
from executors.ps_repl import ps_repl
from executors.win32_uia import focus_hwnd_win32, uia_executor
from tools.file_ops import atomic_write_text, resolve_user_path
from tools.registry import action

# Cross-platform / Windows alias map adapted from Mark-LVI core/appidentity.py
ALIASES: Dict[str, str] = {
    "notepad": "notepad.exe",
    "editor": "notepad.exe",
    "windows editor": "notepad.exe",
    "texteditor": "notepad.exe",
    "calculator": "calc.exe",
    "rechner": "calc.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "paint": "mspaint.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "terminal": "wt.exe",
    "chrome": "chrome",
    "edge": "msedge",
    "firefox": "firefox",
    "vscode": "code",
    "visual studio code": "code",
}


def _fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return "".join(ch for ch in text if ch.isalnum()).casefold()


def resolve_launcher_name(spoken: str) -> str:
    key = (spoken or "").strip().lower()
    if key in ALIASES:
        return ALIASES[key]
    for alias, target in sorted(ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
        if alias in key:
            return target
    return spoken.strip()


def find_running_pids(app_name: str) -> List[int]:
    """Find running process PIDs matching app_name (fast single-pass scan)."""
    launcher = resolve_launcher_name(app_name)
    queries = {_fold(app_name), _fold(os.path.splitext(launcher)[0])}
    queries.discard("")
    self_pid = os.getpid()
    matched: List[int] = []

    for proc in psutil.process_iter(["pid", "name"]):
        try:
            pid = proc.info["pid"]
            if pid == self_pid:
                continue
            stem = _fold(os.path.splitext(proc.info.get("name") or "")[0])
            if not stem:
                continue
            if any(q == stem or (len(q) >= 4 and (stem.startswith(q) or q in stem)) for q in queries):
                matched.append(int(pid))
        except Exception:
            continue
    return matched


def _safe_enum_windows(callback: object) -> None:
    """Enumerate top-level windows on the interactive Default desktop (`Winsta0\\Default`)."""
    try:
        import win32con
        import win32service

        hdesk = win32service.OpenDesktop("Default", 0, False, win32con.MAXIMUM_ALLOWED)
        for h in hdesk.EnumDesktopWindows():
            try:
                if not callback(int(h), 0):
                    break
            except Exception:
                continue
        return
    except Exception:
        pass

    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def _cb(hwnd: int, lparam: int) -> bool:
        try:
            return bool(callback(int(hwnd), lparam))
        except Exception:
            return True

    user32.EnumWindows(WNDENUMPROC(_cb), 0)


def _spawn_on_default_desktop(cmd_vec: List[str]) -> Optional[int]:
    """Launch a GUI process explicitly on `Winsta0\\Default` so it is always visible to the user."""
    import ctypes
    from ctypes import wintypes

    class STARTUPINFOW(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("lpReserved", wintypes.LPWSTR),
            ("lpDesktop", wintypes.LPWSTR),
            ("lpTitle", wintypes.LPWSTR),
            ("dwX", wintypes.DWORD),
            ("dwY", wintypes.DWORD),
            ("dwXSize", wintypes.DWORD),
            ("dwYSize", wintypes.DWORD),
            ("dwXCountChars", wintypes.DWORD),
            ("dwYCountChars", wintypes.DWORD),
            ("dwFillAttribute", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("wShowWindow", wintypes.WORD),
            ("cbReserved2", wintypes.WORD),
            ("lpReserved2", ctypes.POINTER(wintypes.BYTE)),
            ("hStdInput", wintypes.HANDLE),
            ("hStdOutput", wintypes.HANDLE),
            ("hStdError", wintypes.HANDLE),
        ]

    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("hProcess", wintypes.HANDLE),
            ("hThread", wintypes.HANDLE),
            ("dwProcessId", wintypes.DWORD),
            ("dwThreadId", wintypes.DWORD),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    si = STARTUPINFOW()
    si.cb = ctypes.sizeof(STARTUPINFOW)
    si.lpDesktop = "Winsta0\\Default"
    pi = PROCESS_INFORMATION()

    cmd_str = subprocess.list2cmdline(cmd_vec)
    cmd_buf = ctypes.create_unicode_buffer(cmd_str)
    ok = kernel32.CreateProcessW(
        None,
        cmd_buf,
        None,
        None,
        False,
        0,
        None,
        None,
        ctypes.byref(si),
        ctypes.byref(pi),
    )
    if ok:
        if pi.hThread:
            kernel32.CloseHandle(pi.hThread)
        if pi.hProcess:
            kernel32.CloseHandle(pi.hProcess)
        return int(pi.dwProcessId)

    proc = subprocess.Popen(cmd_vec, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return int(proc.pid)


def get_hwnds_for_pids(pids: List[int]) -> List[int]:
    """Return visible top-level window handles belonging to any of the given PIDs."""
    pid_set = set(pids)
    if not pid_set:
        return []
    hwnds: List[int] = []

    def _cb(hwnd: int, _: object) -> bool:
        if win32gui.IsWindowVisible(hwnd):
            _, owner_pid = win32process.GetWindowThreadProcessId(hwnd)
            if int(owner_pid) in pid_set and win32gui.GetWindowTextLength(hwnd) > 0:
                hwnds.append(int(hwnd))
        return True

    _safe_enum_windows(_cb)
    return hwnds


@action(
    name="open_or_focus_app",
    description="Open an application or bring its window to the foreground if already running.",
    parameters={"app_name": "str", "args": "Optional[str]"},
)
def open_or_focus_app(app_name: str = "notepad.exe", args: str = "") -> str:
    """Launch or focus an application using direct argument vectors and Win32 AttachThreadInput."""
    spoken = (app_name or "").strip()
    if not spoken:
        return "status=failed action=open_or_focus_app reason=\"No app_name provided\""

    launcher = resolve_launcher_name(spoken)
    existing_pids = find_running_pids(spoken)
    if existing_pids and not args:
        hwnds = get_hwnds_for_pids(existing_pids)
        for hwnd in hwnds:
            if focus_hwnd_win32(hwnd):
                blackboard.set("last_focused_hwnd", hwnd)
                return f"status=done action=open_or_focus_app app=\"{launcher}\" already_running=true focused=true"

    executable = shutil.which(launcher) or shutil.which(spoken)
    cmd_vec: List[str] = [executable or launcher]
    if args:
        cmd_vec.append(args)

    try:
        spawned_pid = _spawn_on_default_desktop(cmd_vec)
    except Exception:
        # Fallback to os.startfile for URI schemes or shell-registered apps
        os.startfile(launcher)
        spawned_pid = None

    # Wait briefly for process & window to appear and focus it
    deadline = time.perf_counter() + 2.5
    focused_hwnd = None
    while time.perf_counter() < deadline:
        pids = find_running_pids(spoken)
        if spawned_pid is not None and spawned_pid not in pids:
            pids.insert(0, spawned_pid)
        hwnds = get_hwnds_for_pids(pids)
        if hwnds:
            for h in hwnds:
                focus_hwnd_win32(h)
                focused_hwnd = h
                break
            if focused_hwnd:
                break
        time.sleep(0.05)

    if focused_hwnd:
        blackboard.set("last_focused_hwnd", focused_hwnd)
    return f"status=done action=open_or_focus_app app=\"{launcher}\" focused={bool(focused_hwnd)}"


@action(
    name="write_text_to_notepad",
    description=(
        "Clean Window Lifecycle tool for Notepad/Editor: creates a clean UTF-8 text file "
        "or opens a fresh tab via Ctrl+N and writes 'text' without touching pre-existing tabs."
    ),
    parameters={"text": "str", "filename": "Optional[str]", "new_tab_via_hotkey": "Optional[bool]"},
)
def write_text_to_notepad(text: str = "", filename: str = "", new_tab_via_hotkey: bool = False) -> str:
    """
    Implement the Clean Window Lifecycle for Notepad:
    Mode A (default / atomic file):
      1. Atomically write `text` to a dedicated clean file via `tools/file_ops.py` so existing tabs
         (e.g., open files with API keys) are NEVER modified or overwritten.
      2. Launch `notepad.exe <path>` as a direct argument vector, which opens a clean tab/window
         for that file in Windows 11 Notepad.
      3. Wait for the Notepad window to appear and bring it to the foreground.
    Mode B (`new_tab_via_hotkey=True` or fallback):
      1. Launch or focus `notepad.exe` via Win32 Alt-key bypass (`focus_hwnd_win32`).
      2. Trigger `Ctrl+N` (`^n`) to open a clean untitled tab inside Notepad before pasting/typing `text`.
    """
    content = str(text or "")
    notepad_bin = shutil.which("notepad.exe") or "notepad.exe"

    # Also write an atomic backing file so verification and crash-safety always hold
    notes_dir = Path(__file__).resolve().parent.parent / "workspace" / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    if filename and filename.strip():
        target_path = resolve_user_path(filename.strip())
        if target_path.is_dir():
            digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:8]
            target_path = target_path / f"aether_note_{digest}.txt"
    else:
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:8]
        target_path = notes_dir / f"aether_note_{digest}.txt"

    written_path = atomic_write_text(target_path, content)
    blackboard.set("last_notepad_file", str(written_path))

    if new_tab_via_hotkey:
        # Ensure Notepad is running and focused, then open a new tab via Ctrl+N and write the text
        notepad_hwnds: List[int] = []

        def _collect_notepad_hwnds(hwnd: int, _: object) -> bool:
            if win32gui.IsWindowVisible(hwnd):
                cls_name = (win32gui.GetClassName(hwnd) or "").lower()
                title = (win32gui.GetWindowText(hwnd) or "").lower()
                if "notepad" in cls_name or "notepad" in title or "editor" in title:
                    notepad_hwnds.append(int(hwnd))
            return True

        _safe_enum_windows(_collect_notepad_hwnds)
        if not notepad_hwnds:
            spawned_pid = _spawn_on_default_desktop([notepad_bin])
            if spawned_pid:
                blackboard.set("last_spawned_pid", spawned_pid)
            deadline = time.perf_counter() + 1.5
            while time.perf_counter() < deadline:
                _safe_enum_windows(_collect_notepad_hwnds)
                if notepad_hwnds:
                    break
                time.sleep(0.03)

        if notepad_hwnds:
            target_hwnd = notepad_hwnds[0]
            focus_hwnd_win32(target_hwnd)
            blackboard.set("last_focused_hwnd", target_hwnd)
            ok = uia_executor.type_into_window(
                text=content,
                window_title="notepad",
                new_tab_first=True,
                hwnd=target_hwnd,
            )
            if ok:
                return (
                    f"status=done action=write_text_to_notepad mode=ctrl_n_new_tab "
                    f"path=\"{written_path}\" focused=true"
                )

    # Check if a Notepad window with this exact clean note is already open
    target_stem = written_path.stem.lower()
    existing_hwnds: List[int] = []

    def _find_note_hwnd(hwnd: int, _: object) -> bool:
        if win32gui.IsWindowVisible(hwnd):
            title = (win32gui.GetWindowText(hwnd) or "").lower()
            if target_stem in title:
                existing_hwnds.append(int(hwnd))
        return True

    _safe_enum_windows(_find_note_hwnd)
    if existing_hwnds:
        focus_hwnd_win32(existing_hwnds[0])
        blackboard.set("last_focused_hwnd", existing_hwnds[0])
        return f"status=done action=write_text_to_notepad path=\"{written_path}\" focused=true reused_clean_window=true"

    spawned_pid = _spawn_on_default_desktop([notepad_bin, str(written_path)])
    if spawned_pid:
        blackboard.set("last_spawned_pid", spawned_pid)

    # Fast window discovery (<50ms) without repeated full process_iter scans
    deadline = time.perf_counter() + 0.04
    focused = False
    while time.perf_counter() < deadline:
        hwnds = []

        def _find_any_notepad(hwnd: int, _: object) -> bool:
            if win32gui.IsWindowVisible(hwnd):
                cls_name = (win32gui.GetClassName(hwnd) or "").lower()
                title = (win32gui.GetWindowText(hwnd) or "").lower()
                if "notepad" in cls_name or target_stem in title or "notepad" in title or "editor" in title:
                    hwnds.append(int(hwnd))
            return True

        _safe_enum_windows(_find_any_notepad)
        if hwnds:
            focus_hwnd_win32(hwnds[0])
            blackboard.set("last_focused_hwnd", hwnds[0])
            focused = True
            break
        time.sleep(0.008)

    return (
        f"status=done action=write_text_to_notepad path=\"{written_path}\" "
        f"focused={str(focused).lower()}"
    )


@action(
    name="run_ps",
    description="Execute a fast non-destructive PowerShell command via the persistent UTF-8 REPL.",
    parameters={"command": "str"},
)
def run_ps(command: str = "") -> str:
    """Run a PowerShell command in the persistent sub-15ms PowerShell REPL."""
    return ps_repl.run(command)


@action(
    name="uia_click",
    description="Click a UI control by name in the active or specified non-terminal window via Windows UIA.",
    parameters={"control_name": "str", "window_title": "Optional[str]"},
)
def uia_click(control_name: str = "", window_title: str = "") -> str:
    """Tier 2 structural UIA control click."""
    ok = uia_executor.click_control_by_name(control_name=control_name, window_title=window_title)
    if ok:
        return f"status=done action=uia_click control=\"{control_name}\""
    return f"status=failed action=uia_click control=\"{control_name}\""


@action(
    name="uia_type",
    description="Type text into the active or specified non-terminal window via Windows UIA.",
    parameters={"text": "str", "window_title": "Optional[str]", "new_tab_first": "Optional[bool]"},
)
def uia_type(text: str = "", window_title: str = "", new_tab_first: bool = False) -> str:
    """Tier 2 structural UIA text entry."""
    ok = uia_executor.type_into_window(text=text, window_title=window_title, new_tab_first=bool(new_tab_first))
    if ok:
        return f"status=done action=uia_type window=\"{window_title}\""
    return f"status=failed action=uia_type window=\"{window_title}\""
