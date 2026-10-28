# Handoff Report — Explorer Survey 2: Frontend Architecture & Prototype Roadmap

## 1. Observation
- **Current Dashboard Codebase:**
  - Located at `c:\Users\andym\gschwelli-ai\ui\dashboard\index.html` (611 lines).
  - Single monolithic file containing CSS variables (`:root` lines 8–24), layout styles (lines 25–284), DOM markup (lines 286–400), and client JavaScript (lines 402–608).
  - Layout is a 2-column grid (`grid-template-columns: 1.55fr 1fr;`, line 131) with a simple header, command input box, 4 tier cards, raw trace table, and 4 right-column tabs (`TIER 0 CACHE`, `TOOLS`, `MEMORY`, `UNDO STACK`).
- **Dependencies & Libraries:**
  - Zero external JavaScript libraries or npm packages (no React, Vue, Svelte, Lit).
  - Zero external CSS frameworks (no Tailwind, Bootstrap).
  - Zero external font or icon stylesheets imported via CDN (only system fonts: `JetBrains Mono`, `Cascadia Code`, `Consolas`, `Inter`).
  - Zero 3D or vector canvas graphics (no Three.js, no Canvas/SVG rendering).
- **Backend Serving & API Contracts:**
  - In `c:\Users\andym\gschwelli-ai\server\api.py`:
    - `GET /` directly reads `ui/dashboard/index.html` as text and returns an `HTMLResponse` (lines 106–110).
    - No static folder is mounted via `app.mount("/static", ...)` in `server/api.py`.
    - Endpoints implemented: `GET /api/state` (line 113), `POST /api/route` (line 147), `POST /api/tool` (line 155), `POST /api/undo` (line 160), `POST /api/confirm` (line 165), `POST /api/memory` (line 170), `DELETE /api/memory/{key}` (line 175), `DELETE /api/cache` (line 180), `POST /api/voice` (line 185), and `WebSocket /ws` (line 197).
- **Visual Ground Truth Mockup:**
  - `Inspirations/ui_reference_mockup.png` presents a 3-column cyber-physical dark-cyan/amber operations cockpit:
    - Top header: macOS window dots, `gschwelli-ai` logo + status dot, 4-mode segmented switcher (`Mission Control`, `Knowledge Studio`, `Vision SOM`, `Focus Chat`), runtime telemetry badge (`Ollama 7B • 42 tok/s • 4.2GB VRAM`), settings icon.
    - Left sidebar: `PROJECT / LOCAL WORKSPACE` (`Active: 3D Fabrication & Automation`), `TASKS & TO-DOS (2 / 4)` with status badges, `KNOWLEDGE BASE` file tree with sync telemetry, audio meter (`RØDE NT-USB Mini -42 dB`) and `Listening for Wake-Word` pill.
    - Center panel: `SOM Perception Canvas LIVE` with simulated OpenSCAD CAD viewport, 3D isometric CAD mesh with CSG tree snippet, dimension callouts, axis gizmo, camera controls, interactive cyan SOM tags (`[01: Menu]`, `[02: Window Controls]`, `[12: Path Input]`, `[04: Button "Export"]`), path input with safety policy warning, action toolbar (`Re-scan SOM`, `Inspect target`, `Capture`), and fusion status bar (`12 targets mapped`, `UIA + VISION FUSION`, `99.2% confidence`).
    - Right sidebar: `Blackboard AGENT-01` (`[Plan] → [UIA Detect] → [Verify] → [Execute]`, step cards, shared state inspector `$target_dir`, `$exit_code`), and `>_ PowerShell REPL (EXIT 0)` with interactive prompt and `SANDBOX • I/O GUARDED` footer.
    - Bottom docks: Amber-bordered `HUMAN-IN-THE-LOOP APPROVAL NEEDED` gate with `Approve (Space)`, `Edit`, `Abort (Esc)`, `PANIC KILL & UNDO`, and modern Omnibox command bar (`/run...`, voice wave, model router selector).
- **Automated Tests:**
  - Currently, no unit tests or Playwright tests exist in the root repository.

## 2. Logic Chain
1. **Serving Constraint:** Because `server/api.py` serves `ui/dashboard/index.html` directly via `read_text()` without mounting a static files directory, building the dashboard as a self-contained, zero-dependency HTML file (with embedded CSS, inline SVGs, and modular ES2022 JavaScript) is the most robust, zero-regression path forward. It eliminates external bundler steps (Webpack/Vite) and removes runtime CDN network failure modes.
2. **Visual Gap:** The current UI has a 2-column layout designed around raw latency trace tables, whereas the user requirements demand a 3-column cockpit with 4 top-level modes (`Mission Control`, `Knowledge Studio`, `Vision SOM`, `Focus Chat`) and dual bottom docks. Therefore, `ui/dashboard/index.html` requires a total layout restructuring.
3. **Simulated State vs. Live Backend:** The requirement specifies that the UI must work immediately out-of-the-box (showing the `3D Fabrication & Automation` scenario) even when OpenSCAD is not installed or running, while preserving full live connectivity to `server/api.py`. Therefore, the frontend must implement a dual-mode hybrid architecture:
   - Initializing with rich mock state matching `ui_reference_mockup.png`.
   - Dispatching actions to `/api/confirm`, `/api/undo`, `/api/route`, `/api/voice`, `/ws`.
   - Handling empty/failed responses gracefully by updating simulated UI state (e.g. transitioning `PAUSED • APPROVAL` to `COMPLETED` when user clicks `Approve`).
4. **Interactive Perception Viewport:** Rather than loading heavy 3D WebGL engines that require external CDNs or npm packages, an HTML5 Canvas / SVG 2D isometric projection engine can cleanly render the CAD bracket geometry, facets, dimensions, axis gizmo, and SOM tags (`[01]`, `[02]`, `[04]`, `[12]`) with 60 FPS performance and zero external dependencies.

## 3. Caveats
- Host OpenSCAD application interaction in production relies on Windows UI Automation (`executors/win32_uia.py`) and screen capture (`executors/vision_som.py`). In browser-only or headless testing environments, these native Win32 calls cannot be verified directly from the browser without an active Windows desktop session; thus, simulated fallback state in the frontend is essential for prototype testing and evaluation.
- No existing tests were modified or broken; investigation was strictly read-only.

## 4. Conclusion
The frontend investigation is complete. A complete architectural blueprint and technical recommendations report has been written to:
`c:\Users\andym\gschwelli-ai\.agents\teamwork\explorer_survey_2\survey_report.md`.

The recommended implementation strategy is:
1. Re-architect `ui/dashboard/index.html` as a high-performance, self-contained single-page application using modern vanilla CSS Grid/Flexbox, inline SVG iconography, and modular JavaScript (`AppState`, View Renderers, Event Handlers).
2. Faithfully reconstruct all visual elements of `Mission Control` from `Inspirations/ui_reference_mockup.png`, including the 3D isometric CAD perception canvas and SOM tags.
3. Fully build out all 4 top-level views (`Mission Control`, `Knowledge Studio`, `Vision SOM`, `Focus Chat`) with persistent shared state.
4. Wire all interactive controls (`Approve`, `Abort`, `Panic Kill & Undo`, SOM selection, REPL commands, Omnibox commands) to both local reactive state and backend endpoints (`/api/confirm`, `/api/undo`, `/api/route`, `/api/state`, `/ws`).

## 5. Verification Method
1. **Inspection of Survey Report:**
   - Read `c:\Users\andym\gschwelli-ai\.agents\teamwork\explorer_survey_2\survey_report.md` to review the detailed gap analysis, component hierarchy, and technical recommendations.
2. **Verification of Backend API Connectivity:**
   - Run the server in a separate terminal:
     ```powershell
     python -m uvicorn server.api:create_app --factory --port 8765
     ```
   - Verify health and state endpoints via curl:
     ```powershell
     curl -s http://127.0.0.1:8765/api/state
     ```
3. **Frontend Prototype Verification:**
   - Open `http://127.0.0.1:8765` in any modern web browser.
   - Verify visual match with `Inspirations/ui_reference_mockup.png`.
   - Verify zero console errors in browser developer tools (F12).
   - Test tab switching, task toggling, SOM tag clicking, approval gate actions (`Space`, `Esc`), and PowerShell REPL command execution.
