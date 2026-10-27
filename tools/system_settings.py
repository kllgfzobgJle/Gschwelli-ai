"""Core Desktop & OS Control tools: volume, brightness, theme, window management, clipboard, close_app, undo, and confirmation gate (ported from Mark-LVI computer_settings.py & computer_control.py)."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import time
from typing import Optional

import psutil
import win32con
import win32gui

from core.blackboard import blackboard
from core.confirm import request_confirmation, resolve as resolve_confirmation
from core.safety import is_terminal_window, own_process_chain_pids
from core.undo import history as undo_history, push_undo, undo_last
from executors.ps_repl import ps_repl
from executors.win32_uia import _safe_enum_windows, find_window_by_title, focus_hwnd_win32, get_active_target_hwnd
from tools.app_lifecycle import find_running_pids, get_hwnds_for_pids
from tools.registry import action


def _win_endpoint_volume():
    """Return Windows master volume COM endpoint via pycaw."""
    from ctypes import POINTER, cast
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    speakers = AudioUtilities.GetSpeakers()
    endpoint = getattr(speakers, "EndpointVolume", None)
    if endpoint is not None:
        return endpoint
    dev = getattr(speakers, "_dev", speakers)
    return cast(dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None), POINTER(IAudioEndpointVolume))


def get_master_volume() -> Optional[int]:
    try:
        scalar = _win_endpoint_volume().GetMasterVolumeLevelScalar()
        return max(0, min(100, round(scalar * 100)))
    except Exception:
        return None


def set_master_volume(level: int) -> bool:
    level = max(0, min(100, int(level)))
    try:
        _win_endpoint_volume().SetMasterVolumeLevelScalar(level / 100.0, None)
        return True
    except Exception:
        return False


@action(
    name="system_control",
    description=(
        "Adjust or query Windows 11 system settings: volume_set, volume_up, volume_down, volume_mute, "
        "brightness_set, dark_mode, light_mode, minimize_window, maximize_window, snap_left, snap_right, "
        "show_desktop, lock_screen, shutdown, restart."
    ),
    parameters={"action": "str", "value": "Optional[int]", "target": "Optional[str]"},
)
def system_control(action: str = "volume_set", value: int = 50, target: str = "") -> str:
    """Fast sub-50ms Windows 11 system and window control with Undo and Confirmation Gate integration."""
    act = (action or "").strip().lower()
    user32 = ctypes.WinDLL("user32", use_last_error=True)

    if act == "volume_set":
        old = get_master_volume()
        ok = set_master_volume(value)
        if ok and old is not None:
            push_undo(f"volume -> {value}%", lambda prev=old: (set_master_volume(prev), f"Restored volume to {prev}%")[1])
        return f"status={'done' if ok else 'failed'} action=system_control setting=volume value={value}"

    if act in ("volume_up", "volume_down"):
        old = get_master_volume() or 50
        step = int(value) if value and value != 50 else 10
        new_val = min(100, old + step) if act == "volume_up" else max(0, old - step)
        ok = set_master_volume(new_val)
        if ok:
            push_undo(f"volume -> {new_val}%", lambda prev=old: (set_master_volume(prev), f"Restored volume to {prev}%")[1])
        return f"status={'done' if ok else 'failed'} action=system_control setting={act} value={new_val}"

    if act in ("volume_mute", "mute", "unmute"):
        try:
            ep = _win_endpoint_volume()
            cur_mute = bool(ep.GetMute())
            new_mute = False if act == "unmute" else (True if act == "mute" else not cur_mute)
            ep.SetMute(1 if new_mute else 0, None)
            push_undo(f"mute -> {new_mute}", lambda prev=cur_mute: (ep.SetMute(1 if prev else 0, None), "Toggled mute back")[1])
            return f"status=done action=system_control setting=mute muted={str(new_mute).lower()}"
        except Exception:
            VK_VOLUME_MUTE = 0xAD
            user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
            user32.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)
            return "status=done action=system_control setting=mute"

    if act == "brightness_set":
        lvl = max(0, min(100, int(value)))
        out = ps_repl.run(
            f"(Get-WmiObject -Namespace root/wmi -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {lvl})"
        )
        return f"status=done action=system_control setting=brightness value={lvl} detail={out!r}"

    if act in ("dark_mode", "light_mode"):
        val = 0 if act == "dark_mode" else 1
        opposite = 1 - val
        reg_cmd = (
            f"Set-ItemProperty -Path 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize' "
            f"-Name 'AppsUseLightTheme' -Value {val}; "
            f"Set-ItemProperty -Path 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize' "
            f"-Name 'SystemUsesLightTheme' -Value {val}"
        )
        ps_repl.run(reg_cmd)
        push_undo(
            f"theme -> {act}",
            lambda opp=opposite: ps_repl.run(
                f"Set-ItemProperty -Path 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize' "
                f"-Name 'AppsUseLightTheme' -Value {opp}; "
                f"Set-ItemProperty -Path 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize' "
                f"-Name 'SystemUsesLightTheme' -Value {opp}"
            ),
        )
        return f"status=done action=system_control setting={act}"

    if act in ("minimize_window", "maximize_window", "restore_window"):
        hwnd = find_window_by_title(target, exclude_terminal=True) if target else get_active_target_hwnd(exclude_terminal=True)
        if not hwnd:
            return "status=failed action=system_control reason=\"No non-terminal window found\""
        cmd = (
            win32con.SW_MINIMIZE
            if act == "minimize_window"
            else (win32con.SW_MAXIMIZE if act == "maximize_window" else win32con.SW_RESTORE)
        )
        win32gui.ShowWindow(hwnd, cmd)
        return f"status=done action=system_control window_action={act} hwnd={hwnd}"

    if act in ("snap_left", "snap_right"):
        hwnd = find_window_by_title(target, exclude_terminal=True) if target else get_active_target_hwnd(exclude_terminal=True)
        if not hwnd:
            return "status=failed action=system_control reason=\"No non-terminal window found\""
        focus_hwnd_win32(hwnd)
        VK_LWIN = 0x5B
        VK_ARROW = 0x25 if act == "snap_left" else 0x27
        user32.keybd_event(VK_LWIN, 0, 0, 0)
        user32.keybd_event(VK_ARROW, 0, 0, 0)
        user32.keybd_event(VK_ARROW, 0, 2, 0)
        user32.keybd_event(VK_LWIN, 0, 2, 0)
        return f"status=done action=system_control window_action={act} hwnd={hwnd}"

    if act == "lock_screen":
        return request_confirmation(
            "lock_screen",
            "Lock Windows Workstation",
            "Lock the desktop screen immediately?",
            lambda: (ctypes.windll.user32.LockWorkStation(), "Workstation locked")[1],
        )

    if act in ("shutdown", "restart"):
        flag = "/s" if act == "shutdown" else "/r"
        return request_confirmation(
            act,
            f"System {act.title()}",
            f"Are you sure you want to {act} this computer?",
            lambda f=flag: ps_repl.run(f"shutdown.exe {f} /t 5"),
        )

    return f"status=failed action=system_control reason=\"Unknown system_control action '{act}'\""


@action(
    name="close_app",
    description="Politely close a running application via WM_CLOSE without ever closing AETHER or the terminal.",
    parameters={"app_name": "str"},
)
def close_app(app_name: str = "") -> str:
    """Polite WM_CLOSE application shutdown adapted from Mark-LVI appidentity.py & computer_control.py."""
    spoken = (app_name or "").strip()
    if not spoken:
        return "status=failed action=close_app reason=\"No app_name provided\""

    own_pids = own_process_chain_pids()
    pids = [p for p in find_running_pids(spoken) if p not in own_pids]
    if not pids:
        return f"status=failed action=close_app reason=\"No running non-protected process found matching '{spoken}'\""

    hwnds = [h for h in get_hwnds_for_pids(pids) if not is_terminal_window(h)]
    WM_CLOSE = 0x0010
    asked = 0
    for hwnd in hwnds:
        try:
            win32gui.PostMessage(hwnd, WM_CLOSE, 0, 0)
            asked += 1
        except Exception:
            continue

    if asked == 0:
        for pid in pids:
            try:
                psutil.Process(pid).terminate()
                asked += 1
            except Exception:
                continue

    time.sleep(0.15)
    remaining = [p for p in pids if psutil.pid_exists(p)]
    return (
        f"status=done action=close_app app=\"{spoken}\" requested={asked} "
        f"closed={len(pids) - len(remaining)} remaining={len(remaining)}"
    )


@action(
    name="clipboard_op",
    description="Read from or write text to the Windows clipboard (`action='get'` or `action='set'`).",
    parameters={"action": "str", "text": "Optional[str]"},
)
def clipboard_op(action: str = "get", text: str = "") -> str:
    import pyperclip

    mode = (action or "get").strip().lower()
    if mode in ("set", "write", "copy"):
        old = ""
        try:
            old = pyperclip.paste() or ""
        except Exception:
            pass
        pyperclip.copy(str(text or ""))
        if old:
            push_undo("clipboard change", lambda prev=old: (pyperclip.copy(prev), "Restored previous clipboard")[1])
        return f"status=done action=clipboard_op mode=set length={len(text or '')}"
    val = pyperclip.paste() or ""
    return f"status=done action=clipboard_op mode=get content={val!r}"


@action(
    name="undo_action",
    description="Reverse the most recent reversible operation (file write/move, volume, theme, clipboard) or list undo history.",
    parameters={"mode": "Optional[str]"},
)
def undo_action(mode: str = "undo") -> str:
    if (mode or "").strip().lower() == "list":
        items = undo_history()
        return f"status=done action=undo_action count={len(items)} history={items!r}"
    return undo_last()


@action(
    name="confirm_pending",
    description="Approve or cancel a pending irreversible action waiting in the confirmation gate.",
    parameters={"accepted": "bool"},
)
def confirm_pending(accepted: bool = True) -> str:
    return resolve_confirmation(bool(accepted))
