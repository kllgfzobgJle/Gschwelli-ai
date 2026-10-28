# gschwelli-ai UI Prototype — Exhaustive Functional & Visual Specification Report

**Survey ID**: Survey 1 (Specification Mining)  
**Author**: teamwork_preview_spec_miner  
**Authoritative Sources**:
1. `ORIGINAL_REQUEST.md` (`c:\Users\andym\gschwelli-ai\.agents\teamwork\ORIGINAL_REQUEST.md`)
2. Visual Reference Mockup (`c:\Users\andym\gschwelli-ai\Inspirations\ui_reference_mockup.png`)
3. Existing Server & Backend APIs (`c:\Users\andym\gschwelli-ai\server\api.py`, `core/confirm.py`, `core/undo.py`, `core/blackboard.py`, `config/settings.yaml`)

---

## 1. Executive Summary

This report establishes the complete, authoritative functional and visual specification for the **gschwelli-ai** Web UI Prototype (`ui/dashboard/index.html` and `server/api.py`). The interface represents an advanced AI Agent Cockpit designed for multi-tier hybrid automation (local Ollama LLM, UIA accessibility automation, Gemini 3.8 Flash vision perception, and Human-in-the-Loop safety gating).

The prototype must provide an authentic dark-cyan/amber cybernetic control center aesthetic that mirrors `Inspirations/ui_reference_mockup.png` down to the exact telemetry, Set-of-Marks (SOM) visual tags, 3D CAD mesh viewport, interactive Blackboard agent state, PowerShell REPL, and approval gates across four complete views:
- **Mission Control** (Primary 3-column cockpit)
- **Knowledge Studio** (RAG file indexing, chunk inspector, file editor)
- **Vision SOM** (Expanded SOM & UIA perception tree inspector)
- **Focus Chat** (Execution timeline, thought traces, tool/memory/cache inspectors)

---

## 2. Visual Design System & Exact Color Tokens

### 2.1 Color Palette & Tokens
| Token Name | Hex / CSS Value | Description / Usage in UI |
|------------|-----------------|---------------------------|
| `--bg-void` | `#060a10` | Deepest root canvas and background base |
| `--bg-panel` | `#0b121c` / `#0c131f` | Sidebars, main container panels, card backgrounds |
| `--bg-panel-elevated` | `#101a28` / `#131f30` | Hover states, inner cards, dropdown menus, table headers |
| `--bg-dock` | `#080e18` | Top navigation bar and bottom omnibox command dock |
| `--border-subtle` | `#1b2a3e` | Primary structural borders, dividers, subtle outlines |
| `--border-bright` | `rgba(0, 229, 255, 0.35)` | Highlighted panel borders, active SOM tags, active focus rings |
| `--cyan-accent` | `#00e5ff` | Primary branding, active buttons, SOM bounding boxes, live indicators |
| `--teal-accent` | `#14b8a6` | Secondary telemetry, UIA fusion tags, execution indicators |
| `--amber-warning` | `#f59e0b` | Approval gates, warning banners, blocked tasks, safety policies |
| `--amber-bg` | `rgba(245, 158, 11, 0.08)` | Background for approval gates, warning callout cards |
| `--amber-border` | `rgba(245, 158, 11, 0.6)` | Glowing border for approval banner and blocked steps |
| `--emerald-success` | `#10b981` | Completed tasks, exit code 0, live connected indicators, valid manifold |
| `--emerald-bg` | `rgba(16, 185, 129, 0.12)` | Complete badges, terminal exit badges |
| `--red-panic` | `#ef4444` | PANIC KILL & UNDO button, fatal errors, aborted missions |
| `--red-bg` | `rgba(239, 68, 68, 0.15)` | Emergency halt alerts, panic button hover |
| `--text-primary` | `#f1f5f9` / `#ffffff` | Primary headings, active item text, CAD labels |
| `--text-secondary` | `#94a3b8` | Subheaders, step descriptions, variable keys |
| `--text-muted` | `#64748b` | Timestamps, inactive tabs, unselected file items |
| `--text-mono-cyan` | `#38bdf8` / `#00e5ff` | Code snippets, variables `$target_dir`, SOM tag numbers |

### 2.2 Typography
- **Primary Interface Font**: `Inter`, `-apple-system`, `BlinkMacSystemFont`, `"Segoe UI"`, `sans-serif`
  - Body: 13px / line-height 1.45, font-weight 400
  - Section Headers: 11px uppercase, letter-spacing 1.5px, font-weight 700
  - Modal / Main Titles: 15px - 17px, font-weight 700
- **Monospace Telemetry Font**: `"JetBrains Mono"`, `"Cascadia Code"`, `Consolas`, `monospace`
  - Font sizes: 11px - 12px for terminal, logs, breadcrumbs, tags, and CSG trees
  - Letter spacing: 0.5px for crisp terminal aesthetics

### 2.3 Layout Dimensions & Structural Blueprint
```
+----------------------------------------------------------------------------------------------------+
| TOP NAV (48px): [o o o]  gschwelli-ai [•]  |  [Mission Control] [Knowledge] [Vision] [Chat]  | Telemetry [⚙] |
+----------------------------------------------------------------------------------------------------+
|  LEFT SIDEBAR (270px)  |        CENTER VIEWPORT (Flexible ~55%)        |   RIGHT SIDEBAR (340px)   |
|  --------------------  |  -------------------------------------------  |  -----------------------  |
|  - Workspace Selector  |  - Canvas Header (LIVE, Display 01)           |  - Blackboard (AGENT-01)  |
|  - Tasks & To-Dos      |  - Mission Status (M-024 / PAUSED)            |    [Plan]->[UIA]->[Exec]  |
|  - Knowledge Base Tree |  - OpenSCAD Viewport (3D CAD, SOM Tags, CSG)  |    Step Cards & Shared    |
|  - Mic / Wake-Word     |  - Target Path & Safety Policy                |  - PowerShell REPL        |
|                        |  - SOM Toolbar & Fusion Telemetry             |    Logs & PS Prompt       |
+----------------------------------------------------------------------------------------------------+
| BOTTOM APPROVAL GATE (44px): [!] HUMAN-IN-THE-LOOP APPROVAL NEEDED | [Approve] [Edit] [Abort] [PANIC] |
+----------------------------------------------------------------------------------------------------+
| BOTTOM OMNIBOX DOCK (48px): [+] [/run...] [Describe next action...] | [VOICE] [Auto-Route] [↑]      |
+----------------------------------------------------------------------------------------------------+
```

---

## 3. Exhaustive Inventory of Elements Across All 4 Views

### 3.1 View 1: Mission Control (Primary Cockpit)

#### A. Top Navigation Bar (Header)
1. **Window Controls Dot Cluster**:
   - 3 colored circular dots representing macOS/desktop window controls:
     - Red (`#ff5f56`, 11px diameter)
     - Yellow (`#ffbd2e`, 11px diameter)
     - Green (`#27c93f`, 11px diameter)
2. **Brand & Identity**:
   - Dual-chevron or diamond logo icon.
   - Brand text: `gschwelli-ai` (15px bold sans-serif, letter-spacing 1px).
   - Live status indicator: Glowing green dot (`#10b981`, pulsing animation).
3. **Centered Mode Switcher (Segmented Control)**:
   - Rounded container with 4 clickable pills:
     - `Mission Control` (Active: highlighted cyan tint, subtle cyan border, text `#00e5ff`).
     - `Knowledge Studio`
     - `Vision SOM`
     - `Focus Chat`
4. **Runtime Telemetry & Global Actions**:
   - Monospace telemetry badge: `Ollama 7B • 42 tok/s • 4.2GB VRAM` (`#94a3b8`, 11px monospace).
   - Settings trigger: Gear / cog icon button opening modal or settings drawer.

#### B. Left Sidebar
1. **Project / Local Workspace Card**:
   - Small label: `PROJECT / LOCAL WORKSPACE` (uppercase muted).
   - Active project title: `Active: 3D Fabrication & Automation` (bold).
   - Status details: Git branch icon + `main / 6 files indexed`.
   - Interactive dropdown trigger (down-chevron) allowing project switching.
2. **Tasks & To-Dos Panel**:
   - Header with progress fraction: `TASKS & TO-DOS` | `2 / 4`.
   - Task Item 1: Checked checkbox (cyan fill, white checkmark), title `Validate mount geometry`, badges `Agent` (grey) `Complete` (emerald green).
   - Task Item 2: Checked checkbox, title `Resolve export destination`, badges `Agent` `Complete` (emerald green).
   - Task Item 3: Unchecked checkbox (amber glowing border), title `Export toolhead mount`, badges `Agent` `Approval needed` (amber warning).
   - Task Item 4: Unchecked checkbox (muted grey border), title `Run fabrication pipeline`, badges `Agent` `Queued` (muted grey).
   - Interactive: Checkboxes are clickable to toggle tasks; includes quick button `+ Add task`.
3. **Knowledge Base Tree Card**:
   - Header: `KNOWLEDGE BASE` with right-aligned `+` button to add documents.
   - Interactive File Tree:
     - `📁 fabrication/` (collapsible directory node)
       - `📄 workflow.md` (clickable file row)
       - `🐍 agent_kinematics.py` (clickable file row)
       - `⚙️ toolhead_mount.scad` (actively selected row with cyan background highlight and border)
       - `📦 mount_assembly.step` (clickable file row)
       - `📄 pipeline_config.yaml` (clickable file row)
   - Sync Telemetry Footer: Green dot + `Synced 12s ago • 48 chunks`.
4. **Audio / Wake-Word Footer**:
   - Audio input meter: Microphone icon + `RØDE NT-USB Mini -42 dB` with dynamic sound level bars.
   - Wake-word toggle pill: Pulsing green dot + `Listening for Wake-Word` (clickable to mute/unmute).

#### C. Center Panel: SOM Perception Canvas
1. **Canvas Top Header**:
   - Left: Eye / retina perception icon + `SOM Perception Canvas` + cyan pill `LIVE`.
   - Right: Telemetry string `DISPLAY 01 • 1440 × 900`.
2. **Mission Status Subheader**:
   - Yellow/amber dot + `M-024 / Export toolhead_mount.stl`.
   - Right badge: Amber glowing pill `PAUSED • APPROVAL`.
3. **Target Application Viewport (`OpenSCAD — toolhead_mount.scad`)**:
   - Application Window Frame:
     - Window Title Bar: Cube icon + `OpenSCAD — toolhead_mount.scad` + green status dot + window action buttons `— 🗖 ✕`.
     - App Menu Bar: `File  Edit  Design  View  Help` | `▷ Preview F5` | `⚙ Render F6`.
   - Interactive 3D CAD Mesh Viewport:
     - Isometric wireframe/shaded 3D model of the mounting bracket (`mount_v3`):
       - L-shaped bracket geometry with base plate and vertical flange.
       - Dimension callout labels: `80.00 mm` (length), `24.00 mm` (flange height).
       - Bolt holes: 2 vertical through-holes, 3 base countersunk holes.
     - Coordinate Axis Gizmo: Bottom-left 3D axes (Z blue, Y green, X red).
     - CSG Code Snippet Overlay (Top-Left):
       ```openscad
       mount_v3
         difference()
           base_plate
           mount_wall
           bolt_holes × 5
       ```
     - Viewport Camera Navigation Icons (Right Edge):
       - Orbit / Rotate icon
       - Pan icon
       - Zoom In / Out icon
       - Fit-to-screen / Reset camera icon
     - Mesh Quality Telemetry (Bottom Right of CAD area):
       - Green dot + `MANIFOLD • 1,248 FACETS`.
   - Set-of-Marks (SOM) Cyan Overlay Markers:
     - **Tag `[01: Menu]`**: Attached with leader line to the top `File Edit...` menu bar.
     - **Tag `[02: Window Controls]`**: Attached with leader line to `— 🗖 ✕`.
     - **Tag `[12: Path Input]`**: Attached with leader line to the export file path input field.
     - **Tag `[04: Button "Export"]`**: Attached with leader line to the `Export` action button.
   - Application Export Section (Bottom of inner window):
     - Section Label: `EXPORT MODEL` (left) | `STL (binary) • millimeters • 62.4 KB` (right).
     - Input Box: Folder icon + `C:\Fabrication\toolhead_mount.stl` + cyan highlighted `Export` button with download/export icon.
     - Safety Warning Banner: Amber text `Existing file detected. Write operation held by safety policy.`
     - Render Telemetry Bar:
       - Left: `Perspective • $fn=64 • CGAL ready`.
       - Right: `Last render 0.842s`.
4. **SOM Action Toolbar**:
   - Button `[⛶] Re-scan SOM` (active cyan border, clickable to re-scan).
   - Button `[↖] Inspect target` (triggers element inspection modal/popover).
   - Button `[📷] Capture` (captures high-res canvas frame).
   - Right: Telemetry label `FRAME #8184 • 84ms`.
5. **Fusion Status Bar**:
   - Left: Cyan dot + `12 targets mapped`.
   - Center: `UIA + VISION FUSION`.
   - Right: `99.2% confidence` (cyan).

#### D. Right Sidebar: Blackboard & PowerShell REPL
1. **Blackboard Card (`AGENT-01`)**:
   - Header: Network/node icon + `Blackboard` + cyan badge `AGENT-01`.
   - Pipeline Breadcrumb Tracker: `[Plan] → [UIA Detect] → [Verify] → [Execute]`
   - Step 1 Card:
     - Check icon (green) + `[Plan]` + right badge `COMPLETE` (emerald).
     - Title: `Prepare fabrication export`.
     - Detail: `Load toolhead_mount.scad → binary STL`.
   - Step 2 Card:
     - Check icon (green) + `[UIA Detect]` + right badge `COMPLETE` (emerald).
     - Title: `Resolve application targets`.
     - Detail: `12 nodes matched • Export → [04]`.
   - Step 3 Card:
     - Check icon (green) + `[Verify]` + right badge `COMPLETE` (emerald).
     - Title: `Validate path & geometry`.
     - Detail: `Manifold ✓ - overwrite requires approval`.
   - Step 4 Card:
     - Amber pause/alert icon + `[Execute]` + right badge `BLOCKED` (amber).
     - Title: `Commit export to disk`.
     - Detail: `Waiting at human approval gate`.
   - Shared State Inspector:
     - Section Header: `SHARED STATE / READ-ONLY`.
     - Variable rows (monospace):
       - `$target_dir   C:\Fabrication`
       - `$exit_code    0`
     - Checkpoint telemetry: `checkpoint #018`.
2. **PowerShell REPL (`EXIT 0`)**:
   - Header: Terminal prompt icon `>_ PowerShell REPL` + badge `EXIT 0` (emerald).
   - Output Console Area (monospace, dark terminal background, autoscrolling):
     - `15:42:06 > Get-Process openscad`
     - `15:42:06 PID 8044 • UIA attached`
     - `15:42:07 > Test-Path $target_dir`
     - `15:42:07 True` (cyan text)
     - `15:42:08 > openscad --check-parameters`
     - `15:42:09 CGAL: valid 2-manifold mesh` (green text)
     - `15:42:09 1,248 facets • 62.4 KB • exit 0`
     - `15:42:10 > Export-Mesh -Format STL`
     - `15:42:10 SEC-810: existing file at target` (amber text)
     - `15:42:10 WRITE HELD • awaiting approval` (amber text)
   - Interactive Command Input:
     - Prompt prefix: `PS C:\Fabrication> `
     - Input field with blinking cursor, supporting command execution (`Get-Process`, `ls`, `help`, `/clear`).
   - REPL Footer:
     - Left: Green dot + `pwsh 7.4.2`.
     - Right: `SANDBOX • I/O GUARDED`.

#### E. Bottom Approval Gate
- Full-width amber-themed human-in-the-loop safety banner:
  - Left Alert: Amber shield/alert icon + bold text `HUMAN-IN-THE-LOOP APPROVAL NEEDED` + detail `Overwrite toolhead_mount.stl • backup saved • SEC-810`.
  - Right Action Buttons:
    1. `✓ Approve (Space)`: Primary amber button, triggers approval workflow.
    2. `✏ Edit`: Secondary button, allows changing parameters or paths.
    3. `Abort (Esc)`: Cancellation button, halts the mission without disk changes.
    4. `🚫 PANIC KILL & UNDO`: Red alert button, halts agent, executes undo rollback.

#### F. Bottom Omnibox Command Bar
- Full-width dock bar at the bottom:
  - Left attachment button: `+` (open context menu / add file).
  - Slash command prefix chip: `/run...` (clickable to open slash command menu).
  - Main text input: Placeholder `Describe the next action, or type / for commands`.
  - Autocomplete Slash Menu (popup when typing `/`):
    - `/run <instruction>`: Route instruction through AI pipeline.
    - `/scan`: Re-scan SOM marks.
    - `/approve`: Approve pending human-in-the-loop gate.
    - `/abort`: Cancel pending action.
    - `/undo`: Revert last reversible action via `/api/undo`.
    - `/mode <name>`: Switch active view.
    - `/clear`: Clear logs.
  - Right Actions:
    - Voice Toggle: Audio wave icon + `VOICE` (cyan interactive pill).
    - Model Router Selector: Network/brain icon + `Auto-Route: Ollama/Gemini` (dropdown switcher: Auto, Ollama 7B, UIA, Gemini 3.8 Flash).
    - Send button: Teal/cyan circular button with upward arrow `↑`.

---

### 3.2 View 2: Knowledge Studio (RAG & Indexed Files)

1. **Workspace File Explorer & Metadata**:
   - Sidebar/List showing all 6 indexed files from `3D Fabrication & Automation`:
     - `toolhead_mount.scad` (48 chunks, 3.2 KB, OpenSCAD CSG)
     - `workflow.md` (12 chunks, 1.8 KB, Markdown)
     - `agent_kinematics.py` (34 chunks, 5.4 KB, Python)
     - `mount_assembly.step` (82 chunks, 18.2 KB, STEP CAD)
     - `pipeline_config.yaml` (8 chunks, 0.9 KB, YAML)
     - `safety_policy.json` (6 chunks, 1.1 KB, JSON)
2. **File Viewer & In-Browser Code Editor**:
   - Rich code editor with line numbers and syntax highlighting (e.g. OpenSCAD code for `toolhead_mount.scad`):
     ```openscad
     // Toolhead Mount v3 - High Precision Bracket
     $fn = 64;
     module base_plate() {
       cube([80, 50, 6], center=true);
     }
     ...
     ```
   - Actions: `Save Changes`, `Diff vs Head`, `Format Code`.
3. **Chunk Embeddings & Vector Metadata Table**:
   - Table displaying RAG chunks for the selected file:
     - Columns: `Chunk #`, `Token Count`, `Embedding Model` (`text-embedding-3-small` / Ollama), `Vector Preview` (`[0.024, -0.118, ...]`), `Similarity Score`.
   - Filtering and search box to test semantic retrieval queries against indexed chunks.
4. **Re-Indexing & Synchronisation Toolbar**:
   - Button `Re-index Chunks`: Triggers simulated chunk re-embedding with progress bar.
   - Sync telemetry: `Synced 12s ago • 48 chunks • 156KB in cache/aether.db`.

---

### 3.3 View 3: Vision SOM (Deep Perception Inspector)

1. **Dual Inspector View (UIA Accessibility Tree vs. Vision SOM Bounding Boxes)**:
   - Toggle switch: `[ UIA Accessibility Tree ] | [ Vision SOM Marks ] | [ Fused View ]`.
2. **Interactive SOM Perception Canvas**:
   - Full-width canvas showing the captured frame with all 12 detected Set-of-Marks tags:
     - `[01: Menu]` (MenuBar)
     - `[02: Window Controls]` (TitleBarButtons)
     - `[03: File Tree Explorer]` (TreeView)
     - `[04: Button "Export"]` (Button)
     - `[05: Viewport 3D Canvas]` (Graphic3D)
     - `[06: F5 Preview Button]` (ToolButton)
     - `[07: F6 Render Button]` (ToolButton)
     - `[08: CSG Tree View]` (List)
     - `[09: Coordinate Axes]` (Widget)
     - `[10: Status Bar]` (StatusBar)
     - `[11: Dimension Callout]` (Label)
     - `[12: Path Input]` (EditBox)
3. **Element Details & Telemetry Table**:
   - Selecting any mark updates the sidebar inspector with:
     - `Tag ID`: e.g. `[04]`
     - `Element Name`: `Export`
     - `Control Type`: `Button`
     - `Bounding Box`: `x: 666, y: 678, width: 54, height: 32`
     - `Detection Source`: `UIA + Vision Fusion`
     - `Confidence`: `99.7%`
     - `Actions Available`: `Click`, `Set Focus`, `Inspect Parent`, `Extract OCR`
4. **Interactive Action Simulation**:
   - Button `Simulate Click Target`: Shows a pulsing click ring on the selected mark and appends the simulated event to logs.
   - Button `Highlight Target`: Pulses bounding box on canvas.

---

### 3.4 View 4: Focus Chat (Agent Timeline & Execution Trace)

1. **Conversational Agent Thread**:
   - Chat timeline showing user instructions and agent responses.
   - Live integration with `POST /api/route`: Submitting instructions adds user bubble and streams agent response.
2. **Step-by-Step Reasoning & Blackboard Trace Cards**:
   - Thought Cards: Collapsible reasoning blocks (`"Agent Plan: Analyzing user request to export CAD mount..."`).
   - Action Badges: Shows which Tier was utilized:
     - `Tier 0: Cache Hit`
     - `Tier 1: Ollama 7B Local Reasoning`
     - `Tier 2: Windows UIA Automation`
     - `Tier 3: Gemini 3.8 Flash Vision Perception`
3. **Inline Approval Gates in Chat**:
   - When a safety policy is triggered (e.g. SEC-810 overwrite), an inline approval card appears in the chat stream with `Approve`, `Edit`, `Abort`, and `PANIC KILL` buttons.
4. **Quick Telemetry Drawers**:
   - **Tools Tab**: Lists available tools from `registry.get_declarations()` (`powershell`, `write_file`, `uia_click`, `capture_screen`).
   - **Memory Tab**: Shows remembered facts from `/api/memory` with ability to add or delete facts.
   - **Cache Tab**: Shows Tier-0 cache entries from `/api/cache` with `Clear Cache` button.
   - **Undo History Tab**: Shows reversible actions from `/api/undo`.

---

## 4. Interactive State Machine & Workflow Specifications

### 4.1 Human-in-the-Loop Approval Gate State Machine

```
              +---------------------------+
              |    PAUSED • APPROVAL      |
              |  (Amber Banner Glowing)   |
              +-------------+-------------+
                            |
         +------------------+------------------+------------------+
         |                                     |                  |
[Click Approve / Space]             [Click Abort / Esc]     [PANIC KILL & UNDO]
         |                                     |                  |
         v                                     v                  v
+-----------------------+           +--------------------+  +----------------------+
|       APPROVED        |           |      ABORTED       |  |      EMERGENCY       |
| (Banner turns Green)  |           | (Banner turns Red) |  |   (Banner Red Alert) |
+-----------+-----------+           +--------------------+  +----------+-----------+
            |                                                          |
            v                                                          v
    Execute Export                                           Rollback via /api/undo
  Update Task (3/4)                                          All agent threads halted
  Blackboard -> COMPLETE                                     PowerShell -> PANIC log
  REPL -> Exit 0
```

1. **State: `PAUSED • APPROVAL` (Default Prototype State)**:
   - Amber banner visible across the bottom with glowing pulse.
   - Center status badge shows `PAUSED • APPROVAL`.
   - Blackboard `[Execute]` step shows amber `BLOCKED`.
   - Task 3 shows `Approval needed` badge.
   - Safety banner inside CAD viewport shows `Existing file detected. Write operation held by safety policy.`
2. **Transition: `Approve` (Triggered via Button or `Space` key)**:
   - Call `POST /api/confirm` with `{"approve": true}`.
   - Banner changes to green confirmation: `✓ Approved by Operator — Exporting toolhead_mount.stl... Done (exit 0)`.
   - Center status badge transitions to green `COMPLETED`.
   - Blackboard `[Execute]` step transitions to green `COMPLETE`.
   - Task 3 checkbox gets checked, badge changes to `Complete` (emerald). Task progress counter updates from `2 / 4` to `3 / 4`.
   - PowerShell REPL appends:
     ```
     15:42:15 [CONFIRM] User approved SEC-810 override
     15:42:16 > Write-File C:\Fabrication\toolhead_mount.stl (62.4 KB written)
     15:42:16 EXIT 0
     ```
3. **Transition: `Abort` (Triggered via Button or `Esc` key)**:
   - Call `POST /api/confirm` with `{"approve": false}`.
   - Banner changes to neutral/red cancelled notice: `Operation aborted by operator — No changes made to disk.`
   - Center status badge transitions to red `ABORTED`.
   - Blackboard `[Execute]` step transitions to red `CANCELLED`.
   - Task 3 badge updates to `Cancelled`.
   - PowerShell REPL appends:
     ```
     15:42:18 [CONFIRM] Action cancelled by user (Esc)
     15:42:18 Operation terminated safely without disk modification.
     ```
4. **Transition: `PANIC KILL & UNDO` (Triggered via Red Button)**:
   - Call `POST /api/undo`.
   - Banner updates to high-visibility red flashing banner: `EMERGENCY STOP TRIGGERED — All operations halted, rollback complete.`
   - Center status badge transitions to red `EMERGENCY HALT`.
   - PowerShell REPL appends:
     ```
     15:42:20 [PANIC] KILL SIGNAL RECEIVED - EMERGENCY HALT
     15:42:20 Reversing last operation via /api/undo...
     15:42:21 Rollback verified. System safe.
     ```

### 4.2 Set-of-Marks (SOM) Interaction Workflow
1. **Clicking a SOM Tag (`[01]`, `[02]`, `[04]`, `[12]`)**:
   - The clicked tag border and label glow bright cyan.
   - A tool-tip / popover or status line displays the element's metadata (`Tag [04]: Button "Export" | Rect: [666, 678, 54, 32] | Confidence: 99.7%`).
   - PowerShell REPL appends: `[SOM] Focused target [04] (Button "Export")`.
2. **Clicking `Re-scan SOM`**:
   - Canvas displays a scanning scanline effect moving from top to bottom.
   - Telemetry `FRAME #8184 • 84ms` updates with incremented frame counter and randomized latency jitter (`81ms - 89ms`).
   - PowerShell REPL logs: `[SOM] Capture completed. 12 targets detected via UIA + Vision Fusion (99.2% confidence)`.
3. **Clicking `Inspect target`**:
   - Opens or switches to the Vision SOM Inspector panel detailing the active node.
4. **Clicking `Capture`**:
   - Canvas flashes white briefly (simulated camera shutter effect).
   - REPL logs: `[VISION] Viewport snapshot saved to cache/snapshots/frame_8184.png`.

### 4.3 PowerShell REPL Workflow
1. User types in `PS C:\Fabrication> ` input box.
2. Supported commands:
   - `Get-Process`: Returns PID, ProcessName, WorkingSet for active automation targets (`openscad`, `python`, `aether`).
   - `Test-Path <path>`: Returns `True` or `False`.
   - `openscad <args>`: Returns simulated compilation log and facet count.
   - `ls` / `dir`: Lists files in `C:\Fabrication`.
   - `clear` / `/clear`: Clears the terminal screen.
   - `help`: Displays available mock commands and shortcuts.
3. Submitting any command appends timestamped output and automatically scrolls to the bottom.

### 4.4 Omnibox Command Bar Workflow
1. User types natural language instruction or slash command.
2. Typing `/` displays the autocomplete popover with keyboard navigation (Up/Down arrows, Enter).
3. Pressing Enter or clicking `↑`:
   - If starting with `/run` or natural language: Calls `POST /api/route` with `instruction`.
   - Displays agent thought and actions in Focus Chat and updates Blackboard state.
   - If `/approve`, `/abort`, `/undo`: Dispatches the corresponding action.
4. Model router selector allows forcing route execution through specific engines (Auto-Route, Ollama 7B, UIA, Gemini 3.8 Flash).

---

## 5. Backend Integration Contracts (`server/api.py`)

The prototype connects directly to the FastAPI server at `http://127.0.0.1:8765`. When backend endpoints are available, the prototype communicates live; if an endpoint is unreachable or returns an error, it falls back seamlessly to rich default mock state.

| Endpoint | Method | Request Payload | Response Schema | Frontend Usage |
|----------|--------|-----------------|-----------------|----------------|
| `/` | `GET` | None | `HTMLResponse` | Serves `ui/dashboard/index.html` |
| `/api/state` | `GET` | None | `{"system": {...}, "tools": [...], "cache": [...], "memory": [...], "undo": {...}, "pending_confirmation": {...}, "voice": {...}}` | Polls/loads system telemetry, tools, and pending gates |
| `/api/route` | `POST` | `{"instruction": "..."}` | `{"success": bool, "active_tier": int, "elapsed_ms": float, "thought": "...", "actions": [...], "logs": [...]}` | Dispatches commands from Omnibox and Focus Chat |
| `/api/confirm` | `POST` | `{"approve": bool}` | `{"resolved": str, "approved": bool, "pending": dict}` | Resolves human confirmation gate (Approve / Abort) |
| `/api/undo` | `POST` | None | `{"result": str, "can_undo": bool, "history": [...]}` | Executes rollback on PANIC KILL or `/undo` |
| `/api/tool` | `POST` | `{"tool": str, "args": dict}` | `{"tool": str, "output": any}` | Directly invokes tool execution from Tools drawer |
| `/api/memory` | `POST` / `DELETE` | `{"key": str, "value": str, "category": str}` | `{"result": str, "memory": [...]}` | Manages memory facts in Knowledge/Chat inspectors |
| `/api/cache` | `DELETE` | None | `{"cleared": bool, "cache": [...]}` | Clears Tier-0 cache from drawer |
| `/api/voice` | `POST` | `{"tts_enabled": bool, "voice_capture_enabled": bool}` | `{"tts_enabled": bool, ...}` | Toggles voice wake-word or TTS state |
| `/ws` | `WebSocket` | WebSocket text | `{"type": "route_result", "data": {...}}` | Live event push from backend router |

---

## 6. Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Global Shell | Window Controls Dot Cluster | 3-dot traffic light header widget (Red, Yellow, Green) | Click | UI event (minimize/close simulation) | None (visual component) | `ui_reference_mockup.png` |
| 2 | Global Shell | Brand & Status Indicator | `gschwelli-ai` logo title with pulsing emerald live dot | None | Visual rendering | Fallback to grey dot if WS disconnects | `ui_reference_mockup.png` |
| 3 | Global Shell | 4-Mode View Switcher | Segmented pill buttons for `Mission Control`, `Knowledge Studio`, `Vision SOM`, `Focus Chat` | Click on mode pill | Swaps active main view, highlights pill | Default to Mission Control | `ORIGINAL_REQUEST.md`, `ui_reference_mockup.png` |
| 4 | Global Shell | Engine Telemetry Badge | Monospace telemetry showing model, speed, and VRAM (`Ollama 7B • 42 tok/s • 4.2GB VRAM`) | System metrics from `/api/state` | Text badge update | Fallback to mock string if API offline | `ORIGINAL_REQUEST.md`, `ui_reference_mockup.png` |
| 5 | Left Sidebar | Project / Workspace Selector | Card displaying active project `3D Fabrication & Automation`, git branch `main / 6 files indexed`, and switcher dropdown | Click dropdown / select option | Updates active workspace context and file tree | Retains previous workspace on error | `ORIGINAL_REQUEST.md`, `ui_reference_mockup.png` |
| 6 | Left Sidebar | Tasks & To-Dos Tracker | Interactive list of 4 tasks with counter `2 / 4`, checkboxes, and agent status badges | Click checkbox / click `+ Add task` | Toggles task check state, recalculates counter `X / 4` | Prevent negative counts | `ORIGINAL_REQUEST.md`, `ui_reference_mockup.png` |
| 7 | Left Sidebar | Knowledge Base File Tree | Tree showing `fabrication/` folder and 5+ files with active item highlight | Click file item | Selects file, highlights row, switches file in Knowledge Studio | Ignore clicks on invalid nodes | `ORIGINAL_REQUEST.md`, `ui_reference_mockup.png` |
| 8 | Left Sidebar | Sync Telemetry | Telemetry line `Synced 12s ago • 48 chunks` below Knowledge Base | Polling / timer | Updated time string | Display static fallback if unindexed | `ui_reference_mockup.png` |
| 9 | Left Sidebar | Audio / Wake-Word Footer | Mic meter (`RØDE NT-USB Mini -42 dB`) and `Listening for Wake-Word` toggle | Click toggle | Toggles listening state and `/api/voice` | Visual mute indicator if hardware missing | `ORIGINAL_REQUEST.md`, `ui_reference_mockup.png` |
| 10 | Center Canvas | Canvas Header & Live Pill | Displays `SOM Perception Canvas`, `LIVE` cyan badge, and `DISPLAY 01 • 1440 × 900` | None | Monospace telemetry display | Default to 1440x900 | `ui_reference_mockup.png` |
| 11 | Center Canvas | Mission Status Banner | Active mission display: `M-024 / Export toolhead_mount.stl` with badge `PAUSED • APPROVAL` | Mission state updates | Color and text updates across panels | Retains last known mission | `ui_reference_mockup.png` |
| 12 | Center Canvas | Application Window Frame | Simulated OpenSCAD window with title bar, window icons `— 🗖 ✕`, and menu bar | Click menu / window buttons | Visual feedback / menu dropdown | No-op window close (simulated) | `ui_reference_mockup.png` |
| 13 | Center Canvas | Isometric 3D CAD Viewport | Shaded 3D CAD representation of `mount_v3` bracket with dimension callouts (`80.00 mm`, `24.00 mm`) | Orbit/pan/zoom controls | Rotates and scales 3D SVG/Canvas mesh | Graceful reset on double-click | `ui_reference_mockup.png` |
| 14 | Center Canvas | Coordinate Axes Gizmo | Bottom-left 3D coordinate axes indicator (Z, Y, X) | Camera rotation | Synchronized orientation | Fallback to fixed isometric orientation | `ui_reference_mockup.png` |
| 15 | Center Canvas | CSG Code Snippet Overlay | Monospace tree showing `mount_v3 / difference() / base_plate / mount_wall / bolt_holes × 5` | None | Monospace text overlay | None | `ui_reference_mockup.png` |
| 16 | Center Canvas | Set-of-Marks Cyan Tags | Callout boxes with leader lines: `[01: Menu]`, `[02: Window Controls]`, `[12: Path Input]`, `[04: Button "Export"]` | Click on mark or leader | Highlights mark, logs target details to REPL and inspector | Ignore clicks outside mark area | `ORIGINAL_REQUEST.md`, `ui_reference_mockup.png` |
| 17 | Center Canvas | Viewport Camera Controls | Vertical bar with Orbit, Pan, Zoom, and Reset icons | Click icon / drag | Updates camera perspective | Restricts zoom beyond limits | `ui_reference_mockup.png` |
| 18 | Center Canvas | Mesh Quality Telemetry | Badge `MANIFOLD • 1,248 FACETS` with green dot | CAD mesh load | Telemetry text display | Display `ANALYZING...` while loading | `ui_reference_mockup.png` |
| 19 | Center Canvas | Export Path Bar & Warning | Input box showing `C:\Fabrication\toolhead_mount.stl` and amber warning: `Existing file detected. Write operation held by safety policy.` | Click input / edit | Displays path and active safety violation | Retain warning until approval | `ui_reference_mockup.png` |
| 20 | Center Canvas | SOM Action Toolbar | Buttons `Re-scan SOM`, `Inspect target`, `Capture`, and telemetry `FRAME #8184 • 84ms` | Click button | Triggers scanline animation, updates frame count | Graceful error toast if camera fails | `ORIGINAL_REQUEST.md`, `ui_reference_mockup.png` |
| 21 | Center Canvas | Fusion Status Bar | Telemetry bar: `12 targets mapped`, `UIA + VISION FUSION`, `99.2% confidence` | Model inference | Text display with cyan highlight | Updates on re-scan | `ui_reference_mockup.png` |
| 22 | Right Sidebar | Blackboard Pipeline Tracker | Breadcrumb trail: `[Plan] → [UIA Detect] → [Verify] → [Execute]` | Agent execution step | Highlights active/completed breadcrumb | Retains trail on completion | `ORIGINAL_REQUEST.md`, `ui_reference_mockup.png` |
| 23 | Right Sidebar | Blackboard Step Cards | 4 step cards with status badges (`COMPLETE`, `BLOCKED`), descriptions, and details | Execution updates | Status colors (green check vs amber exclamation) | Re-evaluates on state transition | `ORIGINAL_REQUEST.md`, `ui_reference_mockup.png` |
| 24 | Right Sidebar | Shared State Inspector | Read-only variable viewer showing `$target_dir`, `$exit_code`, and `checkpoint #018` | Blackboard state changes | Formatted variable display | Shows `None` for unset keys | `ORIGINAL_REQUEST.md`, `ui_reference_mockup.png` |
| 25 | Right Sidebar | PowerShell REPL Terminal | Timestamped console log with syntax coloring and exit code badge `EXIT 0` | New logs / execution output | Formatted terminal lines | Auto-scrolls to bottom | `ORIGINAL_REQUEST.md`, `ui_reference_mockup.png` |
| 26 | Right Sidebar | PowerShell Command Input | Interactive `PS C:\Fabrication> ` input box | Command string + Enter | Appends command and simulated output | Display help if unknown command | `ORIGINAL_REQUEST.md`, `ui_reference_mockup.png` |
| 27 | Right Sidebar | REPL Status Footer | Telemetry footer showing `pwsh 7.4.2` and `SANDBOX • I/O GUARDED` | Sandbox configuration | Static indicator | None | `ui_reference_mockup.png` |
| 28 | Bottom Dock | Approval Gate Banner | Full-width amber banner with safety warning `Overwrite toolhead_mount.stl • backup saved • SEC-810` | Pending gate state | Renders glowing warning banner | Hides or shows completed banner when resolved | `ORIGINAL_REQUEST.md`, `ui_reference_mockup.png` |
| 29 | Bottom Dock | Approve Action Button | `✓ Approve (Space)` button with amber styling | Click or press Space | Calls `/api/confirm` (approve=true), unblocks execution | Disabled once clicked | `ORIGINAL_REQUEST.md`, `ui_reference_mockup.png` |
| 30 | Bottom Dock | Edit Action Button | `✏ Edit` button | Click | Prompts operator to change path or flags | Cancel edit on Esc | `ORIGINAL_REQUEST.md`, `ui_reference_mockup.png` |
| 31 | Bottom Dock | Abort Action Button | `Abort (Esc)` button | Click or press Esc | Calls `/api/confirm` (approve=false), halts pipeline | Disabled once clicked | `ORIGINAL_REQUEST.md`, `ui_reference_mockup.png` |
| 32 | Bottom Dock | PANIC KILL & UNDO | High-visibility red button with exclamation/halt icon | Click | Immediately aborts agent, calls `/api/undo` | Graceful notification if undo stack empty | `ORIGINAL_REQUEST.md`, `ui_reference_mockup.png` |
| 33 | Bottom Dock | Omnibox Input & Prefix Chip | Full-width prompt bar with `+` button, `/run...` chip, and placeholder | Text typing / enter | Emits instruction to agent router | Disables submit when input empty | `ORIGINAL_REQUEST.md`, `ui_reference_mockup.png` |
| 34 | Bottom Dock | Slash Command Autocomplete | Popup menu showing `/run`, `/scan`, `/approve`, `/abort`, `/undo`, `/mode`, `/clear` | Typing `/` in Omnibox | Interactive dropdown menu | Closes on Escape or outside click | `ORIGINAL_REQUEST.md` |
| 35 | Bottom Dock | Voice Toggle Waveform | Waveform audio icon + `VOICE` pill | Click | Toggles active audio capture / speech input | Visual fallback if no mic | `ORIGINAL_REQUEST.md`, `ui_reference_mockup.png` |
| 36 | Bottom Dock | Model Router Selector | Dropdown menu: `Auto-Route: Ollama/Gemini` | Select model option | Routes subsequent instructions to selected tier | Fallback to Auto-Route | `ORIGINAL_REQUEST.md`, `ui_reference_mockup.png` |
| 37 | Knowledge Studio | File Inspector & Editor | Code editor with line numbers for OpenSCAD / Python / Markdown / YAML | File selection / edit | Formatted syntax viewer | Fallback to raw text if syntax unknown | `ORIGINAL_REQUEST.md` |
| 38 | Knowledge Studio | Chunk Embeddings Table | Table displaying chunk ID, token count, embedding model, and vector preview | File indexing | Chunk list rendering | Displays empty state if unindexed | `ORIGINAL_REQUEST.md` |
| 39 | Knowledge Studio | Re-Index Action | Button `Re-index Chunks` with progress indicator | Click | Triggers simulated RAG embedding refresh | Shows error toast on failure | `ORIGINAL_REQUEST.md` |
| 40 | Vision SOM | Expanded Tree Inspector | Tree view showing all 12 UIA nodes and Vision marks | Toggle switch / selection | Detailed element attribute panel | Handles unmapped nodes | `ORIGINAL_REQUEST.md` |
| 41 | Vision SOM | Target Filtering `[01]`-`[12]` | Filter buttons / search box for mapped marks | Input text / click filter | Filters canvas and table to matching tags | Shows "No targets matched" if empty | `ORIGINAL_REQUEST.md` |
| 42 | Vision SOM | Simulated Click / Highlight | Buttons `Simulate Click Target` and `Highlight Target` | Click | Renders pulsing ripple on canvas mark | Ignore if no mark selected | `ORIGINAL_REQUEST.md` |
| 43 | Focus Chat | Conversational Timeline | Chat stream displaying user queries and agent execution responses | Omnibox submission | Chat message bubbles | Retains chat history in session | `ORIGINAL_REQUEST.md` |
| 44 | Focus Chat | Tiered Thought & Action Trace | Collapsible cards displaying LLM thoughts, actions, and active tier (Tier 0-3) | Agent response stream | Step-by-step trace rendering | Formats raw JSON gracefully | `ORIGINAL_REQUEST.md` |
| 45 | Focus Chat | Quick Telemetry Drawers | Drawers for Tools (`/api/tool`), Memory (`/api/memory`), Cache (`/api/cache`), Undo (`/api/undo`) | Click tab in drawer | Displays live state from backend | Handles empty lists cleanly | `ORIGINAL_REQUEST.md` |

---

## 7. Edge Cases & Robustness Analysis

| # | Feature | Input / Condition | Observed / Required Behavior |
|---|---------|-------------------|------------------------------|
| 1 | Global Approval Hotkeys | User presses `Space` or `Esc` while typing inside Omnibox or PowerShell REPL | Hotkey MUST NOT trigger approval/abort; space/esc should insert space or clear text inside the active input. |
| 2 | Double-Click on Approval Buttons | User clicks `Approve` or `Abort` repeatedly in rapid succession | The button must be disabled immediately on first click to prevent duplicate `/api/confirm` calls or race conditions. |
| 3 | Backend API Offline / Network Failure | Frontend opened when `server/api.py` is not running or returns 500 | All views must render seamlessly with complete mock fallback data; no unhandled console errors or white-screen crashes. |
| 4 | PANIC KILL with Empty Undo Stack | User clicks `PANIC KILL & UNDO` when `/api/undo` has zero history items | System halts agent execution safely and logs `[UNDO] No reversible operations in stack. Emergency halt verified.` |
| 5 | Screen Resolution Responsiveness | Window resized to narrower viewport (< 1200px) | Layout gracefully contracts sidebars, preserves center CAD canvas priority, and allows horizontal scroll or column wrapping without visual clipping. |
| 6 | Terminal Log Overflow | PowerShell REPL logs exceed 500 lines | Terminal must automatically prune oldest lines while maintaining smooth auto-scroll to the newest prompt line. |
| 7 | Rapid Tab Switching | User rapidly clicks between `Mission Control`, `Knowledge Studio`, `Vision SOM`, and `Focus Chat` | Tab transitions must cancel pending render animations cleanly and retain all shared state (task checks, REPL output, active mission). |
| 8 | Invalid PowerShell Command | User enters unrecognized syntax e.g. `foo --bar` | Console outputs `foo: The term 'foo' is not recognized as a cmdlet, function, or script file.` with exit code 1 without crashing REPL. |
| 9 | Large Knowledge Base File | User selects a 500KB+ file in Knowledge Studio | Content viewer must use virtualized rendering or paginated chunk inspection to prevent DOM lag. |
| 10 | Slash Command Unknown Prefix | User types `/unknown_command` in Omnibox | Dropdown indicates "No matching command" and submitting displays helper error prompt. |

---

## 8. Verification Strategy & Acceptance Checklist

To independently verify that the implementation adheres to this specification:
1. **Visual Match Verification**:
   - Inspect `GET /` on `http://127.0.0.1:8765`.
   - Verify all color tokens match Section 2 (`#060a10` void, `#00e5ff` cyan, `#f59e0b` amber, `#10b981` emerald).
   - Verify presence of all 4 views and seamless tab switching.
2. **Interactive Workflow Verification**:
   - Verify clicking `Approve (Space)` transitions `PAUSED` -> `COMPLETED`, updates task counter to `3 / 4`, marks Blackboard `[Execute]` as `COMPLETE`, and adds REPL log.
   - Verify clicking `PANIC KILL & UNDO` triggers emergency halt.
   - Verify clicking SOM tags `[01]`, `[02]`, `[04]`, `[12]` pulses marker and updates target inspector.
   - Verify PowerShell REPL executes commands and scrolls output.
3. **Backend API Compliance**:
   - Verify endpoints in `server/api.py` (`/api/state`, `/api/route`, `/api/confirm`, `/api/undo`, `/api/voice`, `/ws`) respond cleanly without 500 errors.
