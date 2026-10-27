"""Local Speech-to-Text (`WhisperSTT` with lazy loading and energy VAD, ported from Mark-LVI)."""

from __future__ import annotations

import threading
import time
from typing import Callable, Optional
import numpy as np


class WhisperSTT:
    """Lazy-loaded local Speech-to-Text engine using `faster-whisper` (`base`, int8 CPU)."""

    def __init__(self, model_size: str = "base", language: Optional[str] = None) -> None:
        self.model_size = model_size
        self.language = language
        self._model = None
        self._lock = threading.Lock()
        self.available = False
        self._check_availability()

    def _check_availability(self) -> None:
        try:
            import faster_whisper  # noqa: F401

            self.available = True
        except ImportError:
            self.available = False

    def _ensure_model(self) -> bool:
        if self._model is not None:
            return True
        with self._lock:
            if self._model is not None:
                return True
            try:
                from faster_whisper import WhisperModel

                self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
                self.available = True
                return True
            except Exception:
                self.available = False
                return False

    def transcribe_pcm(self, pcm_float32: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe a 16kHz float32 mono numpy array into text."""
        if pcm_float32 is None or pcm_float32.size < int(sample_rate * 0.25):
            return ""
        if not self._ensure_model():
            return ""
        try:
            segments, _ = self._model.transcribe(
                pcm_float32,
                language=self.language,
                beam_size=1,
                vad_filter=True,
            )
            text = " ".join(seg.text.strip() for seg in segments).strip()
            return text
        except Exception:
            return ""

    def record_while_held(
        self,
        is_held_fn: Callable[[], bool],
        max_seconds: float = 15.0,
        sample_rate: int = 16000,
    ) -> np.ndarray:
        """Record 16kHz mono float32 audio from default microphone while `is_held_fn()` is True."""
        try:
            import sounddevice as sd
        except ImportError:
            return np.zeros(0, dtype=np.float32)

        chunks: list[np.ndarray] = []
        block_size = 1024

        def _callback(indata, frames, time_info, status):
            chunks.append(indata[:, 0].copy())

        t0 = time.monotonic()
        try:
            with sd.InputStream(
                samplerate=sample_rate,
                channels=1,
                dtype="float32",
                blocksize=block_size,
                callback=_callback,
            ):
                while is_held_fn() and (time.monotonic() - t0) < max_seconds:
                    time.sleep(0.03)
        except Exception:
            return np.zeros(0, dtype=np.float32)

        if not chunks:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(chunks, axis=0)


stt_engine = WhisperSTT()
