"""Global Push-to-Talk (`Ctrl+Space`) detector using Win32 `GetAsyncKeyState` at 30 Hz (ported from Mark-LVI)."""

from __future__ import annotations

import platform
import threading
import time
from typing import Callable

_OS = platform.system()
DEFAULT_CHORD = ("ctrl", "space")

_VK = {
    "ctrl": 0x11,
    "shift": 0x10,
    "alt": 0x12,
    "space": 0x20,
    "f8": 0x77,
    "f9": 0x78,
    "f10": 0x79,
    "capslock": 0x14,
    "insert": 0x2D,
}

_QT_NAME = {
    "ctrl": "Ctrl",
    "shift": "Shift",
    "alt": "Alt",
    "space": "Space",
    "f8": "F8",
    "f9": "F9",
    "f10": "F10",
    "capslock": "CapsLock",
    "insert": "Ins",
}

_POLL_HZ = 30.0
_DEBOUNCE_S = 0.06


def chord_label(chord=DEFAULT_CHORD) -> str:
    """Human-readable name of the chord."""
    return "+".join(_QT_NAME.get(k, k.title()) for k in chord)


def qt_sequence(chord=DEFAULT_CHORD) -> str:
    """The same chord as a QKeySequence string."""
    return "+".join(_QT_NAME.get(k, k.title()) for k in chord)


class PushToTalk:
    """Calls `on_change(held: bool)` whenever `Ctrl+Space` is pressed or released globally on Windows."""

    def __init__(self, on_change: Callable[[bool], None], chord=DEFAULT_CHORD) -> None:
        self._on_change = on_change
        self._chord = tuple(chord)
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._held = False
        self._scope = "window"

    @property
    def held(self) -> bool:
        return self._held

    @property
    def scope(self) -> str:
        return self._scope

    @property
    def label(self) -> str:
        return chord_label(self._chord)

    def start(self) -> str:
        self.stop()
        self._stop.clear()
        if _OS == "Windows" and self._can_poll():
            self._scope = "global"
            self._thread = threading.Thread(target=self._poll_loop, name="aether-push-to-talk", daemon=True)
            self._thread.start()
        else:
            self._scope = "window"
        return self._scope

    def stop(self) -> None:
        self._stop.set()
        t, self._thread = self._thread, None
        if t is not None and t.is_alive():
            t.join(timeout=1.0)
        self._set_held(False)

    def set_held(self, held: bool) -> None:
        self._set_held(bool(held))

    def _can_poll(self) -> bool:
        try:
            import ctypes

            _ = ctypes.windll.user32.GetAsyncKeyState
            return all(k in _VK for k in self._chord)
        except Exception:
            return False

    def _set_held(self, held: bool) -> None:
        if held == self._held:
            return
        self._held = held
        try:
            self._on_change(held)
        except Exception:
            pass

    def _poll_loop(self) -> None:
        import ctypes

        user32 = ctypes.windll.user32
        codes = [_VK[k] for k in self._chord]
        period = 1.0 / _POLL_HZ
        down_since = 0.0

        while not self._stop.is_set():
            try:
                down = all(user32.GetAsyncKeyState(c) & 0x8000 for c in codes)
            except Exception:
                break
            now = time.monotonic()
            if down:
                if down_since == 0.0:
                    down_since = now
                elif now - down_since >= _DEBOUNCE_S:
                    self._set_held(True)
            else:
                down_since = 0.0
                self._set_held(False)
            self._stop.wait(period)

        self._set_held(False)
        self._scope = "window"
