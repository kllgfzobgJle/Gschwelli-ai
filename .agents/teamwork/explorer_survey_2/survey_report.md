# Frontend Architecture & Technical Implementation Survey (Survey 2)

**Project:** `gschwelli-ai` Control Center Web Dashboard  
**Target File:** `ui/dashboard/index.html` & `server/api.py`  
**Reference Ground-Truth:** `Inspirations/ui_reference_mockup.png`  
**Authoritative Requirements:** `ORIGINAL_REQUEST.md` (R1 – R4)  
**Survey Date:** 2026-10-28  
**Investigator:** Teamwork Explorer Survey 2  

---

## Executive Summary

The current `ui/dashboard/index.html` (611 lines) is an initial proof-of-concept interface for the 4-tier automation waterfall router (AETHER v1). While it demonstrates functional API connectivity to `server/api.py` (via `/api/state`, `/api/route`, `/api/confirm`, `/api/undo`, `/api/memory`, and WebSocket `/ws`), its visual presentation, component structure, and workflow capabilities are completely disconnected from the dark-cyan/amber cyber-physical operations cockpit specified in `ORIGINAL_REQUEST.md` and visually detailed in `Inspirations/ui_reference_mockup.png`.

To achieve 100% fidelity with the reference mockup and fulfill requirements R1 through R4, `ui/dashboard/index.html` must undergo a comprehensive redesign:
1. **Layout & Theme:** Transition from the current 2-column layout to a master 3-column cockpit (`Mission Control`) with a persistent top navigation bar (macOS window controls, `gschwelli-ai` brand, 4-mode segmented tab switcher, Ollama telemetry badge) and full-width bottom docking system (`HUMAN-IN-THE-LOOP APPROVAL NEEDED` gate and modern Omnibox command bar).
2. **Interactive SOM Perception Canvas:** Implement a high-fidelity simulated CAD viewport (`OpenSCAD — toolhead_mount.scad`) featuring an isometric 3D CAD mesh renderer (CSG hierarchy, dimension markers, coordinate axis gizmo, camera controls) coupled with interactive Set-of-Marks (SOM) cyan tags (`[01: Menu]`, `[02: Window Controls]`, `[12: Path Input]`, `[04: Button "Export"]`) with leader lines and telemetry readouts.
3. **Structured Blackboard & PowerShell REPL:** Replace the raw trace table with a structured pipeline breadcrumb (`[Plan] → [UIA Detect] → [Verify] → [Execute]`), step cards, and shared state inspector (`$target_dir`, `$exit_code`), accompanied by an interactive PowerShell REPL terminal with live command execution and syntax coloring.
4. **Dedicated 4-Tab Multi-View Shell:** Expand beyond `Mission Control` to provide rich interactive dedicated views for `Knowledge Studio` (chunk index inspector, code editor), `Vision SOM` (deep UIA tree and SOM target analyzer), and `Focus Chat` (conversational timeline and execution trace cards), all maintaining synchronized global state.
5. **Robust Zero-Dependency Architecture:** Implement the entire interface in vanilla ES2022+ and modern CSS with embedded high-performance Canvas/SVG rendering. This guarantees instant browser loading without npm build pipelines, bundlers, or external CDN vulnerabilities, ensuring 100% offline reliability.

---

## 1. Analysis of Current `ui/dashboard/index.html`

### 1.1 Document Structure & Organization
- **File Length:** 611 lines.
- **Organization:** A single monolithic HTML file containing:
  - Lines 1–7: Standard HTML5 boilerplate (`<!DOCTYPE html>`, `<head>`, meta tags).
  - Lines 8–284: Inline `<style>` block containing CSS variable declarations and UI styles.
  - Lines 287–300: `<header>` bar with branding and basic system telemetry pills.
  - Lines 302–311: `<div id="confirm-banner">` for confirmation approvals.
  - Lines 313–400: `<main>` tag configured as a 2-column CSS Grid (`1.55fr 1fr`).
  - Lines 402–608: Inline `<script>` block managing state, fetch calls, and WebSocket connection.

### 1.2 Current Visual Styling & Theme
- **Color Tokens:**
  - Backgrounds: `--bg-void: #060a10`, `--bg-panel: #0b121c`, `--bg-card: #101a28`.
  - Accents: `--cyan: #00d4ff`, `--green: #10b981`, `--amber: #f59e0b`, `--magenta: #d946ef`, `--red: #ef4444`.
  - Typography: `--text: #e2e8f0`, `--muted: #7a8fa6`.
  - Fonts: Fallback stacks for monospace (`JetBrains Mono`, `Cascadia Code`, `Consolas`) and sans-serif (`Inter`, system UI).
- **Current Layout Flaws:**
  - Left column is overloaded with a simple input box, 4 tier cards (Cache, Ollama, Win32 UIA, Vision), a raw log table, and a history list.
  - Right column contains secondary tabs for Cache, Tools, Memory, and Undo stack.
  - Lacks the 3-column cockpit structure (Left Workspace/Tasks/KB, Center SOM Canvas, Right Blackboard/REPL).
  - Lacks the bottom Human-in-the-loop approval gate and Omnibox command bar.

### 1.3 Current JavaScript Architecture
- **State Storage:** A single global variable `let currentState = {};`.
- **API Fetch Handlers:**
  - `refreshState()`: Fetches `/api/state` and updates telemetry pills, confirmation banner, history list, cache entries, tools count, memory list, and undo items.
  - `sendCommand()`: POSTs instruction to `/api/route` and invokes `renderTrace()`.
  - `triggerUndo()`: POSTs to `/api/undo`.
  - `toggleTTS()`: POSTs to `/api/voice`.
  - `resolveConfirm(approve)`: POSTs `{"approve": bool}` to `/api/confirm`.
  - `saveMemory()` / `deleteMemory()`: Manages `/api/memory`.
- **WebSocket Client:**
  - `connectWS()` opens `ws://${location.host}/ws` and parses JSON messages. If `msg.type === 'route_result'`, it updates the trace table and refreshes state.
- **Polling:** A fallback `setInterval(refreshState, 5000)` polls the server every 5 seconds.

---

## 2. Libraries, Frameworks & Dependency Evaluation

### 2.1 Current Dependencies
- **Zero Third-Party JS Libraries:** No React, Vue, Angular, Svelte, Lit, or jQuery.
- **Zero Third-Party CSS Frameworks:** No Tailwind, Bootstrap, or Bulma.
- **Zero External CDN Assets:** No Google Fonts stylesheets, CDN icon scripts (FontAwesome/Lucide), or remote JS bundles.
- **No Build Tools:** No Webpack, Vite, Rollup, Babel, or TypeScript compilation step.

### 2.2 Serving Mechanism in `server/api.py`
In `server/api.py` (lines 25–26, 106–110):
```python
BASE_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_HTML_PATH = BASE_DIR / "ui" / "dashboard" / "index.html"

@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    if DASHBOARD_HTML_PATH.is_file():
        return HTMLResponse(DASHBOARD_HTML_PATH.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>AETHER Dashboard HTML not found</h1>", status_code=404)
```
Crucially, `server/api.py` does **not** currently mount a static files directory (`app.mount("/static", ...)`). Everything served at `GET /` comes directly from reading `index.html` as raw text.

### 2.3 Recommended Technology Choice for High-Fidelity Prototype
- **Recommendation:** Maintain a **self-contained zero-dependency vanilla architecture** (HTML5 + CSS3 + modern ES2022 JavaScript + embedded SVG/Canvas).
- **Advantages:**
  1. **Instant Loading:** Zero build delays, zero bundle compilation, sub-50ms browser first paint.
  2. **100% Offline Capability:** Works immediately in air-gapped or restricted development environments without network requests to external CDNs.
  3. **High Performance:** Raw DOM operations and HTML5 Canvas / SVG rendering achieve 60+ FPS for 3D isometric CAD rendering and interactive SOM overlays.
  4. **Direct Server Compatibility:** Compatible with the existing FastAPI serving logic without modifying static mount configurations or breaking existing tests.
  5. **Crisp Cyberpunk / High-Tech Visuals:** Embedded inline SVGs allow exact pixel styling, glow filters (`drop-shadow`, `box-shadow`), neon cyan/amber accents, and crisp vector scaling.

---

## 3. Backend Communication Architecture

### 3.1 Endpoint Mapping & Protocol Contract

| Endpoint | Method | Payload / Parameters | Server Response | Dashboard Usage & Integration |
|---|---|---|---|---|
| `GET /` | HTTP GET | None | `text/html` | Serves dashboard shell |
| `GET /api/state` | HTTP GET | None | JSON: `{system, tools, cache, memory, undo, pending_confirmation, history, voice}` | Global telemetry, status synchronization, and background heartbeat |
| `POST /api/route` | HTTP POST | `{"instruction": string}` | JSON: `{success, active_tier, elapsed_ms, instruction, thought, actions, outputs, verification_logs, logs}` | Executed by Omnibox command bar, Focus Chat, and PowerShell REPL |
| `POST /api/confirm` | HTTP POST | `{"approve": boolean}` | JSON: `{resolved: string, approved: bool, pending: Optional[dict]}` | Triggered by Human-in-the-Loop Approval Banner (`Approve` / `Abort`) |
| `POST /api/undo` | HTTP POST | None | JSON: `{result: string, can_undo: bool, history: list}` | Triggered by `PANIC KILL & UNDO` button |
| `POST /api/tool` | HTTP POST | `{"tool": string, "args": dict}` | JSON: `{tool: string, output: any}` | Direct tool execution from Knowledge Studio / Focus Chat |
| `POST /api/memory` | HTTP POST | `{"key": str, "value": str, "category": str}` | JSON: `{result: str, memory: list}` | Knowledge base & memory persistence |
| `DELETE /api/memory/{key}` | HTTP DELETE | Query param `category` | JSON: `{result: str, memory: list}` | Memory item deletion |
| `DELETE /api/cache` | HTTP DELETE | None | JSON: `{cleared: bool, cache: dict}` | Cache store reset |
| `POST /api/voice` | HTTP POST | `{"tts_enabled": bool, "voice_capture_enabled": bool}` | JSON: Voice state dictionary | Voice toggle button & mic status in left sidebar |
| `WebSocket /ws` | WS Connect | Text messages / heartbeats | Broadcasts `{"type": "route_result", "data": {...}}` | Instant real-time UI updates when routes complete asynchronously |

### 3.2 Dual-Mode Hybrid State: Real Backend + Realistic Simulated Mock Fallback
Per requirement R4: The dashboard must seamlessly interface with live backend endpoints when available, while providing realistic mock state for the `3D Fabrication & Automation` / `M-024 Export toolhead_mount.stl` scenario when host desktop applications (e.g. OpenSCAD) are not running.

- **Handling `POST /api/confirm`:**
  - If a real backend confirmation is pending (`st.pending_confirmation != null`), calling `/api/confirm` resolves it on the server.
  - If no backend confirmation is currently active, `/api/confirm` returns `status=failed reason="No pending confirmation"`. The frontend gracefully captures this, immediately transitions its simulated mission state (from `PAUSED • APPROVAL` to `COMPLETED`), marks task `Export toolhead_mount` as complete, updates the Blackboard step `[Execute]` from `BLOCKED` to `COMPLETE`, logs the approval in the PowerShell REPL, and hides the approval banner.
- **Handling `POST /api/undo`:**
  - Calling `/api/undo` issues the backend POST request. The frontend appends a panic abort warning line to the PowerShell REPL, transitions the mission state to `ABORTED / SAFE RESET`, and flashes a visual reset alert.
- **Handling WebSocket Disconnections:**
  - Auto-reconnect with exponential backoff (starting at 1000ms up to 5000ms), maintaining an unobtrusive connection status indicator in the top header.

---

## 4. Gap Analysis: Current UI vs. Reference Mockup & Requirements

```
+------------------------------------------------------------------------------------------------------------------+
| COMPONENT                  | CURRENT IMPLEMENTATION              | REQUIRED SPECIFICATION (R1 - R4)              |
+------------------------------------------------------------------------------------------------------------------+
| Global Shell Layout        | 2-column asymmetric grid            | 3-column cockpit (260px / 1fr / 360px)        |
|                            | (no dock, simple header)            | + Top Header + 2 Full-Width Bottom Dock Bars  |
+------------------------------------------------------------------------------------------------------------------+
| Top Navigation Bar         | "AETHER", simple CPU/RAM pills,     | Window dots, "gschwelli-ai" brand + live dot, |
|                            | basic buttons                       | Centered 4-Tab Switcher, Ollama 7B telemetry  |
+------------------------------------------------------------------------------------------------------------------+
| Left Sidebar: Workspace    | Non-existent                        | Card: "Active: 3D Fabrication & Automation",  |
|                            |                                     | git branch "main / 6 files indexed", dropdown |
+------------------------------------------------------------------------------------------------------------------+
| Left Sidebar: Tasks/To-Dos | Non-existent                        | Card: "TASKS & TO-DOS (2 / 4)" with clickable |
|                            |                                     | checkboxes, status badges (Complete, Approval)|
+------------------------------------------------------------------------------------------------------------------+
| Left Sidebar: Knowledge    | Non-existent (raw cache tab)        | Hierarchical tree (fabrication/, files),      |
|                            |                                     | chunk telemetry ("Synced 12s ago • 48 chunks")|
+------------------------------------------------------------------------------------------------------------------+
| Left Sidebar: Audio/Mic    | Text pill "PTT: Ctrl+Space"         | Mic badge ("RØDE NT-USB Mini -42 dB") +       |
|                            |                                     | "Listening for Wake-Word" interactive button  |
+------------------------------------------------------------------------------------------------------------------+
| Center: SOM Canvas Header  | None                                | "SOM Perception Canvas LIVE", display info    |
|                            |                                     | "DISPLAY 01 • 1440 × 900", Mission M-024 bar  |
+------------------------------------------------------------------------------------------------------------------+
| Center: Simulated Viewport | None (just raw latency label)       | "OpenSCAD — toolhead_mount.scad" window,      |
|                            |                                     | Isometric 3D CAD mesh, CSG tree overlay,      |
|                            |                                     | axis gizmo, camera controls, facet counter    |
+------------------------------------------------------------------------------------------------------------------+
| Center: SOM Callout Tags   | None                                | Interactive tags [01], [02], [04], [12] with  |
|                            |                                     | connector lines to menu, controls, path, btn  |
+------------------------------------------------------------------------------------------------------------------+
| Center: Viewport Controls  | None                                | Export path input, safety warning banner,     |
| & Fusion Status Bar        |                                     | Action toolbar (Re-scan, Inspect, Capture),   |
|                            |                                     | Fusion status (12 targets, 99.2% confidence)  |
+------------------------------------------------------------------------------------------------------------------+
| Right: Blackboard          | Raw table: Time, Tier, Level, Msg   | Pipeline: [Plan] → [UIA Detect] → [Verify]    |
|                            |                                     | → [Execute], step status cards, shared state  |
+------------------------------------------------------------------------------------------------------------------+
| Right: PowerShell REPL     | Simple single-line text input       | Interactive terminal console (EXIT 0),        |
|                            |                                     | colored timestamps, commands, PS prompt,      |
|                            |                                     | sandbox footer ("pwsh 7.4.2 • I/O GUARDED")   |
+------------------------------------------------------------------------------------------------------------------+
| Bottom: Approval Gate      | Hidden div with 2 basic buttons     | Amber-bordered safety banner: icon, warning   |
|                            |                                     | text, "Approve (Space)", "Edit", "Abort(Esc)",|
|                            |                                     | "PANIC KILL & UNDO" button                    |
+------------------------------------------------------------------------------------------------------------------+
| Bottom: Command Bar        | Generic input + "EXECUTE" button    | Modern Omnibox: "+", "/run...", placeholder,  |
|                            |                                     | slash autocomplete, VOICE wave, Model selector|
+------------------------------------------------------------------------------------------------------------------+
| Multi-Tab Architecture     | Right column internal tab toggle    | 4 Full-featured global views: Mission Control,|
|                            | (Cache/Tools/Memory/Undo)           | Knowledge Studio, Vision SOM, Focus Chat      |
+------------------------------------------------------------------------------------------------------------------+
```

---

## 5. Detailed Architecture & Design of the 4 Top-Level Tabs

### 5.1 Tab 1: `Mission Control` (The Primary Operations Cockpit)
This tab matches the layout, density, and cyber-physical visual identity of `Inspirations/ui_reference_mockup.png`.

```
+--------------------------------------------------------------------------------------------------------------------------+
| [● ● ●] [Icon] gschwelli-ai [●]    [ Mission Control | Knowledge Studio | Vision SOM | Focus Chat ]    [Ollama 7B • 42 tok/s] [⚙]|
+--------------------------------------------------------------------------------------------------------------------------+
| LEFT SIDEBAR (270px)    | CENTER PANEL: SOM PERCEPTION CANVAS (1fr)               | RIGHT SIDEBAR: BLACKBOARD & REPL (360px)|
|                         |                                                         |                                         |
| [PROJECT / WORKSPACE]   | ◉ SOM Perception Canvas [LIVE]    DISPLAY 01 • 1440×900 | ⛶ Blackboard                   AGENT-01 |
| Active: 3D Fabrication  | ------------------------------------------------------- | [Plan] → [UIA Detect] → [Verify] → [Exe]|
| main / 6 files indexed  | ● M-024 / Export toolhead_mount.stl  [PAUSED • APPROVAL]|                                         |
|                         | +-----------------------------------------------------+ | ✓ [Plan] Prepare fabrication   COMPLETE |
| [TASKS & TO-DOS  2 / 4] | | [Icon] OpenSCAD — toolhead_mount.scad       [- □ ×] | | ✓ [UIA Detect] Resolve targets COMPLETE |
| [✓] Validate mount geom | | File Edit Design View Help   [01: Menu] [02: Window]| | ✓ [Verify] Validate geometry   COMPLETE |
| [✓] Resolve export dest | | mount_v3            /---------------------/       | | ⚠ [Execute] Commit to disk     BLOCKED  |
| [ ] Export toolhead     | |   difference()     /    [3D Isometric CAD Mesh]   | |                                         |
| [ ] Run fab pipeline    | |     base_plate    /       with Dimension Tags,    | | SHARED STATE / READ-ONLY                |
|                         | |     mount_wall   /         Gizmo, Grid & Faces    | | $target_dir  C:\Fabrication             |
| [KNOWLEDGE BASE    (+)] | |     bolt_holes  /                                 | | $exit_code   0         checkpoint #018  |
| 📁 fabrication/         | | [12: Path Input]                [04: Button Export]| +---------------------------------------+
|   📄 workflow.md        | | EXPORT: [ C:\Fabrication\toolhead_mount.stl ] [Exp] | | >_ PowerShell REPL             EXIT 0 |
|   🐍 agent_kinematics   | | ⚠ Existing file detected. Write held by policy.    | | 15:42:06 > Get-Process openscad       |
|   🧊 toolhead_mount     | +-----------------------------------------------------+ | 15:42:07 > Test-Path $target_dir        |
|   📦 mount_assembly     | [ ⛶ Re-scan SOM ] [ ⌖ Inspect target ] [ 📷 Capture ]  | 15:42:09  1,248 facets • 62.4 KB • exit0|
|   ⚙ pipeline_config     | ------------------------------------------------------- | 15:42:10 ⚠ SEC-810: write held by policy|
| 🟢 Synced 12s ago       | ● 12 targets mapped    UIA + VISION FUSION    99.2% conf| PS C:\Fabrication> █                    |
|                         +---------------------------------------------------------+ pwsh 7.4.2            SANDBOX • GUARDED |
| 🎙 RØDE NT-USB -42 dB   |                                                                                                   |
| [● Listening Wake-Word] |                                                                                                   |
+--------------------------------------------------------------------------------------------------------------------------+
| ⚠ HUMAN-IN-THE-LOOP APPROVAL NEEDED — Overwrite toolhead_mount.stl • backup saved • SEC-810   [✓ Approve] [Edit] [Abort] [⊘ PANIC]|
+--------------------------------------------------------------------------------------------------------------------------+
| [+] [/run...] Describe the next action, or type / for commands                          [🎙 VOICE] [🤖 Auto-Route: Ollama/Gemini] [↑]|
+--------------------------------------------------------------------------------------------------------------------------+
```

### 5.2 Tab 2: `Knowledge Studio`
- **Objective:** Deep exploration and live inspection of indexed project files, chunk embeddings, and RAG metadata.
- **Layout:**
  - **Left Explorer Pane (240px):** Workspace file browser with search bar, file type icons, chunk count badges, and index status. Includes a "Re-index Workspace" trigger button.
  - **Center Editor/Viewer Pane (1fr):** Tabbed code/markdown viewer with line numbers, syntax highlighting (OpenSCAD, Python, Markdown, YAML), and interactive visual chunk boundary banners (e.g. `Chunk #03 • Lines 45–82 • 256 tokens`).
  - **Right Vector & Embedding Inspector (320px):**
    - Semantic Search Simulator: input a natural language query to view real-time cosine similarity scores against indexed chunks.
    - Vector Embedding Card: model used (`text-embedding-3-small` / `all-minilm-l6-v2`), dimension (`768-d`), token count, and raw vector histogram preview.
    - Chunk Metadata Table: chunk UUID, parent document, SHA256 hash, and last modified timestamp.

### 5.3 Tab 3: `Vision SOM` (Deep Set-of-Marks & UIA Inspector)
- **Objective:** Diagnostic workstation for computer vision fusion, coordinate mapping, and Windows UI Automation hierarchy analysis.
- **Layout:**
  - **Left Target List Pane (280px):** Filterable list of all detected controls (`[01]` through `[12]`) with category filters (`All`, `Buttons`, `Inputs`, `Menus`, `Panels`), match confidence badges (`99.2%`, `98.7%`), and search input.
  - **Center Viewport Canvas (1fr):** High-resolution canvas featuring toggleable visual overlays:
    - *Vision SOM Layer:* Bounding boxes with cyan tags and leader lines.
    - *Win32 UIA Tree Layer:* Deep wireframe bounding rects extracted from accessibility APIs.
    - *Fusion Heatmap Layer:* Probability distribution of OCR and element grounding.
  - **Right Inspector & Action Pane (320px):**
    - Target Details: Mark number, control name, control type, native HWND, AutomationId, class name.
    - Spatial Telemetry: Absolute screen rect `[left, top, right, bottom]`, window-relative rect, center click coordinates `(x, y)`.
    - Live Simulator Controls: "Simulate Click", "Highlight On Screen", "Send Text Input", "Verify Target Invalidation".

### 5.4 Tab 4: `Focus Chat`
- **Objective:** Distraction-free conversational interface for conversational automation, extended thinking traces, and interactive review.
- **Layout:**
  - **Conversational Timeline (1fr):**
    - User message bubbles with attached context chips (e.g. `toolhead_mount.scad`).
    - Agent response cards featuring collapsible "Extended Thinking / Plan" accordions.
    - Blackboard execution trace cards displaying tier transitions, tool calls, and execution outputs.
    - Inline human approval cards for pending actions.
  - **Quick-Access Drawer (300px, collapsible):**
    - Instant inspector tabs for Tier 0 SQLite Cache entries, active Tools registry, and persistent Long-Term Memory facts.
  - **Bottom Omnibox:** Fully shared with the global command bar for unified keyboard workflows.

---

## 6. Technical Implementation Recommendations

### 6.1 Unified Reactive State Store (`AppState`)
All UI views and components must share a single reactive JavaScript state object (`AppState`). This ensures that an action performed in `Mission Control` (e.g. approving an operation) is instantly reflected in `Focus Chat`, `Vision SOM`, and `Knowledge Studio`.

```javascript
const AppState = {
  activeTab: 'mission_control', // 'mission_control' | 'knowledge_studio' | 'vision_som' | 'focus_chat'
  project: {
    name: '3D Fabrication & Automation',
    branch: 'main',
    indexedFiles: 6,
    activeFile: 'toolhead_mount.scad',
    lastSync: '12s ago',
    totalChunks: 48,
  },
  mission: {
    id: 'M-024',
    name: 'Export toolhead_mount.stl',
    status: 'PAUSED • APPROVAL', // 'PAUSED • APPROVAL' | 'EXECUTING' | 'COMPLETED' | 'ABORTED'
    confidence: '99.2%',
    targetsMapped: 12,
    fusionMode: 'UIA + VISION FUSION',
    exportPath: 'C:\\Fabrication\\toolhead_mount.stl',
  },
  approvalGate: {
    active: true,
    title: 'HUMAN-IN-THE-LOOP APPROVAL NEEDED',
    detail: 'Overwrite toolhead_mount.stl • backup saved • SEC-810',
    rule: 'SEC-810',
    ageSeconds: 14.2,
  },
  tasks: [
    { id: 't1', title: 'Validate mount geometry', completed: true, badge: 'Complete', badgeType: 'complete' },
    { id: 't2', title: 'Resolve export destination', completed: true, badge: 'Complete', badgeType: 'complete' },
    { id: 't3', title: 'Export toolhead mount', completed: false, badge: 'Approval needed', badgeType: 'approval' },
    { id: 't4', title: 'Run fabrication pipeline', completed: false, badge: 'Queued', badgeType: 'queued' }
  ],
  blackboard: {
    agentId: 'AGENT-01',
    steps: [
      { id: 'plan', label: '[Plan]', desc: 'Prepare fabrication export', detail: 'Load toolhead_mount.scad → binary STL', status: 'COMPLETE' },
      { id: 'uia', label: '[UIA Detect]', desc: 'Resolve application targets', detail: '12 nodes matched • Export → [04]', status: 'COMPLETE' },
      { id: 'verify', label: '[Verify]', desc: 'Validate path & geometry', detail: 'Manifold ✓ • overwrite requires approval', status: 'COMPLETE' },
      { id: 'exec', label: '[Execute]', desc: 'Commit export to disk', detail: 'Waiting at human approval gate', status: 'BLOCKED' }
    ],
    sharedState: {
      target_dir: 'C:\\Fabrication',
      exit_code: 0,
      checkpoint: '#018'
    }
  },
  somTargets: [
    { id: '01', tag: '[01: Menu]', name: 'Menu', rect: [12, 38, 240, 60], type: 'MenuBar', confidence: 0.99 },
    { id: '02', tag: '[02: Window Controls]', name: 'Window Controls', rect: [580, 8, 670, 32], type: 'ButtonGroup', confidence: 0.98 },
    { id: '04', tag: '[04: Button "Export"]', name: 'Button "Export"', rect: [540, 480, 660, 520], type: 'Button', confidence: 0.99 },
    { id: '12', tag: '[12: Path Input]', name: 'Path Input', rect: [30, 480, 520, 520], type: 'Edit', confidence: 0.97 }
  ],
  selectedSomId: null,
  replLogs: [
    { time: '15:42:06', type: 'cmd', text: 'Get-Process openscad' },
    { time: '15:42:06', type: 'info', text: 'PID 8044 • UIA attached' },
    { time: '15:42:07', type: 'cmd', text: 'Test-Path $target_dir' },
    { time: '15:42:07', type: 'info', text: 'True' },
    { time: '15:42:08', type: 'cmd', text: 'openscad --check-parameters' },
    { time: '15:42:09', type: 'success', text: 'CGAL: valid 2-manifold mesh' },
    { time: '15:42:09', type: 'info', text: '1,248 facets • 62.4 KB • exit 0' },
    { time: '15:42:10', type: 'cmd', text: 'Export-Mesh -Format STL' },
    { time: '15:42:10', type: 'warn', text: 'SEC-810: existing file at target' },
    { time: '15:42:10', type: 'warn', text: 'WRITE HELD • awaiting approval' }
  ],
  voice: {
    micName: 'RØDE NT-USB Mini',
    levelDb: -42,
    listening: true,
    ttsEnabled: false
  },
  telemetry: {
    model: 'Ollama 7B',
    tokPerSec: 42,
    vram: '4.2GB',
    cpuPercent: 18,
    ramPercent: 44,
    ramUsedGb: 7.1,
    ramTotalGb: 16.0
  }
};
```

### 6.2 3D Isometric CAD Canvas & SOM Overlay Rendering
The center panel in `Mission Control` represents a simulated OpenSCAD application window. To achieve high fidelity without external 3D engine libraries (Three.js/Babylon.js), we can use an **HTML5 2D Canvas or SVG Isometric Projection Engine**:
1. **Isometric Projection Mathematics:**
   - Standard 30° isometric transform:
     $$\begin{cases} X_{\text{screen}} = (X - Y) \cdot \cos(30^\circ) + X_0 \\ Y_{\text{screen}} = (X + Y) \cdot \sin(30^\circ) - Z + Y_0 \end{cases}$$
2. **CAD Mesh Geometry:**
   - Define vertex arrays and face polygons representing the L-bracket mount (`base_plate` with 4 cylindrical bolt holes, vertical `mount_wall` with 2 slotted mounting holes, chamfered edges, and grid lines).
   - Render polygon faces with subtle gradient shading (dark teal/slate face tones `#0e2638`, `#163b56`, `#1f4f72`) and bright cyan wireframe edges (`#00e5ff88`).
   - Draw dimension callout annotations: `80.00 mm` along the base plate, `24.00 mm` along the wall thickness.
   - Render 3D coordinate axis gizmo (X in red, Y in green, Z in cyan) in the bottom-left corner.
3. **Interactive SOM Callout Overlays:**
   - SVG or Canvas overlay rendering cyan bounding boxes around:
     - Menu bar: `[01: Menu]`
     - Window control buttons: `[02: Window Controls]`
     - File export path bar: `[12: Path Input]`
     - Export action button: `[04: Button "Export"]`
   - Render dynamic leader lines connecting each tag box to its target region with a dot anchor.
   - Attach click handlers: clicking any tag highlights it, updates the target inspector, logs to REPL, and displays element telemetry (`Screen Rect: (540, 480, 120, 40) • UIA: Button.Export • Confidence: 99.2%`).

### 6.3 Human-in-the-Loop Safety Gate Workflow
1. **Visual Styling:**
   - Amber border (`#f59e0b`), dark translucent amber background (`rgba(245, 158, 11, 0.12)`), animated amber pulse indicator.
   - Left: Amber shield/warning icon with bold headline: `HUMAN-IN-THE-LOOP APPROVAL NEEDED — Overwrite toolhead_mount.stl • backup saved • SEC-810`.
   - Right: Interactive action buttons:
     - `✓ Approve (Space)`: Emphasized amber pill button.
     - `Edit`: Neutral gray pill button.
     - `Abort (Esc)`: Neutral gray pill button.
     - `⊘ PANIC KILL & UNDO`: Red accent pill button.
2. **Action Handlers:**
   - **`Approve`**: Calls `/api/confirm` with `{"approve": true}`. Immediately transitions `AppState.mission.status` to `COMPLETED`, updates Blackboard step `[Execute]` to `COMPLETE`, sets task `Export toolhead_mount` to checked/complete, appends `[OK] Export-Mesh completed: toolhead_mount.stl written` to the REPL, and removes the approval banner.
   - **`Abort`**: Calls `/api/confirm` with `{"approve": false}`. Transitions mission status to `CANCELLED`, updates Blackboard step `[Execute]` to `CANCELLED`, appends `[ABORT] User cancelled write operation` to the REPL, and hides the approval banner.
   - **`Panic Kill & Undo`**: Calls `/api/undo`. Appends critical warning to the REPL (`[PANIC] Operation terminated. Reverting state...`), resets the mission to `ABORTED / SAFE RESET`, and plays a brief alert flash.
3. **Global Keyboard Shortcuts:**
   - Listen to `keydown` event on `window`:
     - If active element is not an `<input>` or `<textarea>`:
       - `Space` triggers `Approve`.
       - `Escape` triggers `Abort`.
       - `/` focuses the Omnibox command input.
       - Keys `1`, `2`, `3`, `4` switch between the 4 navigation tabs.

### 6.4 Interactive PowerShell REPL
1. **Visual Presentation:**
   - Dark terminal pane (`#05080f`) with header: `>_ PowerShell REPL` and green badge `EXIT 0`.
   - Scrollable log area formatted in monospace font (`JetBrains Mono` / `Cascadia Code`).
   - Line-by-line syntax coloring:
     - Timestamps: muted blue `#527191`.
     - Commands (`> ...`): cyan `#00d4ff` or bright white.
     - Informational output: neutral silver `#cbd5e1`.
     - Success output (`valid 2-manifold`, `exit 0`): emerald green `#10b981`.
     - Warnings / Security holds (`SEC-810`, `WRITE HELD`): amber `#f59e0b`.
     - Errors: crimson `#ef4444`.
   - Terminal prompt line: `PS C:\Fabrication>` with an active text input and blinking block cursor.
2. **Command Dispatcher:**
   - When the user types a command and presses Enter:
     - Appends the command to REPL log.
     - If the command is a built-in mock command (`Get-Process`, `Test-Path`, `dir`, `ls`, `cat toolhead_mount.scad`, `help`, `clear`): returns immediate simulated terminal output.
     - If the command is an automation instruction: dispatches to `POST /api/route` and pipes execution trace logs into the REPL.
   - Footer: green dot `pwsh 7.4.2` on the left, `SANDBOX • I/O GUARDED` on the right.

### 6.5 Modern Omnibox Command Bar
1. **Layout & Visuals:**
   - Bottom floating/docked container with dark navy surface and subtle cyan glow.
   - Left: `+` attachment button (opens context picker: Files, Screenshots, HWND).
   - Slash Command Chip: `/run...` chip prefix.
   - Input field: `Describe the next action, or type / for commands`.
   - Right:
     - `🎙 VOICE` waveform button (toggles voice listening state).
     - Model router pill: `🤖 Auto-Route: Ollama/Gemini` with dropdown arrow.
     - Submit button: Cyan square button with upward arrow `↑`.
2. **Slash Command Autocomplete Menu:**
   - When input starts with `/`, render an autocomplete popover:
     - `/run <instruction>`: Execute automation waterfall.
     - `/scan`: Trigger SOM Perception re-scan.
     - `/approve`: Confirm pending safety gate.
     - `/undo`: Trigger undo stack rollback.
     - `/mode <mission|knowledge|vision|chat>`: Switch dashboard tabs.
     - `/clear`: Clear REPL and chat history.
   - Navigable with Up/Down arrow keys and Enter.

---

## 7. Automated Testing & Verification Strategy

To guarantee zero regression and satisfy Acceptance Criteria:

1. **Backend Integration Suite (`tests/test_dashboard_api.py`):**
   - Test `GET /`: returns status 200, content-type `text/html`, non-empty body.
   - Test `GET /api/state`: returns 200, valid JSON with `system`, `tools`, `cache`, `memory`, `undo`, `voice`.
   - Test `POST /api/confirm`: handles `{"approve": true}` and `{"approve": false}` gracefully (whether pending gate exists or not).
   - Test `POST /api/undo`: handles undo invocation without exceptions.
   - Test `POST /api/route`: validates instruction handling and response serialization.
   - Test `WebSocket /ws`: connects, sends ping, receives messages without dropping.
2. **Frontend DOM & Interactive Verification Suite:**
   - Automated script utilizing Python `playwright` or headless browser verification:
     - Verifies zero console errors or uncaught JS exceptions during initial load.
     - Checks existence and visibility of all 4 mode switcher tabs (`Mission Control`, `Knowledge Studio`, `Vision SOM`, `Focus Chat`).
     - Verifies switching between tabs updates the view correctly.
     - Verifies SOM tags `[01]`, `[02]`, `[04]`, `[12]` exist and respond to clicks.
     - Verifies clicking `Approve (Space)` resolves the safety banner and updates the task and mission status.
     - Verifies PowerShell REPL accepts input and appends command lines.
     - Verifies Omnibox slash commands and submission.

---

## Conclusion & Next Steps

The existing `ui/dashboard/index.html` provides a solid starting baseline for API connectivity, but requires a complete visual and structural reconstruction to become the high-fidelity cyber-physical cockpit envisioned in `ORIGINAL_REQUEST.md`.

By employing a **zero-dependency vanilla ES2022 + modern CSS + inline SVG/Canvas** architecture:
1. The implementation avoids brittle npm/Node.js dependencies and works instantly when served by FastAPI at `GET /`.
2. All visual elements, colors, layouts, and typography from `Inspirations/ui_reference_mockup.png` can be replicated with mathematical precision.
3. Full interactivity across all 4 tabs, SOM tags, Blackboard steps, PowerShell REPL, and Human-in-the-Loop safety gates can be realized with robust fallback handling and real-time backend synchronization.
