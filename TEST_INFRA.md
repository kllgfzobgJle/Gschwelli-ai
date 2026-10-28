# Test Infrastructure Specification: gschwelli-ai E2E Test Suite

**Document Version**: 1.0.0  
**Target Project**: `gschwelli-ai` (High-Fidelity Interactive Web UI Prototype & Control Center)  
**Author**: E2E Test Writer (`teamwork_preview_test_writer`)  
**Scope**: Full-stack opaque-box automated verification across Tiers 1–4  

---

## 1. Testing Philosophy

The `gschwelli-ai` test infrastructure adheres to five fundamental testing tenets:

1. **Opaque-Box Requirement Verification**:
   Tests interact strictly via public interfaces:
   - Backend: HTTP REST endpoints (`fastapi.testclient.TestClient`) and WebSocket streams.
   - Frontend: Headless browser automation (`playwright`) querying DOM nodes, styles, attributes, and user interaction events.
   No internal private variables or implementation shims are accessed.

2. **Authoritative Expected Output Derivation**:
   Every expected value is derived from the project specification documents:
   - `PROJECT.md` (Architecture, Feature Inventory 1–49, Interface Contracts).
   - `ORIGINAL_REQUEST.md` (Functional requirements R1–R4, Acceptance Criteria).
   - `Inspirations/ui_reference_mockup.png` (Visual ground truth: 3-column cockpit layout, dark-cyan/amber palette, specific labels, telemetry, and interactive controls).

3. **Zero-Facade Integrity Mandate**:
   Tests must never be written as facades or dummy passes. Every assertion verifies real observable logic:
   - API tests verify status codes, exact JSON schema keys, value types, and persistence/side-effects.
   - DOM tests assert that required elements are present, visible, contain exact reference text, respond to click/keyboard events, and trigger state transitions without browser console errors.

4. **Progressive Testability & Tiered Coverage**:
   Tests are partitioned into well-defined tiers (Tiers 1–5):
   - **Tier 1 (Sanity / Smoke)**: Baseline server launch, HTML delivery (`200 OK`), static asset integrity.
   - **Tier 2 (Functional / Happy Path)**: Individual REST endpoints, core component rendering, default mock state.
   - **Tier 3 (Edge Cases & Error Handling)**: Boundary conditions, empty prompts, non-existent keys, unconfirmed approvals, idempotent deletes.
   - **Tier 4 (Multi-Step E2E Workflows)**: End-to-end user journeys (e.g., scenario reset → approval gate → confirm → REPL log; tab switching; SOM mark inspection).
   - **Tier 5 (Adversarial Hardening)**: Extreme inputs, malformed payloads, rapid concurrent interactions (exercised in M6).

5. **Deterministic & Isolated Execution**:
   Each test establishes its own prerequisites or operates on isolated requests. Reset hooks (`POST /api/scenario/reset`, `DELETE /api/cache`) ensure zero state leakage between test runs.

---

## 2. Feature Inventory Tier Coverage Matrix

The 49 features enumerated in `PROJECT.md` § Feature Inventory are verified across Tiers 1–4 as detailed below:

| # | Feature Name | Milestone | Test File & Function | Test Tier | Verifiable Assertion |
|---|--------------|-----------|----------------------|-----------|----------------------|
| 1 | Backend Endpoints & Fixtures | M1 | `tests/test_api.py::test_scenario_reset_endpoint`, `test_repl_endpoint`, `test_som_endpoint` | Tier 1, 2 | `200 OK`, valid JSON structure, seeds confirmation, executes REPL command, returns 12 SOM marks |
| 2 | Window Controls Dot Cluster | M2 | `tests/test_browser_dom.py::test_top_nav_visual_structure` | Tier 2 | `.window-dots` with red, yellow, green indicators present |
| 3 | Brand & Status Indicator | M2 | `tests/test_browser_dom.py::test_top_nav_visual_structure` | Tier 2 | Contains `gschwelli-ai` and live status indicator |
| 4 | 4-Mode View Switcher | M2 | `tests/test_browser_dom.py::test_top_nav_visual_structure`, `test_tab_switching_workflow` | Tier 2, 4 | 4 segmented mode buttons; clicking switches views cleanly |
| 5 | Engine Telemetry Badge | M2 | `tests/test_browser_dom.py::test_top_nav_visual_structure` | Tier 2 | Contains `Ollama 7B` and telemetry metrics |
| 6 | Settings Trigger | M2 | `tests/test_browser_dom.py::test_top_nav_visual_structure` | Tier 2 | Settings icon/button rendered and interactive |
| 7 | Project / Workspace Selector | M2 | `tests/test_browser_dom.py::test_left_sidebar_structure` | Tier 2 | Displays `3D Fabrication & Automation`, git branch telemetry |
| 8 | Tasks & To-Dos Tracker | M2 | `tests/test_browser_dom.py::test_left_sidebar_structure`, `test_task_interaction_workflow` | Tier 2, 4 | Shows `2 / 4`, 4 tasks, toggling updates completion counter |
| 9 | Knowledge Base File Tree | M2 | `tests/test_browser_dom.py::test_left_sidebar_structure`, `test_knowledge_base_selection` | Tier 2, 4 | Shows `fabrication/` folder and files (`toolhead_mount.scad`, etc.); clicking selects file |
| 10 | Sync Telemetry | M2 | `tests/test_browser_dom.py::test_left_sidebar_structure` | Tier 2 | Displays `Synced 12s ago • 48 chunks` |
| 11 | Audio / Wake-Word Footer | M2 | `tests/test_browser_dom.py::test_left_sidebar_structure`, `test_mic_toggle_interaction` | Tier 2, 4 | Mic level meter (`RØDE NT-USB Mini -42 dB`) and toggle button |
| 12 | AppState & WebSocket Engine | M2 | `tests/test_api.py::test_websocket_connection_and_broadcast`, `tests/test_browser_dom.py::test_zero_console_errors` | Tier 1, 4 | Bidirectional WS connection, state reactivity across panels |
| 13 | Canvas Header & Live Pill | M3 | `tests/test_browser_dom.py::test_center_canvas_structure` | Tier 2 | Displays `SOM Perception Canvas`, `LIVE`, `DISPLAY 01 • 1440 × 900` |
| 14 | Mission Status Banner | M3 | `tests/test_browser_dom.py::test_center_canvas_structure` | Tier 2 | Shows `M-024 / Export toolhead_mount.stl`, `PAUSED • APPROVAL` |
| 15 | Application Window Frame | M3 | `tests/test_browser_dom.py::test_center_canvas_structure` | Tier 2 | OpenSCAD simulated window frame with title and controls |
| 16 | Isometric 3D CAD Viewport | M3 | `tests/test_browser_dom.py::test_center_canvas_structure` | Tier 2 | 3D mesh rendering of `mount_v3` with dimension callouts |
| 17 | Coordinate Axes Gizmo | M3 | `tests/test_browser_dom.py::test_center_canvas_structure` | Tier 2 | 3D coordinate axes gizmo (Z, Y, X) rendered |
| 18 | CSG Code Snippet Overlay | M3 | `tests/test_browser_dom.py::test_center_canvas_structure` | Tier 2 | Monospace tree showing `mount_v3 / difference()` |
| 19 | Set-of-Marks Cyan Tags | M3 | `tests/test_browser_dom.py::test_center_canvas_structure`, `test_som_tag_click_interaction` | Tier 2, 4 | Tags `[01]`, `[02]`, `[04]`, `[12]`; clicking highlights tag |
| 20 | Viewport Camera Controls | M3 | `tests/test_browser_dom.py::test_center_canvas_structure` | Tier 2 | Orbit, Pan, Zoom, Reset action buttons present |
| 21 | Mesh Quality Telemetry | M3 | `tests/test_browser_dom.py::test_center_canvas_structure` | Tier 2 | Badge `MANIFOLD • 1,248 FACETS` with green indicator |
| 22 | Export Path Bar & Warning | M3 | `tests/test_browser_dom.py::test_center_canvas_structure` | Tier 2 | Input showing `C:\Fabrication\toolhead_mount.stl` + warning |
| 23 | SOM Action Toolbar | M3 | `tests/test_browser_dom.py::test_center_canvas_structure` | Tier 2 | Buttons `Re-scan SOM`, `Inspect target`, `Capture` |
| 24 | Fusion Status Bar | M3 | `tests/test_browser_dom.py::test_center_canvas_structure` | Tier 2 | `12 targets mapped`, `UIA + VISION FUSION`, `99.2% confidence` |
| 25 | Blackboard Pipeline Tracker | M4 | `tests/test_browser_dom.py::test_right_sidebar_structure` | Tier 2 | Pipeline breadcrumb `[Plan] → [UIA Detect] → [Verify] → [Execute]` |
| 26 | Blackboard Step Cards | M4 | `tests/test_browser_dom.py::test_right_sidebar_structure` | Tier 2 | 4 step cards with status badges (`COMPLETE`, `BLOCKED`) |
| 27 | Shared State Inspector | M4 | `tests/test_browser_dom.py::test_right_sidebar_structure` | Tier 2 | Displays `$target_dir`, `$exit_code`, `checkpoint #018` |
| 28 | PowerShell REPL Terminal | M4 | `tests/test_browser_dom.py::test_right_sidebar_structure` | Tier 2 | Timestamped log view with `EXIT 0` badge |
| 29 | PowerShell Command Input | M4 | `tests/test_browser_dom.py::test_right_sidebar_structure`, `test_repl_command_submission` | Tier 2, 4 | Input prompt `PS C:\Fabrication> `; submitting appends to log |
| 30 | REPL Status Footer | M4 | `tests/test_browser_dom.py::test_right_sidebar_structure` | Tier 2 | Telemetry footer `pwsh 7.4.2`, `SANDBOX • I/O GUARDED` |
| 31 | Approval Gate Banner | M4 | `tests/test_browser_dom.py::test_approval_gate_structure` | Tier 2 | Amber banner `HUMAN-IN-THE-LOOP APPROVAL NEEDED — Overwrite...` |
| 32 | Approve Action Button & Hotkey | M4 | `tests/test_browser_dom.py::test_approval_gate_approve_action`, `tests/test_api.py::test_confirm_resolve_approve` | Tier 2, 4 | Clicking `Approve` resolves gate, updates mission to EXECUTING, calls `/api/confirm` |
| 33 | Edit Action Button | M4 | `tests/test_browser_dom.py::test_approval_gate_structure` | Tier 2 | `Edit` button opens parameter modification |
| 34 | Abort Action Button & Hotkey | M4 | `tests/test_browser_dom.py::test_approval_gate_abort_action`, `tests/test_api.py::test_confirm_resolve_reject` | Tier 2, 4 | Clicking `Abort` cancels gate, marks mission ABORTED |
| 35 | PANIC KILL & UNDO Button | M4 | `tests/test_browser_dom.py::test_panic_kill_action`, `tests/test_api.py::test_undo_endpoint` | Tier 2, 4 | Red button calls `/api/undo`, rolls back action |
| 36 | Omnibox Input & Prefix Chip | M4 | `tests/test_browser_dom.py::test_omnibox_structure`, `test_omnibox_input_workflow` | Tier 2, 4 | `/run...` chip, prompt input, submission produces feedback |
| 37 | Slash Command Autocomplete | M4 | `tests/test_browser_dom.py::test_omnibox_slash_autocomplete` | Tier 3 | Typing `/` shows autocomplete menu (`/run`, `/scan`, etc.) |
| 38 | Voice Toggle Waveform | M4 | `tests/test_browser_dom.py::test_omnibox_structure` | Tier 2 | Audio waveform icon + `VOICE` pill |
| 39 | Model Router Selector | M4 | `tests/test_browser_dom.py::test_omnibox_structure` | Tier 2 | Dropdown showing `Auto-Route: Ollama/Gemini` |
| 40 | Knowledge Studio File Explorer | M5 | `tests/test_browser_dom.py::test_knowledge_studio_view` | Tier 2, 4 | File list with chunk count badges, search filter |
| 41 | Knowledge Studio Code Editor | M5 | `tests/test_browser_dom.py::test_knowledge_studio_view` | Tier 2 | Code editor with line numbers and syntax highlighting |
| 42 | Knowledge Studio Embeddings Table | M5 | `tests/test_browser_dom.py::test_knowledge_studio_view` | Tier 2 | Embeddings table showing token counts and vector previews |
| 43 | Vision SOM Tree & Mark Inspector | M5 | `tests/test_browser_dom.py::test_vision_som_view` | Tier 2, 4 | Tree vs Vision marks toggle, attribute inspector for marks |
| 44 | Vision SOM Simulated Click | M5 | `tests/test_browser_dom.py::test_vision_som_view` | Tier 2, 4 | Simulated target click with pulsing canvas feedback |
| 45 | Focus Chat Conversational Stream | M5 | `tests/test_browser_dom.py::test_focus_chat_view` | Tier 2, 4 | Chat timeline, prompt submission, message bubbles |
| 46 | Focus Chat Thought & Trace Cards | M5 | `tests/test_browser_dom.py::test_focus_chat_view` | Tier 2 | Collapsible tiered thought cards (Tiers 0–3) |
| 47 | Focus Chat Quick Drawers | M5 | `tests/test_browser_dom.py::test_focus_chat_view` | Tier 2 | Drawers for Tools, Memory facts, Cache, Undo stack |
| 48 | E2E Test Suite Implementation | E2E | `tests/test_api.py`, `tests/test_browser_dom.py` | Tier 1–4 | Automated execution via pytest and Playwright |
| 49 | 100% E2E Pass & Hardening | M6 | Full suite + Phase 2 adversarial stress | Tier 5 | Full suite passes without error under stress |

---

## 3. Test Architecture & Environment

### 3.1 Backend API Test Harness (`tests/test_api.py`)
- **Technology**: `fastapi.testclient.TestClient`, `pytest`.
- **Execution Mode**: In-process synchronous HTTP and WebSocket requests against the FastAPI ASGI application returned by `server.api.create_app()`.
- **Scope**:
  - `GET /`: HTML payload delivery, status code `200`, content type `text/html`.
  - `GET /api/state`: System telemetry, tools array, cache list, memory list, undo status, pending confirmation, history array, voice status.
  - `POST /api/route`: Empty instruction validation (`400 Bad Request`), valid instruction execution returning `RouteResult`.
  - `POST /api/confirm`: Safety gate approval (`approve=true`), gate rejection (`approve=false`), resolution status.
  - `POST /api/undo`: Rollback execution, undo history updates, empty history resilience.
  - `POST /api/tool`: Direct tool execution via registry (`read_file_text`, `list_directory`, etc.).
  - `POST /api/memory` & `DELETE /api/memory/{key}`: Fact storage, retrieval in state, deletion, category filtering.
  - `DELETE /api/cache`: Clear cache store, verify empty list.
  - `POST /api/voice`: Voice daemon / TTS toggles.
  - `POST /api/scenario/reset`: Reset scenario, seed `overwrite_stl` pending confirmation.
  - `POST /api/repl`: Direct PowerShell REPL execution returning command, output, and exit code.
  - `GET /api/som`: Catalogue of 12 SOM targets with tags, coordinates, and confidence.
  - `WebSocket /ws`: Connection establishment, frame transmission, broadcast reception.

### 3.2 Headless Browser DOM Test Harness (`tests/test_browser_dom.py`)
- **Technology**: `playwright.sync_api`, `pytest`.
- **Browser Binary**: Chromium (`chromium-1248`) pre-installed at `C:\Users\andym\AppData\Local\ms-playwright\chromium-1248`.
- **Execution Mode**: Headless browser automation interacting with an ephemeral or active FastAPI server instance.
- **Monitoring & Safety**:
  - `page.on("console", ...)` listener captures all console logs. Any `console.error` fails the test.
  - `page.on("pageerror", ...)` listener captures all unhandled JavaScript exceptions. Any unhandled exception fails the test.
  - Zero 404/broken asset detection via `page.on("response", ...)`.

---

## 4. Test Execution Instructions

### 4.1 Running Backend API Tests
```powershell
uv run --with pytest pytest tests/test_api.py -v
```

### 4.2 Running Browser DOM E2E Tests
```powershell
uv run --with pytest,playwright pytest tests/test_browser_dom.py -v
```

### 4.3 Running Complete Test Suite
```powershell
uv run --with pytest,playwright pytest tests/ -v
```

---

## 5. Quality Thresholds & Escalation

1. **Pass Rate Threshold**: 100% of applicable tests must pass without failures or errors.
2. **Console Error Threshold**: 0 `console.error` and 0 unhandled exceptions in browser runs.
3. **Escalation Protocol**: If a test failure is caused by an implementation defect in `server/api.py` or `ui/dashboard/index.html`, the defect is logged and escalated to the responsible worker agent with file, line number, and verbatim failure output.
