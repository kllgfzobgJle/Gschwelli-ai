# Survey 3 Report: Backend & Testing Infrastructure Investigation

**Agent**: `teamwork_preview_explorer` (Survey 3)  
**Date**: 2026-10-28  
**Working Directory**: `c:\Users\andym\gschwelli-ai\.agents\teamwork\explorer_survey_3`  
**Target Files**: `server/api.py`, `main.py`, `requirements.txt`, `executors/`, `core/`, `tests/`, `ui/dashboard/index.html`

---

## 1. Executive Summary

This investigation analyzed the backend architecture, static file serving, state representation, and testing infrastructure of `gschwelli-ai`.

Key findings:
1. **Server Architecture (`server/api.py`)**: Built with FastAPI 0.162.0, Uvicorn 0.54.0, and WebSockets 17.3. The app is created via `create_app(router, voice_daemon)` and exposes 10 core endpoints (`/`, `/api/state`, `/api/route`, `/api/confirm`, `/api/undo`, `/api/tool`, `/api/memory`, `/api/cache`, `/api/voice`, `/ws`). All existing endpoints were tested live via `fastapi.testclient.TestClient` and responded with `200 OK`.
2. **Dashboard Static File Serving**: Currently, `server/api.py` serves `ui/dashboard/index.html` directly via `GET /` as an in-memory `HTMLResponse`. There is no `/static` mount configured. Inlining CSS, SVG, and client JS within `index.html` guarantees zero-dependency asset loading with zero 404 risks; alternatively, `fastapi.staticfiles.StaticFiles` is verified as importable and can be mounted if multi-file assets are needed.
3. **State Representation & Prototype Alignment**: Current `/api/state` returns 8 top-level keys (`system`, `tools`, `cache`, `memory`, `undo`, `pending_confirmation`, `history`, `voice`). To fully support the reference mockup (`3D Fabrication & Automation`, `M-024 / Export toolhead_mount.stl`, SOM tags `[01]`-`[12]`, Blackboard variables `$target_dir`, `$exit_code`, and REPL session), the backend can be enhanced with additive endpoints (`POST /api/repl`, `POST /api/scenario/reset`, `GET /api/som`) while the frontend `index.html` provides robust client-side fallback state.
4. **Existing Test Suite**: The repository currently contains **zero** test files (the `tests/` directory does not exist).
5. **Testing & Headless Browser Feasibility**:
   - `uv` is available on the machine (`C:\Users\andym\.local\bin\uv.exe`).
   - `pytest` runs via `uv run --with pytest pytest` in 150 ms.
   - Playwright was verified live: Chromium (`chromium-1248`) is already pre-installed at `C:\Users\andym\AppData\Local\ms-playwright`.
   - A live headless browser test (`uv run --with playwright python ...`) launched headless Chromium, loaded the FastAPI server, verified the DOM, and completed in 6 seconds with zero errors.

---

## 2. Detailed Inspection of `server/api.py` and `main.py`

### 2.1 Registered Endpoints Inventory

| Method | Path | Request Body / Params | Handler Logic | Response Structure | Verified Live |
|---|---|---|---|---|---|
| `GET` | `/` | None | Reads `BASE_DIR/ui/dashboard/index.html` as UTF-8 | `HTMLResponse(content, status_code=200)` | Yes (`200 OK`) |
| `GET` | `/api/state` | None | Samples `psutil` (CPU, RAM, battery), `registry.get_declarations()`, `cache_store.list_entries(50)`, `all_entries_for_ui()`, `undo.history()`, `confirm.get_pending()`, `router.get_history(25)`, `voice_daemon.status_dict()` | `JSONResponse({ "system", "tools", "cache", "memory", "undo", "pending_confirmation", "history", "voice" })` | Yes (`200 OK`) |
| `POST` | `/api/route` | `RouteRequest(instruction: str)` | Runs `active_router.route(instruction)` in async worker thread; pushes result to registered listeners (broadcasting to `/ws`) | `JSONResponse(serialize_route_result(res))` | Yes (`200 OK`) |
| `POST` | `/api/confirm` | `ConfirmResolveRequest(approve: bool = True)` | Calls `core.confirm.resolve(req.approve)` | `JSONResponse({ "resolved": str, "approved": bool, "pending": dict \| null })` | Yes (`200 OK`) |
| `POST` | `/api/undo` | None | Calls `core.undo.undo_last(1)` in worker thread | `JSONResponse({ "result": str, "can_undo": bool, "history": list })` | Yes (`200 OK`) |
| `POST` | `/api/tool` | `ToolExecRequest(tool: str, args: dict)` | Calls `tools.registry.registry.execute(req.tool, req.args)` | `JSONResponse({ "tool": str, "output": str })` | Yes (`200 OK`) |
| `POST` | `/api/memory` | `MemoryEntryRequest(key: str, value: str, category: str = "notes")` | Calls `memory.memory_manager.remember_fact(key, value, category)` | `JSONResponse({ "result": str, "memory": list })` | Yes (`200 OK`) |
| `DELETE` | `/api/memory/{key}` | Path param `key`, query param `category="notes"` | Calls `memory.memory_manager.forget_fact(key, category)` | `JSONResponse({ "result": str, "memory": list })` | Yes (`200 OK`) |
| `DELETE` | `/api/cache` | None | Calls `engines.cache_store.cache_store.clear()` | `JSONResponse({ "cleared": true, "cache": list })` | Yes (`200 OK`) |
| `POST` | `/api/voice` | `VoiceToggleRequest(tts_enabled: bool?, voice_capture_enabled: bool?)` | Mutates `tts_engine.enabled` and `voice_daemon.voice_capture_enabled` | `JSONResponse(voice_daemon.status_dict())` | Yes (`200 OK`) |
| `WS` | `/ws` | WebSocket text frames | Accepts connection, adds to `ws_clients` list, receives frames, broadcasts `route_result` payloads via `_broadcast()` | `{"type": "route_result", "data": {...}}` | Yes (`Connected OK`) |

### 2.2 Static File Serving

- **Current Implementation**:
  ```python
  BASE_DIR = Path(__file__).resolve().parent.parent
  DASHBOARD_HTML_PATH = BASE_DIR / "ui" / "dashboard" / "index.html"

  @app.get("/", response_class=HTMLResponse)
  async def index() -> HTMLResponse:
      if DASHBOARD_HTML_PATH.is_file():
          return HTMLResponse(DASHBOARD_HTML_PATH.read_text(encoding="utf-8"))
      return HTMLResponse("<h1>AETHER Dashboard HTML not found</h1>", status_code=404)
  ```
- **Observations & Recommendations**:
  1. The existing dashboard is a single-file SPA: all CSS styles, DOM markup, and JavaScript are bundled inside `ui/dashboard/index.html`. This is advantageous for local desktop automation tools because it eliminates static path resolution bugs and avoids MIME-type mismatches.
  2. If additional static files (e.g. mock CAD models, screenshots, icons) are placed in `ui/dashboard/` or `workspace/`, the server can optionally mount them via `fastapi.staticfiles.StaticFiles`:
     ```python
     from fastapi.staticfiles import StaticFiles
     app.mount("/static", StaticFiles(directory=BASE_DIR / "ui" / "dashboard"), name="static")
     ```
  3. `index.html` should maintain complete inline CSS and JavaScript so that `GET /` remains completely self-contained.

### 2.3 Server Lifespan and Entrypoints

- `main.py` provides several entry modes:
  - `python main.py -r "<instruction>"`: One-shot CLI routing.
  - `python main.py --server [--port 8765]`: Runs FastAPI + WebSocket server + `VoiceDaemon` on a background thread.
  - `python main.py --gui`: Launches PyQt6 floating overlay + background server.
  - `python main.py --dashboard`: Launches dual-mode GUI and automatically opens the browser at `http://127.0.0.1:8765`.
  - `python main.py` (interactive CLI): Typing `dashboard` starts background server and opens browser.
- Background server function:
  ```python
  def start_background_server(
      router: AetherRouter,
      voice_daemon: Any = None,
      host: str = "127.0.0.1",
      port: int = 8765,
      open_browser: bool = False,
  ) -> threading.Thread:
  ```
  This is called by both `main.py` and `ui/overlay.py`. Its signature must remain intact.

---

## 3. State Representation & Prototype Scenario Integration

### 3.1 Requirements from Reference Mockup
The reference mockup depicts the **`3D Fabrication & Automation`** scenario:
1. **Global Shell & Telemetry**:
   - Project: `Active: 3D Fabrication & Automation`, git branch `main / 6 files indexed`.
   - Runtime badge: `Ollama 7B • 42 tok/s • 4.2GB VRAM`.
   - Audio/Wake-word: `RØDE NT-USB Mini -42 dB` • `Listening for Wake-Word`.
2. **Left Sidebar Tasks**:
   - Progress: `2 / 4`.
   - Tasks:
     - `Slice mounting bracket v3` (Complete)
     - `Calibrate toolhead offsets` (Complete)
     - `Export toolhead_mount.stl` (Approval needed)
     - `Queue OctoPrint print job` (Queued)
3. **Left Sidebar Knowledge Base**:
   - `fabrication/` folder with 6 files: `workflow.md`, `agent_kinematics.py`, `toolhead_mount.scad`, `mount_assembly.step`, `pipeline_config.yaml`, `safety_protocol.md`.
   - Sync telemetry: `Synced 12s ago • 48 chunks`.
4. **Center SOM Perception Canvas**:
   - Simulated OpenSCAD window (`OpenSCAD — toolhead_mount.scad`).
   - Isometric 3D CAD mesh render with CSG code snippet (`mount_v3 / difference()`), axis gizmo, camera controls.
   - SOM tags: `[01: Menu]`, `[02: Window Controls]`, `[12: Path Input]`, `[04: Button "Export"]`.
   - Action bar: `Re-scan SOM`, `Inspect target`, `Capture`.
   - Fusion telemetry: `12 targets mapped • UIA + VISION FUSION • 99.2% confidence`.
5. **Right Sidebar Blackboard & REPL**:
   - Blackboard: `AGENT-01`, pipeline `[Plan] → [UIA Detect] → [Verify] → [Execute]`. Steps 1-3 Complete, Step 4 `BLOCKED`.
   - Shared variables: `$target_dir: C:\Fabrication\`, `$exit_code: 0`, `checkpoint #018`.
   - PowerShell REPL: `EXIT 0`, `pwsh 7.4.2`, `SANDBOX • I/O GUARDED`, interactive prompt `PS C:\Fabrication>`.
6. **Bottom Approval Gate**:
   - Amber banner: `HUMAN-IN-THE-LOOP APPROVAL NEEDED — Overwrite toolhead_mount.stl • backup saved • SEC-810`.
   - Buttons: `Approve (Space)`, `Edit`, `Abort (Esc)`, `PANIC KILL & UNDO`.

### 3.2 Backend Endpoints Enhancements (Additive & Backward-Compatible)

To bridge the backend directly to this prototype scenario without breaking existing code:

1. **`POST /api/scenario/reset`**:
   Seeds the human confirmation gate in `core/confirm.py`:
   ```python
   @app.post("/api/scenario/reset")
   async def reset_scenario() -> JSONResponse:
       from core.confirm import request_confirmation
       request_confirmation(
           key="overwrite_stl",
           title="Overwrite toolhead_mount.stl",
           detail="backup saved • SEC-810",
           run=lambda: "Overwrote toolhead_mount.stl in C:\\Fabrication",
       )
       return JSONResponse({
           "status": "scenario_reset",
           "project": "3D Fabrication & Automation",
           "mission": "M-024 / Export toolhead_mount.stl",
       })
   ```
   When seeded, `GET /api/state` naturally returns `pending_confirmation`:
   `{"key": "overwrite_stl", "title": "Overwrite toolhead_mount.stl", "detail": "backup saved • SEC-810"}`.
   When the user clicks `Approve`, `POST /api/confirm` calls `resolve_confirm(True)` which actually executes and clears the pending confirmation in the backend!

2. **`POST /api/repl`**:
   The backend already has a persistent PowerShell REPL in `executors/ps_repl.py` and a registered tool `run_ps` in `tools/app_lifecycle.py`. Adding a dedicated `/api/repl` endpoint allows direct REPL execution:
   ```python
   class REPLRequest(BaseModel):
       command: str

   @app.post("/api/repl")
   async def execute_repl_command(req: REPLRequest) -> JSONResponse:
       cmd = (req.command or "").strip()
       if not cmd:
           return JSONResponse({"command": "", "output": "", "exit_code": 0})
       from executors.ps_repl import ps_repl
       out = await asyncio.to_thread(ps_repl.run, cmd)
       return JSONResponse({"command": cmd, "output": out, "exit_code": 0 if "failed" not in out else 1})
   ```

3. **`GET /api/som`**:
   Returns the SOM mark catalogue (the 12 mapped targets with tags, labels, coordinates, and confidence):
   ```python
   @app.get("/api/som")
   async def get_som_targets() -> JSONResponse:
       return JSONResponse({
           "status": "ok",
           "fusion_confidence": 0.992,
           "targets_mapped": 12,
           "resolution": "1440x900",
           "display": "DISPLAY 01",
           "marks": [
               {"mark": 1, "tag": "[01]", "name": "Menu Bar", "type": "menu", "rect": [10, 30, 220, 54], "confidence": 0.99},
               {"mark": 2, "tag": "[02]", "name": "Window Controls", "type": "titlebar", "rect": [1340, 6, 1432, 28], "confidence": 0.99},
               {"mark": 4, "tag": "[04]", "name": "Button 'Export'", "type": "button", "rect": [1280, 810, 1400, 846], "confidence": 0.992},
               {"mark": 12, "tag": "[12]", "name": "Path Input", "type": "textbox", "rect": [180, 810, 1100, 846], "confidence": 0.985},
               # ... marks 3, 5-11
           ]
       })
   ```

4. **Knowledge Base Files on Disk**:
   Create `workspace/fabrication/` containing the 6 realistic files:
   - `workspace/fabrication/workflow.md`
   - `workspace/fabrication/agent_kinematics.py`
   - `workspace/fabrication/toolhead_mount.scad`
   - `workspace/fabrication/mount_assembly.step`
   - `workspace/fabrication/pipeline_config.yaml`
   - `workspace/fabrication/safety_protocol.md`
   These can be read and listed using existing `@action` tools (`read_file_text`, `list_directory`) through `POST /api/tool`.

5. **Frontend Fallback Guarantee**:
   The frontend `ui/dashboard/index.html` must embed the default mock state so that if the backend is not running, or has an empty pending confirmation, the UI displays the complete, high-fidelity `3D Fabrication & Automation` scenario immediately upon load.

---

## 4. Testing Infrastructure & Headless Browser Inspection

### 4.1 Audit of Existing Test Files
- Search across the workspace for `test*.py`, `*test*.py`, or any `tests/` directory: **0 matches found**.
- There is currently no `tests/` directory.

### 4.2 Available Toolchain & Packages

| Component | Status | Details |
|---|---|---|
| **Python** | 3.12.10 | Installed at `C:\Users\andym\AppData\Local\Programs\Python\Python312\python.exe` |
| **FastAPI** | 0.162.0 | Installed |
| **Starlette** | 1.10.0 | Installed |
| **HTTPX** | 0.28.1 | Installed |
| **Uvicorn** | 0.54.0 | Installed |
| **WebSockets** | 17.3 | Installed |
| **Node.js** | 24.22.1 | Installed at `C:\Program Files\nodejs\node.exe` |
| **NPM** | 12.2.1 | Installed |
| **uv** | 0.0.0.0 | Installed at `C:\Users\andym\.local\bin\uv.exe` |
| **pytest** | Available via uv | `uv run --with pytest pytest` runs in 150 ms |
| **playwright** | Available via uv | `uv run --with playwright python` runs in <1 s |
| **Playwright Browsers** | Pre-installed | `C:\Users\andym\AppData\Local\ms-playwright\chromium-1248` exists and works |

### 4.3 Live Headless Browser Verification
We ran a live test using Playwright with Chromium against an active FastAPI server instance:
- FastAPI background server started on port 8911.
- Headless Chromium launched via Playwright sync API.
- Navigated to `http://127.0.0.1:8911/`.
- Successfully inspected the DOM and retrieved page title: `AETHER // 4-Tier Hybrid Automation Control Center`.
- Verified page contents and closed cleanly in 6.0 seconds.

This verifies that automated headless browser DOM tests can run locally without any extra driver installation.

---

## 5. Recommended Test Suite Architecture

We recommend creating a `tests/` directory with two test suites:

### 5.1 Backend API Test Suite (`tests/test_api.py`)
Tests all server endpoints using `fastapi.testclient.TestClient`:
1. `test_root_dashboard`: Verifies `GET /` returns `200 OK`, `text/html`, and contains key UI markers (`gschwelli-ai`, `Mission Control`).
2. `test_get_state`: Verifies `GET /api/state` returns `200 OK` and contains `system`, `tools`, `cache`, `memory`, `undo`, `pending_confirmation`, `history`, `voice`.
3. `test_route_instruction`: Verifies `POST /api/route` with valid instruction returns 200 and serialized `RouteResult`.
4. `test_confirm_resolve`: Verifies `POST /api/confirm` with `approve: true` and `approve: false` returns 200 and expected status.
5. `test_undo`: Verifies `POST /api/undo` returns 200 and history array.
6. `test_tool_execution`: Verifies `POST /api/tool` with `read_file_text` or `run_ps` returns 200 and output.
7. `test_memory_crud`: Verifies `POST /api/memory` and `DELETE /api/memory/{key}`.
8. `test_cache_clear`: Verifies `DELETE /api/cache`.
9. `test_voice_settings`: Verifies `POST /api/voice` toggles TTS and voice capture.
10. `test_websocket`: Verifies `WS /ws` establishes connection and handles broadcast messages.

### 5.2 Browser DOM Test Suite (`tests/test_browser_dom.py`)
Automated Playwright test verifying the interactive prototype:
1. **Zero Console Errors**: Listens to `page.on("console", ...)` and `page.on("pageerror", ...)` to ensure no unhandled exceptions or broken asset links occur.
2. **Visual Structure Verification**:
   - Top Bar: Brand, live status dot, 4 segmented mode tabs (`Mission Control`, `Knowledge Studio`, `Vision SOM`, `Focus Chat`), runtime telemetry badge (`Ollama 7B • 42 tok/s • 4.2GB VRAM`).
   - Left Sidebar: Project selector card (`Active: 3D Fabrication & Automation`), Tasks panel (`2 / 4`), Knowledge Base tree (`toolhead_mount.scad`, etc.), Wake-word mic footer.
   - Center SOM Canvas: Viewport header (`LIVE`, `DISPLAY 01 • 1440 × 900`), mission status bar (`M-024 / Export toolhead_mount.stl`, `PAUSED • APPROVAL`), 3D CAD mesh render, SOM tags `[01]`, `[02]`, `[04]`, `[12]`, toolbar, fusion telemetry (`12 targets mapped`, `99.2% confidence`).
   - Right Sidebar: Blackboard `[Plan] → [UIA Detect] → [Verify] → [Execute]` step cards, variable inspector (`$target_dir`, `$exit_code`), PowerShell REPL terminal and input prompt.
   - Bottom Approval Banner: Amber border, `HUMAN-IN-THE-LOOP APPROVAL NEEDED — Overwrite toolhead_mount.stl • backup saved • SEC-810`, buttons `Approve (Space)`, `Edit`, `Abort (Esc)`, `PANIC KILL & UNDO`.
   - Omnibox Command Bar: Prefix chip `/run...`, text input, voice toggle, model router selector.
3. **Interactive Actions Verification**:
   - Tab switching: Clicking `Knowledge Studio`, `Vision SOM`, `Focus Chat`, and `Mission Control` renders each dedicated view.
   - Approval Gate: Clicking `Approve` or `Abort` updates Mission status, Blackboard step, REPL output, and invokes `/api/confirm`.
   - SOM tag click: Clicking `[04: Button "Export"]` highlights tag and displays inspection telemetry.
   - Task toggle: Clicking a task checkbox updates task counter and status.
   - Knowledge Base file click: Selecting a file displays file preview / chunk telemetry.
   - REPL command: Submitting a command updates the terminal log.
   - Command Bar: Submitting a prompt or slash command updates the trace / timeline.

---

## 6. Verifiable Execution Commands

### Server Execution
```powershell
# Run the FastAPI + WebSocket background server:
python main.py --server --port 8765

# Launch Dual-Mode GUI and open Web Control Center in browser:
python main.py --dashboard

# Run server directly with uvicorn:
uvicorn server.api:create_app --factory --port 8765 --host 127.0.0.1
```

### Automated Backend Tests
```powershell
# Run backend API tests with pytest via uv:
uv run --with pytest pytest tests/test_api.py -v

# Run backend API tests with standard library unittest (zero extra packages):
python -m unittest tests/test_api.py
```

### Automated Headless Browser DOM Tests
```powershell
# Run Playwright DOM tests via uv:
uv run --with pytest,playwright pytest tests/test_browser_dom.py -v

# Or run as a standalone Python test script:
uv run --with playwright python tests/test_browser_dom.py
```

### Full Test Suite Execution
```powershell
uv run --with pytest,playwright pytest tests/ -v
```

---

## 7. Conclusion & Next Steps for Teamwork

1. `server/api.py` is robust, lightweight, and directly compatible with the proposed prototype.
2. Minor additive enhancements (`POST /api/repl`, `POST /api/scenario/reset`, `GET /api/som`) will give the frontend live backend responsiveness while keeping 100% backward compatibility.
3. Seeding `workspace/fabrication/` with the 6 mock files bridges real file operations to the UI.
4. The testing infrastructure can be implemented immediately in `tests/test_api.py` and `tests/test_browser_dom.py`, runnable with `uv run --with pytest,playwright pytest tests/` or standard `python -m unittest`.
