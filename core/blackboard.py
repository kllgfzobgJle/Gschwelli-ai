"""Shared in-memory state blackboard for AETHER execution turns."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LogEntry:
    timestamp_ms: float
    tier: int
    message: str
    level: str = "INFO"


class Blackboard:
    """Thread-safe shared state and telemetry log across tiers and tools."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._state: Dict[str, Any] = {}
        self._logs: List[LogEntry] = []
        self._t0: float = time.perf_counter()

    def reset_turn(self) -> None:
        with self._lock:
            self._t0 = time.perf_counter()
            self._logs.clear()

    def elapsed_ms(self) -> float:
        return (time.perf_counter() - self._t0) * 1000.0

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._state[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._state.get(key, default)

    def log(self, tier: int, message: str, level: str = "INFO") -> None:
        with self._lock:
            self._logs.append(
                LogEntry(
                    timestamp_ms=self.elapsed_ms(),
                    tier=tier,
                    message=message,
                    level=level,
                )
            )

    def get_logs(self) -> List[LogEntry]:
        with self._lock:
            return list(self._logs)


# Singleton blackboard instance
blackboard = Blackboard()
