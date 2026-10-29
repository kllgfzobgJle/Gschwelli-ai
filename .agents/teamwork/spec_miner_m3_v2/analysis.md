# Technical Specification Blueprint: Milestone 3 — Polymorphic Stage

**Document:** `analysis.md`  
**Author:** `spec_miner_m3_v2` (teamwork_spec_miner subagent)  
**Target Milestone:** Milestone 3 (Polymorphic Stage: 4 Viewports, Split-Screen Mode, Quick Telemetry Drawers, and Center Stage CAD Eradication)  
**Parent Orchestrator:** `db3d98a0-f6a4-45e7-9dea-32dceda77cf0`  
**Date:** 2026-10-29  

---

## 1. Executive Summary & Authoritative Ground Truth

Following the authoritative user mandate in `ORIGINAL_REQUEST.md` (R2, R4, R5) and project definition in `PROJECT.md` (Features #15, #22, #23, #24, #25, #26, #27, #28), this specification establishes the technical architecture to transform the center stage from a legacy domain-specific OpenSCAD CAD/3D viewer into a high-performance, domain-agnostic Polymorphic 4-Viewport Operating Canvas.

The stage enables operators and autonomous multimodal agents to freely switch among four universal workspace contexts (Vision Stream, Document Studio, Reasoning Graph, and Shell Sandbox) with hotkey navigation (`Ctrl+1..4`), run dual viewports in 50/50 Split-Screen mode, slide out real-time telemetry drawers, and operate with 0.0% CAD artifact residue.

---

## Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Stage Architecture | Feature #15: Polymorphic 4-Viewport Container | Switchable main stage container hosting 4 viewports (Vision Stream, Document Studio, Reasoning Graph, Shell Sandbox) with segmented tabs and keyboard hotkeys (Ctrl+1, Ctrl+2, Ctrl+3, Ctrl+4). | Mouse clicks on tab buttons (`[data-viewport="1..4"]`), keyboard shortcuts (`Ctrl+1..4`), Omnibar `/mode` command, file tree click-to-preview. | Renders targeted viewport (`display: flex`), hides inactive viewports, updates tab indicator and stage telemetry bar without DOM re-creation. | Non-existent viewport index ignored safely; rapid switching stress maintains DOM state without memory leaks. | `ORIGINAL_REQUEST.md` R2, `PROJECT.md` #15, `test_browser_dom.py:345` |
| 2 | Blackboard & Visual Reasoning | Feature #22: Task & Reasoning Graph (Blackboard Visualizer) | Interactive Directed Acyclic Graph (DAG) visualizing execution paths: Goal ➔ Sub-Tasks ➔ Gates ➔ Artifacts, with status badges (`pending`, `in_progress`, `done`, `blocked`). | Task updates from `/api/tasks` or `/api/state`, confirmation gate events from `pending_confirmation`, node clicks. | Dynamic SVG/HTML DAG diagram with directed connectors, glowing status rings, and node property inspection. | Empty task list renders Goal node connected to neutral placeholder node without SVG syntax errors. | `ORIGINAL_REQUEST.md` R2, `PROJECT.md` #22, `test_browser_dom.py:407` |
| 3 | Telemetry & Memory | Feature #23: Live Variables & Memory State Inspector | Inspector panel displaying live agent context variables (`$workspace`, `$exit_code`, `$current_task`, etc.) and persistent memory key-values synced with `/api/memory`. | User clicks variable to insert into REPL, form submission for `POST /api/memory`, delete click for `DELETE /api/memory/{key}`. | Table of reactive variables with monospace formatting, category badges (`notes`, `facts`, `system`), and direct memory CRUD. | Special characters and HTML in memory values strictly escaped via textContent; network disconnect shows cached state. | `ORIGINAL_REQUEST.md` R2, `PROJECT.md` #23, `server/api.py:424` |
| 4 | Terminal & Execution | Feature #24: Multi-Tab Shell Sandbox | Monospace terminal emulator container with dedicated shell profile tabs (`PowerShell`, `Bash`, `Sandbox`). | Tab clicks, command prompt input, terminal focus. | Active tab styling, prompt prefix updates (`PS C:\...>` vs `bash$` vs `sandbox>`), isolated session history buffers. | Unknown shell profile defaults gracefully to PowerShell without crashing terminal container. | `ORIGINAL_REQUEST.md` R2, `PROJECT.md` #24, `test_browser_dom.py:422` |
| 5 | Terminal & Execution | Feature #25: REPL Execution & Log Styling | Interactive command execution sending commands to `POST /api/repl`, rendering command timestamps, exit codes, and colored stdout/stderr streams. | Text command + `Enter`, Up/Down arrow history cycling, Clear button `⊘`. | Colored monospace log lines (`log-cmd`, `log-stdout`, `log-stderr`, `log-warn`, `log-success`), exit code badge (`EXIT 0` / `EXIT 1`), auto-scroll to bottom. | Empty command returns exit code 0 without output; failed commands highlight in crimson (`#ef4444`) with exit 1. | `ORIGINAL_REQUEST.md` R2, `PROJECT.md` #25, `server/api.py:467`, `ps_repl.py` |
| 6 | Layout & Display | Feature #26: Split-Screen Canvas Mode | 50/50 side-by-side layout button/toggle (`#btn-split-screen`, icon `◫`) rendering two viewports simultaneously (e.g. Vision Stream + Shell Sandbox). | Click on split button, slash command `/split`, window resize. | Stage container switches to 2-column grid (`grid-template-columns: 1fr 1fr`), displays primary & secondary viewports with independent controls. | 1024x768 compact width preserves horizontal bounds without overflow (`scrollWidth <= innerWidth`); uninitialized side defaults to Viewport 4. | `ORIGINAL_REQUEST.md` R2, `PROJECT.md` #26, `test_browser_dom.py:440` |
| 7 | Drawers & Inspections | Feature #27: Quick Telemetry Drawers | Slide-out quick panels for Tools (`/api/tool`), Memory (`/api/memory`), Cache (`/api/cache`), and Undo Stack (`/api/undo`). | Drawer trigger buttons (`[data-drawer]`), backdrop click, `Esc` key. | Smooth slide-out panel from right margin with live data listing, interactive execution forms, and clear/rollback actions. | `Esc` inside drawer input closes drawer without triggering global Safety Interceptor Abort; API failure shows cached state. | `ORIGINAL_REQUEST.md` R2, `PROJECT.md` #27, `test_browser_dom.py:455` |
| 8 | Cleanliness & Integrity | Feature #28: Center Stage CAD Eradication | 100% removal and eradication of OpenSCAD window frames, 3D CAD mesh SVG, polygon shaders, STL export docks, CSG overlays, and 3D printing widgets. | Automated regex scan against `CAD_FORBIDDEN_PATTERNS` across HTML, CSS, JavaScript, and backend endpoints. | Universal domain-agnostic perception canvas and viewports; zero occurrences of forbidden CAD tokens. | Any lingering CAD token fails verification immediately with zero-tolerance policy. | `ORIGINAL_REQUEST.md` R1, R2, `PROJECT.md` #28, `test_adversarial_m1_endpoints.py:618` |
| 9 | Perception (Related) | Feature #16: Screen & Vision Stream (Set-of-Marks) | Universal desktop/window perception viewer with 12 Set-of-Marks tags (`[01]`-`[12]`) mapping to universal UI components. | Mouse hover/click on marks, `/api/som` payload. | Visual mark bounding boxes, non-occluding pointer events, active focus rings. | Missing targets in perception feed render warning badge without disrupting viewport layout. | `ORIGINAL_REQUEST.md` R2, `PROJECT.md` #16, `server/api.py:476` |
| 10 | Perception (Related) | Feature #17: SOM Non-Occluding Pointer Events | Pointer-events pass-through guaranteeing `0.0 px²` occlusion of underlying UI controls. | Mouse click through SOM tag overlay to underlying canvas elements. | Click passes transparently to underlying button/input/canvas without interception bug. | Tag click handler preserved via target coordinate hit-testing or pass-through delegation. | `ORIGINAL_REQUEST.md` R2, `PROJECT.md` #17, `test_browser_dom.py:602` |
| 11 | Perception (Related) | Feature #18: Perception Toolbar Controls | Toolbar with Zoom In/Out, Pan, Element Inspector toggle, and real-time Coordinates readout (`X: 0, Y: 0`). | Mouse movement over canvas, toolbar button clicks (`#btn-cam-zoom`, `#btn-cam-reset`). | Canvas transform matrix updates (`scale()`, `translate()`), coordinates readout in toolbar telemetry. | Rapid zoom operations clamped within safe bounds (`0.5x` to `3.0x`). | `ORIGINAL_REQUEST.md` R2, `PROJECT.md` #18, `test_browser_dom.py:364` |
| 12 | Studio (Related) | Feature #19: Markdown 2-Column Split Studio | 2-column document editor/viewer: left raw editable text, right live formatted HTML preview with strict XSS sanitization. | Typing in raw textarea, file selection (`.md`). | Synchronized rendered HTML preview with tables, headings, code blocks; script tags neutralized. | Injected `<script>` or `onerror` attributes sanitized completely without script execution. | `ORIGINAL_REQUEST.md` R2, `PROJECT.md` #19, `test_browser_dom.py:388` |
| 13 | Studio (Related) | Feature #20: Code & Config Monospace Studio | Syntax-highlighted monospace viewer/editor for `.py`, `.js`, `.json`, `.yaml`, `.toml`, `.sh` with line numbers and copy button. | File selection from file tree. | Formatted code viewer with line number gutter, token color highlighting, line count telemetry. | Large source files (>10,000 lines) truncated or scrolled efficiently without UI freeze. | `ORIGINAL_REQUEST.md` R2, `PROJECT.md` #20 |
| 14 | Studio (Related) | Feature #21: Tabular / CSV Data-Grid View | Dense spreadsheet-like data grid with sticky column headers, row numbering, and zebra striping for `.csv`, `.tsv`, `.jsonl`. | File selection (`.csv`, `.tsv`). | Table grid rendered with column headers, formatted cells, and record count badge. | Malformed CSV or mismatched columns rendered safely with fallback raw text view. | `ORIGINAL_REQUEST.md` R2, `PROJECT.md` #21 |
| 15 | Studio (Related) | Feature #13: File Quick Preview Integration | Clicking any file in Left Sidebar File Explorer immediately routes to Viewport 2 with MIME-detected preview. | File item click in `#file-tree`. | Viewport 2 activated, file content loaded from `/api/workspace/files` or local store. | Non-existent file path shows error toast and resets preview pane safely. | `ORIGINAL_REQUEST.md` R1, `PROJECT.md` #13, `test_browser_dom.py:321` |

---

## Edge Cases

| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | Feature #15 (Viewport Hotkeys) | User focuses text input (`#repl-input` or Omnibar) and presses `Ctrl+1..4`. | `Ctrl+1..4` switches the active viewport without typing literal numbers into the input field, while preserving input text content. |
| 2 | Feature #15 (Switching Stress) | Automated script triggers 20 viewport switches per second across all 4 views. | Zero memory leak, zero uncaught JavaScript exceptions, CSS transitions settle cleanly, and active view state remains synchronized with Top Nav and stage tabs. |
| 3 | Feature #26 (Split-Screen on 1024x768) | `#btn-split-screen` toggled at 1024px compact width. | Container maintains `scrollWidth <= innerWidth` (0.0px horizontal overflow); each viewport column measures 504px with compact scrollbars and legible controls. |
| 4 | Feature #26 (Concurrent Operations) | User types commands into Shell Sandbox in Right pane while hovering SOM tags in Vision Stream in Left pane. | Events route independently to respective viewports: keyboard focus remains in terminal, while mouse coordinates and hover leader lines track in Vision canvas without stealing input focus. |
| 5 | Feature #22 (Empty Tasks DAG) | Active workspace has 0 tasks and 0 confirmation gates. | DAG renderer draws Goal node connected with dotted line to neutral placeholder card: `[○ No tasks queued. Enter a task in Left Sidebar]`, avoiding null SVG coordinate errors. |
| 6 | Feature #22 (Task Status Transitions) | Task status transitions `backlog` ➔ `in_progress` ➔ `blocked` ➔ `done`. | DAG node dynamically transitions border color and icon: `#64748b` (circle) ➔ `#00e5ff` (pulsing dot) ➔ `#f59e0b` (warning badge) ➔ `#10b981` (checkmark), updating connecting line gradients in real time. |
| 7 | Feature #23 (XSS in Memory Facts) | User or backend injects memory key `<script>alert('pwn')</script>` and value `<img src=x onerror=alert(1)>`. | Displayed using `textContent` and HTML entity escaping; text renders literally as characters; zero script execution (`window.__XSS_DETECTED__ = false`). |
| 8 | Feature #23 (Live Variable Click-to-Insert) | User clicks `$workspace` or `$exit_code` row in Live Variables table. | Variable name (e.g. `$workspace`) is immediately appended to active cursor position in `#repl-input` or `#command-input`, with subtle highlight pulse feedback. |
| 9 | Feature #24 & #25 (REPL Multiline & ANSI Output) | Command outputs 500 lines containing ANSI escape sequences and mixed stdout/stderr. | ANSI sequences parsed or stripped into CSS classes (`log-stdout`, `log-stderr`); logs container auto-scrolls to bottom; scroll height capped cleanly. |
| 10 | Feature #25 (Empty REPL Command) | User presses `Enter` on blank REPL input field. | No network request sent or backend returns `{command: "", output: "", exit_code: 0}`; prompt remains clean without appending blank error lines. |
| 11 | Feature #27 (Quick Drawer Esc Precedence) | Quick Drawer is open and user presses `Escape`. | Drawer closes immediately (`transform: translateX(100%)`). Crucially, does NOT trigger the global Human-in-the-Loop Safety Interceptor Abort action (`handleAbort`). |
| 12 | Feature #27 (Drawer Mutex Exclusivity) | User opens Tools Drawer (`data-drawer="tools"`), then clicks Memory Drawer (`data-drawer="memory"`). | Tools drawer transitions to Memory drawer in-place without stacking multiple overlapping drawer panes or orphaned backdrops. |
| 13 | Feature #28 (Zero CAD Token Scan) | Full text scan of `ui/dashboard/index.html` against `CAD_FORBIDDEN_PATTERNS`. | Zero occurrences of `openscad`, `toolhead_mount`, `cad-mesh-svg`, `csg-overlay`, `facet-base-top`, `btn_export_stl`, or `overwrite_stl` on center stage or sidebars. |

---

## 2. Technical Blueprint: Feature #15 (Polymorphic 4-Viewport Container)

### 2.1 Container DOM Architecture
Replace the legacy `#cad-viewport-frame` within `#center-canvas-container` with a unified polymorphic stage container:

```html
<main id="center-canvas-container">
  <!-- A. Polymorphic Stage Header & Viewport Switcher -->
  <div class="stage-nav-bar" id="stage-nav-bar">
    <div class="viewport-selector-tabs" role="tablist" aria-label="Viewport Switcher">
      <button class="viewport-tab-btn active" id="tab-vp-1" data-viewport="1" role="tab" aria-selected="true" title="Shortcut: Ctrl+1">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="3"></circle>
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
        </svg>
        <span>1: Vision Stream</span>
        <span class="tab-hotkey-hint">Ctrl+1</span>
      </button>

      <button class="viewport-tab-btn" id="tab-vp-2" data-viewport="2" role="tab" aria-selected="false" title="Shortcut: Ctrl+2">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
          <line x1="16" y1="13" x2="8" y2="13"></line>
          <line x1="16" y1="17" x2="8" y2="17"></line>
        </svg>
        <span>2: Document Studio</span>
        <span class="tab-hotkey-hint">Ctrl+2</span>
      </button>

      <button class="viewport-tab-btn" id="tab-vp-3" data-viewport="3" role="tab" aria-selected="false" title="Shortcut: Ctrl+3">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="18" cy="5" r="3"></circle>
          <circle cx="6" cy="12" r="3"></circle>
          <circle cx="18" cy="19" r="3"></circle>
          <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
          <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
        </svg>
        <span>3: Reasoning Graph</span>
        <span class="tab-hotkey-hint">Ctrl+3</span>
      </button>

      <button class="viewport-tab-btn" id="tab-vp-4" data-viewport="4" role="tab" aria-selected="false" title="Shortcut: Ctrl+4">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="4 17 10 11 4 5"></polyline>
          <line x1="12" y1="19" x2="20" y2="19"></line>
        </svg>
        <span>4: Shell Sandbox</span>
        <span class="tab-hotkey-hint">Ctrl+4</span>
      </button>
    </div>

    <!-- Controls Cluster (Right Side of Stage Header) -->
    <div class="stage-header-actions">
      <!-- Feature #26: Split-Screen Toggle Button -->
      <button class="stage-action-btn" id="btn-split-screen" title="Toggle 50/50 Split-Screen Canvas (Shortcut: Alt+S)">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <line x1="12" y1="3" x2="12" y2="21"></line>
        </svg>
        <span>Split 50/50</span>
      </button>

      <!-- Stage Telemetry Readout -->
      <div class="stage-telemetry" id="stage-telemetry-readout">
        DISPLAY 01 • 1440 × 900
      </div>
    </div>
  </div>

  <!-- B. Polymorphic Viewports Stage Body -->
  <div class="stage-viewports-container" id="stage-viewports-container">
    <!-- Viewport 1: Vision & Set-of-Marks Stream -->
    <div class="viewport-panel active" id="viewport-1" data-viewport-id="1">
      <!-- (Integrated Vision SOM Canvas, Leader Lines & Perception Toolbar) -->
    </div>

    <!-- Viewport 2: Artifact & Document Studio -->
    <div class="viewport-panel" id="viewport-2" data-viewport-id="2">
      <!-- (Auto-MIME 2-Column Markdown, Monospace Code & CSV Grid) -->
    </div>

    <!-- Viewport 3: Task & Reasoning Graph (Blackboard) -->
    <div class="viewport-panel" id="viewport-3" data-viewport-id="3">
      <!-- (DAG Visualizer + Live Variables & Memory State Inspector) -->
    </div>

    <!-- Viewport 4: Shell & Execution Sandbox -->
    <div class="viewport-panel" id="viewport-4" data-viewport-id="4">
      <!-- (Multi-Tab PowerShell / Bash / Sandbox Monospace Terminal) -->
    </div>
  </div>
</main>
```

### 2.2 Hotkey & Event Wiring
```javascript
// Global Viewport Switcher Handler
function switchViewport(viewportId) {
  const vpNum = String(viewportId);
  AppState.activeViewport = vpNum;

  // Update tabs
  document.querySelectorAll('.viewport-tab-btn').forEach(btn => {
    const isActive = btn.getAttribute('data-viewport') === vpNum;
    btn.classList.toggle('active', isActive);
    btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
  });

  if (!AppState.isSplitScreen) {
    // Single Viewport Mode
    document.querySelectorAll('.viewport-panel').forEach(panel => {
      panel.classList.toggle('active', panel.getAttribute('data-viewport-id') === vpNum);
    });
  } else {
    // Split Screen Mode: update right pane or active focused pane
    updateSplitScreenPanes(vpNum);
  }

  // Refresh dynamic layout (e.g. SOM leader lines if Viewport 1 activated)
  if (vpNum === '1') {
    setTimeout(updateSomLeaderLines, 60);
  } else if (vpNum === '3') {
    renderDagVisualizer();
    renderLiveVariables();
  }
}

// Hotkey Listener (Ctrl+1, Ctrl+2, Ctrl+3, Ctrl+4)
document.addEventListener('keydown', (e) => {
  if (e.ctrlKey && !e.shiftKey && !e.altKey) {
    if (['1', '2', '3', '4'].includes(e.key)) {
      e.preventDefault();
      switchViewport(e.key);
    }
  }
});
```

---

## 3. Technical Blueprint: Feature #22 (Task & Reasoning Graph / Blackboard DAG)

### 3.1 DAG Visualizer Architecture
Viewport 3 provides a visual DAG pipeline that synthesizes the agent's goals, reactive tasks, safety gates, and produced artifacts into an interactive execution tree.

```
┌─────────────────┐       ┌────────────────────────┐       ┌────────────────────────┐       ┌────────────────────┐
│   🎯 GOAL NODE  │ ──►   │ ⚡ SUB-TASKS (T1..Tn)   │ ──►   │  🛡️ SAFETY GATE NODE   │ ──►   │ 📦 ARTIFACT NODES  │
│ Active Mission  │       │ Priority / Status Tags │       │ Risk Badge & Hold State│       │ Produced Workspace │
│ from Workspace  │       │ (Done, In-Prog, Block) │       │ (Approved / Blocked)   │       │ Files & Reports    │
└─────────────────┘       └────────────────────────┘       └────────────────────────┘       └────────────────────┘
```

### 3.2 DOM Structure for Viewport 3
```html
<div class="viewport-panel" id="viewport-3" data-viewport-id="3">
  <div class="reasoning-graph-layout">
    <!-- Left/Center: Interactive DAG Blackboard (70% width) -->
    <div class="dag-canvas-container" id="dag-canvas-container">
      <div class="dag-toolbar">
        <div class="dag-title-group">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="18" cy="5" r="3"></circle>
            <circle cx="6" cy="12" r="3"></circle>
            <circle cx="18" cy="19" r="3"></circle>
            <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
            <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
          </svg>
          <span class="dag-title-text">Execution DAG Blackboard</span>
          <span class="badge badge-complete" id="dag-progress-badge">3/4 NODES RESOLVED</span>
        </div>
        <div class="dag-controls">
          <button class="dag-btn" id="btn-dag-fit" title="Fit Graph to Frame">⛶ Fit</button>
          <button class="dag-btn" id="btn-dag-refresh" title="Re-sync with Backend State">⟳ Sync</button>
        </div>
      </div>

      <!-- SVG Graph Flow Rendering Surface -->
      <div class="dag-stage" id="dag-stage">
        <svg class="dag-connector-svg" id="dag-connector-svg" width="100%" height="100%">
          <defs>
            <marker id="dag-arrow-cyan" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
              <path d="M 0 1 L 8 5 L 0 9 z" fill="#00e5ff" />
            </marker>
            <marker id="dag-arrow-emerald" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
              <path d="M 0 1 L 8 5 L 0 9 z" fill="#10b981" />
            </marker>
            <marker id="dag-arrow-slate" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
              <path d="M 0 1 L 8 5 L 0 9 z" fill="#64748b" />
            </marker>
          </defs>
          <g id="dag-links-group"></g>
        </svg>

        <!-- HTML Node Flow Grid (Aligned with SVG Links) -->
        <div class="dag-columns-wrapper" id="dag-columns-wrapper">
          <!-- Column 1: Goal -->
          <div class="dag-column" id="dag-col-goal">
            <span class="dag-col-header">1. MISSION GOAL</span>
            <div class="dag-node node-goal active" id="dag-node-goal" data-node-type="goal">
              <div class="node-badge">GOAL</div>
              <div class="node-title" id="dag-goal-title">Universal Agent Task Execution</div>
              <div class="node-status-tag status-done">✓ INITIALIZED</div>
            </div>
          </div>

          <!-- Column 2: Sub-Tasks -->
          <div class="dag-column" id="dag-col-tasks">
            <span class="dag-col-header">2. SUB-TASKS PIPELINE</span>
            <div class="dag-nodes-list" id="dag-tasks-nodes-list">
              <!-- Dynamically mapped from AppState.tasks -->
            </div>
          </div>

          <!-- Column 3: Safety Gates -->
          <div class="dag-column" id="dag-col-gates">
            <span class="dag-col-header">3. SAFETY GATES</span>
            <div class="dag-nodes-list" id="dag-gates-nodes-list">
              <div class="dag-node node-gate blocked" id="dag-node-gate" data-node-type="gate">
                <div class="node-badge badge-gate">GATE</div>
                <div class="node-title" id="dag-gate-title">System File Write Gate</div>
                <div class="node-status-tag status-blocked" id="dag-gate-status">⚠ HELD: MODERATE</div>
              </div>
            </div>
          </div>

          <!-- Column 4: Artifacts -->
          <div class="dag-column" id="dag-col-artifacts">
            <span class="dag-col-header">4. ARTIFACTS &amp; OUTPUTS</span>
            <div class="dag-nodes-list" id="dag-artifacts-nodes-list">
              <!-- Dynamically mapped from workspace files -->
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Right: Live Variables & Memory State Inspector (30% width) -->
    <div class="variables-inspector-panel" id="variables-inspector-panel">
      <!-- (Feature #23 implementation detailed below) -->
    </div>
  </div>
</div>
```

---

## 4. Technical Blueprint: Feature #23 (Live Variables & Memory State Inspector)

### 4.1 Inspector Architecture
Embedded in Viewport 3 (and accessible in the Quick Drawers), this panel provides real-time state inspection and interactive click-to-REPL insertion for agent context variables and persistent memory facts.

```html
<div class="variables-inspector-container">
  <!-- Section 1: Agent Context Variables -->
  <div class="inspector-section">
    <div class="inspector-section-header">
      <span class="section-title">AGENT CONTEXT VARIABLES</span>
      <span class="badge badge-agent">READ-ONLY</span>
    </div>
    <div class="variables-table" id="context-variables-table">
      <div class="var-row" data-var="$workspace" title="Click to insert $workspace into REPL">
        <span class="var-name">$workspace</span>
        <span class="var-val" id="var-val-workspace">workspace/default</span>
        <button class="var-copy-btn" title="Copy value">📋</button>
      </div>
      <div class="var-row" data-var="$exit_code" title="Click to insert $exit_code into REPL">
        <span class="var-name">$exit_code</span>
        <span class="var-val status-success" id="var-val-exit-code">0</span>
        <button class="var-copy-btn" title="Copy value">📋</button>
      </div>
      <div class="var-row" data-var="$current_task" title="Click to insert $current_task into REPL">
        <span class="var-name">$current_task</span>
        <span class="var-val" id="var-val-current-task">Synthesize backend telemetry and state</span>
        <button class="var-copy-btn" title="Copy value">📋</button>
      </div>
      <div class="var-row" data-var="$active_tier" title="Click to insert $active_tier into REPL">
        <span class="var-name">$active_tier</span>
        <span class="var-val" id="var-val-active-tier">Tier 1 (Local Ollama 7B)</span>
        <button class="var-copy-btn" title="Copy value">📋</button>
      </div>
      <div class="var-row" data-var="$fusion_confidence" title="Click to insert $fusion_confidence into REPL">
        <span class="var-name">$fusion_confidence</span>
        <span class="var-val status-cyan" id="var-val-confidence">99.2%</span>
        <button class="var-copy-btn" title="Copy value">📋</button>
      </div>
      <div class="var-row" data-var="$checkpoint" title="Click to insert $checkpoint into REPL">
        <span class="var-name">$checkpoint</span>
        <span class="var-val" id="var-val-checkpoint">checkpoint #018</span>
        <button class="var-copy-btn" title="Copy value">📋</button>
      </div>
    </div>
  </div>

  <!-- Section 2: Persistent Memory Facts (/api/memory) -->
  <div class="inspector-section" style="margin-top:12px;flex:1;display:flex;flex-direction:column;min-height:0;">
    <div class="inspector-section-header">
      <span class="section-title">PERSISTENT MEMORY FACTS</span>
      <button class="btn-sm-action" id="btn-add-memory-fact" title="Add New Memory Key-Value">+ Add Fact</button>
    </div>

    <!-- Inline Add Fact Form (Collapsible) -->
    <div class="memory-add-form hidden" id="memory-add-form">
      <input type="text" id="mem-key-input" placeholder="key (e.g. timeout_ms)" class="form-input-sm" />
      <input type="text" id="mem-val-input" placeholder="value" class="form-input-sm" />
      <select id="mem-cat-select" class="form-select-sm">
        <option value="notes">notes</option>
        <option value="facts">facts</option>
        <option value="system">system</option>
      </select>
      <div class="form-actions-sm">
        <button class="btn-xs btn-primary" id="btn-save-mem-fact">Save</button>
        <button class="btn-xs btn-secondary" id="btn-cancel-mem-fact">Cancel</button>
      </div>
    </div>

    <!-- Memory Key-Value List -->
    <div class="memory-facts-list" id="memory-facts-list">
      <!-- Populated from GET /api/state or /api/memory -->
    </div>
  </div>
</div>
```

### 4.2 Interactive Behavior & Click-to-REPL
```javascript
// Click on variable inserts token into active terminal input
document.addEventListener('click', (e) => {
  const row = e.target.closest('.var-row');
  if (row && !e.target.classList.contains('var-copy-btn')) {
    const varName = row.getAttribute('data-var');
    const replInput = document.getElementById('repl-input') || document.getElementById('terminal-active-input');
    if (replInput) {
      replInput.value = (replInput.value ? replInput.value + ' ' : '') + varName;
      replInput.focus();
      // Optional subtle highlight pulse on variable row
      row.classList.add('inserted-pulse');
      setTimeout(() => row.classList.remove('inserted-pulse'), 400);
    }
  }
});
```

---

## 5. Technical Blueprint: Features #24 & #25 (Multi-Tab Shell Sandbox & REPL)

### 5.1 Monospace Terminal DOM Structure (Viewport 4)
```html
<div class="viewport-panel" id="viewport-4" data-viewport-id="4">
  <div class="shell-sandbox-container">
    <!-- Terminal Header & Shell Profile Tabs -->
    <div class="terminal-header-bar">
      <div class="terminal-tabs-cluster" role="tablist">
        <button class="terminal-tab active" data-shell="pwsh" id="term-tab-pwsh" role="tab" aria-selected="true">
          <span class="shell-tab-icon">&gt;_</span>
          <span>PowerShell 7.4</span>
        </button>
        <button class="terminal-tab" data-shell="bash" id="term-tab-bash" role="tab" aria-selected="false">
          <span class="shell-tab-icon">$</span>
          <span>Bash Shell</span>
        </button>
        <button class="terminal-tab" data-shell="sandbox" id="term-tab-sandbox" role="tab" aria-selected="false">
          <span class="shell-tab-icon">⚡</span>
          <span>Agent Sandbox</span>
        </button>
      </div>

      <div class="terminal-header-telemetry">
        <button class="term-btn-icon" id="btn-term-clear" title="Clear Buffer (cls)">⊘ Clear</button>
        <button class="term-btn-icon" id="btn-term-copy" title="Copy Log Buffer">📋 Copy</button>
        <span class="badge badge-complete" id="terminal-exit-badge">EXIT 0</span>
      </div>
    </div>

    <!-- Scrollable Monospace Logs Area -->
    <div class="terminal-logs-surface" id="terminal-logs-surface" role="log" aria-live="polite">
      <div class="terminal-log-row log-info">
        <span class="log-ts">[15:42:01]</span>
        <span class="log-msg">AETHER Universal Shell Sandbox initialized • Session #4102</span>
      </div>
      <div class="terminal-log-row log-info">
        <span class="log-ts">[15:42:02]</span>
        <span class="log-msg">Working directory: c:\Users\andym\gschwelli-ai\workspace\default</span>
      </div>
    </div>

    <!-- Interactive Terminal Command Input Row -->
    <div class="terminal-input-bar">
      <label class="terminal-prompt-label" id="terminal-prompt-label" for="terminal-active-input">PS C:\workspace&gt;</label>
      <input
        type="text"
        class="terminal-active-input"
        id="terminal-active-input"
        placeholder="Enter shell or agent command..."
        autocomplete="off"
        autocorrect="off"
        autocapitalize="off"
        spellcheck="false"
      />
      <button class="terminal-submit-btn" id="btn-term-run">↵ Run</button>
    </div>

    <!-- Terminal Footer Status Bar -->
    <div class="terminal-footer-bar">
      <div class="term-footer-left">
        <span class="term-status-dot active">●</span>
        <span id="term-active-profile-desc">pwsh 7.4.2 • I/O Guarded Sandbox</span>
      </div>
      <div class="term-footer-right">
        <span>SECURITY TIER 1 • AUDIT LOGGED</span>
      </div>
    </div>
  </div>
</div>
```

### 5.2 Execution Flow & Stream Color Formatting
```javascript
let commandHistory = [];
let historyIndex = -1;

async function executeTerminalCommand(cmdText) {
  const cmd = (cmdText || '').trim();
  if (!cmd) return;

  commandHistory.unshift(cmd);
  historyIndex = -1;

  const now = new Date();
  const ts = now.toTimeString().split(' ')[0];

  // 1. Echo command in cyan
  appendTerminalLine(ts, `> ${cmd}`, 'cmd');

  try {
    // 2. Call backend /api/repl
    const resp = await fetch('/api/repl', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: cmd })
    });
    const data = await resp.json();

    // 3. Update Exit Code Badge
    const exitBadge = document.getElementById('terminal-exit-badge');
    const exitCode = data.exit_code !== undefined ? data.exit_code : 0;
    if (exitBadge) {
      exitBadge.textContent = `EXIT ${exitCode}`;
      exitBadge.className = exitCode === 0 ? 'badge badge-complete' : 'badge badge-panic';
    }

    // 4. Update Live Variables
    const exitVar = document.getElementById('var-val-exit-code');
    if (exitVar) {
      exitVar.textContent = String(exitCode);
      exitVar.className = exitCode === 0 ? 'var-val status-success' : 'var-val status-panic';
    }

    // 5. Append stdout/stderr stream lines
    if (data.output) {
      const lines = data.output.split('\n');
      lines.forEach(line => {
        if (!line.trim()) return;
        let lineType = 'stdout';
        if (line.includes('[PS_ERROR]') || line.includes('Error:') || exitCode !== 0) {
          lineType = 'stderr';
        } else if (line.includes('WARN') || line.includes('warning')) {
          lineType = 'warn';
        } else if (line.includes('SUCCESS') || line.includes('True')) {
          lineType = 'success';
        }
        appendTerminalLine(ts, line, lineType);
      });
    }
  } catch (err) {
    appendTerminalLine(ts, `[NETWORK ERROR] Failed to reach /api/repl: ${err.message}`, 'stderr');
  }
}

function appendTerminalLine(ts, text, type) {
  const container = document.getElementById('terminal-logs-surface') || document.getElementById('repl-logs');
  if (!container) return;

  const row = document.createElement('div');
  row.className = `terminal-log-row log-${type}`;

  const tsSpan = document.createElement('span');
  tsSpan.className = 'log-ts';
  tsSpan.textContent = `[${ts}]`;

  const msgSpan = document.createElement('span');
  msgSpan.className = 'log-msg';
  msgSpan.textContent = text; // Safe textContent (prevents XSS)

  row.appendChild(tsSpan);
  row.appendChild(msgSpan);
  container.appendChild(row);

  // Auto-scroll
  container.scrollTop = container.scrollHeight;
}
```

---

## 6. Technical Blueprint: Feature #26 (Split-Screen Canvas Mode)

### 6.1 Layout CSS & Dual-Pane Grid
```css
/* Master Stage Body */
.stage-viewports-container {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  position: relative;
  background: var(--bg-void);
}

/* Default Single Viewport Mode */
.stage-viewports-container .viewport-panel {
  display: none;
  flex: 1;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

.stage-viewports-container .viewport-panel.active {
  display: flex;
  flex-direction: column;
}

/* Split-Screen Active State (50/50 Dual Layout) */
.stage-viewports-container.split-screen-active {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  padding: 6px;
  background: var(--bg-void);
}

.stage-viewports-container.split-screen-active .viewport-panel.split-left,
.stage-viewports-container.split-screen-active .viewport-panel.split-right {
  display: flex;
  flex-direction: column;
  height: 100%;
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  background: var(--bg-card);
  overflow: hidden;
}
```

### 6.2 Toggle Logic & Responsive Boundaries
```javascript
function toggleSplitScreen() {
  const container = document.getElementById('stage-viewports-container');
  const splitBtn = document.getElementById('btn-split-screen');
  if (!container || !splitBtn) return;

  AppState.isSplitScreen = !AppState.isSplitScreen;
  splitBtn.classList.toggle('active', AppState.isSplitScreen);
  container.classList.toggle('split-screen-active', AppState.isSplitScreen);

  if (AppState.isSplitScreen) {
    // Default dual viewports: Left = Viewport 1 (Vision), Right = Viewport 4 (Shell) or 2 (Studio)
    const leftVp = document.getElementById('viewport-1');
    const rightVp = document.getElementById('viewport-4') || document.getElementById('viewport-2');

    document.querySelectorAll('.viewport-panel').forEach(p => p.classList.remove('active', 'split-left', 'split-right'));
    if (leftVp) leftVp.classList.add('split-left');
    if (rightVp) rightVp.classList.add('split-right');

    setTimeout(updateSomLeaderLines, 80);
  } else {
    // Return to single viewport
    document.querySelectorAll('.viewport-panel').forEach(p => p.classList.remove('split-left', 'split-right'));
    switchViewport(AppState.activeViewport || '1');
  }
}
```

---

## 7. Technical Blueprint: Feature #27 (Quick Telemetry Drawers)

### 7.1 Slide-Out Drawer Structure
Positioned as a fixed/absolute drawer overlay on the right margin with a semi-transparent backdrop:

```html
<!-- Quick Telemetry Drawer Slide-Out Panel -->
<div class="telemetry-drawer-overlay hidden" id="telemetry-drawer-overlay"></div>

<aside class="telemetry-drawer-panel" id="telemetry-drawer-panel" aria-label="System Quick Drawer">
  <!-- Drawer Top Bar -->
  <div class="drawer-header">
    <div class="drawer-tabs-cluster" role="tablist">
      <button class="drawer-tab active" data-drawer-tab="tools" role="tab">
        <span>🔧 Tools</span>
      </button>
      <button class="drawer-tab" data-drawer-tab="memory" role="tab">
        <span>🧠 Memory</span>
      </button>
      <button class="drawer-tab" data-drawer-tab="cache" role="tab">
        <span>⚡ Cache</span>
      </button>
      <button class="drawer-tab" data-drawer-tab="undo" role="tab">
        <span>↶ Undo</span>
      </button>
    </div>
    <button class="drawer-close-btn" id="btn-close-drawer" title="Close Drawer (Esc)">✕</button>
  </div>

  <!-- Drawer Body: 4 Panes -->
  <div class="drawer-body">
    <!-- 1. Tools Pane (/api/tool) -->
    <div class="drawer-pane active" id="drawer-pane-tools">
      <div class="drawer-pane-header">
        <span class="pane-title">REGISTERED SYSTEM TOOLS</span>
        <span class="badge badge-agent" id="drawer-tools-count">14 TOOLS</span>
      </div>
      <div class="tools-catalogue-list" id="drawer-tools-list">
        <!-- Rendered tool items with name, description, execute button -->
      </div>
    </div>

    <!-- 2. Memory Pane (/api/memory) -->
    <div class="drawer-pane" id="drawer-pane-memory">
      <div class="drawer-pane-header">
        <span class="pane-title">PERSISTENT KNOWLEDGE FACTS</span>
        <button class="btn-xs btn-primary" id="btn-drawer-add-mem">+ Add</button>
      </div>
      <div class="drawer-memory-list" id="drawer-memory-list">
        <!-- Live memory facts fetched from /api/memory -->
      </div>
    </div>

    <!-- 3. Cache Pane (/api/cache) -->
    <div class="drawer-pane" id="drawer-pane-cache">
      <div class="drawer-pane-header">
        <span class="pane-title">TIER-0 PLAN CACHE</span>
        <button class="btn-xs btn-secondary" id="btn-drawer-clear-cache">Clear Cache</button>
      </div>
      <div class="cache-entries-list" id="drawer-cache-list">
        <!-- Cached exact & template query plans -->
      </div>
    </div>

    <!-- 4. Undo Stack Pane (/api/undo) -->
    <div class="drawer-pane" id="drawer-pane-undo">
      <div class="drawer-pane-header">
        <span class="pane-title">REVERSIBLE OPERATION STACK</span>
        <button class="btn-xs btn-panic" id="btn-drawer-undo-last">Rollback Last</button>
      </div>
      <div class="undo-history-list" id="drawer-undo-list">
        <!-- Reversible checkpoints from core/undo.py -->
      </div>
    </div>
  </div>
</aside>
```

### 7.2 Drawer CSS Animation & Escape Key Protocol
```css
.telemetry-drawer-panel {
  position: fixed;
  top: var(--top-nav-height);
  right: 0;
  width: 360px;
  height: calc(100vh - var(--top-nav-height) - var(--omnibox-height));
  background: var(--bg-card);
  border-left: 1px solid var(--border-bright);
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.6);
  transform: translateX(100%);
  transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  z-index: 100;
  display: flex;
  flex-direction: column;
}

.telemetry-drawer-panel.open {
  transform: translateX(0);
}
```

```javascript
function openDrawer(tabName) {
  const panel = document.getElementById('telemetry-drawer-panel');
  if (!panel) return;
  panel.classList.add('open');
  switchDrawerTab(tabName || 'tools');
}

function closeDrawer() {
  const panel = document.getElementById('telemetry-drawer-panel');
  if (panel) panel.classList.remove('open');
}

// In global keydown listener:
if (e.key === 'Escape') {
  const panel = document.getElementById('telemetry-drawer-panel');
  if (panel && panel.classList.contains('open')) {
    e.preventDefault();
    e.stopPropagation();
    closeDrawer();
    return; // Crucial: stops propagation so Safety Interceptor abort is NOT triggered!
  }
}
```

---

## 8. Technical Blueprint: Feature #28 (Center Stage CAD Eradication)

### 8.1 Exhaustive Inventory of CAD Elements to Remove

| # | Current Location in `ui/dashboard/index.html` | Offending CAD / 3D Element | Eradication & Domain-Agnostic Replacement Action |
|---|------------------------------------------------|----------------------------|--------------------------------------------------|
| 1 | Line 2822 (`#active-mission-label`) | `M-024 / Export toolhead_mount.stl` | Replace with dynamic active workspace mission: `M-001 / Universal Autonomous Agent Execution` or `activeWorkspace.prompt`. |
| 2 | Lines 2827–2828 | `<div class="cad-viewport-frame" id="cad-viewport-frame">` | Eradicate `cad-viewport-frame` ID and class; replace with `#stage-viewports-container`. |
| 3 | Lines 2844–2862 (`#target-window-header`) | `OpenSCAD — toolhead_mount.scad` + `.app-title-cube` | Replace with generic application header: `Desktop Workspace Stream — System Canvas` without 3D cube glyph. |
| 4 | Lines 2872–2873 (`#target-menubar`) | `▷ Preview F5` & `⚙ Render F6` | Eradicate CAD preview/render triggers; replace with universal application menu actions (`Run`, `Inspect`, `Clear`). |
| 5 | Lines 2883–2896 | `<div class="csg-overlay">` (`mount_v3 / difference() / base_plate / bolt_holes × 5`) | 100% eradicate CSG overlay and all mentions of boolean difference operations. |
| 6 | Lines 2914–3029 | `#cad-mesh-svg` & `#cad-mesh-group` (shaded polygons `#facet-base-top`, bolt holes, slotted holes, `80.00 mm`, `24.00 mm`) | 100% eradicate 3D vector bracket mesh; replace with 2D Set-of-Marks Perception Canvas mapping arbitrary desktop/window marks. |
| 7 | Lines 3031–3051 (`.axis-gizmo`) | 3D Coordinate Axes Gizmo (X red, Y green, Z cyan) | Eradicate 3D axis gizmo. |
| 8 | Lines 3053–3058 (`.mesh-telemetry`) | `MANIFOLD • 1,248 FACETS` | Eradicate mesh manifold telemetry; replace with universal stream telemetry (`DISPLAY 01 • 1440 × 900`). |
| 9 | Lines 3060–3082 (`#target-export-dock`) | `EXPORT MODEL`, `STL (binary) • 62.4 KB`, `#export-path-input`, `#btn-export-mesh` | 100% eradicate STL export dock; replace with universal Artifact Export or quick file inspector. |
| 10 | Lines 3159, 3208 (`#blackboard-pane`) | `Load toolhead_mount.scad → binary STL`, `$target_dir: C:\Fabrication` | Replace with domain-agnostic step `Initialize workspace pipeline`, `$workspace: workspace/default`. |
| 11 | Lines 3234, 3238, 3241 (`#repl-logs`) | `Get-Process openscad`, `openscad --check-parameters`, `Export-Mesh -Format STL` | Replace with generic system initialization commands (`Get-Process python`, `python -m core.orchestrator --verify`, `Invoke-Pipeline`). |
| 12 | Lines 3421, 3437, 3463–3469 | `OpenSCAD — toolhead_mount.scad`, `C:\Fabrication\toolhead_mount.stl`, `btn_export_stl` | Replace with generic window marks: `[01: MenuBar]`, `[02: Window Controls]`, `[03: Explorer]`, `[04: Action 'Execute']`. |
| 13 | Lines 3502, 3511, 3561, 3586 | `Export toolhead mount bracket`, `toolhead_mount.stl.bak`, `Overwrite toolhead_mount.stl` | Replace with universal safety gate: `Update workspace configuration • Risk: Moderate`. |
| 14 | Lines 3840, 5199, 5209, 5292, 5313, 5344, 5758, 5767, 5786, 5794, 5811, 6166, 6261, 6339 (JS) | All hardcoded JavaScript string literals referencing OpenSCAD, STL, `cad-mesh-group`, and CGAL | Replace all handlers with generic DOM state updates and clean event bindings. |

---

## 9. Verification & Automated Test Strategy

To verify Milestone 3 compliance and ensure zero regressions:

1. **Backend Integration Suite**:
   ```powershell
   uv run --with pytest pytest tests/test_api.py -v
   ```
   *Expected:* 22/22 tests PASSED (all HTTP and WebSocket endpoints).

2. **Headless Browser DOM & Interactivity Suite**:
   ```powershell
   uv run --with pytest,playwright pytest tests/test_browser_dom.py -v
   ```
   *Expected:* 30/30 tests PASSED across Viewport switching, Split-screen toggle, Quick drawers, and 0.0px² occlusion.

3. **Strict Zero CAD Token Audit**:
   ```powershell
   uv run --with pytest pytest tests/test_adversarial_m1_endpoints.py -k "TestZeroCadTokenEradication" -v
   ```
   *Expected:* PASSED with 0 matches against all 12 `CAD_FORBIDDEN_PATTERNS`.

4. **Multi-Resolution Responsiveness**:
   - `1024x768` (Compact): `scrollWidth <= innerWidth`, 0 horizontal overflow.
   - `1440x900` (Baseline): 4 viewports + split mode render smoothly.
   - `1920x1080` (Full HD): Crisp layout with zero visual artifacts.

---
*Report compiled and verified by `spec_miner_m3_v2` for Milestone 3.*
