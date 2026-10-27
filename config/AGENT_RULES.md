# AETHER Agent Operational Rules

1. **Latency & Waterfall Priority**:
   - Always resolve identical verified requests via **Tier 0** (`cache/aether.db`) in `<10 ms`.
   - Execute OS commands, file creations, and clean app lifecycles via **Tier 1** (`qwen2.5-coder:7b` on local Ollama) in `<1.5 s`. No screenshots are permitted in Tier 1.
   - Use **Tier 2** (Windows UIA / `win32gui` / `pywinauto`) for structural control interaction in `0.1s - 0.5s`.
   - Escalate to **Tier 3** (`gemini-3.8-flash` Cloud Vision with Set-of-Marks) ONLY when Tiers 0, 1, and 2 fail or cannot address unmapped canvases.

2. **Clean Window Lifecycle**:
   - Never overwrite or type blindly into pre-existing Notepad tabs or open user documents.
   - When writing text to Notepad/Editor, atomically write a new file via `tools/file_ops.py` and launch `notepad.exe <path>`, or explicitly open a fresh tab/window (`Ctrl+N`) after verifying window focus.

3. **Terminal & Self-Protection**:
   - Never target the active console/terminal running AETHER (`WindowsTerminal`, `powershell`, `cmd`, `python`) for blind clicks, OCR clicks, or window closure.

4. **Strict JSON & Thought Stripping**:
   - All LLM responses must be normalized through `core/schemas.py` pre-validators.
   - Strip all `thought` and `thought_signature` parts from Gemini `v1beta` candidates prior to JSON parsing.
