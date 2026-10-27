"""Persistent PowerShell REPL with UTF-8 encoding and UUID sentinel output markers for sub-15ms execution."""

from __future__ import annotations

import subprocess
import threading
import time
import uuid
from typing import Optional

from core.safety import is_safe_powershell_command


class PowerShellREPL:
    """Persistent background PowerShell session using UUID sentinel markers."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._proc: Optional[subprocess.Popen[str]] = None

    def _ensure_started(self) -> subprocess.Popen[str]:
        if self._proc is not None and self._proc.poll() is None:
            return self._proc

        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        self._proc = subprocess.Popen(
            [
                "powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "-",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            creationflags=creationflags,
        )
        # Initialize UTF-8 console output encoding once
        init_sentinel = f"__AETHER_INIT_{uuid.uuid4().hex}__"
        assert self._proc.stdin is not None
        assert self._proc.stdout is not None
        init_cmd = (
            "[Console]::InputEncoding = [System.Text.Encoding]::UTF8; "
            "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
            "$OutputEncoding = [System.Text.Encoding]::UTF8; "
            f"Write-Output '{init_sentinel}'\n"
        )
        self._proc.stdin.write(init_cmd)
        self._proc.stdin.flush()
        while True:
            line = self._proc.stdout.readline()
            if not line or init_sentinel in line:
                break
        return self._proc

    def run(self, command: str, timeout: float = 10.0) -> str:
        """Execute a PowerShell command inside the persistent session and return stdout."""
        ok, reason = is_safe_powershell_command(command)
        if not ok:
            return f"status=failed action=run_ps reason=\"{reason}\""

        with self._lock:
            proc = self._ensure_started()
            assert proc.stdin is not None
            assert proc.stdout is not None

            sentinel = f"__AETHER_DONE_{uuid.uuid4().hex}__"
            wrapped = (
                f"try {{ {command} }} catch {{ Write-Output ('[PS_ERROR] ' + $_.Exception.Message) }}; "
                f"Write-Output '{sentinel}'\n"
            )
            proc.stdin.write(wrapped)
            proc.stdin.flush()

            lines: list[str] = []
            deadline = time.perf_counter() + timeout
            while time.perf_counter() < deadline:
                line = proc.stdout.readline()
                if not line:
                    break
                if sentinel in line:
                    before = line.split(sentinel)[0].rstrip("\r\n")
                    if before:
                        lines.append(before)
                    break
                lines.append(line.rstrip("\r\n"))

            output = "\n".join(lines).strip()
            return output if output else "status=done action=run_ps"

    def close(self) -> None:
        with self._lock:
            if self._proc is not None and self._proc.poll() is None:
                try:
                    self._proc.terminate()
                except Exception:
                    pass
                self._proc = None


# Singleton persistent REPL instance
ps_repl = PowerShellREPL()
