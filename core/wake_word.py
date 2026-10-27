"""Optional hands-free wake-word detector using `openwakeword` (ported from Mark-LVI)."""

from __future__ import annotations

import threading
import time
from typing import Callable


class WakeWordDetector:
    """Listens for a wake phrase ('Hey Jarvis' / 'Aether') when enabled; falls back cleanly to Push-to-Talk."""

    def __init__(self, on_wake: Callable[[], None], model_name: str = "hey_jarvis") -> None:
        self._on_wake = on_wake
        self.model_name = model_name
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.available = False
        try:
            import openwakeword  # noqa: F401

            self.available = True
        except ImportError:
            self.available = False

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> bool:
        if not self.available or self.running:
            return False
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="aether-wakeword", daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        self._stop.set()
        t, self._thread = self._thread, None
        if t is not None and t.is_alive():
            t.join(timeout=1.0)

    def _loop(self) -> None:
        try:
            import numpy as np
            from openwakeword.model import Model
            import sounddevice as sd

            oww = Model(wakeword_models=[self.model_name])
            cooldown_until = 0.0

            def _cb(indata, frames, time_info, status):
                nonlocal cooldown_until
                now = time.monotonic()
                if now < cooldown_until:
                    return
                pcm16 = (indata[:, 0] * 32767).astype(np.int16)
                preds = oww.predict(pcm16)
                for score in preds.values():
                    if float(score) >= 0.55:
                        cooldown_until = now + 2.5
                        try:
                            self._on_wake()
                        except Exception:
                            pass
                        break

            with sd.InputStream(samplerate=16000, channels=1, dtype="float32", blocksize=1280, callback=_cb):
                while not self._stop.is_set():
                    self._stop.wait(0.1)
        except Exception:
            return
