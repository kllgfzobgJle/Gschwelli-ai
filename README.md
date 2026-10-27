# AETHER — 4-Tier Hybrid Windows 11 Desktop Automation Router

AETHER is a lightweight, zero-latency, local-first Windows 11 desktop automation system. It routes every incoming instruction through a strict 4-Tier Waterfall and features a Dual-Mode GUI (Floating Overlay + Web Control Center), Parameterized Tier 0 Template Caching, Persistent Memory, Reversible Undo Stack, Confirmation Gates, and Global Hotkey/Voice Control.

## Architecture (4-Tier Waterfall)

1. **TIER 0 (Deterministic SQLite & Parameterized Template Cache, `<10 ms`):**
   - Checks `cache/aether.db` (`verified_plans` for exact SHA-256 matches and `plan_templates` for parameterized `{slot_0}` matches).
   - Replays verified execution plans immediately without invoking any LLM.
2. **TIER 1 (Local Fast-Path Executor, `<1.5 s`):**
   - Queries local Ollama (`qwen2.5-coder:7b` at `http://localhost:11434/api/chat`).
   - Executes actions via native Python tools or persistent PowerShell REPL (`executors/ps_repl.py`). No screenshots allowed in Tier 1.
3. **TIER 2 (Structural Windows UIA / Accessibility, `0.1s - 0.5s`):**
   - Queries the active window's UI Automation tree (`executors/win32_uia.py`) and performs direct handle actions.
   - Blocks terminal/console self-clicks (`core/safety.py`).
4. **TIER 3 (Selective Cloud Vision Fallback, `3s - 8s`):**
   - Captures only the active target window bounding box (`executors/vision_som.py`), draws Set-of-Marks (`[1]`, `[2]`, ...) tags, compresses to JPEG, and queries `gemini-3.8-flash` (`v1beta`), stripping `thought` and `thought_signature` parts before JSON validation.

## Capabilities & Phases

- **Phase 1 — Core Action Library, Parameterized Cache, Memory & Gates:**
  - **22 Registered `@action` Tools** across `tools/app_lifecycle.py`, `tools/file_ops.py`, `tools/system_settings.py`, `tools/browser_ops.py`, `tools/productivity.py`, `tools/dev_tools.py`, and `memory/memory_manager.py`.
  - **Reversible Undo Stack (`core/undo.py`):**Snapshots overwritten files, newly created files, moves/renames, and system settings so `undo` reverses the last operation.
  - **Human Confirmation Gate (`core/confirm.py`):** Non-forgeable gate for destructive/power actions.
- **Phase 2 — Dual-Mode GUI:**
  - **Mode A (`ui/overlay.py`):** Frameless PyQt6 Floating Command Bar + System Tray icon summoned globally via `Ctrl+Space`.
  - **Mode B (`server/api.py` + `ui/dashboard/index.html`):** Full Dark-Glass Web/Desktop Control Center with live WebSocket telemetry, Cache Inspector, Tool Explorer, Memory Manager, and Undo Stack viewer.
- **Phase 3 — Hybrid Voice & Global Hotkey Daemon:**
  - **Global Push-to-Talk (`core/hotkey.py`):** 30 Hz Win32 `GetAsyncKeyState` listener for `Ctrl+Space`.
  - **Self-Calibrating Echo Cancellation (`core/echo.py`):** Band-energy subtraction (`EchoGuard`).
  - **Local STT & TTS (`core/stt.py`, `core/tts.py`, `engines/voice_engine.py`):** Lazy-loaded `faster-whisper` + non-blocking TTS feedback.

## Usage

```powershell
# Direct CLI execution
python main.py -r "Starte den Windows Editor (Notepad) und schreibe den Text 'AETHER Setup erfolgreich' in ein neues Dokument."

# Launch Dual-Mode GUI (Floating Overlay + System Tray + Control Center Server)
python main.py --gui

# Launch Dual-Mode GUI and open the Full Web Control Center Dashboard (http://127.0.0.1:8765)
python main.py --dashboard

# Interactive Terminal REPL
python main.py
```
