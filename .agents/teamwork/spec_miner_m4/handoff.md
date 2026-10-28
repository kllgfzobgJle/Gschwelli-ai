# Handoff Report — Milestone 4 (Blackboard, PowerShell REPL, Approval Gate & Omnibox)

**Agent**: `spec_miner_m4`  
**Working Directory**: `c:\Users\andym\gschwelli-ai\.agents\teamwork\spec_miner_m4`  
**Handoff Type**: Hard (Task Complete)  
**Parent Agent**: `orchestrator_1` (`20ee9337-54d2-4ed7-a02f-42aad4232d45`)  
**Timestamp**: 2026-10-28T18:15:00Z  

---

## 1. Observation

1. **Authoritative Specification Inputs**:
   - `ORIGINAL_REQUEST.md` (`c:\Users\andym\gschwelli-ai\.agents\teamwork\ORIGINAL_REQUEST.md`):
     - Lines 28–30 (R1): Right Sidebar specifies Blackboard (`AGENT-01`) with pipeline breadcrumb (`[Plan] → [UIA Detect] → [Verify] → [Execute]`), step cards (`COMPLETE`, `BLOCKED`), and `SHARED STATE / READ-ONLY` variable inspector (`$target_dir`, `$exit_code`, `checkpoint #018`). Specifies PowerShell REPL (`EXIT 0`) with timestamped terminal log view, interactive command input (`PS C:\Fabrication>`), and footer (`pwsh 7.4.2`, `SANDBOX • I/O GUARDED`).
     - Lines 32–36 (R2): Specifies Bottom Human-in-the-Loop Approval Gate banner (`HUMAN-IN-THE-LOOP APPROVAL NEEDED — Overwrite toolhead_mount.stl • backup saved • SEC-810`) with working buttons and keyboard shortcuts: `Approve (Space)`, `Edit`, `Abort (Esc)`, and red `PANIC KILL & UNDO`. Triggering actions must visibly update Mission status, Blackboard `[Execute]` step, PowerShell REPL output, task list, and `/api/confirm` or `/api/undo` endpoints. Specifies Omnibox Command Bar with `+` attachment button, `/run...` chip, natural language input (`Describe the next action, or type / for commands`), slash command autocomplete menu (`/run`, `/scan`, `/approve`, `/undo`, `/clear`, `/mode`), interactive `VOICE` toggle, and model router selector (`Auto-Route: Ollama/Gemini`).
     - Lines 52, 56, 58: Acceptance criteria mandate coherent visual and state feedback across all connected panels upon clicking buttons, pressing shortcuts, or executing REPL / Omnibox commands.
   - `PROJECT.md` (`c:\Users\andym\gschwelli-ai\PROJECT.md`):
     - Feature Inventory items 25–39 explicitly define Milestone 4 scope:
       - Item 25: Blackboard Pipeline Tracker (`[Plan] → [UIA Detect] → [Verify] → [Execute]`)
       - Item 26: Blackboard Step Cards (4 step cards with status badges `COMPLETE`, `BLOCKED`)
       - Item 27: Shared State Inspector (`$target_dir`, `$exit_code`, `checkpoint #018`)
       - Item 28: PowerShell REPL Terminal (Timestamped console log with `EXIT 0` badge)
       - Item 29: PowerShell Command Input (`PS C:\Fabrication> ` input box)
       - Item 30: REPL Status Footer (`pwsh 7.4.2`, `SANDBOX • I/O GUARDED`)
       - Item 31: Approval Gate Banner (`HUMAN-IN-THE-LOOP APPROVAL NEEDED — Overwrite toolhead_mount.stl • backup saved • SEC-810`)
       - Item 32: Approve Action Button & Hotkey (`✓ Approve (Space)` calling `/api/confirm`)
       - Item 33: Edit Action Button (`✏ Edit` parameter / path modification)
       - Item 34: Abort Action Button & Hotkey (`Abort (Esc)` calling `/api/confirm`)
       - Item 35: PANIC KILL & UNDO Button (Red button calling `/api/undo`)
       - Item 36: Omnibox Input & Prefix Chip (`+` button, `/run...` chip, prompt placeholder)
       - Item 37: Slash Command Autocomplete (`/run`, `/scan`, `/approve`, `/abort`, `/undo`, `/mode`, `/clear`)
       - Item 38: Voice Toggle Waveform (Audio waveform icon + `VOICE` pill)
       - Item 39: Model Router Selector (`Auto-Route: Ollama/Gemini`)
     - Lines 121–134: Interface contracts define REST schemas for `/api/confirm`, `/api/undo`, and `/api/repl`.
   - `TEST_INFRA.md` (`c:\Users\andym\gschwelli-ai\TEST_INFRA.md`):
     - Lines 74–88: Documents verifiable assertions and expected behaviors for M4 features.
   - Test Suites:
     - `tests/test_api.py`:
       - `test_confirm_resolve`: tests `/api/confirm` with `approve=true` and `approve=false`.
       - `test_undo`: tests `/api/undo`.
       - `test_scenario_reset_endpoint`: seeds `pending_confirmation` (`overwrite_stl`).
       - `test_repl_endpoint_execution`: tests `/api/repl` for empty commands (`exit_code=0`) and PowerShell output.
       - `test_full_scenario_reset_and_approval_workflow` & `test_full_scenario_reset_and_abort_workflow`: verifies multi-step integration.
     - `tests/test_browser_dom.py`:
       - `test_right_sidebar_structure` (lines 217–232): asserts "Blackboard" or "AGENT-01" or "Plan", and "PowerShell" or "REPL" or "PS " or "pwsh".
       - `test_bottom_approval_gate_structure` (lines 234–248): asserts "APPROVAL", "Approve", "Abort" or "Esc".
       - `test_bottom_omnibox_structure` (lines 250–259): asserts "/run" or "commands".
       - `test_approval_gate_interaction` (lines 279–290): asserts clicking `Approve` does not trigger JS errors.
       - `test_repl_command_submission` (lines 304–315): queries `input[placeholder*='PS'], #repl-input, .repl-input input, input[name='repl']`, fills command, submits Enter.
       - `test_omnibox_input_workflow` (lines 317–327): queries `#command-input, input[placeholder*='Describe']`, enters text.
   - Reference Mockup (`c:\Users\andym\gschwelli-ai\Inspirations\ui_reference_mockup.png`):
     - Visually grounds the Right Sidebar Column (Blackboard with AGENT-01 badge, breadcrumb, 4 step cards, shared state box, PowerShell REPL with 10 initial log lines, `PS C:\Fabrication>` prompt, footer) and Bottom Docks (Amber approval gate with 4 buttons, Omnibox dock with `+`, `/run...`, prompt, `VOICE`, `Auto-Route: Ollama/Gemini`, `↑`).

2. **Existing Implementation Analysis (`ui/dashboard/index.html`)**:
   - Layout Grid (lines 48–54, 290–300):
     - `--top-nav-height: 48px;`
     - `--left-sidebar-width: 270px;`
     - `--right-sidebar-width: 360px;`
     - `--approval-gate-height: 44px;`
     - `--omnibox-height: 48px;`
     - `#view-mission-control`: `grid-template-columns: var(--left-sidebar-width) 1fr var(--right-sidebar-width);`
   - Existing HTML Scaffolding:
     - Right Sidebar (lines 2424–2530): `#right-sidebar-container`, `.blackboard-pane`, `.pipeline-breadcrumb`, `.step-card-list`, `.shared-state-box`, `.repl-pane`, `#repl-logs`, `#repl-input`, `.repl-footer`.
     - Bottom Docks (lines 2655–2717): `#bottom-docks-wrapper`, `#approval-gate-dock`, `#btn-approve`, `#btn-edit`, `#btn-abort`, `#btn-panic`, `#omnibox-dock`, `#btn-attach`, `#chip-slash`, `#command-input`, `#slash-menu`, `#btn-voice-toggle`, `#model-router-select`, `#btn-submit-cmd`.
   - Existing JavaScript Logic (lines 2763–3577):
     - `AppState` store contains `approvalGate`, `blackboard`, `mission`, `tasks`.
     - Handlers: `handleApprove()`, `handleAbort()`, `handlePanic()`, `executeReplCommand(cmd)`, `submitOmniboxCommand(instruction)`.
     - Event listeners: Space/Escape keyboard listener with active element tag check.

---

## 2. Logic Chain

1. **Visual and Layout Consistency (Column C & Bottom Dock)**:
   - The global layout relies on strict fixed dimensions: Right Sidebar must remain at exactly `360px` width (`--right-sidebar-width: 360px;`). The center canvas expands dynamically with `1fr`.
   - The bottom bars are stacked inside `#bottom-docks-wrapper`:
     - Top row: `#approval-gate-dock` (height 44px, background `var(--amber-bg)`, border `var(--amber-border)`).
     - Bottom row: `#omnibox-dock` (height 48px, background `var(--bg-dock)`, border `var(--border-subtle)`).
     Total bottom height is exactly `92px`.
   - In the right sidebar, vertical distribution divides height cleanly:
     - `.blackboard-pane` has `flex: 1.1`, containing the header, pipeline breadcrumb, 4 step cards, and the shared state box.
     - `.repl-pane` has `flex: 1.2`, containing the 30px header (`EXIT 0`), autoscrolling `.repl-logs`, 32px `.repl-input-row`, and 22px `.repl-footer`.

2. **Cross-Component State Synchronization**:
   - The system is an interconnected agent cockpit; actions in the approval gate must cascade instantaneously to 5 different panels:
     1. **Mission Header**: `#mission-status-badge` (`PAUSED • APPROVAL` -> `COMPLETED` on approve, `ABORTED` on abort, `EMERGENCY HALT` on panic).
     2. **Left Sidebar Tasks**: Task 3 (`t3`: "Export toolhead mount") checkbox checks and badge switches from `Approval needed` to `Complete`. Task counter `#task-counter` updates from `2 / 4` to `3 / 4`.
     3. **Blackboard Pipeline & Step Cards**:
        - Breadcrumb `#pipeline-exec-step` (`[Execute]`) changes from `active` (amber) to `complete` (emerald) or `cancelled` (red).
        - Step 4 Header `#step-exec-label` changes from `⚠ [Execute]` to `✓ [Execute]`.
        - Step 4 Badge `#step-exec-badge` changes from `BLOCKED` (`badge-approval`) to `COMPLETE` (`badge-complete`).
        - Step 4 Detail `#step-exec-detail` changes from `Waiting at human approval gate` to `Overwrote toolhead_mount.stl • 62.4 KB written`.
        - Shared State `#state-exit-code` remains `0` on approve, or sets to `1` on failure/cancellation.
     4. **PowerShell REPL**:
        - Appends timestamped confirmation / rollback logs.
        - `#repl-exit-badge` displays `EXIT 0` (or `EXIT 1` on abort).
     5. **Approval Banner**:
        - Transitions styling and text to indicate resolved state.
     6. **Backend Service**:
        - Invokes `POST /api/confirm` (`{"approve": true/false}`) or `POST /api/undo`.
   - This tight synchronization guarantees that the prototype satisfies Acceptance Criteria R1, R2, and R4.

3. **PowerShell REPL Autoscroll & Command Execution**:
   - The REPL must emulate a real terminal: every command entered by the user or log line emitted by the agent must append to `#repl-logs` with automatic scrolling to bottom (`replLogs.scrollTop = replLogs.scrollHeight`).
   - Command dispatch must support:
     - `clear` or `/clear`: clears `#repl-logs` content.
     - Real backend execution: calls `POST /api/repl` with `{"command": cleanCmd}`.
     - Realistic local fallback: handles `Get-Process`, `Test-Path`, `openscad`, `ls`/`dir`, `help` when backend is offline or in simulated mode.
     - Exit code badge updating: updates `#repl-exit-badge` based on returned `exit_code`.

4. **Omnibox Slash Command Autocomplete & Dispatch**:
   - When `#command-input` receives a `/` prefix, `#slash-menu` must open at `bottom: 54px; left: 60px;`.
   - The menu must display 7 commands:
     - `/run <instruction>` (Route through AI)
     - `/scan` (Re-scan SOM Marks)
     - `/approve` (Confirm Safety Gate)
     - `/abort` (Halt Pipeline)
     - `/undo` (Emergency Rollback)
     - `/mode <name>` (Switch View)
     - `/clear` (Clear Console)
   - Selecting a slash command (via click or Enter) inserts the command into `#command-input` and closes the menu.
   - Submitting `/approve`, `/abort`, or `/undo` routes directly to the approval gate state machine.
   - Submitting natural language or `/run` invokes `POST /api/route`.

5. **Keyboard Hotkey Guards (Space & Escape)**:
   - Crucial edge case: If the user presses `Space` while typing a command into `#command-input` or `#repl-input`, the system must NOT approve the safety gate!
   - Similarly, pressing `Escape` while typing must not abort the entire mission.
   - Guard condition: Check `document.activeElement.tagName.toLowerCase()`. If `activeElement` is `input` or `textarea`, ignore global hotkey actions.
   - If `#slash-menu` is open, pressing `Escape` must close the menu without triggering `handleAbort()`.

---

## 3. Detailed Technical Specification for Milestone 4

### 3.1 DOM Element Inventory & IDs
| Element ID | Tag / Element | Location / Component | Purpose |
|------------|---------------|----------------------|---------|
| `right-sidebar-container` | `<aside>` | Mission Control Column 3 | 360px container housing Blackboard and REPL |
| `pipeline-exec-step` | `<span>` | Blackboard Breadcrumb | Active/blocked/completed indicator for `[Execute]` |
| `step-exec-label` | `<span>` | Blackboard Step 4 Header | Displays `⚠ [Execute]` or `✓ [Execute]` |
| `step-exec-badge` | `<span>` | Blackboard Step 4 Header | Status badge (`BLOCKED`, `COMPLETE`, `CANCELLED`) |
| `step-exec-detail` | `<div>` | Blackboard Step 4 Body | Explanatory detail text for Step 4 |
| `state-exit-code` | `<span>` | Shared State Inspector | Displays variable `$exit_code` value (`0` or `1`) |
| `repl-exit-badge` | `<span>` | REPL Header | Shows exit code badge `EXIT 0` |
| `repl-logs` | `<div>` | REPL Body | Autoscrolling container for timestamped terminal logs |
| `repl-input` | `<input>` | REPL Command Row | Interactive prompt input (`placeholder="PS C:\Fabrication>"`) |
| `approval-gate-dock` | `<div>` | Bottom Dock Row 1 | 44px Amber Human-in-the-Loop approval banner |
| `gate-detail-text` | `<span>` | Approval Gate Left | Description: `Overwrite toolhead_mount.stl • backup saved • SEC-810` |
| `btn-approve` | `<button>` | Approval Gate Actions | Approve button: `✓ Approve (Space)` |
| `btn-edit` | `<button>` | Approval Gate Actions | Edit button: `✏ Edit` |
| `btn-abort` | `<button>` | Approval Gate Actions | Abort button: `Abort (Esc)` |
| `btn-panic` | `<button>` | Approval Gate Actions | Panic button: `🚫 PANIC KILL & UNDO` |
| `omnibox-dock` | `<div>` | Bottom Dock Row 2 | 48px Omnibox command bar |
| `btn-attach` | `<button>` | Omnibox Left | `+` attachment / context button |
| `chip-slash` | `<span>` | Omnibox Input Row | `/run...` chip triggering slash autocomplete |
| `command-input` | `<input>` | Omnibox Center | Natural language input (`placeholder="Describe the next action..."`) |
| `slash-menu` | `<div>` | Omnibox Popover | Autocomplete dropdown menu with 7 commands |
| `btn-voice-toggle` | `<button>` | Omnibox Right | Audio waveform toggle pill (`VOICE`) |
| `model-router-select` | `<select>` | Omnibox Right | Dropdown: `Auto-Route: Ollama/Gemini` |
| `btn-submit-cmd` | `<button>` | Omnibox Right | Submit button: `↑` (circular cyan send button) |

### 3.2 CSS Classes & Design Tokens
- **Borders & Backgrounds**:
  - `var(--bg-panel)`: `#0b121c`
  - `var(--bg-card)`: `#101a28`
  - `var(--bg-dock)`: `#080e18`
  - `var(--border-subtle)`: `#1b2a3e`
  - `var(--border-bright)`: `rgba(0, 229, 255, 0.35)`
  - `var(--amber-bg)`: `rgba(245, 158, 11, 0.12)`
  - `var(--amber-border)`: `rgba(245, 158, 11, 0.6)`
  - `var(--emerald-bg)`: `rgba(16, 185, 129, 0.12)`
  - `var(--red-bg)`: `rgba(239, 68, 68, 0.15)`
- **Component Classes**:
  - `.blackboard-pane`: flex 1.1, border-bottom 1px solid subtle, padding 12px 14px
  - `.pipeline-breadcrumb`: font-family mono, font-size 10px, gap 4px
  - `.breadcrumb-step.complete`: color `var(--emerald-success)` (`#10b981`)
  - `.breadcrumb-step.active`: color `var(--amber-warning)` (`#f59e0b`)
  - `.breadcrumb-step.error`: color `var(--red-panic)` (`#ef4444`)
  - `.step-card`: background `var(--bg-card)`, border-radius 6px, padding 7px 10px
  - `.badge-complete`: background `var(--emerald-bg)`, color `var(--emerald-success)`
  - `.badge-approval`: background `var(--amber-bg)`, color `var(--amber-warning)`
  - `.shared-state-box`: background `#060a10`, border-radius 6px, padding 8px 10px
  - `.repl-pane`: flex 1.2, background `#05080f`, overflow hidden
  - `.repl-header`: height 30px, background `#09101b`, border-bottom 1px solid subtle
  - `.repl-logs`: padding 10px 12px, font-family mono, font-size 10.5px, overflow-y auto
  - `.log-line`: display flex, gap 8px
  - `.log-time`: color `#527191`, min-width 50px
  - `.log-cmd`: color `var(--cyan-accent)` (`#00e5ff`)
  - `.log-info`: color `#cbd5e1`
  - `.log-warn`: color `var(--amber-warning)` (`#f59e0b`)
  - `.log-success`: color `var(--emerald-success)` (`#10b981`)
  - `.repl-input-row`: height 32px, background `#070d16`, border-top 1px solid subtle
  - `.repl-prompt`: font-family mono, font-size 11px, color `var(--cyan-accent)`
  - `.repl-input`: flex 1, background transparent, border none, color `#ffffff`
  - `.repl-footer`: height 22px, background `#060a10`, border-top 1px solid rgba(27,42,62,0.6)
  - `.gate-btn`: font-size 11px, font-weight 600, padding 5px 12px, border-radius 5px
  - `.btn-approve`: background `var(--amber-warning)`, color `#060a10`
  - `.btn-edit`: background `var(--bg-card)`, border subtle, color `var(--text-secondary)`
  - `.btn-abort`: background `var(--bg-card)`, border subtle, color `var(--text-secondary)`
  - `.btn-panic`: background `var(--red-bg)`, border rgba(239,68,68,0.6), color `var(--red-panic)`
  - `.slash-menu`: position absolute, bottom 54px, left 60px, width 280px, background `var(--bg-card-elevated)`
  - `.slash-item`: padding 6px 10px, display flex, justify-content space-between

### 3.3 State Machine Transition Matrix
| Trigger / Event | Mission Badge | Task 3 Status | Blackboard Step 4 | Breadcrumb Step 4 | REPL Output Appended | Backend API Call |
|-----------------|---------------|---------------|-------------------|-------------------|----------------------|------------------|
| **Initial Prototype Load / Reset** | `PAUSED • APPROVAL` (amber) | `Approval needed` (2/4 checked) | `BLOCKED` (amber) | `active` (amber) | 10 default lines (Mockup ground truth) | `POST /api/scenario/reset` |
| **Click `#btn-approve` or `Space`** | `COMPLETED` (emerald) | `Complete` (3/4 checked) | `COMPLETE` (emerald) | `complete` (emerald) | `[CONFIRM] User approved SEC-810...` + `EXIT 0` | `POST /api/confirm` (`{"approve": true}`) |
| **Click `#btn-abort` or `Esc`** | `ABORTED` (red) | `Cancelled` (amber/red) | `CANCELLED` (red) | `error` (red) | `[ABORT] Operation cancelled...` | `POST /api/confirm` (`{"approve": false}`) |
| **Click `#btn-panic` (`PANIC KILL`)** | `EMERGENCY HALT` (red pulsing) | `Halted` (red) | `HALTED` (red) | `error` (red) | `[PANIC] KILL SIGNAL RECEIVED...` | `POST /api/undo` |
| **Click `#btn-edit`** | `PAUSED • APPROVAL` | `Approval needed` | `BLOCKED` | `active` | `[EDIT] Destination path modified: ...` | None (client-side update) |

### 3.4 Slash Command Autocomplete Inventory
| Command | Label / Description | Behavior on Selection / Submit |
|---------|---------------------|--------------------------------|
| `/run <instruction>` | Route through AI | Dispatches instruction to `POST /api/route` |
| `/scan` | Re-scan SOM Marks | Triggers perception canvas scanline animation and telemetry increment |
| `/approve` | Confirm Safety Gate | Dispatches `handleApprove()` resolving gate to `COMPLETED` |
| `/abort` | Halt Pipeline | Dispatches `handleAbort()` resolving gate to `ABORTED` |
| `/undo` | Emergency Rollback | Dispatches `handlePanic()` invoking `POST /api/undo` |
| `/mode <name>` | Switch View | Changes active top-level tab (`mission_control`, `knowledge_studio`, `vision_som`, `focus_chat`) |
| `/clear` | Clear Console | Clears `#repl-logs` terminal view |

### 3.5 REPL Built-in / Fallback Commands
| Command | Output / Response | Exit Code |
|---------|-------------------|-----------|
| `clear` / `/clear` | Clears terminal log view | 0 |
| `Get-Process` | `PID 8044 • openscad.exe • WorkingSet: 124.6 MB`<br>`PID 9102 • python.exe (aether) • WorkingSet: 88.2 MB` | 0 |
| `Test-Path $target_dir` | `True` | 0 |
| `openscad --check-parameters` | `CGAL: valid 2-manifold mesh`<br>`1,248 facets • 62.4 KB • exit 0` | 0 |
| `Export-Mesh -Format STL` | `SEC-810: existing file at target`<br>`WRITE HELD • awaiting approval` | 0 |
| `ls` / `dir` | Lists fabrication directory files (`workflow.md`, `toolhead_mount.scad`, etc.) | 0 |
| `help` | Lists supported commands and shortcuts | 0 |
| Other Arbitrary String | Proxies to backend `POST /api/repl` (or fallback: `Command executed: <cmd> (exit 0)`) | 0 (or 1 on error) |

---

## Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Blackboard | Pipeline Tracker | Monospace breadcrumb trail showing 4 stages: `[Plan] → [UIA Detect] → [Verify] → [Execute]` | Agent execution stage updates | Highlights active/complete stages in green/amber/red | Defaults to `[Execute]` active/blocked | `ORIGINAL_REQUEST.md`, `PROJECT.md` #25 |
| 2 | Blackboard | Step Cards | 4 cards displaying step name, badge, description, and execution details | State updates | Rendered cards with status badges (`COMPLETE`, `BLOCKED`) | Graceful fallback on missing details | `ORIGINAL_REQUEST.md`, `PROJECT.md` #26 |
| 3 | Blackboard | Shared State Inspector | Read-only variable box displaying `$target_dir`, `$exit_code`, and `checkpoint #018` | Shared state store | Key-value variable rows | Shows `None` or default string if unset | `ORIGINAL_REQUEST.md`, `PROJECT.md` #27 |
| 4 | REPL | PowerShell REPL Terminal | Timestamped console log view with syntax coloring classes and exit code badge | Log events / command outputs | Color-coded terminal lines (`.log-time`, `.log-cmd`, etc.) | Auto-scrolls to bottom | `ORIGINAL_REQUEST.md`, `PROJECT.md` #28 |
| 5 | REPL | PowerShell Command Input | Interactive `PS C:\Fabrication> ` input box with Enter key submission | Command text + Enter | Appends command and output to terminal log | Ignores empty string submissions | `ORIGINAL_REQUEST.md`, `PROJECT.md` #29 |
| 6 | REPL | REPL Status Footer | Telemetry footer displaying green dot, `pwsh 7.4.2`, and `SANDBOX • I/O GUARDED` | Sandbox configuration | Monospace footer text | Static indicator | `ORIGINAL_REQUEST.md`, `PROJECT.md` #30 |
| 7 | Approval Gate | Approval Banner Dock | Full-width amber banner (#approval-gate-dock) with warning icon, title, and SEC-810 detail | Pending safety gate state | 44px glowing amber dock | Transitions color on resolution | `ORIGINAL_REQUEST.md`, `PROJECT.md` #31 |
| 8 | Approval Gate | Approve Action & Hotkey | `✓ Approve (Space)` button calling `/api/confirm` (approve=true) | Click or Space keypress | Unblocks mission, updates tasks, blackboard, and REPL | Guarded when typing in input | `ORIGINAL_REQUEST.md`, `PROJECT.md` #32 |
| 9 | Approval Gate | Edit Action Button | `✏ Edit` button allowing parameter or path modification | Click | Prompts operator to update destination path | Cancels edit on Escape | `ORIGINAL_REQUEST.md`, `PROJECT.md` #33 |
| 10 | Approval Gate | Abort Action & Hotkey | `Abort (Esc)` button calling `/api/confirm` (approve=false) | Click or Esc keypress | Cancels execution safely, marks mission ABORTED | Guarded when typing in input | `ORIGINAL_REQUEST.md`, `PROJECT.md` #34 |
| 11 | Approval Gate | PANIC KILL & UNDO | High-visibility red button calling `/api/undo` | Click | Triggers emergency halt, rolls back last action | Safe notice if undo stack empty | `ORIGINAL_REQUEST.md`, `PROJECT.md` #35 |
| 12 | Omnibox | Omnibox Input & Prefix Chip | Full-width prompt dock with `+` button, `/run...` chip, and placeholder | Text input / Enter | Dispatches command / route | Disables submit when empty | `ORIGINAL_REQUEST.md`, `PROJECT.md` #36 |
| 13 | Omnibox | Slash Autocomplete Popover | Dropdown menu displaying 7 slash commands (`/run`, `/scan`, `/approve`, etc.) | Typing `/` in input or clicking chip | 280px popup menu with command descriptions | Closes on Escape or outside click | `ORIGINAL_REQUEST.md`, `PROJECT.md` #37 |
| 14 | Omnibox | Voice Toggle Waveform | Waveform audio icon + `VOICE` pill | Click | Toggles active audio capture / speech input | Visual fallback if mic unavailable | `ORIGINAL_REQUEST.md`, `PROJECT.md` #38 |
| 15 | Omnibox | Model Router Selector | Dropdown menu: `Auto-Route: Ollama/Gemini` | Select option (auto, ollama, uia, gemini) | Sets active routing engine for `/api/route` | Defaults to auto-route | `ORIGINAL_REQUEST.md`, `PROJECT.md` #39 |
| 16 | Integration | Multi-Panel State Engine | Synchronizes state across Mission Header, Tasks, Blackboard, REPL, and Gate Dock | Approve / Abort / Panic actions | Unified UI state transition across 5 widgets | Idempotent transitions | Discovered in code analysis |
| 17 | Integration | Typing Focus Guard | Protects `Space` and `Escape` from triggering approval when typing in inputs | Keydown events | Disables hotkey handler when activeElement is INPUT | Normal text editing preserved | Discovered in code analysis |
| 18 | Integration | REPL Terminal Clear | `clear` or `/clear` command entered in REPL or Omnibox | Command string | Empties `#repl-logs` DOM node | Resets scroll position to top | Discovered in code analysis |
| 19 | Integration | REPL Dynamic Exit Badge | `#repl-exit-badge` updates to `EXIT 0` or `EXIT 1` based on execution result | Execution exit_code | Updates text and class (`badge-complete` vs `badge-approval`) | Defaults to `EXIT 0` | Discovered in code analysis |
| 20 | Integration | Scenario Reset State Sync | `POST /api/scenario/reset` re-arms pending confirmation in backend and UI | HTTP POST | Seeds `overwrite_stl` gate in backend and restores UI state | 200 OK with scenario metadata | Discovered in `server/api.py` |
| 21 | Integration | Slash Menu Keyboard Navigation | Up/Down arrows cycle active item, Enter selects command, Esc closes menu | ArrowUp, ArrowDown, Enter, Esc | Changes highlighted item and autofills input | Prevents page scrolling | Discovered in UI analysis |
| 22 | Integration | Omnibox Context Attachment | Clicking `#btn-attach` (`+`) allows adding file context to prompt | Click | Context indicator / prompt prefix addition | No-op fallback if file unselected | Discovered in mockup analysis |

---

## Edge Cases

| # | Feature | Input / Condition | Observed / Required Behavior |
|---|---------|-------------------|------------------------------|
| 1 | Hotkey Typing Guard | User presses `Space` while typing in `#repl-input` or `#command-input` | Hotkey MUST NOT trigger `handleApprove()`; space character is inserted into input text. |
| 2 | Hotkey Typing Guard | User presses `Escape` while typing in `#repl-input` or `#command-input` | Hotkey MUST NOT trigger `handleAbort()`; input field loses focus or clears without mission abortion. |
| 3 | Slash Menu Dismissal | User presses `Escape` while `#slash-menu` autocomplete is open | `#slash-menu` closes immediately without triggering `handleAbort()`. |
| 4 | Rapid / Repeated Clicks | User clicks `#btn-approve` 5 times in rapid succession | The action is idempotent: first click resolves gate and updates state; subsequent clicks are ignored and do not flood `/api/confirm`. |
| 5 | Server Offline Fallback | User executes `Test-Path $target_dir` in REPL when server is offline | UI returns simulated fallback output (`True`) without throwing uncaught JS exceptions or console errors. |
| 6 | Empty REPL Command | User presses `Enter` in `#repl-input` with empty string or whitespace | Input field is cleared, no command is dispatched, no empty log lines are appended. |
| 7 | REPL Terminal Log Pruning | REPL logs accumulate more than 500 lines | Oldest DOM lines are pruned to maintain high rendering performance; auto-scrolls smoothly to bottom. |
| 8 | Empty Undo Stack | User clicks `🚫 PANIC KILL & UNDO` when undo history is empty | UI halts agent safely, calls `POST /api/undo` (returning `can_undo: false`), and logs `[UNDO] Emergency halt verified.` without crashing. |
| 9 | Unconfirmed Resolution | User visits dashboard after backend `/api/confirm` was already resolved | UI initializes in resolved or unblocked state without showing conflicting approval banner. |
| 10 | Slash Command Autofill | User clicks `/mode` in `#slash-menu` | `#command-input` value becomes `/mode `, menu closes, and cursor focuses ready for parameter entry. |
| 11 | Viewport Responsiveness | Browser viewport resized to 1024x768 | Right sidebar maintains 360px width, bottom docks remain pinned at 44px + 48px, horizontal scroll enabled if required without layout breakage. |
| 12 | `/clear` in REPL | User types `clear` or `/clear` in REPL input | `#repl-logs` is completely cleared; prompt remains ready. |

---

## 4. Caveats

1. **Host-Level PowerShell Execution**: The `/api/repl` endpoint uses `executors.ps_repl.ps_repl` when the backend is active. If running on a non-Windows host (e.g. Linux container without PowerShell installed), the backend falls back to simulated execution. The frontend handles this seamlessly by displaying the output.
2. **Audio Hardware Access**: The `#btn-voice-toggle` button updates voice status in `AppState` and calls `POST /api/voice`. It does not require physical microphone hardware to be attached to the test machine.
3. **OpenSCAD Dependency**: OpenSCAD does not need to be running on the machine; the simulated process PID (`PID 8044`) and CGAL mesh diagnostics are provided as rich realistic fixtures.

---

## 5. Conclusion

Milestone 4 specification discovery is complete. The exact element inventory, DOM IDs, CSS classes, layout grid constraints, keyboard bindings (Space, Esc), slash commands, REPL command behaviors, and backend integration endpoints (`/api/repl`, `/api/confirm`, `/api/undo`, `/api/scenario/reset`) have been rigorously analyzed and documented.

All 15 Milestone 4 features (Items 25–39 from `PROJECT.md`) and 7 discovered related integration features have been verified against authoritative project documents (`ORIGINAL_REQUEST.md`, `PROJECT.md`, `TEST_INFRA.md`, `test_api.py`, `test_browser_dom.py`, and `ui_reference_mockup.png`). This report provides an exact, self-contained implementation and verification blueprint for Milestone 4.

---

## 6. Verification Method

1. **Verify Documentation Structure**:
   - Inspect `c:\Users\andym\gschwelli-ai\.agents\teamwork\spec_miner_m4\handoff.md`.
   - Confirm presence of all 5 mandatory components: Observation, Logic Chain, Caveats, Conclusion, Verification Method.
   - Confirm presence of `## Features Discovered` (22 items) and `## Edge Cases` (12 items) tables.
2. **Execute Backend API Verification**:
   ```powershell
   uv run --with pytest pytest tests/test_api.py -v
   ```
   Assert 100% pass across all REST and WebSocket tests (`test_scenario_reset_endpoint`, `test_repl_endpoint_execution`, `test_full_scenario_reset_and_approval_workflow`, `test_full_scenario_reset_and_abort_workflow`).
3. **Execute Browser DOM Headless Tests**:
   ```powershell
   uv run --with pytest,playwright pytest tests/test_browser_dom.py -v
   ```
   Assert that `test_right_sidebar_structure`, `test_bottom_approval_gate_structure`, `test_bottom_omnibox_structure`, `test_approval_gate_interaction`, `test_repl_command_submission`, and `test_omnibox_input_workflow` all pass with zero console errors.
4. **Invalidation Conditions**:
   - Any omission of the 15 core features (Items 25–39).
   - Any DOM ID mismatch with `test_browser_dom.py` (e.g. `#repl-input`, `#command-input`, `#btn-approve`, `#btn-abort`, `#btn-panic`).
   - Any failure of the typing focus guard allowing `Space` to trigger approval while typing in input fields.
