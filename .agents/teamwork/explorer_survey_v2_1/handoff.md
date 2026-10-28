# Architectural Survey & Refactoring Blueprint: Universal Domain-Agnostic Agent Workstation

**Author**: `explorer_survey_v2_1`  
**Date**: 2026-10-28  
**Scope**: Transformation of `ui/dashboard/index.html` from a 3D-fabrication cockpit into a domain-agnostic Operating Canvas for autonomous agents.

---

## 1. Observations

### 1.1 Existing Codebase & Test Baselines
- **Project Structure**:
  - `ui/dashboard/index.html`: Unified Single Page Application (4,899 lines total; CSS lines 1–2166, HTML lines 2167–3255, JS lines 3256–4899).
  - `server/api.py`: FastAPI + Uvicorn + WebSocket backend (398 lines). Serves dashboard at `GET /` and exposes REST endpoints (`/api/state`, `/api/route`, `/api/confirm`, `/api/undo`, `/api/tool`, `/api/memory`, `/api/cache`, `/api/voice`, `/api/repl`, `/api/som`, `/api/scenario/reset`) and WebSocket `/ws`.
  - `tests/test_api.py`: 16 integration tests. Ran `uv run --with pytest pytest tests/test_api.py` → **16 passed in 8.03s (Exit Code 0)**.
  - `tests/test_browser_dom.py`: 13 Playwright browser DOM tests. Ran `uv run --with pytest,playwright pytest tests/test_browser_dom.py` → **13 passed in 14.23s (Exit Code 0)**.

### 1.2 Identification of Hardcoded CAD & 3D-Printing Elements
A comprehensive scan of `ui/dashboard/index.html` and `server/api.py` revealed hardcoded domain-specific fabrication elements:

| Component / Area | File & Line Numbers | Observed Hardcoded Fabrication Elements |
|---|---|---|
| **Top Nav / Project Selector** | `index.html:2244, 2253-2262` | `Active: 3D Fabrication & Automation`, static items: `Robotic Pick & Place`, `Drone Vision Inspection`. |
| **Mission Status Bar** | `index.html:2368` | `M-024 / Export toolhead_mount.stl`, badge `PAUSED • APPROVAL`. |
| **Simulated Application Frame** | `index.html:2373-2421` | Title: `OpenSCAD — toolhead_mount.scad`, cube icon, menu items: `▷ Preview F5`, `⚙ Render F6` (CGAL render). |
| **3D CAD Mesh Viewport** | `index.html:2460-2576` | Static SVG isometric L-bracket mesh (`mount_v3`), base plate, upright mount wall, countersunk bolt holes x 5, dimension callouts `80.00 mm`, `24.00 mm`. |
| **CSG Code Overlay** | `index.html:2436-2442` | `mount_v3 / difference() / base_plate / mount_wall / bolt_holes × 5`. |
| **Coordinate Axes Gizmo** | `index.html:2578-2597` | Bottom-left XYZ coordinate axes gizmo. |
| **Mesh Telemetry** | `index.html:2601-2603` | `MANIFOLD • 1,248 FACETS`. |
| **Export Dock** | `index.html:2607-2628` | `EXPORT MODEL`, `STL (binary) • millimeters • 62.4 KB`, `C:\Fabrication\toolhead_mount.stl`, button `Export`. |
| **Left Sidebar Tasks** | `index.html:3283-3288` | `Validate mount geometry`, `Resolve export destination`, `Export toolhead mount`, `Run fabrication pipeline`. |
| **Left Sidebar File Tree** | `index.html:2287-2316` | Static folder `fabrication/`, files: `workflow.md`, `agent_kinematics.py`, `toolhead_mount.scad`, `mount_assembly.step`, `pipeline_config.yaml`, `safety_protocol.md`. |
| **Right Sidebar Blackboard** | `index.html:2684-2742, 3292-3297` | Pipeline steps: `[Plan] Prepare fabrication export`, `[UIA Detect] Resolve application targets`, `[Verify] Validate path & geometry (Manifold ✓)`, `[Execute] Commit export to disk`. |
| **Right Sidebar Shared State** | `index.html:2754` | `$target_dir` = `C:\Fabrication`. |
| **PowerShell REPL Logs** | `index.html:2780-2790, 3733-3754` | `Get-Process openscad`, `PID 8044`, `Test-Path $target_dir`, `openscad --check-parameters`, `CGAL: valid 2-manifold mesh`, `Export-Mesh -Format STL`. |
| **Approval Gate Dock** | `index.html:3149, 3280` | `Overwrite toolhead_mount.stl • backup saved • SEC-810`. |
| **Knowledge Studio View** | `index.html:2850-2932, 4604-4610` | Hardcoded fabrication files and vector chunks with PA12 and bolt holes. |
| **Vision SOM View** | `index.html:2984-3032, 4703-4714` | Target marks: `[03: 3D Viewport Mesh • 1,248 facets]`, `[04: Button "Export"]`, `[05: Preview F5]`, `[06: Render F6]`, `[11: Manifold Badge]`, `[12: Path Input]`. |
| **Focus Chat View** | `index.html:3065-3076, 3112-3125` | Operator prompt requesting `toolhead_mount.stl` export; agent response citing OpenSCAD CGAL mesh; memory `cad_tolerance = ±0.05mm (PA12)`. |
| **Backend API (`server/api.py`)** | `server/api.py:204-216, 237-358` | `/api/scenario/reset` resets `overwrite_stl` and returns `"project": "3D Fabrication & Automation"`; `/api/som` marks reference `OpenSCAD::*` and `Button.ExportSTL`. |

### 1.3 Zero-Dependency Offline & CSS Tokens
- In `ui/dashboard/index.html`:
  - No external fonts (no `fonts.googleapis.com`). Standard system font stacks are used (`--font-sans` and `--font-mono`).
  - No external JS libraries or CDN stylesheets.
  - All icons are inline SVGs.
  - CSS variables define the dark cybernetic aesthetic. Requirements in `ORIGINAL_REQUEST.md` (R5) demand strict adherence to DESIGN tokens: `#0A0D12` (Canvas), `#121824` (Panels/Cards), `1px solid #1E293B` (Borders), with Cyan (`#06B6D4`), Amber (`#F59E0B`), and Crimson (`#EF4444`). Currently, `--bg-void` is `#060a10` and `--cyan-accent` is `#00e5ff`, which should be harmonized to the exact DESIGN tokens.

---

## 2. Logic Chain

### 2.1 Decoupling from 3D-Fabrication to Universal Agent Workstation
1. **Premise**: The current UI is tightly coupled to a single scenario ("3D Fabrication & Automation - M-024"), rendering 3D CAD meshes, CSG overlays, and hardcoded fabrication files.
2. **Requirement (R1, R2)**: An autonomous agent operates across diverse tasks: web research, code refactoring, data analysis, terminal automation, OS navigation, and system orchestration.
3. **Inference**: The hardcoded 3D-printing visuals must be replaced with domain-agnostic polymorphic components:
   - Specific CAD window → Generic, universal Application/Desktop Viewer with Set-of-Marks perception.
   - Specific SCAD code viewer → Full-featured Artifact & Document Studio with auto-MIME detection (Markdown split-editor, syntax-highlighted code editor, CSV data-grid).
   - Hardcoded 4-step pipeline → Universal Directed Acyclic Graph (DAG) / Blackboard Reasoning Visualizer (`Goal → Subtasks → Gates → Artifacts`).
   - Static REPL output → Multi-tab Monospace Terminal & Execution Sandbox.

### 2.2 Preserving Test Suite Compatibility
1. **Observation**: `tests/test_browser_dom.py` and `tests/test_api.py` verify existing selectors, IDs, and text tokens (e.g. `is_m2_deployed`, `is_m3_deployed`, `is_m4_deployed`, `#btn-approve`, `#command-input`, `#repl-input`, `.som-tag`, `.ks-file-entry`, etc.).
2. **Requirement (Acceptance Criterion #74)**: Existing test suites must pass 100% while being extended for new capabilities.
3. **Inference**:
   - The refactored frontend must retain all existing element IDs, classes, and backward-compatible data attributes (`id="btn-approve"`, `id="command-input"`, `id="repl-input"`, `data-mark`, `data-mode`, etc.).
   - The default workspace fixture should provide a default workspace state that satisfies baseline text queries or provides domain-agnostic data with alias fallbacks.
   - New domain-agnostic UI elements (`[+ Neuer Workspace]` modal, task delegation toggle, split-screen button, MIME studio) will be added additively with new test cases in `tests/test_browser_dom.py`.

---

## 3. Architecture Blueprint for the Universal Workstation

### 3.1 Workspace Manager & Project Data Model (R1)
- **Data Structure (`AppState.workspaces`)**:
  ```typescript
  interface Workspace {
    id: string;                       // e.g. "ws-default", "ws-code-audit"
    name: string;                     // e.g. "Full-Stack Web Audit"
    path: string;                     // e.g. "C:\\Projects\\repo"
    systemPrompt: string;             // Agent mission/context
    activeFile?: string;
    model: string;                    // e.g. "auto", "ollama", "gemini"
    tasks: AgentTask[];
    files: WorkspaceFileNode[];
    createdAt: number;
    updatedAt: number;
  }
  ```
- **Modal Component (`#workspace-modal-backdrop` & `#workspace-modal`)**:
  - `[+ Neuer Workspace]` button in Top Bar or Left Sidebar.
  - Inputs: Workspace Name, Local Directory Path, System Prompt/Mission textarea, Model selection.
  - Buttons: `[Abbrechen]`, `[Workspace speichern]`, `[Löschen]` (if editing).
- **Hot-Switching & Persistence**:
  - Persisted in `localStorage` key `'gschwelli_workspaces'` and `'gschwelli_active_workspace_id'`.
  - Selecting a workspace triggers `switchWorkspace(wsId)`: immediately updates `AppState`, re-renders Left Sidebar tasks, file tree, system prompt, and central stage without browser page reload.

### 3.2 Reactive Task & Pipeline System (R1)
- **Task Schema**:
  ```typescript
  interface AgentTask {
    id: string;                       // Unique ID (e.g. "task-1730150400")
    title: string;                    // Task description
    status: 'backlog' | 'in_progress' | 'agent_delegated' | 'blocked' | 'done';
    priority: 'P1' | 'P2' | 'P3';
    delegated: boolean;               // True when lightning/bot toggle active
    meta?: Record<string, any>;
  }
  ```
- **UI Components & Interactions**:
  - **Inline Task Creator**: Text input `<input id="task-inline-input" placeholder="Neuer Task... (Enter)">` at the top of the tasks panel. Pressing `Enter` adds a task with priority `P2` and status `backlog`.
  - **Progress Bar & Metrics**:
    - Progress counter text: `<span id="task-progress-counter">3/7 erledigt (42%)</span>`
    - Reactive visual bar: `<div class="task-progress-bar"><div class="task-progress-fill" style="width: 42%;"></div></div>`
  - **Status Pill Toggle**: Clicking cycles through `backlog` (slate) → `in_progress` (cyan pulse) → `agent_delegated` (purple bot) → `blocked` (amber) → `done` (emerald).
  - **Priority Badge**: Click to cycle `P1` (Crimson `#EF4444`) → `P2` (Amber `#F59E0B`) → `P3` (Slate `#64748B`).
  - **Agent Delegation Toggle**: Button with `⚡` / Bot icon (`.btn-delegate-task`). When clicked, toggles `delegated = true`, switches status to `agent_delegated`, and adds glowing aura.
  - **Filter Tabs**: `[Alle]` | `[Aktiv]` | `[Delegiert ⚡]` | `[Erledigt ✓]`.

### 3.3 Dynamic Knowledge & Artifact Browser (R1)
- **Dynamic Directory Tree**:
  - Displays files from the active workspace directory.
  - Folder collapse/expand chevrons.
- **Type Filtering Bar**:
  - Segmented pills: `[Alle]` | `[Code]` | `[Docs]` | `[Data]` | `[Configs]`.
  - Filter logic matches extensions:
    - `Code`: `.py`, `.js`, `.ts`, `.html`, `.css`, `.json`, `.rs`, `.go`
    - `Docs`: `.md`, `.txt`, `.rst`
    - `Data`: `.csv`, `.tsv`, `.parquet`
    - `Configs`: `.yaml`, `.yml`, `.toml`, `.env`, `.ini`
- **Click-to-Preview**: Clicking any file immediately opens it in Viewport 2 (Artifact Studio).

### 3.4 The 4 Polymorphic Viewports & Split-Screen (R2)

```
+-----------------------------------------------------------------------------------------+
|                                TOP NAVIGATION BAR (48px)                                |
| [● ● ●] gschwelli-ai   [Screen & Vision] [Artifacts] [Graph] [Shell]   [◫ Split] Ollama |
+------------------+----------------------------------------------------------------------+
| LEFT SIDEBAR     | CENTRAL POLYMORPHIC STAGE (Single or Split 50/50)                   |
|                  |                                                                      |
| [Workspace Card] | [Pane 1: Screen & Vision Stream]  | [Pane 2: Shell Sandbox]          |
| [+ Neuer WS]     | - Desktop/Window stream viewer    | - Multi-tab terminal (pwsh/bash) |
|                  | - Set-of-Marks tags [01]..[n]     | - Color-coded stdout/stderr/cmd  |
| [Tasks (3/7)]    | - Non-occluding tags & leader-line| - Exit codes (EXIT 0 / EXIT 1)   |
| [■■■■□□□ 42%]    | - Zoom, Pan, Inspector, Coords    | - History buffer & /api/repl     |
| [Inline Input ↵] |                                   |                                  |
| [Task List CRUD] | OR [Artifact Studio]              | OR [Task & Reasoning Graph]      |
| [⚡ Delegated]    | - Markdown (Raw / HTML Split)     | - Node DAG (Goal→Subtask→Gate)   |
|                  | - Code Editor (Syntax highlight)  | - Live agent state & variables   |
| [File Browser]   | - Data Grid (CSV/TSV table)       | - Memory facts inspector         |
| [Code|Docs|Data] |                                   |                                  |
+------------------+----------------------------------------------------------------------+
| SAFETY INTERCEPTOR: [CRITICAL] WRITE_FILE: C:\path\out.json  [✓ Approve (Space)] [Esc]  |
+-----------------------------------------------------------------------------------------+
| UNIVERSAL OMNIBAR: [+] [/run...] "Describe action or type /"          [VOICE] [Auto-Route] |
+-----------------------------------------------------------------------------------------+
```

#### Viewport 1: Screen & Vision Stream (Set-of-Marks Perception)
- **Universal Application Window Frame**: Container for screen capture or window stream (e.g. desktop session, browser window, or active application target).
- **Set-of-Marks (SOM) Perception**:
  - Renders bounding boxes and marks (`[01]`, `[02]`, ... `[n]`) with confidence scores.
  - Non-occluding tag positioning: `pointer-events: none` on bounding box boxes; tags positioned on corners with leader lines so interactive elements underneath remain clickable.
  - Key marks from contract preserved: `[01: Menu Bar]`, `[02: Window Controls]`, `[04: Primary Action / Export]`, `[12: Input Path]`.
- **Stream Toolbar**:
  - Zoom: `[-]`, `[100%]`, `[+]`, `[Fit]`.
  - Pan: Toggle pan mode (grab/grabbing cursor).
  - Inspector Focus: Clicking mark highlights target with cyan border and reveals element telemetry.
  - Live Coordinates: Display mouse cursor position: `X: 524 | Y: 312`.
  - Re-scan trigger: Calls `/api/som` and shows scanline effect.

#### Viewport 2: Artifact & Document Studio (MIME Detection)
- Automatic detection based on file extension:
  1. **Markdown (`.md`, `.txt`)**: 2-Column Split:
     - Left column: Raw editable monospace textarea with line wrap.
     - Right column: Formatted HTML live preview rendered via an internal, safe zero-dependency Markdown parser (supports headings, bold/italics, lists, tables, blockquotes, inline code, and code blocks).
  2. **Code & Configs (`.py`, `.js`, `.json`, `.yaml`, `.html`, `.css`, `.ps1`)**:
     - Monospace code editor with line numbering gutter.
     - Token-based syntax highlighting in pure JS/CSS (keywords in purple/cyan, strings in emerald, comments in muted slate, numbers in amber).
  3. **Data & Tables (`.csv`, `.tsv`)**:
     - Interactive Data-Grid Table: parses CSV into headers and rows.
     - Sticky header row, zebra row striping, cell selection, row/column counter badge.
- Action Bar: File path, MIME type badge, save button, format button, file statistics.

#### Viewport 3: Task & Reasoning Graph (Blackboard Visualizer)
- **Interactive DAG / Node Graph**:
  - Graph flow: `Goal Node` (Cyan `#06B6D4`) → `Sub-Task Nodes` (Blue/Slate) → `Decision / Safety Gate Nodes` (Amber `#F59E0B`) → `Artifact Nodes` (Emerald `#10B981`).
  - Connecting arrows indicating execution order.
  - Node status badges: `PENDING`, `RUNNING` (pulsing glow), `COMPLETE` (check mark), `BLOCKED` (warning icon), `FAILED` (cross).
- **Node Inspection**: Clicking any node opens details: Thought trace, execution duration, inputs/outputs.
- **Shared State & Variables Inspector**:
  - Dynamic table showing live variables (`$workspace_path`, `$exit_code`, `$active_model`, custom variables).
  - Clicking any variable inserts it into the shell or clipboard.
- **Agent Memory Inspector**: Quick sync with `/api/memory`.

#### Viewport 4: Shell & Execution Sandbox
- **Multi-Tab Monospace Terminal**:
  - Tabs: `[Terminal 1 (Main Shell)]`, `[Subprocess Logs]`, `[Sandbox Stream]`, `[+]`.
  - Independent scrollback and history per tab.
- **Color-Coded Output Stream**:
  - Timestamps (`HH:MM:SS`) in muted slate.
  - Prompt commands in bold cyan (`> ...`).
  - Stdout in neutral text.
  - Warnings in amber.
  - Stderr / errors in crimson (`#EF4444`).
  - Success messages in emerald (`#10B981`).
  - Exit code indicators (`EXIT 0`, `EXIT 1`).
- **Interactive Input**:
  - Prompt line with prompt prefix (`PS >` or `$ >`).
  - Command history buffer with `ArrowUp` / `ArrowDown`.
  - Backend execution via `/api/repl` with simulated fallback.

#### Split-Screen Layout Capability
- Top navigation bar includes a `[◫ Split Screen]` toggle button (and shortcut `Ctrl+\`).
- When toggled, central stage switches from single-pane container to a 2-column container (`display: grid; grid-template-columns: 1fr 1fr; gap: 8px;`).
- Each split pane has its own View Selector dropdown (allowing any combination: e.g. View 1 Vision Stream + View 4 Terminal, or View 3 Graph + View 2 Artifact Studio).
- When toggled off, returns to full-width active view.

### 3.5 Human-in-the-Loop Safety Interceptor & Controls (R3)
- **Universal Safety Banner (`#approval-gate-dock`)**:
  - Displays: Action Type (`FILE_WRITE`, `SHELL_EXEC`, `SYSTEM_CALL`), Target Path / Command, Risk Badge (`Info`, `Moderate`, `Critical`), Security Rule reference.
  - Action Buttons:
    - `[✓ Approve (Space)]`: Resolves via `/api/confirm` (`approve: true`), unblocks execution.
    - `[✏ Edit]`: Unlocks target parameters inline for editing before approval.
    - `[Abort (Esc)]`: Safely cancels via `/api/confirm` (`approve: false`).
    - `[🚫 PANIC KILL & UNDO]`: High-priority red button, halts all agent execution, dispatches emergency kill signal, triggers `/api/undo` rollback.
- **Keyboard Scoping Guardrail**:
  - Hotkeys (`Space`, `Esc`) **MUST NEVER** fire while the user's cursor is inside any input element (`input`, `textarea`, or `contenteditable`).
  - Verified logic:
    ```javascript
    window.addEventListener('keydown', (e) => {
      const activeEl = document.activeElement;
      const tag = activeEl ? activeEl.tagName.toLowerCase() : '';
      if (tag === 'input' || tag === 'textarea' || activeEl?.isContentEditable) {
        return; // Prevent hotkeys while user is typing!
      }
      if (AppState.approvalGate?.active) {
        if (e.code === 'Space') { e.preventDefault(); handleApprove(); }
        else if (e.code === 'Escape') { e.preventDefault(); handleAbort(); }
      }
    });
    ```

### 3.6 Universal Omnibar Command Dock (R3)
- Prompt input field `#command-input`.
- **Slash Commands & Autocomplete**:
  - `/workspace [name]` (manage or switch workspace)
  - `/task [title]` (create task or list tasks)
  - `/run <instruction>` (dispatch AI prompt)
  - `/inspect <target>` (inspect target mark or node)
  - `/undo` (trigger rollback)
  - `/clear` (clear active console)
  - Autocomplete dropdown (`#slash-menu`) with keyboard navigation (`ArrowDown`, `ArrowUp`, `Tab`, `Escape`).
- **File Dropzone / Attachment (`+` button)**:
  - Drag-and-drop file onto Omnibar or click `+` button to attach context files.
- **Clickable Audio Viseme Pill**:
  - Optical feedback: Animated audio bars when listening vs muted flat line.
  - Synchronized with `/api/voice`.
- **Model Selector**:
  - Dropdown options: `Auto-Route (Hybrid)`, `Ollama 7B (Local)`, `Win32 UIA (Direct OS)`, `Gemini 3.8 Flash (Cloud)`.

### 3.7 Offline Zero-Dependency & UI Consistency Guardrails (R4, R5)
- **Zero-Dependency Guarantee**:
  - All fonts, styles, scripts, and SVG icons must remain completely local/embedded.
  - Zero external CDN links (`https://fonts.googleapis.com`, `cdnjs`, etc.).
- **DESIGN Color Tokens**:
  - Canvas: `#0A0D12`
  - Panels/Cards: `#121824`
  - Borders: `1px solid #1E293B`
  - Accents: Cyan `#06B6D4`, Amber `#F59E0B`, Crimson `#EF4444`, Emerald `#10B981`.
- **Error Safety & XSS Protection**:
  - Pure zero-error runtime: all DOM operations guard against `null`/`undefined`.
  - Dynamic user inputs (workspace names, task titles, chat strings, terminal commands, markdown text) are sanitized via `escapeHtml()` or `textContent` before rendering.
- **Resolution Stability**:
  - Fluid flex/grid styling with `min-width: 0` tested at `1024x768`, `1440x900`, and `1920x1080`.

---

## 4. Caveats
1. **DOM Backward-Compatibility Hooks**: Existing tests in `tests/test_browser_dom.py` look for legacy strings like "3D Fabrication", "M-024", "toolhead_mount", etc. During the refactoring, these strings should either be maintained as default fixtures or aliases, OR the test suite should be updated alongside the refactoring (as mandated by Acceptance Criterion #74: *"Die bestehenden Test-Suites werden erweitert und `uv run --with pytest,playwright pytest tests/test_browser_dom.py tests/test_api.py` läuft vollständig fehlerfrei durch."*).
2. **Read-Only Investigation**: As an explorer subagent, no modifications were made to `ui/dashboard/index.html` or `server/api.py`. The implementation agent can directly consume this blueprint.

---

## 5. Conclusion & Recommendations

The frontend in `ui/dashboard/index.html` has a solid foundation (reactive global `AppState`, responsive layout, zero-dependency offline setup), but is deeply saturated with 3D-fabrication hardcodings. 

### Implementation Roadmap for Developer Agent:
1. **Phase 1: Design Tokens & Base Styles**:
   - Update CSS variables to DESIGN tokens: `#0A0D12` (canvas), `#121824` (panels), `1px solid #1E293B` (borders), `#06B6D4` (cyan), `#F59E0B` (amber), `#EF4444` (crimson).
2. **Phase 2: Left Sidebar Components**:
   - Implement `[+ Neuer Workspace]` modal + `localStorage` persistence and hot-switching.
   - Implement Reactive Task system with inline creation (`Enter`), 5 status states, 3 priorities, agent delegation toggle (`⚡`), and real-time progress bar.
   - Implement Knowledge & Artifact Browser with folder tree and file-type filters (`Code`, `Docs`, `Data`, `Configs`).
3. **Phase 3: Central Stage & The 4 Polymorphic Viewports**:
   - Viewport 1 (Screen & Vision Stream): Universal application stream viewer with Set-of-Marks tags `[01]`..`[n]`, non-occluding layout, zoom/pan toolbar, and coordinate tracker.
   - Viewport 2 (Artifact Studio): MIME-driven viewer (Markdown 2-column split editor/previewer, Code editor with syntax highlighting, CSV data-grid table).
   - Viewport 3 (Task & Reasoning Graph): Visual DAG node graph (`Goal → Subtasks → Gates → Artifacts`) + live variables & memory inspector.
   - Viewport 4 (Shell Sandbox): Multi-tab monospace terminal with timestamps, exit codes, and colored streams.
   - Implement Split-Screen toggle (`[◫ Split Screen]`) supporting 2 parallel viewports side-by-side.
4. **Phase 4: Safety Interceptor & Universal Omnibar**:
   - Safety Interceptor with risk badges (`Info`, `Moderate`, `Critical`), inline edit, `[Approve (Space)]`, `[Abort (Esc)]`, and `[PANIC KILL & UNDO]`.
   - Keyboard scoping guardrail disabling hotkeys while typing in inputs/textareas.
   - Omnibar with slash command autocomplete (`/workspace`, `/task`, `/run`, `/inspect`, `/undo`, `/clear`), file dropzone, audio viseme pill, and model selector.
5. **Phase 5: Backend & Test Suite Alignment**:
   - Ensure generic default fixtures in `server/api.py` (`/api/som`, `/api/scenario/reset`).
   - Extend `tests/test_browser_dom.py` to assert new workspace creation, task CRUD, split-screen toggle, and MIME studio rendering.

---

## 6. Verification Method

To independently verify this survey and future implementations:
1. **API Integration Suite**:
   ```powershell
   uv run --with pytest pytest tests/test_api.py -v
   ```
   *Expected*: All 16 tests pass.
2. **Playwright Browser DOM Suite**:
   ```powershell
   uv run --with pytest,playwright pytest tests/test_browser_dom.py -v
   ```
   *Expected*: All 13 tests pass with zero console errors and zero uncaught JS exceptions across all viewports.
3. **Offline & CDN Check**:
   ```powershell
   # Ensure zero external network links in ui/dashboard/index.html
   Select-String -Path "ui/dashboard/index.html" -Pattern "(https?://|fonts\.googleapis|cdnjs|unpkg)"
   ```
   *Expected*: Only internal local websocket protocol detection (`location.protocol === 'https:' ? 'wss:' : 'ws:'`).
