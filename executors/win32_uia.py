"""Structural Windows UIA / Accessibility Executor (Tier 2, 0.1s - 0.5s)."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import win32con
import win32gui
import win32process

from core.blackboard import blackboard
from core.safety import is_terminal_window


def _safe_enum_windows(callback: Any) -> None:
    """Enumerate top-level windows on the interactive Default desktop (`Winsta0\\Default`)."""
    try:
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


def get_active_target_hwnd(exclude_terminal: bool = True) -> Optional[int]:
    """Return the foreground window handle, or the top-most visible non-terminal window."""
    fg = win32gui.GetForegroundWindow()
    if fg and win32gui.IsWindowVisible(fg):
        if not (exclude_terminal and is_terminal_window(fg)):
            return int(fg)

    # Enumerate Z-order top-to-bottom to find the most recent user window
    found: List[int] = []

    def _enum_cb(hwnd: int, _: Any) -> bool:
        if not win32gui.IsWindowVisible(hwnd) or win32gui.IsIconic(hwnd):
            return True
        title = win32gui.GetWindowText(hwnd) or ""
        if not title.strip():
            return True
        cls_name = win32gui.GetClassName(hwnd) or ""
        if cls_name in {"Progman", "WorkerW", "Shell_TrayWnd"}:
            return True
        if exclude_terminal and is_terminal_window(hwnd):
            return True
        found.append(int(hwnd))
        return True

    _safe_enum_windows(_enum_cb)
    return found[0] if found else None


def find_window_by_title(title_fragment: str, exclude_terminal: bool = True) -> Optional[int]:
    """Find a visible top-level window whose title contains title_fragment."""
    query = (title_fragment or "").strip().lower()
    if not query:
        return get_active_target_hwnd(exclude_terminal=exclude_terminal)

    matches: List[int] = []

    def _enum_cb(hwnd: int, _: Any) -> bool:
        if not win32gui.IsWindowVisible(hwnd):
            return True
        if exclude_terminal and is_terminal_window(hwnd):
            return True
        title = (win32gui.GetWindowText(hwnd) or "").lower()
        cls_name = (win32gui.GetClassName(hwnd) or "").lower()
        if query in title or (query == "notepad" and ("notepad" in cls_name or "editor" in title)):
            matches.append(int(hwnd))
        return True

    _safe_enum_windows(_enum_cb)
    return matches[0] if matches else None


def focus_hwnd_win32(hwnd: int) -> bool:
    """Focus a window reliably using Win32 AttachThreadInput + Alt-key bypass."""
    if not hwnd or not win32gui.IsWindow(hwnd):
        return False
    try:
        import ctypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, win32con.SW_RESTORE)

        if user32.SetForegroundWindow(hwnd):
            return True

        # Alt-key bypass + AttachThreadInput (adapted from Mark-LVI appidentity.py)
        VK_MENU = 0x12
        KEYEVENTF_EXTENDEDKEY = 0x0001
        KEYEVENTF_KEYUP = 0x0002
        user32.keybd_event(VK_MENU, 0, KEYEVENTF_EXTENDEDKEY, 0)
        try:
            fore = user32.GetForegroundWindow()
            their = user32.GetWindowThreadProcessId(fore, None) if fore else 0
            ours = kernel32.GetCurrentThreadId()
            attached = False
            if their and their != ours:
                attached = bool(user32.AttachThreadInput(ours, their, True))
            try:
                user32.BringWindowToTop(hwnd)
                user32.ShowWindow(hwnd, win32con.SW_SHOW)
                user32.SetForegroundWindow(hwnd)
            finally:
                if attached:
                    user32.AttachThreadInput(ours, their, False)
        finally:
            user32.keybd_event(VK_MENU, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)

        return int(user32.GetForegroundWindow()) == int(hwnd)
    except Exception:
        return False


class Win32UIAExecutor:
    """Tier 2 executor for querying and operating on Windows UIA controls."""

    def inspect_window_controls(self, hwnd: Optional[int] = None, max_elements: int = 40) -> List[Dict[str, Any]]:
        """Query the target window's UIA tree for interactive controls and their bounding boxes."""
        target_hwnd = hwnd or get_active_target_hwnd(exclude_terminal=True)
        if not target_hwnd or is_terminal_window(target_hwnd):
            return []

        elements: List[Dict[str, Any]] = []
        try:
            from pywinauto import Desktop

            win = Desktop(backend="uia").window(handle=target_hwnd)
            descendants = win.descendants()
            interactive_types = {
                "Button",
                "Edit",
                "Document",
                "MenuItem",
                "TabItem",
                "ComboBox",
                "CheckBox",
                "RadioButton",
                "Hyperlink",
                "ListItem",
            }
            for idx, ctrl in enumerate(descendants):
                if len(elements) >= max_elements:
                    break
                try:
                    info = ctrl.element_info
                    ctrl_type = getattr(info, "control_type", "") or ""
                    if ctrl_type not in interactive_types:
                        continue
                    if not info.visible:
                        continue
                    rect = info.rectangle
                    w = rect.right - rect.left
                    h = rect.bottom - rect.top
                    if w <= 4 or h <= 4:
                        continue
                    name = (info.name or "").strip()
                    elements.append(
                        {
                            "id": len(elements) + 1,
                            "name": name,
                            "control_type": ctrl_type,
                            "rect": (int(rect.left), int(rect.top), int(rect.right), int(rect.bottom)),
                            "center": (int(rect.left + w // 2), int(rect.top + h // 2)),
                            "hwnd": target_hwnd,
                        }
                    )
                except Exception:
                    continue
        except Exception as exc:
            blackboard.log(2, f"UIA inspection warning: {exc}", "WARN")
        return elements

    def click_control_by_name(self, control_name: str, window_title: str = "") -> bool:
        """Find a UIA control by name in the target non-terminal window and invoke/click it."""
        hwnd = find_window_by_title(window_title, exclude_terminal=True)
        if not hwnd or is_terminal_window(hwnd):
            return False

        query = (control_name or "").strip().lower()
        if not query:
            return False

        try:
            from pywinauto import Desktop

            focus_hwnd_win32(hwnd)
            win = Desktop(backend="uia").window(handle=hwnd)
            for ctrl in win.descendants():
                try:
                    info = ctrl.element_info
                    if not info.visible:
                        continue
                    name = (info.name or "").strip().lower()
                    if query == name or query in name:
                        try:
                            ctrl.invoke()
                            return True
                        except Exception:
                            ctrl.click_input()
                            return True
                except Exception:
                    continue
        except Exception as exc:
            blackboard.log(2, f"UIA click_control_by_name error: {exc}", "WARN")
        return False

    def type_into_window(
        self,
        text: str,
        window_title: str = "",
        new_tab_first: bool = False,
        hwnd: Optional[int] = None,
    ) -> bool:
        """Focus target window via UIA/Win32 and type or set text in its Edit/Document control."""
        target_hwnd = hwnd or find_window_by_title(window_title, exclude_terminal=True)
        if not target_hwnd or is_terminal_window(target_hwnd):
            return False

        focus_hwnd_win32(target_hwnd)
        time.sleep(0.04)

        try:
            import ctypes

            user32 = ctypes.WinDLL("user32", use_last_error=True)
            VK_CONTROL = 0x11
            VK_N = 0x4E
            VK_V = 0x56
            KEYEVENTF_KEYUP = 0x0002

            if new_tab_first:
                # Send Ctrl+N via Win32 keybd_event to open a new tab cleanly
                user32.keybd_event(VK_CONTROL, 0, 0, 0)
                user32.keybd_event(VK_N, 0, 0, 0)
                user32.keybd_event(VK_N, 0, KEYEVENTF_KEYUP, 0)
                user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
                time.sleep(0.12)

            # Try UIA Document/Edit value/focus if available on same desktop
            try:
                from pywinauto import Desktop

                win = Desktop(backend="uia").window(handle=target_hwnd)
                for ctrl in win.descendants():
                    try:
                        ctype = ctrl.element_info.control_type
                        if ctype in ("Document", "Edit") and ctrl.element_info.visible:
                            ctrl.set_focus()
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            import pyperclip

            pyperclip.copy(text)
            time.sleep(0.02)
            user32.keybd_event(VK_CONTROL, 0, 0, 0)
            user32.keybd_event(VK_V, 0, 0, 0)
            user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
            return True
        except Exception as exc:
            blackboard.log(2, f"UIA type_into_window error: {exc}", "WARN")
            return False


uia_executor = Win32UIAExecutor()
