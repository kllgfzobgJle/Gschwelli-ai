# Project: Universal Domain-Agnostic Agent Workstation (Operating Canvas)

## Architecture
The system consists of a dual-track architecture:
1. **Backend Service (`server/api.py`)**:
   - Built on FastAPI + Uvicorn + WebSockets.
   - Delivers the self-contained dashboard SPA at `GET /`.
   - Domain-agnostic REST endpoints (`/api/state`, `/api/route`, `/api/confirm`, `/api/undo`, `/api/tool`, `/api/memory`, `/api/cache`, `/api/voice`, `/api/repl`, `/api/som`, `/api/workspaces`, `/api/tasks`, `/api/workspace/files`) and WebSocket (`/ws`) for bidirectional event streaming.
   - Zero hardcoded CAD / 3D-printing data; universal application mark set and generic safety/rollback states.
   - Dual-persistence support (in-memory + backend JSON store + client-side localStorage fallback).
2. **Frontend Cockpit (`ui/dashboard/index.html`)**:
   - Zero external CDN or network dependencies (pure vanilla ES2022 + modern CSS3 + embedded SVG/Canvas).
   - Strict adherence to DESIGN.md palette: `#0A0D12` (Canvas), `#121824` (Panels/Cards), `1px solid #1E293B` (Borders), with Cyan (`#06B6D4`), Amber (`#F59E0B`), and Crimson (`#EF4444`).
   - Dynamic Workspace Manager with `[+ Neuer Workspace]` modal and hot-switching without page reload.
   - Reactive Task & Pipeline system with 5 states (`backlog`, `in_progress`, `agent_delegated`, `blocked`, `done`), priority (`P1`, `P2`, `P3`), inline creation (`Enter`), agent delegation toggle (`⚡`/`🤖`), and real-time progress metrics.
   - Knowledge & Artifact browser with dynamic directory tree, category filters (`All`, `Code`, `Docs`, `Tables`, `Media`, `Configs`), and click-to-preview.
   - Polymorphic Main Stage with 4 viewports + 50/50 Split-Screen layout:
     1. Screen & Vision Stream (Set-of-Marks Perception for arbitrary apps with zoom, pan, SOM tags `[01]`-`[12]`, non-occluding pointer events, coordinates).
     2. Artifact & Document Studio (auto-MIME detection: Markdown 2-column split raw/preview, syntax-highlighted code editor, dense CSV data-grid).
     3. Task & Reasoning Graph (Blackboard visualizer: Goal → Subtasks → Gates → Artifacts DAG node graph + live variables & memory inspector).
     4. Shell & Execution Sandbox (multi-tab monospace terminal with timestamps, exit codes, and colored stdout/stderr streams).
   - Human-in-the-Loop Safety Interceptor with risk badges (`Info`, `Moderate`, `Critical`), `[Approve (Space)]`, `[Edit]`, `[Abort (Esc)]`, and `[PANIC KILL & UNDO]`, scoped with keyboard input guards.
   - Universal Omnibar with prompt input on `Enter`, Slash command autocompletion menu (`/workspace`, `/task`, `/run`, `/inspect`, `/undo`, `/clear`), audio-viseme pill (`Listening` vs `Muted`), model selector, file dropzone.
3. **Automated Verification Harness (`tests/`)**:
   - `tests/test_api.py`: Comprehensive backend HTTP and WebSocket API tests via `TestClient`.
   - `tests/test_browser_dom.py`: Headless Chromium DOM & interactivity test suite via `playwright`.
   - Executable with `uv run --with pytest,playwright pytest tests/ -v`.

---

## Feature Inventory
Every feature from the survey phase is enumerated below with its assigned milestone:

| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Backend Domain-Agnostic Endpoints | Replace CAD fixtures in `/api/som` and `/api/scenario/reset` with domain-agnostic generic fallback data | M1 | Survey Spec, Exp 2 |
| 2 | Backend Workspace & Task Endpoints | Additive REST endpoints (`/api/workspaces`, `/api/tasks`, `/api/workspace/files`) and `/api/state` extension | M1 | Survey Spec, Exp 2 |
| 3 | Workspace Creation Modal | Dialog `[+ Neuer Workspace]` for Name, Mission/Prompt, and Working Directory | M2 | Survey Spec, Exp 1 |
| 4 | Workspace Hot-Switcher | Switch between workspaces without page reload, updating files, tasks, and stage | M2 | Survey Spec, Exp 1 |
| 5 | Workspace State Persistence | Multi-workspace state persistence across browser reload (`localStorage` & backend) | M2 | Survey Spec, Exp 1 |
| 6 | Universal Task Object Model | To-Dos conforming to `{ id, title, status, priority, delegated, meta }` | M2 | Survey Spec, Exp 1 |
| 7 | Fast Inline Task Creation | Pressing `Enter` in task input field immediately creates a task | M2 | Survey Spec, Exp 1 |
| 8 | Task Status Lifecycle | Status switching across `backlog`, `in_progress`, `agent_delegated`, `blocked`, `done` | M2 | Survey Spec, Exp 1 |
| 9 | Agent Delegation Toggle | Quick button (⚡ / 🤖) to delegate task to autonomous execution queue | M2 | Survey Spec, Exp 1 |
| 10 | Reactive Progress Metrics | Dynamic counter (`X / Y erledigt`) and real-time visual progress bar | M2 | Survey Spec, Exp 1 |
| 11 | Dynamic Workspace File Tree | Dynamic file explorer displaying files from active workspace | M2 | Survey Spec, Exp 1 |
| 12 | File Type Filtering | Category tabs (`All`, `Code`, `Docs`, `Tables`, `Media`, `Configs`) filtering tree items | M2 | Survey Spec, Exp 1 |
| 13 | File Quick Preview | Clicking a file in the tree displays it in Viewport 2 | M2 | Survey Spec, Exp 1 |
| 14 | Left Sidebar CAD Removal | Eradicate all 3D fabrication/CAD tasks, folders, and text from Left Sidebar | M2 | Survey Spec, Exp 1 |
| 15 | Polymorphic 4-Viewport Container | Switchable main stage container hosting 4 viewports via tabs and shortcuts | M3 | Survey Spec, Exp 1 |
| 16 | Screen & Vision Stream (SOM) | Universal desktop/window perception viewer with Set-of-Marks tags `[01]`-`[12]` | M3 | Survey Spec, Exp 1 |
| 17 | SOM Non-Occluding Pointer Events | Pointer events pass-through so UI elements underneath remain interactive (`0.0 px²` occlusion) | M3 | Survey Spec, Exp 1 |
| 18 | Perception Toolbar Controls | Toolbar with Zoom In/Out, Pan, Element Inspector focus, and Coordinates readout | M3 | Survey Spec, Exp 1 |
| 19 | Markdown 2-Column Split Studio | Left raw editor, right live formatted markdown preview with XSS sanitization | M3 | Survey Spec, Exp 1 |
| 20 | Code & Config Monospace Studio | Monospace editor for Python, JS, JSON, YAML with syntax highlight and line numbers | M3 | Survey Spec, Exp 1 |
| 21 | Tabular / CSV Data-Grid View | Dense spreadsheet-like grid for CSV, TSV, JSONL data with column headers | M3 | Survey Spec, Exp 1 |
| 22 | Task & Reasoning Graph (Blackboard) | DAG visualizer showing `Goal ➔ Sub-Tasks ➔ Gates ➔ Artifacts` node flow | M3 | Survey Spec, Exp 1 |
| 23 | Live Variables & Memory State | Inspector displaying agent variables (`$workspace`, `$exit_code`) and memory facts | M3 | Survey Spec, Exp 1 |
| 24 | Multi-Tab Shell Sandbox | Monospace terminal with tab switching (`PowerShell`, `Bash`, `Sandbox`) | M3 | Survey Spec, Exp 1 |
| 25 | REPL Execution & Log Styling | Interactive prompt calling `/api/repl` with timestamps, exit codes, stdout/stderr colors | M3 | Survey Spec, Exp 1 |
| 26 | Split-Screen Canvas Mode | Renders two selected viewports side-by-side in 50/50 dual layout | M3 | Survey Spec, Exp 1 |
| 27 | Quick Telemetry Drawers | Slide-out drawers for Tools, Memory facts, Tier-0 Cache, and Undo Stack | M3 | Survey Spec, Exp 1 |
| 28 | Center Stage CAD Removal | Eradicate OpenSCAD window frame, 3D CAD mesh, CSG snippet, and STL export dock | M3 | Survey Spec, Exp 1 |
| 29 | Human-in-the-Loop Safety Interceptor | Action banner with action type, target path/command, and risk badge (`Info`, `Moderate`, `Critical`) | M4 | Survey Spec, Exp 1 |
| 30 | Safety Action Buttons | `Approve (Space)`, `Edit`, and `Abort (Esc)` buttons | M4 | Survey Spec, Exp 1 |
| 31 | PANIC KILL & Emergency Rollback | Red emergency stop button calling `/api/undo`, halting agents and triggering rollback | M4 | Survey Spec, Exp 1 |
| 32 | Keyboard Scope Guard | Suppresses `Space` and `Esc` when focus is inside an input, textarea, or contenteditable | M4 | Survey Spec, Exp 1 |
| 33 | Universal Input Omnibar | Dock with prompt input, `Enter` to submit, model selector, and file dropzone | M4 | Survey Spec, Exp 1 |
| 34 | Slash Commands Autocomplete | Popup menu for `/workspace`, `/task`, `/run`, `/inspect`, `/undo`, `/clear` | M4 | Survey Spec, Exp 1 |
| 35 | Audio-Viseme Pill | Microphone meter pill toggling listening mode and visual visemes | M4 | Survey Spec, Exp 1 |
| 36 | XSS Input Sanitization | Strictly sanitizes all user inputs (tasks, workspaces, chat, terminal) before DOM insertion | M4 | Survey Spec, Exp 1 |
| 37 | Zero-Dependency Offline SPA | Completely self-contained SPA with zero external CDNs, fonts, or scripts | M4 | Survey Spec, Exp 1 |
| 38 | DESIGN Tokens & Responsiveness | Theme tokens (`#0A0D12`, `#121824`, `#1E293B`, `#06B6D4`, `#F59E0B`, `#EF4444`) & resolutions `1024x768`, `1440x900`, `1920x1080` | M4 | Survey Spec, Exp 1 |
| 39 | Automated E2E Test Suite | Requirement-driven automated test suite across Tiers 1-4 (`tests/`) | E2E Track | Survey Spec, Exp 2 |
| 40 | 100% E2E Pass & Adversarial Hardening | Phase 1: 100% test pass; Phase 2: Tier 5 adversarial stress testing | M5 | Orchestration Pattern |

---

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Backend Domain-Agnostic Endpoints & Persistence | Clean `/api/som` and `/api/scenario/reset` from CAD/OpenSCAD; add `/api/workspaces`, `/api/tasks`, `/api/workspace/files`; extend `/api/state` | none | PLANNED |
| M2 | Workspace Manager & Reactive Task Pipeline (Left Sidebar & State) | Workspace modal `[+ Neuer Workspace]`, `localStorage` persistence, hot-switch; universal task model with 5 statuses, priorities, inline creation, delegation toggle, progress metrics; dynamic file tree with type filters; CAD removal | M1 | PLANNED |
| M3 | Polymorphic Stage: 4 Viewports & Split-Screen | 4 switchable viewports (SOM desktop perception, Artifact MIME studio, Blackboard DAG visualizer, Multi-tab terminal), 50/50 split-screen, quick drawers, CAD removal | M2 | PLANNED |
| M4 | Safety Interceptor, Universal Omnibar & Polish | Safety Interceptor with risk levels, hotkeys & keyboard scope guard; PANIC KILL; Omnibar with slash autocomplete, audio pill, model selector, file dropzone; XSS sanitization; DESIGN tokens; multi-resolution stability | M2, M3 | PLANNED |
| M5 | Final Milestone: 100% E2E Test Pass & Adversarial Hardening | Phase 1: Pass 100% of E2E tests (Tiers 1-4). Phase 2: Adversarial coverage hardening (Tier 5) with Challengers & Auditor | M1, M2, M3, M4, TEST_READY | PLANNED |

In parallel:
- **E2E Testing Track**: Dispatched concurrently to upgrade `tests/test_api.py` and `tests/test_browser_dom.py` with requirement-driven test cases across Tiers 1-4, publishing `TEST_READY.md`.

---

## Interface Contracts

### 1. Backend ↔ Frontend State Contract (`GET /api/state`)
- `workspaces`: Array of `{ id: string, name: string, prompt: string, working_dir: string, is_active: boolean }`
- `active_workspace_id`: string
- `tasks`: Array of `{ id: string, title: string, status: "backlog" | "in_progress" | "agent_delegated" | "blocked" | "done", priority: "P1" | "P2" | "P3", delegated: boolean, meta: object }`
- Standard system keys: `system`, `tools`, `cache`, `memory`, `undo`, `pending_confirmation`, `history`, `voice`.

### 2. Backend ↔ Frontend Perception Contract (`GET /api/som`)
- Returns `{ status: "ok", targets_mapped: number, fusion_confidence: number, resolution: string, display: string, fusion_engine: string, marks: Mark[] }`
- Each `Mark` contains: `{ mark: number, tag: string, name: string, type: string, rect: [x1, y1, x2, y2], confidence: number, selector: string, uia_id: string }`
- Mark types: `menu`, `titlebar`, `treeview`, `button`, `viewport`, `gizmo`, `toolbar`, `panel`, `badge`, `terminal`, `textbox`.

### 3. Backend ↔ Frontend Safety & Confirmation Contract (`POST /api/confirm`)
- Request: `{ key: string, approve: boolean }`
- Response: `{ status: "resolved", resolved: boolean, key: string, action: string }`
- Emergency Undo (`POST /api/undo`): `{ result: string, can_undo: boolean, history: array }`

### 4. Workspace & Task Local/Remote Contract
- Local key: `'gschwelli_workspaces'`, `'gschwelli_active_workspace'`, `'gschwelli_tasks'`
- Remote sync: REST endpoints `/api/workspaces`, `/api/tasks` with graceful fallback to local store when offline.

---

## Code Layout
- `server/api.py`: FastAPI server, endpoints, mock data, and WebSocket broadcast.
- `ui/dashboard/index.html`: Self-contained Single Page Application (CSS, HTML, JS).
- `tests/test_api.py`: Backend integration tests.
- `tests/test_browser_dom.py`: Playwright headless Chromium DOM & interactivity test suite.
- `workspace/`: Root directory for agent workspaces and file storage.
