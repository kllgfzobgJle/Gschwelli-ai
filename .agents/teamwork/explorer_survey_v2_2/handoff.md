# Handoff Report: Backend Service & Test Suite Survey for Universal Workstation Transformation

**Author**: `teamwork_explorer`  
**Date**: 2026-10-28T21:42:00Z  
**Target Milestone**: Backend Service (`server/api.py`), Integration Endpoints & Verification Suites (`tests/test_api.py`, `tests/test_browser_dom.py`)  
**Status**: Investigation Complete  

---

## 1. Observation

### 1.1 Existing Endpoint Inventory in `server/api.py`
Inspection of `server/api.py` reveals 14 registered routes (13 HTTP endpoints + 1 WebSocket endpoint):

| # | Route | Method | Line | Signature / Handler | Current Data / Status |
|---|---|---|---|---|---|
| 1 | `/` | `GET` | 111 | `index() -> HTMLResponse` | Delivers `ui/dashboard/index.html` (self-contained single-page dashboard). |
| 2 | `/api/state` | `GET` | 117 | `get_state() -> JSONResponse` | Returns dictionary with 8 keys: `system`, `tools`, `cache`, `memory`, `undo`, `pending_confirmation`, `history`, `voice`. |
| 3 | `/api/route` | `POST` | 152 | `route_instruction(req: RouteRequest) -> JSONResponse` | Validates non-empty `instruction`, runs `AetherRouter.route(instruction)`, serializes `RouteResult`. Returns 400 on empty instruction. |
| 4 | `/api/tool` | `POST` | 160 | `execute_tool_direct(req: ToolExecRequest) -> JSONResponse` | Executes registered tool in `tools.registry.registry` (e.g., `read_file_text`, `list_directory`). |
| 5 | `/api/undo` | `POST` | 165 | `trigger_undo() -> JSONResponse` | Calls `core.undo.undo_last(1)`. Returns `{ result, can_undo, history }`. |
| 6 | `/api/confirm` | `POST` | 170 | `resolve_confirmation(req: ConfirmResolveRequest) -> JSONResponse` | Approves (`approve=True`) or aborts (`approve=False`) active confirmation gate via `core.confirm.resolve`. |
| 7 | `/api/memory` | `POST` | 175 | `add_memory(req: MemoryEntryRequest) -> JSONResponse` | Remembers fact via `memory_manager.remember_fact(key, value, category)`. Returns updated memory list. |
| 8 | `/api/memory/{key}` | `DELETE` | 180 | `delete_memory(key: str, category: str = "notes") -> JSONResponse` | Forgets fact via `memory_manager.forget_fact(key, category)`. Returns updated memory list. |
| 9 | `/api/cache` | `DELETE` | 185 | `clear_cache_endpoint() -> JSONResponse` | Clears Tier-0 cache store via `cache_store.clear()`. Returns `{ cleared: True, cache: [] }`. |
| 10 | `/api/voice` | `POST` | 190 | `update_voice_settings(req: VoiceToggleRequest) -> JSONResponse` | Toggles `tts_enabled` and `voice_capture_enabled`. |
| 11 | `/api/scenario/reset`| `POST` | 202 | `reset_scenario() -> JSONResponse` | Hardcoded fabrication fixture! Seeds `overwrite_stl` pending confirmation: `{"status": "scenario_reset", "project": "3D Fabrication & Automation", "mission": "M-024 / Export toolhead_mount.stl"}`. |
| 12 | `/api/repl` | `POST` | 218 | `execute_repl_command(req: REPLRequest) -> JSONResponse` | Executes PowerShell commands via `ps_repl.run(cmd)`. Returns `{ command, output, exit_code }`. |
| 13 | `/api/som` | `GET` | 227 | `get_som_targets() -> JSONResponse` | Hardcoded OpenSCAD CAD marks! Returns 12 marks with selectors `OpenSCAD::*` and CAD elements (`CSG Tree View`, `3D CAD Mesh Viewport`, `Dimension X (80.00 mm)`). |
| 14 | `/ws` | `WS` | 362 | `websocket_endpoint(ws: WebSocket)` | Bi-directional WebSocket. Broadcasts route results via `_on_route_finished`. |

### 1.2 Verbatim CAD & Domain-Specific Hardcodings
The following files and code blocks contain hardcoded references to 3D printing, CAD, and OpenSCAD:

1. **`server/api.py` lines 202–216 (`reset_scenario`)**:
   ```python
   request_confirmation(
       key="overwrite_stl",
       title="Overwrite toolhead_mount.stl",
       detail="backup saved • SEC-810",
       run=lambda: "Overwrote toolhead_mount.stl in C:\\Fabrication",
   )
   return JSONResponse(
       {
           "status": "scenario_reset",
           "project": "3D Fabrication & Automation",
           "mission": "M-024 / Export toolhead_mount.stl",
       }
   )
   ```

2. **`server/api.py` lines 237–358 (`get_som_targets`)**:
   - `selector: "OpenSCAD::MenuBar"`, `uia_id: "MenuBar.Main"`
   - `selector: "OpenSCAD::CSGView"`, `name: "CSG Tree View"`
   - `selector: "OpenSCAD::ButtonExport"`, `name: "Button 'Export'"`
   - `selector: "OpenSCAD::OpenGLViewport"`, `name: "3D CAD Mesh Viewport"`
   - `selector: "OpenSCAD::AxesGizmo"`, `name: "Coordinate Axes Gizmo"`
   - `selector: "OpenSCAD::DimensionDimX"`, `name: "Dimension X (80.00 mm)"`
   - `selector: "OpenSCAD::DimensionDimZ"`, `name: "Dimension Z (24.00 mm)"`
   - `selector: "OpenSCAD::ManifoldBadge"`, `name: "Mesh Quality Telemetry"`

3. **`workspace/fabrication/` Directory**:
   Contains `workflow.md`, `agent_kinematics.py`, `toolhead_mount.scad`, `mount_assembly.step`, `pipeline_config.yaml`, `safety_protocol.md`.

### 1.3 Test Suite Baseline Execution Results
Both test suites were executed directly via `uv run`:
- **`tests/test_api.py`**:
  `uv run --with pytest pytest tests/test_api.py -v`
  **Result**: 16 passed, 33 warnings in 16.01s (100% pass).
- **`tests/test_browser_dom.py`**:
  `uv run --with pytest,playwright pytest tests/test_browser_dom.py -v`
  **Result**: 13 passed, 2 warnings in 15.01s (100% pass).

### 1.4 Hardcoded Assertions in Current Tests
Current tests assert CAD-specific strings directly:
- **`tests/test_api.py`**:
  - Line 194: `assert "3D Fabrication" in data.get("project", "")`
  - Line 195: `assert "M-024" in data.get("mission", "")`
  - Line 202: `assert pending.get("key") == "overwrite_stl"`
  - Line 203: `assert "toolhead_mount.stl" in pending.get("title", "")`
  - Line 204: `assert "SEC-810" in pending.get("detail", "")`
  - Line 278: `assert "Overwrote toolhead_mount.stl" in confirm_data["resolved"]`
- **`tests/test_browser_dom.py`**:
  - Line 126: `is_m2_deployed`: `"3D Fabrication" in content`
  - Line 131: `is_m3_deployed`: `"M-024" in content`
  - Line 136: `is_m4_deployed`: `"SEC-810" in content`
  - Line 180: `assert "3D Fabrication" in content or "Fabrication" in content`
  - Line 186: `assert "fabrication" in content.lower() or "workflow" in content.lower() or "toolhead" in content.lower()`
  - Line 203: `assert "SOM Perception Canvas" in content or "M-024" in content`
  - Line 241: `assert "APPROVAL" in content or "Overwrite" in content or "SEC-810" in content`
  - Line 336: `page.locator(".ks-file-entry[data-ks-file='workflow.md']").click()`
  - Line 347: `assert "[12: Path Input]" in (page.locator("#vsom-detail-id").text_content() or "")`
  - Line 353: `page.locator("#fc-chat-input").fill("Verify manifold tolerance")`

---

## 2. Logic Chain

### 2.1 Backward Compatibility vs Domain-Agnostic Transformation
1. From Observation 1.1, the public interfaces (`GET /api/state`, `POST /api/route`, `POST /api/tool`, `POST /api/undo`, `POST /api/confirm`, `POST /api/memory`, `DELETE /api/memory/{key}`, `DELETE /api/cache`, `POST /api/voice`, `POST /api/repl`, `WS /ws`) are already largely domain-agnostic in their signatures.
2. `GET /api/state` defines 8 mandatory keys verified by `test_get_state_all_keys`. Extending `/api/state` with additional keys (`workspaces`, `active_workspace_id`, `tasks`) strictly preserves compatibility with existing tests because `test_get_state_all_keys` only asserts presence of the 8 required keys, without disallowing extra fields.
3. From Observation 1.2, only `GET /api/som` and `POST /api/scenario/reset` return hardcoded CAD/OpenSCAD data.
4. By modifying `GET /api/som` to represent a clean, generic application window with universal UI controls (Menu Bar `[01]`, Window Titlebar `[02]`, Workspace Tree `[03]`, Primary Action Button `[04]`, Main Canvas Viewport `[05]`, Status Gizmo `[06]`, Viewport Toolbar `[07]`, Inspector Panel `[08]`, Live Telemetry `[09]`, Terminal Console `[10]`, Safety Status Badge `[11]`, Command Input `[12]`), we preserve tags `[01]`, `[02]`, `[04]`, `[12]` (which satisfies `test_som_endpoint_catalogue`), while eradicating all OpenSCAD/3D printing references.
5. In `POST /api/scenario/reset`, we can transition to a domain-agnostic high-risk action (e.g., "Execute high-privilege system file modification", `key: "system_file_write"`, `detail: "Modifying workspace configuration • Risk: Critical"`).

### 2.2 Workspace and Task Persistence Architecture
1. To satisfy **R1** ("Dynamischer Workspace-Manager mit `[+ Neuer Workspace]`-Modal ... Reaktives Aufgaben- & Pipeline-System mit To-Dos als universelle State-Objekte"), the backend must support workspace persistence, task lifecycle management, and workspace file browsing.
2. In-memory state combined with backend JSON persistence (`workspace/workspaces_store.json`) allows the server to retain state across restarts.
3. Dual-layer synchronization: The frontend stores state in `localStorage` (`gschwelli_workspaces`, `gschwelli_active_workspace`, `gschwelli_tasks`), falling back seamlessly when offline or when the server is restarted.
4. New additive REST endpoints to be added to `server/api.py`:
   - `GET /api/workspaces`: Lists all workspaces + active workspace ID.
   - `POST /api/workspaces`: Creates new workspace (`{ name, prompt, working_dir }`).
   - `POST /api/workspaces/activate`: Switches active workspace (`{ id }`).
   - `DELETE /api/workspaces/{id}`: Removes workspace.
   - `GET /api/tasks`: Returns list of universal task objects.
   - `POST /api/tasks`: Creates inline task (`{ title, status, priority, delegated }`).
   - `PATCH /api/tasks/{id}`: Updates task status (`backlog`, `in_progress`, `agent_delegated`, `blocked`, `done`), priority (`P1`, `P2`, `P3`), title, or delegation flag.
   - `DELETE /api/tasks/{id}`: Deletes task.
   - `GET /api/workspace/files`: Lists files for the active workspace path, returning structured JSON with file categories (`code`, `doc`, `data`, `media`, `config`).

### 2.3 Polymorphic Stage Viewports & Drawer Integration (R2)
1. In `ORIGINAL_REQUEST.md`, R2 defines 4 polymorphic viewports:
   - **View 1: Screen & Vision Stream (Set-of-Marks Perception)**: Desktop/window perception viewer with non-overlapping SOM tags and pan/zoom toolbar.
   - **View 2: Artifact & Document Studio**: 2-column Markdown raw/preview split, syntax-highlighted code editor, dense CSV/table data-grid view.
   - **View 3: Task & Reasoning Graph**: Blackboard visualizer showing execution path (Goal → Sub-Tasks → Gates → Artifacts) + live agent variables.
   - **View 4: Shell & Execution Sandbox**: Multi-tab terminal with timestamps, exit codes, and stdout/stderr coloring.
2. A split-screen layout must allow side-by-side rendering of two viewports.
3. Quick-Drawers must remain accessible for:
   - Tools (`/api/tool` and declarations from `/api/state`)
   - Memory Facts (`/api/memory`)
   - Tier-0 Cache (`/api/cache`)
   - Undo Stack (`/api/undo`)

### 2.4 Test Suite Evolution Strategy
1. From Observation 1.4, existing tests in `tests/test_browser_dom.py` and `tests/test_api.py` rely on hardcoded strings from the old CAD demo.
2. To satisfy the prompt's instructions ("What tests need to be updated or added for the new Acceptance Criteria?"), `tests/test_api.py` and `tests/test_browser_dom.py` must be upgraded:
   - Update `tests/test_api.py` to assert domain-agnostic reset responses and test the new workspace/task/file endpoints.
   - Update `tests/test_browser_dom.py` to assert the 4 polymorphic viewports, split-screen toggle, Workspace modal CRUD, inline To-Do creation with statuses & delegation, Safety Interceptor hotkeys (`Space`, `Esc`, Panic Kill) with input scope guard, Omnibar slash commands, offline zero-dependency, and multi-resolution layout stability (`1024x768`, `1440x900`, `1920x1080`).

---

## 3. Caveats

1. **Pre-installed Chromium**: Playwright tests depend on the local Chromium installation at `C:\Users\andym\AppData\Local\ms-playwright\chromium-1248`. The test suite should continue using `sync_playwright` with standard headless launch options.
2. **FastAPI Lifespan Deprecation Warnings**: Current server uses `@app.on_event("startup")`, generating 33 deprecation warnings in pytest. While functional, migrating to `@asynccontextmanager` lifespan handler will eliminate all warnings.
3. **Local Filesystem Isolation**: Workspace file operations must be restricted to safe directory paths (preventing path traversal outside project root or user workspace folders).

---

## 4. Conclusion & Proposed Specifications

### 4.1 Schema Specification for Backend Extensions

#### 1. Extended `GET /api/state` Response Schema
```json
{
  "system": {
    "cpu_percent": 12.5,
    "ram_percent": 45.2,
    "ram_used_gb": 7.2,
    "ram_total_gb": 16.0,
    "battery_percent": null,
    "battery_plugged": null
  },
  "workspaces": [
    {
      "id": "ws-default",
      "name": "General Workspace",
      "prompt": "Universal Autonomous Agent Operating Canvas",
      "working_dir": "workspace/default",
      "is_active": true
    }
  ],
  "active_workspace_id": "ws-default",
  "tasks": [
    {
      "id": "task-1",
      "title": "Analyze repository architecture",
      "status": "done",
      "priority": "P1",
      "delegated": false,
      "meta": {}
    },
    {
      "id": "task-2",
      "title": "Synthesize backend telemetry and state",
      "status": "in_progress",
      "priority": "P1",
      "delegated": true,
      "meta": {}
    },
    {
      "id": "task-3",
      "title": "Draft cross-platform integration tests",
      "status": "backlog",
      "priority": "P2",
      "delegated": false,
      "meta": {}
    },
    {
      "id": "task-4",
      "title": "Verify offline zero-dependency bundle",
      "status": "blocked",
      "priority": "P3",
      "delegated": false,
      "meta": {}
    }
  ],
  "tools": [ ... ],
  "cache": [ ... ],
  "memory": [ ... ],
  "undo": {
    "can_undo": false,
    "history": []
  },
  "pending_confirmation": null,
  "history": [ ... ],
  "voice": {
    "state": "idle",
    "hotkey": "Ctrl+Space",
    "hotkey_scope": "global",
    "tts_enabled": true
  }
}
```

#### 2. Domain-Agnostic `GET /api/som` Marks
```json
{
  "status": "ok",
  "targets_mapped": 12,
  "fusion_confidence": 0.992,
  "resolution": "1440x900",
  "display": "DISPLAY 01",
  "fusion_engine": "UIA + VISION FUSION",
  "marks": [
    { "mark": 1, "tag": "[01]", "name": "Navigation Menu", "type": "menu", "rect": [10, 30, 220, 54], "confidence": 0.991, "selector": "Window::MenuBar", "uia_id": "MenuBar.Main" },
    { "mark": 2, "tag": "[02]", "name": "Window Controls", "type": "titlebar", "rect": [1340, 6, 1432, 28], "confidence": 0.995, "selector": "Window::Controls", "uia_id": "TitleBar.Controls" },
    { "mark": 3, "tag": "[03]", "name": "Workspace Explorer", "type": "treeview", "rect": [14, 70, 260, 420], "confidence": 0.988, "selector": "Window::FileTree", "uia_id": "Tree.Workspace" },
    { "mark": 4, "tag": "[04]", "name": "Action Button 'Execute'", "type": "button", "rect": [1280, 810, 1400, 846], "confidence": 0.992, "selector": "Window::ButtonExecute", "uia_id": "Button.Execute" },
    { "mark": 5, "tag": "[05]", "name": "Main Canvas Viewport", "type": "viewport", "rect": [270, 70, 1420, 780], "confidence": 0.998, "selector": "Window::CanvasViewport", "uia_id": "Viewport.Main" },
    { "mark": 6, "tag": "[06]", "name": "Canvas Status Gizmo", "type": "gizmo", "rect": [285, 730, 345, 790], "confidence": 0.989, "selector": "Window::StatusGizmo", "uia_id": "Gizmo.Status" },
    { "mark": 7, "tag": "[07]", "name": "Viewport Controls (Pan/Zoom)", "type": "toolbar", "rect": [1390, 80, 1424, 210], "confidence": 0.984, "selector": "Window::ViewTools", "uia_id": "Toolbar.Controls" },
    { "mark": 8, "tag": "[08]", "name": "Property Inspector", "type": "panel", "rect": [640, 520, 760, 545], "confidence": 0.987, "selector": "Window::Inspector", "uia_id": "Panel.Inspector" },
    { "mark": 9, "tag": "[09]", "name": "Live Telemetry", "type": "badge", "rect": [880, 360, 990, 385], "confidence": 0.986, "selector": "Window::TelemetryBadge", "uia_id": "Badge.Telemetry" },
    { "mark": 10, "tag": "[10]", "name": "Terminal Console", "type": "terminal", "rect": [14, 780, 260, 870], "confidence": 0.979, "selector": "Window::TerminalDrawer", "uia_id": "Drawer.Terminal" },
    { "mark": 11, "tag": "[11]", "name": "Integrity Badge", "type": "badge", "rect": [290, 80, 480, 108], "confidence": 0.994, "selector": "Window::IntegrityBadge", "uia_id": "Badge.Integrity" },
    { "mark": 12, "tag": "[12]", "name": "Command / Path Input", "type": "textbox", "rect": [180, 810, 1260, 846], "confidence": 0.985, "selector": "Window::CommandInput", "uia_id": "TextBox.Command" }
  ]
}
```

#### 3. Workspace File Browser Endpoint `GET /api/workspace/files`
```json
[
  { "name": "README.md", "path": "workspace/default/README.md", "is_dir": false, "size": 1420, "ext": "md", "category": "doc" },
  { "name": "pipeline.py", "path": "workspace/default/pipeline.py", "is_dir": false, "size": 2840, "ext": "py", "category": "code" },
  { "name": "config.yaml", "path": "workspace/default/config.yaml", "is_dir": false, "size": 612, "ext": "yaml", "category": "config" },
  { "name": "metrics.csv", "path": "workspace/default/metrics.csv", "is_dir": false, "size": 3450, "ext": "data", "category": "data" },
  { "name": "architecture.svg", "path": "workspace/default/architecture.svg", "is_dir": false, "size": 8900, "ext": "svg", "category": "media" }
]
```

### 4.2 Comprehensive Test Tier Strategy

```
========================================================================================
                                     TEST TIERS
========================================================================================
[Tier 1: Sanity & Zero-Leakage Smoke]
  • GET / serves 200 OK text/html.
  • Offline zero-dependency verification (zero external CDN network requests).
  • Zero console.error and zero uncaught JS exceptions during initial load.

[Tier 2: API Interface Contracts & Default Schema]
  • GET /api/state: asserts 8 required keys + workspaces, active_workspace_id, tasks.
  • GET /api/som: asserts 12 marks, tags [01, 02, 04, 12], generic selectors.
  • POST /api/route: 400 on empty instruction, RouteResult on valid instruction.
  • POST /api/confirm: resolves gate with approve=True/False.
  • POST /api/undo: rolls back reversible operations.
  • Workspace CRUD: GET/POST/DELETE /api/workspaces.
  • Task CRUD: GET/POST/PATCH/DELETE /api/tasks (statuses, priorities, delegation).
  • Workspace file listing: GET /api/workspace/files with category categorization.

[Tier 3: Visual Structure & Multi-Resolution Ergonomics]
  • Color token adherence (#0A0D12, #121824, #1E293B, #06B6D4, #F59E0B, #EF4444).
  • Multi-resolution layout verification at 1024x768, 1440x900, and 1920x1080 without clipping.
  • SOM Perception marks non-overlapping and zero pointer occlusion.

[Tier 4: Polymorphic Interactive Workflows]
  • Workspace Manager modal workflow: [+ Neuer Workspace], validation, creation, switching.
  • To-Do system: Inline creation (Enter), status transitions (backlog -> in_progress -> agent_delegated -> blocked -> done), delegation toggle, dynamic progress bar updates.
  • 4 Viewport navigation: Screen & Vision Stream, Artifact & Document Studio, Task & Reasoning Graph, Shell & Execution Sandbox.
  • Split-Screen mode: Parallel rendering of two viewports side-by-side.
  • Artifact Studio polymorphic views: Markdown 2-column split (Raw/Preview), Code editor, Data-Grid CSV.
  • Safety Interceptor hotkeys: Space (Approve), Esc (Abort), Panic Kill emergency stop & undo.
  • Keyboard scope guard: Space/Esc hotkeys isolated from typing in inputs/textareas.
  • Omnibar: Slash command menu (/workspace, /task, /run, /inspect, /undo, /clear), Audio Viseme pill toggle, Model Selector.
  • Quick Drawers: Tools, Memory, Cache, Undo inspection.

[Tier 5: Adversarial Hardening & Persistence Resilience]
  • Browser reload state restoration (workspaces, active workspace, tasks survive F5).
  • XSS input sanitization across Task titles, Workspace prompts, Omnibar chat, Terminal input.
  • Panic Kill under active pipeline execution.
========================================================================================
```

### 4.3 Concrete Test Case Inventory to Implement

#### Additions to `tests/test_api.py`:
1. `test_get_state_includes_workspaces_and_tasks`: Verifies `workspaces` and `tasks` in `/api/state`.
2. `test_workspace_crud_endpoints`: Tests `GET /api/workspaces`, `POST /api/workspaces`, `POST /api/workspaces/activate`, `DELETE /api/workspaces/{id}`.
3. `test_task_management_lifecycle`: Tests `POST /api/tasks`, `PATCH /api/tasks/{id}` status cycling, priority changes, delegation toggle, and `DELETE /api/tasks/{id}`.
4. `test_workspace_files_categorization`: Tests `GET /api/workspace/files` returns categorized items (`code`, `doc`, `data`, `media`, `config`).
5. `test_domain_agnostic_som_catalogue`: Tests `GET /api/som` returns 12 generic marks without OpenSCAD/CAD references.
6. `test_domain_agnostic_safety_reset_workflow`: Tests `/api/scenario/reset` with generic high-risk action approval and rollback.

#### Additions / Updates to `tests/test_browser_dom.py`:
1. `test_workspace_modal_crud_and_switching`: Tests modal opening, form filling, workspace creation, and non-reloading workspace switching.
2. `test_workspace_and_task_persistence_across_reload`: Tests creating tasks and workspaces, executing `page.reload()`, and verifying complete restoration.
3. `test_todo_inline_creation_and_status_cycling`: Tests inline creation via `Enter`, cycling through all 5 statuses, clicking delegation button, and verifying reactive progress bar calculations.
4. `test_knowledge_browser_and_category_filtering`: Tests dynamic file tree and category filters (`code`, `doc`, `data`, `media`, `config`).
5. `test_four_polymorphic_viewports_switching`: Tests tab and shortcut switching across all 4 viewports.
6. `test_viewport_1_som_perception_canvas`: Tests Set-of-Marks tags, zoom/pan toolbar, coordinate display, and pointer-events non-blocking.
7. `test_viewport_2_artifact_document_studio`: Tests Markdown 2-column split (raw/preview), Code editor syntax highlighting, and CSV data-grid view.
8. `test_viewport_3_task_reasoning_graph`: Tests execution graph nodes (Goal → Sub-Tasks → Gates → Artifacts) and live variable viewer.
9. `test_viewport_4_shell_sandbox_multitab`: Tests multi-tab terminal, timestamps, and stdout/stderr colors.
10. `test_split_screen_side_by_side`: Tests split-screen toggle and simultaneous rendering of two viewports.
11. `test_quick_drawers_consistency`: Tests opening Drawers for Tools, Memory facts, Cache, and Undo stack.
12. `test_safety_interceptor_hotkeys_and_panic`: Tests `Space` approve, `Esc` abort, risk badge display, and `PANIC KILL & UNDO`.
13. `test_keyboard_scope_guard_isolation`: Tests typing space and escape in input fields without triggering safety interceptor actions.
14. `test_omnibar_slash_autocomplete_and_audio`: Tests `/` slash command popup, Audio pill toggle, and Model Selector dropdown.
15. `test_xss_sanitization_defense`: Injects script payloads into task and workspace inputs to verify safe HTML escaping.
16. `test_multi_resolution_layout_stability`: Tests resolutions `1024x768`, `1440x900`, `1920x1080` for zero overflow or layout breakage.

---

## 5. Verification Method

To independently verify these findings:
1. **Run Current API Suite**:
   ```powershell
   uv run --with pytest pytest tests/test_api.py -v
   ```
   *Expected*: 16 passed.
2. **Run Current Browser DOM Suite**:
   ```powershell
   uv run --with pytest,playwright pytest tests/test_browser_dom.py -v
   ```
   *Expected*: 13 passed.
3. **Inspect Server Code**:
   View `server/api.py` lines 117-151 (`get_state`), 202-216 (`reset_scenario`), 227-360 (`get_som_targets`).
4. **Invalidation Conditions**:
   - If `test_get_state_all_keys` fails after adding `workspaces` and `tasks` to `/api/state`, the backward compatibility assumption is invalidated. (Verified: `test_get_state_all_keys` checks key containment, not exact dictionary equality).
   - If external CDN URLs (e.g. `fonts.googleapis.com`, `cdnjs.cloudflare.com`) are present in `ui/dashboard/index.html`, the zero-dependency offline requirement is violated. (Verified: currently zero external scripts/styles loaded).
