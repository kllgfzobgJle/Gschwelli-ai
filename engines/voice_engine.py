"""Hybrid Voice & Global Hotkey Daemon (`Ctrl+Space` Push-to-Talk + Local STT/TTS + Optional Gemini Live)."""

from __future__ import annotations

import threading
from typing import Callable, Optional

from core.blackboard import blackboard
from core.echo import EchoGuard
from core.hotkey import PushToTalk
from core.router import AetherRouter, RouteResult
from core.stt import stt_engine
from core.tts import tts_engine
from core.wake_word import WakeWordDetector


class VoiceDaemon:
    """
    Coordinates:
      1. Global Push-to-Talk (`Ctrl+Space`) at 30 Hz via Win32 `GetAsyncKeyState`
      2. Optional Wake-Word detection (`openwakeword`)
      3. Self-calibrating `EchoGuard`
      4. Local STT (`faster-whisper`) -> `AetherRouter.route()` -> TTS feedback
    """

    def __init__(
        self,
        router: AetherRouter,
        on_overlay_summon: Optional[Callable[[], None]] = None,
        on_status_change: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.router = router
        self._on_overlay_summon = on_overlay_summon
        self._on_status_change = on_status_change
        self.echo_guard = EchoGuard()
        self.ptt = PushToTalk(on_change=self._on_ptt_change)
        self.wake_word = WakeWordDetector(on_wake=self._on_wake_word)
        self.voice_capture_enabled = False
        self._recording_lock = threading.Lock()
        self.state = "idle"

    def _set_state(self, new_state: str) -> None:
        self.state = new_state
        if self._on_status_change:
            try:
                self._on_status_change(new_state)
            except Exception:
                pass

    def start(self, enable_wake_word: bool = False) -> str:
        scope = self.ptt.start()
        if enable_wake_word:
            self.wake_word.start()
        return scope

    def stop(self) -> None:
        self.ptt.stop()
        self.wake_word.stop()
        self._set_state("idle")

    def _on_wake_word(self) -> None:
        if self._on_overlay_summon:
            try:
                self._on_overlay_summon()
            except Exception:
                pass

    def _on_ptt_change(self, held: bool) -> None:
        if held:
            if self._on_overlay_summon:
                try:
                    self._on_overlay_summon()
                except Exception:
                    pass
            if self.voice_capture_enabled and stt_engine.available:
                threading.Thread(target=self._capture_and_route, daemon=True).start()
        else:
            if self.state == "listening":
                self._set_state("transcribing")

    def _capture_and_route(self) -> None:
        if not self._recording_lock.acquire(blocking=False):
            return
        try:
            self._set_state("listening")
            pcm = stt_engine.record_while_held(lambda: self.ptt.held)
            self._set_state("transcribing")
            transcript = stt_engine.transcribe_pcm(pcm)
            if transcript:
                blackboard.log(1, f"Voice STT transcript: '{transcript}'")
                self._set_state("routing")
                res: RouteResult = self.router.route(transcript)
                if tts_engine.enabled:
                    msg = f"Completed on Tier {res.active_tier}" if res.success else "Task could not be completed"
                    tts_engine.speak_async(msg)
        finally:
            self._set_state("idle")
            self._recording_lock.release()

    def status_dict(self) -> dict:
        return {
            "state": self.state,
            "hotkey": self.ptt.label,
            "hotkey_scope": self.ptt.scope,
            "stt_available": stt_engine.available,
            "wake_word_available": self.wake_word.available,
            "wake_word_running": self.wake_word.running,
            "tts_enabled": tts_engine.enabled,
            "voice_capture_enabled": self.voice_capture_enabled,
        }
