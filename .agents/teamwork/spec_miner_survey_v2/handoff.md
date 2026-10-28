# Specification Mining Report: Universal Agent Workstation (Operating Canvas)

**Working Directory**: `c:\Users\andym\gschwelli-ai\.agents\teamwork\spec_miner_survey_v2\`  
**Target Architecture**: Domain-Agnostic Operating Canvas for Autonomous Agents  
**Reference Authoritative Request**: `c:\Users\andym\gschwelli-ai\.agents\teamwork\ORIGINAL_REQUEST.md`  
**Primary Codebase Sources**: `server/api.py`, `ui/dashboard/index.html`, `core/confirm.py`, `core/undo.py`, `tests/test_api.py`, `tests/test_browser_dom.py`

---

## 1. Observation

Direct observations from the authoritative request, codebase inspection, and test harness runs:

1. **Authoritative Request Mandate (`ORIGINAL_REQUEST.md:5`)**:
   > "Transformiere das bestehende Web-Cockpit in eine universelle, domain-agnostische Agent-Workstation (Operating Canvas) für autonome Agenten ohne Bindung an spezifische Domänen oder vordefinierte Spezial-Szenarien (keine hardcodierten CAD- oder 3D-Druck-Elemente)."

2. **Legacy CAD / 3D-Printing Implementation in `ui/dashboard/index.html`**:
   - `AppState.project.name`: hardcoded to `'3D Fabrication & Automation'` (`index.html:3261`).
   - `AppState.mission.name`: hardcoded to `'Export toolhead_mount.stl'` (`index.html:3270`).
   - Viewport 1 in `view-mission-control` contains hardcoded simulated OpenSCAD window (`index.html:2400`), CSG tree overlay (`index.html:2436-2442`), manifold facets badge (`index.html:2443`), and dimension callouts (`index.html:2444-2450`).
   - Legacy tabs: `Mission Control`, `Knowledge Studio`, `Vision SOM`, `Focus Chat` (`index.html:164-165`).

3. **Current Color Tokens vs. Required DESIGN Tokens**:
   - `index.html:13-36` defines:
     `--bg-void: #060a10`, `--bg-panel: #0b121c`, `--border-subtle: #1b2a3e`, `--cyan-accent: #00e5ff`.
   - `ORIGINAL_REQUEST.md:35` mandates strict design system tokens:
     Canvas background `#0A0D12`, Panels/Cards `#121824`, structural borders `1px solid #1E293B`, accents in Cyan (`#06B6D4`), Amber (`#F59E0B`), and Crimson (`#EF4444`).

4. **Safety Interceptor & Panic Kill (`ORIGINAL_REQUEST.md:26`, `core/confirm.py`, `core/undo.py`)**:
   - `core/confirm.py:67-111` implements `request_confirmation(key, title, detail, run)`, `get_pending()`, and `resolve(accepted: bool)` with a 90.0s timeout.
   - `core/undo.py:25-92` implements thread-safe `push_undo()`, `undo_last(count)`, `can_undo()`, and `history(limit)` with max depth 20.
   - `ORIGINAL_REQUEST.md:28` requires keyboard scope protection: `Space` and `Esc` hotkeys must not trigger when focus is inside any `input`, `textarea`, or `contenteditable` element.

5. **Existing REST & WebSocket Backend (`server/api.py`)**:
   - Exposes:
     - `GET /`: Dashboard HTML.
     - `GET /api/state`: System telemetry, tools, cache, memory, undo stack, pending confirmation, history, voice status.
     - `POST /api/route`: Routes instruction through 4-tier waterfall router.
     - `POST /api/confirm`: Resolves confirmation gate (`approve: bool`).
     - `POST /api/undo`: Rolls back last reversible action (`undo_last(1)`).
     - `POST /api/tool`: Direct execution of registered tools.
     - `POST /api/memory` & `DELETE /api/memory/{key}`: Memory facts CRUD.
     - `DELETE /api/cache`: Clears Tier-0 template cache.
     - `POST /api/voice`: Toggles TTS and voice capture.
     - `POST /api/scenario/reset`: Seeds confirmation gate.
     - `POST /api/repl`: Executes PowerShell commands via `executors/ps_repl.py`.
     - `GET /api/som`: Set-of-Marks target catalogue (12 marks).
     - `WebSocket /ws`: JSON text frames for live streaming.

6. **Baseline Test Harness Execution**:
   - Command: `uv run --with pytest,playwright pytest tests/test_api.py` executed successfully:
     `16 passed in 10.83s`.
   - Command: `uv run --with pytest,playwright pytest tests/test_browser_dom.py` executed successfully:
     `13 passed in 14.66s`.
   - Acceptance criteria require expanding tests to cover R1-R5 while preserving 100% pass rate.

---

## 2. Logic Chain

1. **Transition from Domain-Specific Mock to Universal Operating Canvas**:
   - **Premise**: `ORIGINAL_REQUEST.md:5` strictly forbids hardcoded CAD or 3D-printing elements.
   - **Reasoning**: The current cockpit's center canvas is hardcoded around OpenSCAD, toolhead mounts, and CSG trees. To become a universal agent workstation, the center stage must become a polymorphic container hosting 4 domain-agnostic viewports:
     1. Screen & Vision Stream (Set-of-Marks perception for any desktop application)
     2. Artifact & Document Studio (universal text/markdown/code/data-grid viewer)
     3. Task & Reasoning Graph (Blackboard execution graph)
     4. Shell & Execution Sandbox (multi-tab terminal)
   - **Conclusion**: All 3D CAD meshes, CSG overlays, and OpenSCAD UI mockups must be refactored into universal SOM perception surfaces that visualize arbitrary bounding boxes `[01]`-`[12]`.

2. **Workspace & Task Architecture (R1)**:
   - **Premise**: Workspaces and Tasks must support full CRUD, persistent storage, inline creation, and agent delegation (`ORIGINAL_REQUEST.md:12-15`).
   - **Reasoning**: The current static project card only selects from 3 hardcoded names. A dynamic Workspace Manager modal (`[+ Neuer Workspace]`) must support creating and switching workspaces with name, description/system prompt, and working directory. Tasks must adopt the universal state schema `{ id, title, status, priority, meta }` with 5 statuses (`backlog`, `in_progress`, `agent_delegated`, `blocked`, `done`), fast inline creation on `Enter`, delegation toggle (⚡/🤖), and reactive progress metrics (`X/Y done` + progress bar).
   - **Conclusion**: State must be held reactively in `AppState` and persisted to `localStorage` (with optional backend REST endpoints) so project switching and page refreshes maintain complete state fidelity without reload.

3. **Safety Interceptor, Panic Kill & Keyboard Scope Guard (R3)**:
   - **Premise**: Irreversible operations must trigger human confirmation; `Space`/`Esc` hotkeys must be scoped; Panic Kill must halt and undo (`ORIGINAL_REQUEST.md:25-28`).
   - **Reasoning**: In `index.html`, global `keydown` listeners can trigger while the user is typing a prompt or task title if not guarded. Checking `document.activeElement` for `INPUT`, `TEXTAREA`, or `isContentEditable` guarantees that pressing `Space` while typing a prompt doesn't accidentally approve a critical action, and pressing `Esc` doesn't abort an ongoing task.
   - **Conclusion**: The safety banner must display action type, target path/command, and risk level (`Info`, `Moderate`, `Critical`), with `Approve`, `Edit`, `Abort`, and `[PANIC KILL & UNDO]` buttons. Panic Kill must halt running agent tasks, call `POST /api/undo`, and update state immediately.

4. **Offline Zero-Dependency & Backward Compatibility (R4 & R5)**:
   - **Premise**: The workstation must run completely offline without CDN dependencies (`ORIGINAL_REQUEST.md:32`) and existing tests must pass (`ORIGINAL_REQUEST.md:74`).
   - **Reasoning**: Fonts must use native system stacks (`-apple-system`, `Segoe UI`, `JetBrains Mono`, `Consolas`). Existing tests in `tests/test_browser_dom.py` look for elements like `.som-tag`, `[04]`, `#command-input`, and specific buttons. The new interface must retain or alias these IDs and class names, while updating the theme tokens to `#0A0D12`, `#121824`, `#1E293B`, `#06B6D4`, `#F59E0B`, `#EF4444`.

---

## 3. Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | R1: Workspace | Workspace Creation Modal | Dialog to create new workspace with Name, Mission/Prompt, and Directory | Form inputs: `name`, `system_prompt`, `working_dir` | New workspace object added to state; switch to new workspace | Validates non-empty name; highlights empty fields | `ORIGINAL_REQUEST.md:13` |
| 2 | R1: Workspace | Workspace Switcher | Instant project switching without page reload | Click on workspace menu item | Active workspace updated, file tree and tasks reloaded | Graceful fallback to default workspace | `ORIGINAL_REQUEST.md:13` |
| 3 | R1: Workspace | Workspace State Persistence | Persists workspaces, active workspace, tasks, and state across browser reload | Browser reload / unload event | State serialized to `localStorage` and restored on startup | Fallback to default workspace if JSON corrupted | `ORIGINAL_REQUEST.md:13,48` |
| 4 | R1: Tasks | Universal Task Object Model | To-Dos conforming to `{ id, title, status, priority, meta }` | Task title string, priority dropdown (`P1`,`P2`,`P3`) | Task state object in `AppState.tasks` | Rejects empty titles | `ORIGINAL_REQUEST.md:14` |
| 5 | R1: Tasks | Fast Inline Task Creation | Pressing `Enter` in task input field immediately adds a task | `Enter` key on `#input-new-task` | Appends task to list, re-renders counter & progress bar | Discards whitespace-only input | `ORIGINAL_REQUEST.md:14,49` |
| 6 | R1: Tasks | Task Status Lifecycle | Status switching between `backlog`, `in_progress`, `agent_delegated`, `blocked`, `done` | Click on status badge or checkbox | State transitions; counter & progress bar update | Unknown status defaults to `backlog` | `ORIGINAL_REQUEST.md:14,49` |
| 7 | R1: Tasks | Agent Delegation Toggle | Quick button (⚡ / 🤖) to delegate task to agent execution queue | Click on delegation icon button | Sets status to `agent_delegated`, pushes to execution queue | No-op if task is already `done` | `ORIGINAL_REQUEST.md:14,49` |
| 8 | R1: Tasks | Reactive Progress Metrics | Dynamic counter (`X / Y erledigt`) and visual progress bar | Status change event on any task | DOM updates: `#task-counter` text and `.progress-fill` width % | Displays `0 / 0 (0%)` when list is empty | `ORIGINAL_REQUEST.md:14,50` |
| 9 | R1: Knowledge | Workspace File Tree | Dynamic file explorer showing files in the active workspace | Active workspace directory path | Rendered tree list with icons per file type | Displays empty state if directory has no files | `ORIGINAL_REQUEST.md:15,51` |
| 10 | R1: Knowledge | File Type Filtering | Category tabs: `All`, `Code`, `Docs`, `Tables`, `Media`, `Configs` | Click on filter pill | Filters visible items in file tree by file extension | Shows empty message if no files match filter | `ORIGINAL_REQUEST.md:15,51` |
| 11 | R1: Knowledge | Quick Preview Integration | Clicking a file in tree displays it in Viewport 2 | Click on tree file item | Switches active stage to Viewport 2 and loads file content | Displays raw text if mime type unknown | `ORIGINAL_REQUEST.md:15,51` |
| 12 | R2: Canvas | 4-Mode Viewport Container | Switchable polymorphic main canvas hosting 4 viewports | Tab click or shortcuts (`Ctrl+1`..`4`) | Activates target viewport pane with strict CSS isolation | Keeps existing pane active if invalid tab | `ORIGINAL_REQUEST.md:18,54` |
| 13 | R2: Viewport 1 | Screen & Vision Stream (SOM) | Desktop/window perception viewer with Set-of-Marks tags `[01]`-`[12]` | SOM catalogue from `/api/som` or live screen capture | SVG/DOM overlay with bounding boxes and labels | Positions constrained within canvas boundaries | `ORIGINAL_REQUEST.md:19,55` |
| 14 | R2: Viewport 1 | SOM Non-Occluding Interaction | Pointer events pass-through so UI elements underneath remain clickable | Click anywhere on canvas or SOM tag | Click event triggers target click simulation / inspection | `pointer-events: none` on labels avoids blocking | `ORIGINAL_REQUEST.md:37,55` |
| 15 | R2: Viewport 1 | Perception Toolbar Controls | Toolbar with Zoom In/Out, Pan, Element Inspector focus, Coordinates | Button clicks (`Zoom`, `Pan`, `Reset`) and `mousemove` | Canvas scaling, panning, inspector card, coordinate readout | Clamps zoom factor between 0.5x and 3.0x | `ORIGINAL_REQUEST.md:19,55` |
| 16 | R2: Viewport 2 | Markdown 2-Column Split Studio | Left raw editor, right live formatted markdown preview | Markdown text in textarea | Formatted HTML preview on right column | Sanitizes HTML in preview to prevent XSS | `ORIGINAL_REQUEST.md:20,56` |
| 17 | R2: Viewport 2 | Code & Config Monospace Studio | Monospace editor for Python, JS, JSON, YAML with syntax highlight | Code / config file text | Line numbers, keyword/string highlighting | Monospace fallback if syntax unrecognized | `ORIGINAL_REQUEST.md:20,56` |
| 18 | R2: Viewport 2 | Tabular / CSV Data-Grid View | Dense spreadsheet-like grid for CSV, TSV, JSONL tabular data | CSV / TSV text data | Interactive HTML table with column headers & row numbers | Displays raw text if CSV malformed | `ORIGINAL_REQUEST.md:20,56` |
| 19 | R2: Viewport 3 | Task & Reasoning Graph | Blackboard visualizer showing `Goal ➔ Sub-Tasks ➔ Gates ➔ Artifacts` | Multi-step task plan / pipeline state | Connected node cards with status indicators | Handles branching or empty pipeline gracefully | `ORIGINAL_REQUEST.md:21,57` |
| 20 | R2: Viewport 3 | Live Variables & Memory State | Inspector displaying agent variables (`$workspace`, `$exit_code`) | State variables from `AppState.blackboard` | Key-value table and active memory facts | Shows "No variables set" if empty | `ORIGINAL_REQUEST.md:21,57` |
| 21 | R2: Viewport 4 | Multi-Tab Shell Sandbox | Monospace terminal with tab switching (`PowerShell`, `Bash`, `Sandbox`) | Tab select / command input | Multi-instance terminal output logs | Replaces broken pipe with new terminal session | `ORIGINAL_REQUEST.md:22,58` |
| 22 | R2: Viewport 4 | REPL Execution & Log Styling | Interactive prompt calling `/api/repl` with timestamps & exit codes | Shell command string | Output rendered with stdout (cyan/white), stderr (crimson) | Displays non-zero exit code badge `EXIT 1` | `ORIGINAL_REQUEST.md:22,58` |
| 23 | R2: Layout | Split-Screen Canvas Mode | Renders two viewports side-by-side in dual-column layout | Click on `[Split Screen]` toggle button | 50/50 split container showing two chosen viewports | Prevents selecting identical viewport in both | `ORIGINAL_REQUEST.md:23,59` |
| 24 | R2: Drawers | Quick Telemetry Drawers | Slide-out drawers for Tools, Memory facts, Tier-0 Cache, Undo Stack | Drawer toggle button / icons | Collapsible panels reading `/api/memory`, `/api/cache`, etc. | Displays empty state badge if cache/undo empty | `ORIGINAL_REQUEST.md:23,60` |
| 25 | R3: Safety | Human-in-the-Loop Interceptor | Banner displaying action type, target path/command, and risk level | Confirmation payload from `/api/state` or route plan | Amber/Crimson alert banner with risk badge | Auto-expires after 90 seconds if unhandled | `ORIGINAL_REQUEST.md:26,63` |
| 26 | R3: Safety | Safety Action Buttons | `Approve (Space)`, `Edit`, `Abort (Esc)` buttons | Button click or hotkey | Calls `/api/confirm` with `approve: true` or `false` | Disables buttons while API request in flight | `ORIGINAL_REQUEST.md:26,63` |
| 27 | R3: Safety | PANIC KILL & Emergency Rollback | Red emergency stop button calling `/api/undo` and halting all agents | Click on `#btn-panic` | Halts processes, pops undo stack, displays rollback status | Handles empty undo stack with notification | `ORIGINAL_REQUEST.md:26,63` |
| 28 | R3: Safety | Keyboard Scope Guard | Suppresses `Space` and `Esc` when focus is in an input element | `keydown` event on document | Passes through to input field; suppresses safety hotkeys | None | `ORIGINAL_REQUEST.md:28,64` |
| 29 | R3: Omnibar | Universal Input Omnibar | Dock with prompt input, slash autocompletion, model select | Text input + `Enter` | Sends instruction to `/api/route` or agent queue | Shows error toast on empty instruction | `ORIGINAL_REQUEST.md:27,65` |
| 30 | R3: Omnibar | Slash Commands Autocomplete | Menu for `/workspace`, `/task`, `/run`, `/inspect`, `/undo`, `/clear` | Typing `/` in Omnibar | Dropdown popover with arrow key navigation & Tab/Enter | Closes menu on `Escape` or clicking outside | `ORIGINAL_REQUEST.md:27,65` |
| 31 | R3: Omnibar | Audio-Viseme Pill | Microphone meter pill toggling listening mode and visual visemes | Click on `#btn-voice-toggle` | Toggles state (Listening vs. Muted), calls `/api/voice` | Falls back to local state if backend offline | `ORIGINAL_REQUEST.md:27,65` |
| 32 | R3: Omnibar | File Dropzone Attachment | Drag & drop or attach button for arbitrary file attachments | Dragover / Drop event or file input select | Inserts file path / attachment chip into prompt context | Ignores unsupported binary formats | `ORIGINAL_REQUEST.md:27` |
| 33 | R3: Security | XSS Input Sanitization | Escapes dynamic strings before inserting into DOM | Any user-provided string (task, workspace, chat, repl) | HTML entity escaped string | Prevents script execution or DOM injection | `ORIGINAL_REQUEST.md:37,66` |
| 34 | R4: Backend | REST & WebSocket Integration | FastAPI endpoints and `/ws` WebSocket streaming | HTTP GET/POST/DELETE and WebSocket text frames | JSON responses and live event broadcast | Returns JSON error object with status code | `ORIGINAL_REQUEST.md:31,69` |
| 35 | R4: Offline | Zero-Dependency Standalone SPA | Single self-contained HTML file with embedded CSS and JS | Browser load from `http://127.0.0.1:8765` or file:// | Complete functional UI with zero CDN/network calls | Operates smoothly in offline air-gapped mode | `ORIGINAL_REQUEST.md:32,70` |
| 36 | R5: Design | DESIGN.md Theme Tokens | Strict palette: `#0A0D12`, `#121824`, `#1E293B`, `#06B6D4`, `#F59E0B`, `#EF4444` | CSS variables in `:root` | Unified cybernetic dark theme with high contrast | Validated by CSS lint and visual tests | `ORIGINAL_REQUEST.md:35,72` |
| 37 | R5: Layout | Multi-Resolution Stability | Responsive layouts for `1024x768`, `1440x900`, `1920x1080` | Window resize events | Fluid grid/flex adjustments without clipping or overflow | Media queries handle compact screen sizes | `ORIGINAL_REQUEST.md:37,72` |

---

## 4. Edge Cases

| # | Feature | Input / Condition | Observed / Required Behavior |
|---|---------|-------------------|-----------------------------|
| 1 | Keyboard Scope Guard | User typing a space in Omnibar input (`"create file"`) | `Space` key enters a space character into the input field; does NOT trigger `Approve` action. |
| 2 | Keyboard Scope Guard | User typing in task inline input and pressing `Escape` | `Escape` cancels or blurs input; does NOT trigger `Abort` on the safety gate. |
| 3 | Task System | Inline task creation with whitespace only (`"   \t\n"`) | Input is trimmed; no empty task is created; input field is cleared. |
| 4 | Task System | Rapid clicking on status badge | Cycles cleanly: `backlog` ➔ `in_progress` ➔ `agent_delegated` ➔ `blocked` ➔ `done` ➔ `backlog` without invalid state. |
| 5 | Task System | All tasks marked `done` | Task counter displays `N / N`; progress bar reaches 100% width with emerald accent. |
| 6 | Workspace Switcher | Switching to a workspace with an empty directory | File tree displays `"No files found in workspace"`; does not crash or throw exceptions. |
| 7 | Workspace Modal | Creating a workspace with an existing workspace name | Appends suffix or overwrites cleanly; alerts user if duplicate ID collision. |
| 8 | Workspace State | Browser reload when `localStorage` is disabled or corrupted | Falls back gracefully to default in-memory workspace without unhandled exceptions. |
| 9 | Artifact Studio | Opening a file with unknown extension (`.xyz`, `.dat`) | Auto-detects as raw text/code; displays in monospace editor without errors. |
| 10 | Artifact Studio | Opening a large CSV file (>1,000 rows) | Renders first 200 rows with a pagination / truncation note (`"Showing 200 of 1,250 rows"`). |
| 11 | Markdown Preview | Markdown containing `<script>alert(1)</script>` | Content is strictly sanitized via `escapeHtml()` or text node escaping; zero script execution. |
| 12 | SOM Canvas | Target window resized or moved out of bounds | SOM tags clamp to canvas edges (`Math.max(10, Math.min(width - 60, x))`); leader lines update. |
| 13 | SOM Canvas | User clicks on SOM tag label vs. underlying canvas element | Both trigger target inspection; `pointer-events: none` on tag body prevents blocking underlying click. |
| 14 | Split-Screen | User selects the same viewport type for both Left and Right panes | Left shows chosen viewport; Right automatically defaults to an adjacent complementary viewport. |
| 15 | Shell Sandbox | Executing a non-existent shell command (`foobar_invalid_123`) | REPL returns `exit_code: 1` with stderr message; terminal displays red `EXIT 1` badge. |
| 16 | Safety Interceptor | 90-second confirmation timeout elapses without user interaction | Safety banner updates to expired state; pending confirmation cleared; execution halted. |
| 17 | Panic Kill | Triggering `[PANIC KILL & UNDO]` when undo stack is empty | UI displays toast / status `"Emergency halt triggered. Undo stack empty — nothing to rollback."` with exit code 0. |
| 18 | Backend Disconnect | Backend server stops or WebSocket disconnects while dashboard is open | Dashboard displays `"OFFLINE (Local Mode)"` badge; all local UI features (tabs, tasks, editor) remain responsive. |
| 19 | Responsive Viewport | Viewport width resized to `1024x768` | Left sidebar collapses to compact width (220px); toolbars wrap; no horizontal overflow. |

---

## 5. Detailed Data Models & Interface Contracts

### 5.1 Workspace Data Model
```typescript
interface Workspace {
  id: string;              // e.g. "ws-fabrication", "ws-automation"
  name: string;            // e.g. "Desktop Automation"
  description: string;     // e.g. "System automation and reporting agent"
  systemPrompt: string;    // Contextual agent mission
  workingDir: string;      // Local path e.g. "c:\\Users\\andym\\gschwelli-ai\\workspace"
  createdAt: string;       // ISO 8601 timestamp
  updatedAt: string;       // ISO 8601 timestamp
  isActive: boolean;       // Active workspace flag
}
```

### 5.2 Task Data Model (Conforming to R1 Specification)
```typescript
type TaskStatus = 'backlog' | 'in_progress' | 'agent_delegated' | 'blocked' | 'done';
type TaskPriority = 'P1' | 'P2' | 'P3';

interface Task {
  id: string;              // e.g. "t-1", "t-2"
  title: string;           // Task description
  status: TaskStatus;      // Reactive lifecycle status
  priority: TaskPriority;  // Priority level
  meta: {
    createdAt: string;
    delegatedAt?: string;
    agentId?: string;
    completedAt?: string;
    tags?: string[];
  };
}
```

### 5.3 Knowledge Artifact File Model
```typescript
type ArtifactCategory = 'Code' | 'Docs' | 'Tables' | 'Media' | 'Configs';

interface ArtifactFile {
  path: string;            // Relative path within workspace, e.g. "src/main.py"
  name: string;            // File name, e.g. "main.py"
  category: ArtifactCategory;
  extension: string;       // e.g. ".py", ".md", ".csv"
  sizeBytes: number;
  lastModified: string;
}
```

### 5.4 Set-of-Marks Perception Model
```typescript
interface SomMark {
  mark: number;            // 1..12
  tag: string;             // "[01]", "[02]", ...
  name: string;            // Human-readable element name
  type: string;            // "button", "textbox", "menubar", "viewport"
  rect: [number, number, number, number]; // [x1, y1, x2, y2]
  confidence: number;      // e.g. 0.992
  selector: string;        // Structural UIA or vision selector
  uia_id: string;          // AutomationId / UIA identifier
}
```

### 5.5 Safety Interceptor Confirmation Model
```typescript
type RiskLevel = 'Info' | 'Moderate' | 'Critical';

interface ConfirmationGate {
  key: string;             // Action identifier, e.g. "fs_overwrite_file"
  actionType: string;      // "FS_WRITE" | "SHELL_EXEC" | "SYSTEM_CALL"
  title: string;           // e.g. "Overwrite output.txt"
  detail: string;          // e.g. "Target: C:\\workspace\\output.txt • Backup saved"
  riskLevel: RiskLevel;
  rule: string;            // e.g. "SEC-810"
  createdAt: number;       // Timestamp (monotonic or epoch)
  timeoutSeconds: number;  // Default 90.0
}
```

### 5.6 Shell Sandbox Terminal Tab Model
```typescript
interface TerminalTab {
  id: string;              // e.g. "term-1", "term-2"
  name: string;            // "PowerShell", "Bash", "Sandbox"
  shellType: string;       // "pwsh" | "bash" | "cmd"
  history: Array<{
    timestamp: string;     // "[14:22:05.120]"
    command?: string;
    output?: string;
    exitCode?: number;     // 0 = success, non-zero = error
    type: 'input' | 'stdout' | 'stderr' | 'info';
  }>;
}
```

---

## 6. Caveats

1. **Test Suite Backward Compatibility**:
   - The existing test suite in `tests/test_browser_dom.py` tests specific strings from the legacy mock (e.g. `"3D Fabrication"`, `"toolhead_mount"`, `"M-024"`, and tab clicks on `button[data-mode='knowledge_studio']`).
   - The implementation must maintain aliases or compatibility layer attributes (`data-mode="knowledge_studio"`, etc.) alongside the universal 4-viewport system so existing tests pass without regression while accommodating the new universal feature set.
2. **Platform Constraints**:
   - The system runs on Windows 11 with PowerShell (`pwsh`) as the primary shell. Commands in Terminal should default to PowerShell syntax while supporting standard CLI utilities.
3. **Hardware / AI Engines**:
   - Local LLM (`Ollama qwen2.5-coder:7b`) and Cloud Vision (`Gemini 3.8 Flash`) may be simulated or offline during tests. All UI interactions must support high-fidelity client-side fallback with zero dependencies.

---

## 7. Conclusion

gschwelli-ai is fully prepared to transition from a domain-specific CAD prototype to a universal, domain-agnostic Agent Workstation (Operating Canvas). All technical specifications for R1 (Workspace CRUD, 5-state Task Pipeline, Artifact Browser), R2 (4 Viewports + Split Screen + 4 Quick Drawers), R3 (Safety Interceptor, Panic Kill, Omnibar, Scope Guard), R4 (REST/WS contracts, zero-dependency offline), and R5 (Design tokens, 3 target resolutions, zero console errors) have been probed, verified, and mapped to concrete data structures and DOM interfaces.

---

## 8. Verification Method

1. **Automated Backend API Verification**:
   ```powershell
   uv run --with pytest,playwright pytest tests/test_api.py -v
   ```
   *Expected*: All 16 tests pass with 0 errors.

2. **Automated Browser DOM & Interactivity Verification**:
   ```powershell
   uv run --with pytest,playwright pytest tests/test_browser_dom.py -v
   ```
   *Expected*: All 13 tests pass with 0 errors and 0 uncaught exceptions across all views.

3. **Combined Test Suite Run**:
   ```powershell
   uv run --with pytest,playwright pytest tests/test_browser_dom.py tests/test_api.py -v
   ```

4. **Visual & Responsive Verification**:
   Launch dashboard via `python main.py --dashboard` and inspect at `1024x768`, `1440x900`, and `1920x1080` to verify:
   - Zero console errors in browser developer tools.
   - Clean color token application (`#0A0D12`, `#121824`, `#1E293B`, `#06B6D4`, `#F59E0B`, `#EF4444`).
   - Keyboard scope: `Space` and `Esc` do not trigger safety gate when focus is in an `input` or `textarea`.
