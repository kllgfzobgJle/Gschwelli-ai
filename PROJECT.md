# Project: gschwelli-ai High-Fidelity Interactive Web UI Prototype

## Architecture
The system consists of a dual-track architecture:
1. **Backend Service (`server/api.py`)**:
   - Built on FastAPI + Uvicorn + WebSockets.
   - Serves the dashboard directly at `GET /` as a self-contained single-page application.
   - Provides REST APIs (`/api/state`, `/api/route`, `/api/confirm`, `/api/undo`, `/api/tool`, `/api/memory`, `/api/cache`, `/api/voice`, `/api/repl`, `/api/scenario/reset`, `/api/som`) and WebSocket (`/ws`) for bidirectional event streaming.
   - Exposes mock workspace fixtures under `workspace/fabrication/`.
2. **Frontend Cockpit (`ui/dashboard/index.html`)**:
   - Zero external npm/CDN dependencies (pure vanilla ES2022 + modern CSS3 + embedded SVG/Canvas).
   - Reactive global state store (`AppState`) synchronizing across 4 top-level views:
     - `Mission Control`: 3-column cybernetic cockpit matching `Inspirations/ui_reference_mockup.png`.
     - `Knowledge Studio`: RAG file explorer, code editor, chunk embeddings table, and semantic search tester.
     - `Vision SOM`: Deep perception inspector, UIA accessibility tree vs Vision SOM toggle, 12 target marks, click simulation.
     - `Focus Chat`: Conversational execution timeline, tiered thought trace cards, inline safety gates, telemetry drawers.
   - Dual-mode synchronization: live connectivity to backend endpoints with seamless fallback to high-fidelity mock state for `3D Fabrication & Automation`.
   - Bottom Human-in-the-Loop Safety Gate & modern Omnibox command dock.
3. **Automated Verification Harness (`tests/`)**:
   - `tests/test_api.py`: Comprehensive backend HTTP and WebSocket API tests via `TestClient`.
   - `tests/test_browser_dom.py`: Headless Chromium DOM & interactivity test suite via `playwright`.
   - Executable with `uv run --with pytest,playwright pytest tests/ -v`.

---

## Feature Inventory
Every feature from the survey phase is enumerated below with its assigned milestone:

| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Backend Endpoints & Fixtures | Additive endpoints (`/api/repl`, `/api/scenario/reset`, `/api/som`) & `workspace/fabrication/` files | M1 | Survey 3 |
| 2 | Window Controls Dot Cluster | 3-dot traffic light header widget (Red, Yellow, Green) | M2 | Survey 1, 2 |
| 3 | Brand & Status Indicator | `gschwelli-ai` logo title with pulsing emerald live dot | M2 | Survey 1, 2 |
| 4 | 4-Mode View Switcher | Segmented pill buttons for `Mission Control`, `Knowledge Studio`, `Vision SOM`, `Focus Chat` | M2 | Survey 1, 2 |
| 5 | Engine Telemetry Badge | Monospace telemetry showing model, speed, and VRAM (`Ollama 7B • 42 tok/s • 4.2GB VRAM`) | M2 | Survey 1, 2 |
| 6 | Settings Trigger | Header gear icon triggering settings drawer/modal | M2 | Survey 1, 2 |
| 7 | Project / Workspace Selector | Card displaying `Active: 3D Fabrication & Automation`, git branch `main / 6 files indexed`, and switcher dropdown | M2 | Survey 1, 2 |
| 8 | Tasks & To-Dos Tracker | Interactive list of 4 tasks with counter `2 / 4`, checkboxes, and agent status badges | M2 | Survey 1, 2 |
| 9 | Knowledge Base File Tree | Tree showing `fabrication/` folder and 5+ files with active item highlight | M2 | Survey 1, 2 |
| 10 | Sync Telemetry | Telemetry line `Synced 12s ago • 48 chunks` below Knowledge Base | M2 | Survey 1, 2 |
| 11 | Audio / Wake-Word Footer | Mic meter (`RØDE NT-USB Mini -42 dB`) and `Listening for Wake-Word` toggle | M2 | Survey 1, 2 |
| 12 | AppState & WebSocket Engine | Shared reactive state store with live WS/REST sync and simulated fallback | M2 | Survey 2 |
| 13 | Canvas Header & Live Pill | Displays `SOM Perception Canvas`, `LIVE` cyan badge, and `DISPLAY 01 • 1440 × 900` | M3 | Survey 1, 2 |
| 14 | Mission Status Banner | Active mission display: `M-024 / Export toolhead_mount.stl` with badge `PAUSED • APPROVAL` | M3 | Survey 1, 2 |
| 15 | Application Window Frame | Simulated OpenSCAD window with title bar, window icons `— 🗖 ✕`, and menu bar | M3 | Survey 1, 2 |
| 16 | Isometric 3D CAD Viewport | Shaded 3D CAD mesh of `mount_v3` bracket with dimension callouts (`80.00 mm`, `24.00 mm`) | M3 | Survey 1, 2 |
| 17 | Coordinate Axes Gizmo | Bottom-left 3D coordinate axes indicator (Z, Y, X) | M3 | Survey 1, 2 |
| 18 | CSG Code Snippet Overlay | Monospace tree showing `mount_v3 / difference() / base_plate / mount_wall / bolt_holes × 5` | M3 | Survey 1, 2 |
| 19 | Set-of-Marks Cyan Tags | Callout boxes with leader lines: `[01: Menu]`, `[02: Window Controls]`, `[12: Path Input]`, `[04: Button "Export"]` | M3 | Survey 1, 2 |
| 20 | Viewport Camera Controls | Vertical bar with Orbit, Pan, Zoom, and Reset icons | M3 | Survey 1, 2 |
| 21 | Mesh Quality Telemetry | Badge `MANIFOLD • 1,248 FACETS` with green dot | M3 | Survey 1, 2 |
| 22 | Export Path Bar & Warning | Input box showing `C:\Fabrication\toolhead_mount.stl` and safety policy warning | M3 | Survey 1, 2 |
| 23 | SOM Action Toolbar | Buttons `Re-scan SOM` (scanline effect), `Inspect target`, `Capture`, and telemetry `FRAME #8184 • 84ms` | M3 | Survey 1, 2 |
| 24 | Fusion Status Bar | Telemetry bar: `12 targets mapped`, `UIA + VISION FUSION`, `99.2% confidence` | M3 | Survey 1, 2 |
| 25 | Blackboard Pipeline Tracker | Breadcrumb trail: `[Plan] → [UIA Detect] → [Verify] → [Execute]` | M4 | Survey 1, 2 |
| 26 | Blackboard Step Cards | 4 step cards with status badges (`COMPLETE`, `BLOCKED`), descriptions, and details | M4 | Survey 1, 2 |
| 27 | Shared State Inspector | Read-only variable viewer showing `$target_dir`, `$exit_code`, and `checkpoint #018` | M4 | Survey 1, 2 |
| 28 | PowerShell REPL Terminal | Timestamped console log with syntax coloring and exit code badge `EXIT 0` | M4 | Survey 1, 2 |
| 29 | PowerShell Command Input | Interactive `PS C:\Fabrication> ` input box with command execution | M4 | Survey 1, 2 |
| 30 | REPL Status Footer | Telemetry footer showing `pwsh 7.4.2` and `SANDBOX • I/O GUARDED` | M4 | Survey 1, 2 |
| 31 | Approval Gate Banner | Full-width amber banner with safety warning `Overwrite toolhead_mount.stl • backup saved • SEC-810` | M4 | Survey 1, 2 |
| 32 | Approve Action Button & Hotkey | `✓ Approve (Space)` button calling `/api/confirm` (approve=true), updating state across panels | M4 | Survey 1, 2 |
| 33 | Edit Action Button | `✏ Edit` button allowing parameter / path modification | M4 | Survey 1, 2 |
| 34 | Abort Action Button & Hotkey | `Abort (Esc)` button calling `/api/confirm` (approve=false), halting pipeline safely | M4 | Survey 1, 2 |
| 35 | PANIC KILL & UNDO Button | High-visibility red button calling `/api/undo`, triggering emergency rollback | M4 | Survey 1, 2 |
| 36 | Omnibox Input & Prefix Chip | Full-width prompt bar with `+` button, `/run...` chip, and placeholder | M4 | Survey 1, 2 |
| 37 | Slash Command Autocomplete | Popup menu showing `/run`, `/scan`, `/approve`, `/abort`, `/undo`, `/mode`, `/clear` | M4 | Survey 1, 2 |
| 38 | Voice Toggle Waveform | Waveform audio icon + `VOICE` pill | M4 | Survey 1, 2 |
| 39 | Model Router Selector | Dropdown menu: `Auto-Route: Ollama/Gemini` | M4 | Survey 1, 2 |
| 40 | Knowledge Studio File Explorer | Workspace file browser with chunk count badges, search, and re-index trigger | M5 | Survey 1, 2 |
| 41 | Knowledge Studio Code Editor | In-browser code editor with line numbers and syntax highlighting | M5 | Survey 1, 2 |
| 42 | Knowledge Studio Embeddings Table | Chunk embeddings table showing token count, embedding model, and vector preview | M5 | Survey 1, 2 |
| 43 | Vision SOM Tree & Mark Inspector | Toggle between UIA tree and Vision marks, attribute inspector for tags `[01]`-`[12]` | M5 | Survey 1, 2 |
| 44 | Vision SOM Simulated Click | Interactive click and highlight simulation with pulsing rings on canvas | M5 | Survey 1, 2 |
| 45 | Focus Chat Conversational Stream | Chat timeline with live `/api/route` integration and user/agent bubbles | M5 | Survey 1, 2 |
| 46 | Focus Chat Thought & Trace Cards | Collapsible tiered reasoning cards (Tiers 0-3) and inline approval cards | M5 | Survey 1, 2 |
| 47 | Focus Chat Quick Drawers | Drawers for Tools, Memory facts, Cache entries, and Undo stack | M5 | Survey 1, 2 |
| 48 | E2E Test Suite Implementation | Requirement-driven automated test suite across Tiers 1-4 (`tests/`) | E2E Track | Survey 3 |
| 49 | 100% E2E Pass & Adversarial Hardening | Phase 1: 100% test pass; Phase 2: Tier 5 adversarial stress testing | M6 | Orchestration Pattern |

---

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Backend Endpoints & Workspace Fixtures | Add `/api/repl`, `/api/scenario/reset`, `/api/som` to `server/api.py`, create `workspace/fabrication/` mock files | none | DONE (16/16 tests pass, 6 fixtures created, gate passed) |
| M2 | Global Shell, Design System & Left Sidebar | Color tokens, layout grid, Top Bar (brand, 4 tabs, telemetry), Left Sidebar (workspace, tasks 2/4, KB tree, mic), reactive `AppState` | none | DONE (45/45 tests pass, clean tab isolation, gate passed) |
| M3 | Center SOM Canvas & Isometric CAD Viewport | Viewport header, mission status, OpenSCAD window frame, 3D CAD mesh SVG/Canvas, SOM tags `[01, 02, 04, 12]`, toolbar & fusion status | M2 | DONE (78/78 tests pass, 0.0 px² occlusion, cold-load active line class, gate passed) |
| M4 | Blackboard, PowerShell REPL, Approval Gate & Omnibox | Blackboard cards & shared state, REPL console & input, amber approval gate (`Approve`, `Edit`, `Abort`, `PANIC`), Omnibox command dock with slash autocomplete | M2, M3 | DONE (All M4 DOM & interactive tests pass) |
| M5 | Multi-View Screens (Knowledge Studio, Vision SOM, Focus Chat) | Knowledge Studio (code editor, chunks table), Vision SOM (12 targets, UIA toggle, click simulation), Focus Chat (chat timeline, trace cards, inline gates, drawers) | M2, M3, M4 | DONE (All M5 multi-view interactive workflows pass) |
| M6 | Final Milestone: 100% E2E Test Pass & Adversarial Hardening | Phase 1: Pass 100% of E2E tests (Tiers 1-4). Phase 2: Adversarial coverage hardening (Tier 5) with Challengers & Auditor | M1, M2, M3, M4, M5, TEST_READY | DONE (16/16 API + 13/13 E2E Browser DOM tests pass) |

In parallel:
- **E2E Testing Track**: Dispatched concurrently to build `tests/test_api.py` and `tests/test_browser_dom.py`, publishing `TEST_READY.md`.

---

## Interface Contracts

### Frontend (`ui/dashboard/index.html`) ↔ Backend (`server/api.py`)
1. **`GET /`**:
   - Status: `200 OK`
   - Content-Type: `text/html; charset=utf-8`
   - Body: Self-contained dashboard SPA.
2. **`GET /api/state`**:
   - Status: `200 OK`
   - Schema:
     ```json
     {
       "system": { "cpu_percent": float, "ram_percent": float, "ram_used_gb": float, "ram_total_gb": float },
       "tools": [ { "name": str, "description": str } ],
       "cache": [ { "key": str, "instruction": str, "tier": int } ],
       "memory": [ { "key": str, "value": str, "category": str } ],
       "undo": { "count": int, "can_undo": bool, "history": [ ... ] },
       "pending_confirmation": { "key": str, "title": str, "detail": str } | null,
       "history": [ ... ],
       "voice": { "tts_enabled": bool, "voice_capture_enabled": bool }
     }
     ```
3. **`POST /api/confirm`**:
   - Request: `{ "approve": boolean }`
   - Response: `{ "resolved": str, "approved": boolean, "pending": dict | null }`
   - Behavior: Resolves pending safety gate; unblocks execution or cancels safely.
4. **`POST /api/undo`**:
   - Request: `{}`
   - Response: `{ "result": str, "can_undo": boolean, "history": [ ... ] }`
   - Behavior: Rolls back last reversible action or reports empty stack.
5. **`POST /api/route`**:
   - Request: `{ "instruction": str }`
   - Response: `{ "success": bool, "active_tier": int, "elapsed_ms": float, "thought": str, "actions": list, "logs": list }`
6. **`POST /api/repl`**:
   - Request: `{ "command": str }`
   - Response: `{ "command": str, "output": str, "exit_code": int }`
7. **`POST /api/scenario/reset`**:
   - Request: `{}`
   - Response: `{ "status": "scenario_reset", "project": "3D Fabrication & Automation", "mission": "M-024 / Export toolhead_mount.stl" }`
8. **`GET /api/som`**:
   - Response: `{ "targets_mapped": 12, "fusion_confidence": 0.992, "resolution": "1440x900", "marks": [ ... ] }`
9. **`WebSocket /ws`**:
   - Text frame format: `JSON`
   - Broadcast events: `{ "type": "route_result", "data": { ... } }`

---

## Code Layout
- `server/api.py`: FastAPI server definitions, endpoints, static serving, WebSocket handler.
- `ui/dashboard/index.html`: Unified self-contained frontend prototype (styles, HTML structure, vanilla JS logic).
- `workspace/fabrication/`: Mock files for Knowledge Base (`workflow.md`, `agent_kinematics.py`, `toolhead_mount.scad`, `mount_assembly.step`, `pipeline_config.yaml`, `safety_protocol.md`).
- `tests/test_api.py`: Backend integration tests for all REST/WS endpoints.
- `tests/test_browser_dom.py`: Headless Playwright browser DOM test suite.
- `.agents/teamwork/`: Metadata and coordination artifacts only.
