# AETHER — Tiered Hybrid Automation Router

Lightweight, zero-latency, local-first Windows 11 desktop automation router built around a **4-Tier Waterfall Architecture**:

1. **Tier 0 — Deterministic SQLite Cache (`<10 ms`)**:
   - Instant SHA-256 instruction lookup via `cache/aether.db` (`engines/cache_store.py`).
2. **Tier 1 — Local Fast-Path Executor (`<1.5 s`)**:
   - Local planning via Ollama (`qwen2.5-coder:7b` at `http://localhost:11434/api/chat`), executing direct OS/file/app actions or persistent UTF-8 PowerShell REPL commands (`executors/ps_repl.py`). No screenshots in Tier 1.
3. **Tier 2 — Structural Windows UIA / Accessibility (`0.1s - 0.5s`)**:
   - Direct Windows UI Automation tree inspection and control invocation (`executors/win32_uia.py`) with terminal self-protection (`core/safety.py`).
4. **Tier 3 — Selective Cloud Vision Fallback (`3s - 8s`)**:
   - Active target window bounding-box capture (`mss` + `win32gui.GetWindowRect`), Pillow Set-of-Marks (`[1]`, `[2]`, ...) overlay (`executors/vision_som.py`), and `gemini-3.8-flash` (`v1beta`) planning with `thought` / `thought_signature` stripping (`engines/gemini_engine.py`).

## Clean Window Lifecycle for Notepad
`tools/app_lifecycle.py` supports two safe ways to open Notepad and write text without overwriting pre-existing tabs:
- **Atomic Document Launch**: Atomically writes a clean UTF-8 file via `tools/file_ops.py` and launches `notepad.exe <path>` on the interactive desktop (`Winsta0\Default`).
- **In-App New Tab (`Ctrl+N`)**: Focuses or launches Notepad on `Winsta0\Default`, triggers `Ctrl+N` to open a fresh tab, and pastes/types the text.

## Usage
```powershell
# Direct execution mode
python main.py -r "Starte den Windows Editor (Notepad) und schreibe den Text 'AETHER Setup erfolgreich' in ein neues Dokument."

# Open a new tab inside Notepad via Ctrl+N and write text
python main.py -r "Open notepad and write 'Hello from a new tab' in a new tab"

# Interactive REPL mode
python main.py
```
