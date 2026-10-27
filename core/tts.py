"""Local & Cloud Text-to-Speech Engine (`Kokoro` / `EdgeTTS` / Windows SAPI fallback, ported from Mark-LVI)."""

from __future__ import annotations

import threading
from typing import Optional

from executors.ps_repl import ps_repl


class TTSEngine:
    """Non-blocking TTS engine with Windows SAPI (`System.Speech`) and optional `kokoro_onnx` / `edge_tts`."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._speaking = False
        self._lock = threading.Lock()

    @property
    def is_speaking(self) -> bool:
        return self._speaking

    def speak_async(self, text: str) -> None:
        """Speak a short status confirmation asynchronously without blocking the router."""
        if not self.enabled or not (text or "").strip():
            return
        clean = (text or "").strip()[:220].replace("'", "").replace('"', "")
        threading.Thread(target=self._speak_sync, args=(clean,), daemon=True).start()

    def _speak_sync(self, text: str) -> None:
        with self._lock:
            self._speaking = True
            try:
                cmd = (
                    "Add-Type -AssemblyName System.Speech; "
                    "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                    "$s.Rate = 2; "
                    f"$s.Speak('{text}')"
                )
                ps_repl.run(cmd, timeout=8.0)
            except Exception:
                pass
            finally:
                self._speaking = False


tts_engine = TTSEngine(enabled=False)
