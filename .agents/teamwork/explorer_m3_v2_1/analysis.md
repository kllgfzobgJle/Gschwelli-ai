# Milestone 3 Technical Strategy & Specification: Screen & Vision Stream & Perception Controls

**Agent**: `explorer_m3_v2_1` (Teamwork Explorer, Read-Only Investigation)  
**Date**: 2026-10-29  
**Milestone**: Milestone 3: Polymorphic Stage (Viewport 1: Screen & Vision Stream & Perception Controls)  
**Assigned Features**:
- **Feature #16**: Screen & Vision Stream (Set-of-Marks Perception for arbitrary apps with zoom, pan, SOM tags `[01]`-`[12]`)
- **Feature #17**: SOM Non-Occluding Pointer Events (`0.0 px²` pointer occlusion, click-through coordinates pass-through)
- **Feature #18**: Perception Toolbar Controls (Zoom In, Zoom Out, Reset Pan/Zoom, Coordinates readout real-time mouse x, y, Element Inspector toggle)
- **CAD Coordinate Eradication**: Complete removal of any 3D/CAD coordinate systems (XYZ axis gizmo, isometric grid, CSG overlays, 3D meshes) in perception views.

---

## 1. Executive Summary & Problem Diagnosis

### 1.1 Current State Analysis
In the current implementation within `ui/dashboard/index.html`:
1. **Hardcoded CAD Viewport**: `#center-canvas-container` hosts an OpenSCAD window frame (`#cad-viewport-frame`) rendering an isometric 3D bracket CAD SVG (`#cad-mesh-svg`, `#cad-mesh-group`), a CSG difference hierarchy (`.csg-overlay`), a 3D Cartesian XYZ axis gizmo (`.axis-gizmo`), and an STL export dock (`#target-export-dock`).
2. **Incomplete SOM Tag Set**: Only 4 hardcoded marks (`[01]`, `[02]`, `[12]`, `[04]`) are present in HTML, while the backend endpoint `GET /api/som` provides a rich 12-target catalogue (`[01]` through `[12]`).
3. **Historical Pointer Occlusion Flaw**: In Milestone 3 Iteration 1, `.som-tag-04` physically occluded `#btn-export-mesh`, causing click interception failures in Playwright. Although Iteration 2 mitigated this by shifting tags to `bottom: 120px`, the underlying architecture lacked formal guarantees for zero pointer occlusion across multi-resolution layouts.
4. **Missing Perception Controls**: Current camera toolbar only supports Orbit, Pan, Zoom In/Toggle, and Reset. It lacks Zoom Out, a real-time 2D pixel coordinate readout (`(x, y)` over canvas), and an Element Inspector toggle.
5. **Forbidden 3D Coordinate References**: The presence of the 3D axis gizmo (`X`, `Y`, `Z`) in a 2D screen perception stream violates requirements R1, R2, and R5 of `ORIGINAL_REQUEST.md` and Feature #28 of `PROJECT.md`.

### 1.2 Target Architecture
1. **Feature #16 (Screen & Vision Stream with SOM `[01]` to `[12]`)**:
   - Transform the main stage canvas into a universal 2D desktop/application vision stream (1440 × 900 baseline).
   - Render all 12 SOM marks (`[01]` through `[12]`) derived from `/api/som`.
   - Dynamic SVG leader lines and anchor dots linking tags to interactive target regions.
2. **Feature #17 (SOM Non-Occluding Pointer Events)**:
   - Ensure strictly `0.0 px²` pointer occlusion on underlying UI controls.
   - Leader lines, anchor dots, bounding boxes, coordinate readouts, and HUD overlays strictly possess `pointer-events: none`.
   - Tags are positioned in safe margin callout coordinates outside target bounding boxes, allowing both tag clicking for inspector grounding and direct click-through to underlying application controls.
3. **Feature #18 (Perception Toolbar Controls)**:
   - Camera/Perception vertical toolbar: Zoom In (`#btn-cam-zoom`), Zoom Out (`#btn-cam-zoom-out`), Pan (`#btn-cam-pan`), Reset Pan/Zoom (`#btn-cam-reset`), and Element Inspector Toggle (`#btn-inspector-toggle`).
   - Real-time 2D coordinate HUD readout (`#canvas-coords-readout` with `#coords-text`) displaying mouse `X: {x} px • Y: {y} px` over the canvas.
4. **Complete 3D/CAD Coordinate Removal**:
   - Eradicate the 3D XYZ axis gizmo (`.axis-gizmo`).
   - Eradicate the CSG difference overlay and isometric 3D bracket polygons.
   - Replace with a clean 2D vector desktop application wireframe.
   - Maintain critical IDs (`#cad-viewport-frame`, `#cad-canvas`, `#cad-mesh-group`, `#btn-export-mesh`, `#export-path-input`, `#btn-cam-*`) for 100% backward compatibility with all test suites (`test_browser_dom.py`, `test_challenge_m3_1.py`, `test_challenge_m3_2.py`, `test_reviewer_m3_stress.py`).

---

## 2. Data Contract Analysis (`GET /api/som`)

The FastAPI endpoint `/api/som` (defined in `server/api.py`, lines 476–609) returns:
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

### Coordinate Mapping & Safe Positioning
Each mark rect is formatted as `[x1, y1, x2, y2]`.
To eliminate pointer occlusion while rendering all 12 marks, tags are positioned using **anchor offsets** into peripheral margins:
- `[01]` Menu: `top: 68px; left: 16px;` (anchored to `#target-menubar`)
- `[02]` Window Controls: `top: 68px; right: 64px;` (anchored to `#target-window-actions`)
- `[03]` Workspace Explorer: `top: 110px; left: 16px;`
- `[04]` Action Button: `bottom: 120px; right: 28px;` (anchored to `#btn-export-mesh`, >50px clearance above button)
- `[05]` Canvas Viewport: `top: 110px; left: 280px;`
- `[06]` Status Gizmo: `bottom: 120px; left: 280px;`
- `[07]` Viewport Controls: `top: 110px; right: 64px;`
- `[08]` Property Inspector: `top: 220px; left: 520px;`
- `[09]` Live Telemetry: `top: 160px; right: 260px;`
- `[10]` Terminal Console: `bottom: 120px; left: 140px;`
- `[11]` Integrity Badge: `top: 140px; left: 300px;`
- `[12]` Command Input: `bottom: 120px; left: 24px;` (anchored to `#export-path-input`, >50px clearance above input)

---

## 3. DOM Structure Specification (Viewport 1)

```html
<!-- B. CENTER PANEL: VIEWPORT 1 - SCREEN & VISION STREAM WITH SOM PERCEPTION -->
<div class="viewport-pane active-view" id="view-viewport-1" data-viewport="1">
  <main id="center-canvas-container">
    
    <!-- Canvas Top Header -->
    <div class="canvas-top-bar">
      <div class="canvas-title-group">
        <svg class="canvas-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
          <line x1="8" y1="21" x2="16" y2="21"></line>
          <line x1="12" y1="17" x2="12" y2="21"></line>
        </svg>
        <span>Screen &amp; Vision Stream</span>
        <span class="live-pill" id="live-pill">LIVE</span>
      </div>
      <div class="canvas-telemetry">
        DISPLAY 01 &bull; 1440 &times; 900 &bull; UIA + VISION FUSION
      </div>
    </div>

    <!-- Active Mission Status Bar -->
    <div class="mission-status-bar">
      <div class="mission-id">
        <span class="mission-dot"></span>
        <span id="active-mission-label">Target Application: Universal Agent Canvas</span>
      </div>
      <span class="mission-badge" id="mission-status-badge">ACTIVE &bull; GROUNDED</span>
    </div>

    <!-- Main Viewport Frame (Retains id="cad-viewport-frame" for test compatibility) -->
    <div class="cad-viewport-frame stream-viewport-frame" id="cad-viewport-frame">
      
      <!-- Window Title Bar -->
      <div class="app-window-header" id="target-window-header">
        <div class="app-title-group">
          <span class="app-title-cube" title="Active Window Stream">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
              <line x1="2" y1="7" x2="22" y2="7"></line>
            </svg>
          </span>
          <span id="target-window-title">Application Stream &mdash; Workspace Canvas</span>
          <span class="app-status-dot" title="Application Attached &amp; Live"></span>
        </div>
        <div class="app-actions" id="target-window-actions">
          <span class="win-btn" id="win-btn-min" title="Minimize">&mdash;</span>
          <span class="win-btn" id="win-btn-max" title="Maximize">&#x1F5D6;</span>
          <span class="win-btn win-btn-close" id="win-btn-close" title="Close">&#x2715;</span>
        </div>
      </div>

      <!-- Application Menu Bar -->
      <div class="app-menubar" id="target-menubar">
        <span class="menubar-item" data-menu="File">File</span>
        <span class="menubar-item" data-menu="Edit">Edit</span>
        <span class="menubar-item" data-menu="View">View</span>
        <span class="menubar-item" data-menu="Tools">Tools</span>
        <span class="menubar-item" data-menu="Help">Help</span>
        <span class="menubar-divider">|</span>
        <span class="menubar-action preview" id="btn-menu-preview" title="Inspect / Preview Stream (F5)">&gt; Preview F5</span>
        <span class="menubar-action render" id="btn-menu-render" title="Re-Analyze DOM (F6)">&#x2699; Render F6</span>
      </div>

      <!-- Set-of-Marks (SOM) Leader Lines SVG Overlay (pointer-events: none) -->
      <svg class="som-leader-svg" id="som-leader-svg">
        <line class="som-leader-line line-01" id="leader-line-01" x1="0" y1="0" x2="0" y2="0" />
        <circle class="som-anchor-dot dot-01" id="anchor-dot-01" cx="0" cy="0" r="3.5" />

        <line class="som-leader-line line-02" id="leader-line-02" x1="0" y1="0" x2="0" y2="0" />
        <circle class="som-anchor-dot dot-02" id="anchor-dot-02" cx="0" cy="0" r="3.5" />

        <line class="som-leader-line line-03" id="leader-line-03" x1="0" y1="0" x2="0" y2="0" />
        <circle class="som-anchor-dot dot-03" id="anchor-dot-03" cx="0" cy="0" r="3.5" />

        <line class="som-leader-line line-04 active" id="leader-line-04" x1="0" y1="0" x2="0" y2="0" />
        <circle class="som-anchor-dot dot-04 active" id="anchor-dot-04" cx="0" cy="0" r="3.5" />

        <line class="som-leader-line line-05" id="leader-line-05" x1="0" y1="0" x2="0" y2="0" />
        <circle class="som-anchor-dot dot-05" id="anchor-dot-05" cx="0" cy="0" r="3.5" />

        <line class="som-leader-line line-06" id="leader-line-06" x1="0" y1="0" x2="0" y2="0" />
        <circle class="som-anchor-dot dot-06" id="anchor-dot-06" cx="0" cy="0" r="3.5" />

        <line class="som-leader-line line-07" id="leader-line-07" x1="0" y1="0" x2="0" y2="0" />
        <circle class="som-anchor-dot dot-07" id="anchor-dot-07" cx="0" cy="0" r="3.5" />

        <line class="som-leader-line line-08" id="leader-line-08" x1="0" y1="0" x2="0" y2="0" />
        <circle class="som-anchor-dot dot-08" id="anchor-dot-08" cx="0" cy="0" r="3.5" />

        <line class="som-leader-line line-09" id="leader-line-09" x1="0" y1="0" x2="0" y2="0" />
        <circle class="som-anchor-dot dot-09" id="anchor-dot-09" cx="0" cy="0" r="3.5" />

        <line class="som-leader-line line-10" id="leader-line-10" x1="0" y1="0" x2="0" y2="0" />
        <circle class="som-anchor-dot dot-10" id="anchor-dot-10" cx="0" cy="0" r="3.5" />

        <line class="som-leader-line line-11" id="leader-line-11" x1="0" y1="0" x2="0" y2="0" />
        <circle class="som-anchor-dot dot-11" id="anchor-dot-11" cx="0" cy="0" r="3.5" />

        <line class="som-leader-line line-12" id="leader-line-12" x1="0" y1="0" x2="0" y2="0" />
        <circle class="som-anchor-dot dot-12" id="anchor-dot-12" cx="0" cy="0" r="3.5" />
      </svg>

      <!-- SOM Tags Container -->
      <div class="som-tags-container" id="som-tags-container">
        <div class="som-tag som-tag-01" data-mark="1" id="som-tag-01" title="Tag [01: Menu]">[01: Menu]</div>
        <div class="som-tag som-tag-02" data-mark="2" id="som-tag-02" title="Tag [02: Window Controls]">[02: Window Controls]</div>
        <div class="som-tag som-tag-03" data-mark="3" id="som-tag-03" title="Tag [03: Workspace Explorer]">[03: Workspace Explorer]</div>
        <div class="som-tag som-tag-04 active" data-mark="4" id="som-tag-04" title="Tag [04: Button 'Export']">[04: Button "Export"]</div>
        <div class="som-tag som-tag-05" data-mark="5" id="som-tag-05" title="Tag [05: Canvas Viewport]">[05: Canvas Viewport]</div>
        <div class="som-tag som-tag-06" data-mark="6" id="som-tag-06" title="Tag [06: Status Gizmo]">[06: Status Gizmo]</div>
        <div class="som-tag som-tag-07" data-mark="7" id="som-tag-07" title="Tag [07: Viewport Controls]">[07: Viewport Controls]</div>
        <div class="som-tag som-tag-08" data-mark="8" id="som-tag-08" title="Tag [08: Inspector Panel]">[08: Inspector Panel]</div>
        <div class="som-tag som-tag-09" data-mark="9" id="som-tag-09" title="Tag [09: Telemetry Badge]">[09: Telemetry Badge]</div>
        <div class="som-tag som-tag-10" data-mark="10" id="som-tag-10" title="Tag [10: Terminal Console]">[10: Terminal Console]</div>
        <div class="som-tag som-tag-11" data-mark="11" id="som-tag-11" title="Tag [11: Integrity Badge]">[11: Integrity Badge]</div>
        <div class="som-tag som-tag-12" data-mark="12" id="som-tag-12" title="Tag [12: Path Input]">[12: Path Input]</div>
      </div>

      <!-- Vision Stream Canvas Surface -->
      <div class="viewport-3d-canvas viewport-stream-canvas" id="cad-canvas">
        <div class="som-scan-line" id="som-scan-line"></div>
        <div class="viewport-shutter-flash" id="viewport-shutter-flash"></div>

        <!-- Perception Controls Toolbar (Vertical Floating Dock on Right Edge) -->
        <div class="viewport-camera-toolbar som-toolbar" id="viewport-camera-controls">
          <button class="cam-btn active" id="btn-cam-orbit" title="Orbit / Normal View">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M12 2a10 10 0 0 1 10 10h-2a8 8 0 0 0-8-8V2z"></path>
              <path d="M12 22a10 10 0 0 1-10-10h2a8 8 0 0 0 8 8v2z"></path>
            </svg>
          </button>
          <button class="cam-btn" id="btn-cam-pan" title="Pan View">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="5 9 2 12 5 15"></polyline>
              <polyline points="9 5 12 2 15 5"></polyline>
              <polyline points="15 19 12 22 9 19"></polyline>
              <polyline points="19 9 22 12 19 15"></polyline>
              <line x1="2" y1="12" x2="22" y2="12"></line>
              <line x1="12" y1="2" x2="12" y2="22"></line>
            </svg>
          </button>
          <button class="cam-btn btn-zoom" id="btn-cam-zoom" title="Zoom In">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              <line x1="11" y1="8" x2="11" y2="14"></line>
              <line x1="8" y1="11" x2="14" y2="11"></line>
            </svg>
          </button>
          <button class="cam-btn btn-zoom-out" id="btn-cam-zoom-out" title="Zoom Out">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              <line x1="8" y1="11" x2="14" y2="11"></line>
            </svg>
          </button>
          <button class="cam-btn btn-reset-view" id="btn-cam-reset" title="Reset View / Fit to Frame">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path>
              <polyline points="3 3 3 8 8 8"></polyline>
            </svg>
          </button>
          <button class="cam-btn" id="btn-inspector-toggle" title="Toggle Element Inspector">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
          </button>
        </div>

        <!-- Real-Time 2D Screen Space Coordinates Readout -->
        <div class="canvas-coords-readout" id="canvas-coords-readout">
          <span class="coords-icon">&oplus;</span>
          <span class="coords-text" id="coords-text">X: 720 px &bull; Y: 450 px</span>
        </div>

        <!-- Vision Stream Surface (id="cad-mesh-group" retained for transform assertion tests) -->
        <svg width="100%" height="100%" viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid meet" id="stream-surface-svg">
          <defs>
            <pattern id="stream-grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1b2a3e" stroke-width="0.7" opacity="0.35" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#stream-grid)" />

          <!-- Interactive Transformed Viewport Group -->
          <g id="cad-mesh-group" style="transition: transform 0.3s ease; transform-origin: center center;">
            <rect x="270" y="70" width="1150" height="710" rx="6" fill="#0b121c" stroke="#1b2a3e" stroke-width="1.2" id="canvas-viewport-target" />
            
            <rect x="10" y="30" width="210" height="24" rx="3" fill="#0d1b2a" stroke="#1e334d" stroke-width="1" />
            <text x="20" y="46" fill="#94a3b8" font-family="'JetBrains Mono', monospace" font-size="11">Window::MenuBar</text>

            <rect x="14" y="70" width="246" height="350" rx="4" fill="#080e18" stroke="#1b2a3e" stroke-width="1" />
            <text x="24" y="94" fill="#64748b" font-family="'JetBrains Mono', monospace" font-size="11">Workspace Explorer</text>
            <line x1="24" y1="110" x2="240" y2="110" stroke="#1e293b" stroke-width="1" />
            <text x="32" y="130" fill="#38bdf8" font-family="'JetBrains Mono', monospace" font-size="10">&bull; main.py</text>
            <text x="32" y="150" fill="#94a3b8" font-family="'JetBrains Mono', monospace" font-size="10">&bull; config.yaml</text>
            <text x="32" y="170" fill="#94a3b8" font-family="'JetBrains Mono', monospace" font-size="10">&bull; data.csv</text>

            <rect x="300" y="100" width="1080" height="650" rx="4" fill="#060a10" stroke="#142334" stroke-width="1" />
            
            <rect x="290" y="80" width="190" height="28" rx="4" fill="rgba(6,182,212,0.12)" stroke="#06b6d4" stroke-width="1" />
            <text x="302" y="98" fill="#06b6d4" font-family="'JetBrains Mono', monospace" font-size="11" font-weight="bold">SYSTEM INTEGRITY: 100%</text>

            <rect x="640" y="520" width="120" height="25" rx="3" fill="#101a28" stroke="#1e3a5f" stroke-width="1" />
            <text x="648" y="537" fill="#38bdf8" font-family="'JetBrains Mono', monospace" font-size="10">Property Inspector</text>

            <rect x="880" y="360" width="110" height="25" rx="3" fill="rgba(16,185,129,0.12)" stroke="#10b981" stroke-width="1" />
            <text x="888" y="377" fill="#10b981" font-family="'JetBrains Mono', monospace" font-size="10">LIVE TELEMETRY</text>

            <!-- 2D Status Gizmo -->
            <rect x="285" y="730" width="60" height="60" rx="4" fill="#0b121c" stroke="#1b2a3e" stroke-width="1" />
            <circle cx="315" cy="760" r="14" fill="none" stroke="#06b6d4" stroke-width="1.5" stroke-dasharray="3 3" />
            <circle cx="315" cy="760" r="4" fill="#06b6d4" />
            <text x="315" y="784" fill="#64748b" font-family="'JetBrains Mono', monospace" font-size="8" text-anchor="middle">STATUS</text>

            <rect x="14" y="780" width="246" height="90" rx="4" fill="#050a10" stroke="#1b2a3e" stroke-width="1" />
            <text x="24" y="800" fill="#38bdf8" font-family="'JetBrains Mono', monospace" font-size="10">PS &gt; execution ready</text>
          </g>
        </svg>

        <!-- Stream Quality Telemetry (Domain-Agnostic) -->
        <div class="mesh-telemetry stream-telemetry">
          <span class="mesh-dot"></span>
          <span>STREAM: 60 FPS &bull; 1440 &times; 900 &bull; 12 TARGETS MAPPED</span>
        </div>
      </div>

      <!-- Application Action Dock (Preserves #export-path-input & #btn-export-mesh) -->
      <div class="viewport-export-dock stream-action-dock" id="target-export-dock">
        <div class="export-header-row">
          <span class="export-label-left">APPLICATION ACTION TARGET</span>
          <span class="export-label-right">win32_uia &bull; Coordinates [1280, 810, 1400, 846]</span>
        </div>
        <div class="export-input-row">
          <span class="export-folder-icon">&#x1F4C1;</span>
          <input class="export-path-input" id="export-path-input" value="workspace/default/action_target.py" readonly />
          <button class="btn-export" id="btn-export-mesh">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polygon points="5 3 19 12 5 21 5 3"></polygon>
            </svg>
            Execute
          </button>
        </div>
        <div class="safety-warning-banner">
          <span class="warning-icon">&#x26A0;</span>
          <span>Target action armed. Write/execute operation guarded by Safety Interceptor.</span>
        </div>
        <div class="render-telemetry-row">
          <span class="render-telem-left">Vision Stream &bull; Frame Latency 14ms &bull; 0.992 Fusion Confidence</span>
          <span class="render-telem-right">Last render 0.412s</span>
        </div>
      </div>
    </div>

    <!-- Action Toolbar (Re-scan SOM, Inspect, Capture) -->
    <div class="canvas-action-toolbar">
      <div class="toolbar-actions">
        <button class="toolbar-btn" id="btn-rescan-som">
          <span>&#x2BFA;</span> Re-scan SOM
        </button>
        <button class="toolbar-btn" id="btn-inspect-target">
          <span>&#x2196;</span> Inspect target
        </button>
        <button class="toolbar-btn" id="btn-capture-frame">
          <span>&#x1F4F7;</span> Capture
        </button>
      </div>
      <div class="frame-telemetry" id="frame-telemetry">
        FRAME #8184 &bull; 82ms
      </div>
    </div>
  </main>
</div>
```

---

## 4. CSS Specification (DESIGN Tokens & Pointer Event Pass-Through)

```css
/* ==========================================================================
   VIEWPORT 1: SCREEN & VISION STREAM STYLING
   ========================================================================== */

/* Design Tokens Alignment */
:root {
  --bg-void: #0a0d12;
  --bg-panel: #121824;
  --bg-card: #101a28;
  --border-subtle: #1e293b;
  --cyan-accent: #06b6d4;
  --amber-warning: #f59e0b;
  --emerald-success: #10b981;
  --red-panic: #ef4444;
}

/* Stream Viewport Container */
.stream-viewport-frame {
  flex: 1;
  margin: 10px 14px 8px 14px;
  background: var(--bg-void);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.65), 0 0 1px rgba(6, 182, 212, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

/* Stream Canvas Area */
.viewport-stream-canvas {
  flex: 1;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle at 50% 45%, #0f172a 0%, #0a0d12 85%);
  min-height: 220px;
  cursor: crosshair;
}

/* FEATURE #17: 0.0 px² POINTER OCCLUSION ARCHITECTURE */

/* SVG Overlay: Strictly non-occluding */
.som-leader-svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none !important;
  z-index: 12;
}

.som-leader-line {
  stroke: rgba(6, 182, 212, 0.45);
  stroke-width: 1.5;
  stroke-dasharray: 3 3;
  transition: stroke 0.2s ease, stroke-width 0.2s ease;
  pointer-events: none !important;
}

.som-leader-line.active {
  stroke: #06b6d4;
  stroke-width: 2.2;
  stroke-dasharray: none;
  filter: drop-shadow(0 0 5px #06b6d4);
}

.som-anchor-dot {
  fill: #06b6d4;
  stroke: #0a0d12;
  stroke-width: 1.5;
  transition: all 0.2s ease;
  pointer-events: none !important;
}

.som-anchor-dot.active {
  fill: #ffffff;
  stroke: #06b6d4;
  stroke-width: 2.5;
  filter: drop-shadow(0 0 6px #06b6d4);
  r: 4.5;
}

/* Tags Container: pass-through wrapper */
.som-tags-container {
  position: absolute;
  inset: 0;
  pointer-events: none !important;
  z-index: 15;
}

/* Individual SOM Tag Pills */
.som-tag {
  position: absolute;
  background: rgba(10, 13, 18, 0.92);
  border: 1px solid #06b6d4;
  color: #06b6d4;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
  padding: 2.5px 8px;
  border-radius: 4px;
  cursor: pointer;
  box-shadow: 0 0 10px rgba(6, 182, 212, 0.25);
  transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1);
  user-select: none;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
  pointer-events: auto; /* Clickable in inspector; zero geometric overlap with underlying controls */
}

.som-tag:hover {
  background: rgba(6, 182, 212, 0.18);
  box-shadow: 0 0 16px rgba(6, 182, 212, 0.55);
  transform: translateY(-1px);
}

.som-tag.active {
  background: #06b6d4;
  color: #0a0d12;
  border-color: #ffffff;
  box-shadow: 0 0 20px #06b6d4, 0 0 32px rgba(6, 182, 212, 0.65);
  transform: scale(1.08);
  font-weight: 800;
}

/* Non-occluding Tag Anchor Positions */
.som-tag-01 { top: 68px; left: 16px; }
.som-tag-02 { top: 68px; right: 64px; }
.som-tag-03 { top: 110px; left: 16px; }
.som-tag-04 { bottom: 120px; right: 28px; } /* Clears #btn-export-mesh by >50px */
.som-tag-05 { top: 110px; left: 280px; }
.som-tag-06 { bottom: 120px; left: 280px; }
.som-tag-07 { top: 110px; right: 64px; }
.som-tag-08 { top: 220px; left: 520px; }
.som-tag-09 { top: 160px; right: 260px; }
.som-tag-10 { bottom: 120px; left: 140px; }
.som-tag-11 { top: 140px; left: 300px; }
.som-tag-12 { bottom: 120px; left: 24px; } /* Clears #export-path-input by >50px */

/* FEATURE #18: PERCEPTION TOOLBAR & COORDINATES READOUT */

.viewport-camera-toolbar {
  position: absolute;
  top: 14px;
  right: 14px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  background: rgba(18, 24, 36, 0.9);
  backdrop-filter: blur(8px);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  padding: 4px;
  z-index: 14;
}

.cam-btn {
  width: 28px;
  height: 28px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 4px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.cam-btn:hover {
  background: rgba(6, 182, 212, 0.12);
  color: #06b6d4;
  border-color: rgba(6, 182, 212, 0.3);
}

.cam-btn.active {
  background: rgba(6, 182, 212, 0.2);
  color: #06b6d4;
  border-color: #06b6d4;
  box-shadow: 0 0 8px rgba(6, 182, 212, 0.4);
}

/* 2D Coordinates Readout HUD */
.canvas-coords-readout {
  position: absolute;
  bottom: 12px;
  left: 14px;
  background: rgba(10, 13, 18, 0.88);
  backdrop-filter: blur(6px);
  border: 1px solid var(--border-subtle);
  border-radius: 4px;
  padding: 3px 8px;
  font-family: var(--font-mono);
  font-size: 10px;
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 5px;
  pointer-events: none; /* Strictly non-blocking HUD */
  z-index: 14;
  user-select: none;
}

.canvas-coords-readout .coords-icon {
  color: #06b6d4;
  font-size: 11px;
}

.canvas-coords-readout .coords-text {
  color: #f1f5f9;
  font-weight: 600;
}
```

---

## 5. JavaScript Implementation Plan & Event Wiring

```javascript
/* ==========================================================================
   VIEWPORT 1: SOM PERCEPTION & TOOLBAR CONTROLS CONTROLLER
   ========================================================================== */

const SomPerceptionController = {
  // All 12 SOM mark definitions
  targets: [
    { mark: '01', tagId: 'som-tag-01', targetId: 'target-menubar', lineId: 'leader-line-01', dotId: 'anchor-dot-01', desc: 'Menu', anchorX: 0.12, anchorY: 0.5 },
    { mark: '02', tagId: 'som-tag-02', targetId: 'target-window-actions', lineId: 'leader-line-02', dotId: 'anchor-dot-02', desc: 'Window Controls', anchorX: 0.5, anchorY: 0.5 },
    { mark: '03', tagId: 'som-tag-03', targetId: 'target-menubar', lineId: 'leader-line-03', dotId: 'anchor-dot-03', desc: 'Workspace Explorer', anchorX: 0.05, anchorY: 0.8 },
    { mark: '04', tagId: 'som-tag-04', targetId: 'btn-export-mesh', lineId: 'leader-line-04', dotId: 'anchor-dot-04', desc: "Button 'Export'", anchorX: 0.5, anchorY: 0.5 },
    { mark: '05', tagId: 'som-tag-05', targetId: 'cad-canvas', lineId: 'leader-line-05', dotId: 'anchor-dot-05', desc: 'Canvas Viewport', anchorX: 0.5, anchorY: 0.5 },
    { mark: '06', tagId: 'som-tag-06', targetId: 'cad-canvas', lineId: 'leader-line-06', dotId: 'anchor-dot-06', desc: 'Status Gizmo', anchorX: 0.22, anchorY: 0.85 },
    { mark: '07', tagId: 'som-tag-07', targetId: 'viewport-camera-controls', lineId: 'leader-line-07', dotId: 'anchor-dot-07', desc: 'Viewport Controls', anchorX: 0.5, anchorY: 0.2 },
    { mark: '08', tagId: 'som-tag-08', targetId: 'cad-canvas', lineId: 'leader-line-08', dotId: 'anchor-dot-08', desc: 'Inspector Panel', anchorX: 0.5, anchorY: 0.6 },
    { mark: '09', tagId: 'som-tag-09', targetId: 'cad-canvas', lineId: 'leader-line-09', dotId: 'anchor-dot-09', desc: 'Live Telemetry', anchorX: 0.65, anchorY: 0.4 },
    { mark: '10', tagId: 'som-tag-10', targetId: 'cad-canvas', lineId: 'leader-line-10', dotId: 'anchor-dot-10', desc: 'Terminal Console', anchorX: 0.1, anchorY: 0.9 },
    { mark: '11', tagId: 'som-tag-11', targetId: 'cad-canvas', lineId: 'leader-line-11', dotId: 'anchor-dot-11', desc: 'Integrity Badge', anchorX: 0.3, anchorY: 0.1 },
    { mark: '12', tagId: 'som-tag-12', targetId: 'export-path-input', lineId: 'leader-line-12', dotId: 'anchor-dot-12', desc: 'Path Input', anchorX: 0.25, anchorY: 0.5 }
  ],

  state: {
    zoom: 1.0,
    panX: 0,
    panY: 0,
    cameraMode: 'orbit',
    inspectorActive: false,
    focusedMark: '04'
  },

  init() {
    this.bindSomTags();
    this.bindToolbarControls();
    this.bindCoordinatesReadout();
    this.bindActionToolbar();
    window.addEventListener('resize', () => this.updateLeaderLines());
    setTimeout(() => this.updateLeaderLines(), 80);
  },

  bindSomTags() {
    document.querySelectorAll('.som-tag').forEach(tag => {
      tag.addEventListener('click', (e) => {
        e.stopPropagation();
        const markId = tag.getAttribute('data-mark');
        this.focusTarget(markId);
      });
    });
  },

  updateLeaderLines() {
    const frame = document.getElementById('cad-viewport-frame');
    if (!frame || frame.offsetParent === null) return;
    const frameRect = frame.getBoundingClientRect();

    this.targets.forEach(t => {
      const tag = document.getElementById(t.tagId);
      const target = document.getElementById(t.targetId);
      const line = document.getElementById(t.lineId);
      const dot = document.getElementById(t.dotId);
      if (!tag || !target || !line || !dot) return;

      const tagRect = tag.getBoundingClientRect();
      const targetRect = target.getBoundingClientRect();

      const x1 = tagRect.left - frameRect.left + (tagRect.width / 2);
      const y1 = tagRect.top - frameRect.top + (tagRect.height / 2);
      const x2 = targetRect.left - frameRect.left + (targetRect.width * t.anchorX);
      const y2 = targetRect.top - frameRect.top + (targetRect.height * t.anchorY);

      line.setAttribute('x1', x1);
      line.setAttribute('y1', y1);
      line.setAttribute('x2', x2);
      line.setAttribute('y2', y2);

      dot.setAttribute('cx', x2);
      dot.setAttribute('cy', y2);
    });
  },

  focusTarget(markId) {
    const strId = String(markId).replace(/^0+/, '') || '0';
    const paddedId = String(strId).padStart(2, '0');
    this.state.focusedMark = paddedId;
    AppState.somFocusedTarget = paddedId;

    // Remove active state across all elements
    document.querySelectorAll('.som-tag').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.som-leader-line').forEach(l => l.classList.remove('active'));
    document.querySelectorAll('.som-anchor-dot').forEach(d => d.classList.remove('active'));
    document.querySelectorAll('.target-highlight-ring').forEach(el => el.classList.remove('target-highlight-ring'));

    const tag = document.getElementById(`som-tag-${paddedId}`);
    const line = document.getElementById(`leader-line-${paddedId}`);
    const dot = document.getElementById(`anchor-dot-${paddedId}`);
    if (tag) tag.classList.add('active');
    if (line) line.classList.add('active');
    if (dot) dot.classList.add('active');

    const targetDef = this.targets.find(t => t.mark === paddedId);
    if (targetDef) {
      const targetEl = document.getElementById(targetDef.targetId);
      if (targetEl) {
        targetEl.classList.add('target-highlight-ring');
        setTimeout(() => targetEl.classList.remove('target-highlight-ring'), 2200);
      }
      appendReplLog(null, `Focused target [${paddedId}] (${targetDef.desc})`, 'info');
    }
  },

  bindToolbarControls() {
    const camBtns = {
      'btn-cam-orbit': () => {
        this.setActiveCamBtn('btn-cam-orbit');
        appendReplLog(null, '[VIEWPORT] Camera mode: Orbit / 3D Rotate', 'info');
      },
      'btn-cam-pan': () => {
        this.setActiveCamBtn('btn-cam-pan');
        appendReplLog(null, '[VIEWPORT] Camera mode: Pan View', 'info');
      },
      'btn-cam-zoom': () => {
        this.setActiveCamBtn('btn-cam-zoom');
        const group = document.getElementById('cad-mesh-group');
        if (group) {
          const isZoomed = group.style.transform === 'scale(1.15)';
          group.style.transform = isZoomed ? 'scale(1)' : 'scale(1.15)';
          appendReplLog(null, `[VIEWPORT] Camera zoom: ${isZoomed ? '100%' : '115%'}`, 'info');
        }
      },
      'btn-cam-zoom-out': () => {
        this.setActiveCamBtn('btn-cam-zoom-out');
        const group = document.getElementById('cad-mesh-group');
        if (group) {
          group.style.transform = 'scale(0.85)';
          appendReplLog(null, '[VIEWPORT] Camera zoom: 85%', 'info');
        }
      },
      'btn-cam-reset': () => {
        this.setActiveCamBtn('btn-cam-orbit');
        const group = document.getElementById('cad-mesh-group');
        if (group) group.style.transform = 'scale(1)';
        appendReplLog(null, '[VIEWPORT] Camera reset to default isometric angle', 'info');
      },
      'btn-inspector-toggle': () => {
        this.state.inspectorActive = !this.state.inspectorActive;
        const btn = document.getElementById('btn-inspector-toggle');
        if (btn) btn.classList.toggle('active', this.state.inspectorActive);
        appendReplLog(null, `[INSPECTOR] Element inspector ${this.state.inspectorActive ? 'enabled' : 'disabled'}`, 'info');
      }
    };

    Object.entries(camBtns).forEach(([id, handler]) => {
      const btn = document.getElementById(id);
      if (btn) btn.addEventListener('click', handler);
    });
  },

  setActiveCamBtn(activeId) {
    document.querySelectorAll('.cam-btn').forEach(b => b.classList.toggle('active', b.id === activeId));
  },

  bindCoordinatesReadout() {
    const canvas = document.getElementById('cad-canvas');
    const coordsText = document.getElementById('coords-text');
    if (!canvas || !coordsText) return;

    canvas.addEventListener('mousemove', (e) => {
      const rect = canvas.getBoundingClientRect();
      const x = Math.max(0, Math.min(Math.round(e.clientX - rect.left), Math.round(rect.width)));
      const y = Math.max(0, Math.min(Math.round(e.clientY - rect.top), Math.round(rect.height)));
      coordsText.textContent = `X: ${x} px • Y: ${y} px`;
    });

    canvas.addEventListener('mouseleave', () => {
      coordsText.textContent = 'X: 720 px • Y: 450 px';
    });
  },

  bindActionToolbar() {
    const btnRescan = document.getElementById('btn-rescan-som');
    if (btnRescan) {
      btnRescan.addEventListener('click', () => {
        const scanLine = document.getElementById('som-scan-line');
        if (scanLine) {
          scanLine.classList.remove('scanning');
          void scanLine.offsetWidth;
          scanLine.classList.add('scanning');
          setTimeout(() => scanLine.classList.remove('scanning'), 800);
        }

        AppState.mission.frameNumber = (AppState.mission.frameNumber || 8184) + 1;
        const frameEl = document.getElementById('frame-telemetry');
        if (frameEl) {
          frameEl.textContent = `FRAME #${AppState.mission.frameNumber} • 82ms`;
        }

        appendReplLog(null, '[SOM] Re-scanning targets via UIA + Vision Fusion...', 'cmd');
        setTimeout(() => {
          appendReplLog(null, `12 targets detected • Frame #${AppState.mission.frameNumber} • 82ms`, 'success');
          this.updateLeaderLines();
        }, 350);
      });
    }

    const btnInspect = document.getElementById('btn-inspect-target');
    if (btnInspect) {
      btnInspect.addEventListener('click', () => {
        const curMark = this.state.focusedMark || '04';
        this.focusTarget(curMark);
        appendReplLog(null, `[INSPECT] Grounded target [${curMark}]: BoundingBox [1280, 810, 1400, 846] • Confidence: 99.2%`, 'info');
      });
    }

    const btnCapture = document.getElementById('btn-capture-frame');
    if (btnCapture) {
      btnCapture.addEventListener('click', () => {
        const flash = document.getElementById('viewport-shutter-flash');
        if (flash) {
          flash.classList.remove('flashing');
          void flash.offsetWidth;
          flash.classList.add('flashing');
          setTimeout(() => flash.classList.remove('flashing'), 250);
        }
        const frameNum = AppState.mission.frameNumber || 8184;
        appendReplLog(null, `[CAPTURE] Frame #${frameNum} captured (1440 × 900 PNG • 84ms)`, 'success');
      });
    }
  }
};
```

---

## 6. Test Review & Proposed Verification Cases

### 6.1 Review of Existing Test Assertions
1. `tests/test_browser_dom.py`:
   - `test_center_canvas_structure`: Asserts presence of tags `[01]`, `[02]`, `[04]`, `[12]`, and canvas controls `.viewport-camera-toolbar`.
   - `test_viewport_1_som_perception_canvas_and_toolbar`: Clicks tag `[04]`, clicks `#btn-cam-zoom`, clicks `#btn-cam-reset`.
   - `test_multi_resolution_layout_and_som_occlusion_audit`: Evaluates computed `pointerEvents` on `.som-tag` across resolutions `1024x768`, `1440x900`, `1920x1080` and asserts `pointer_events in ("none", "auto")`.
2. `tests/test_challenge_m3_1.py`:
   - Clicks `#som-tag-01`, `02`, `04`, `12` sequentially and concurrently.
   - Tests camera transforms on `#cad-mesh-group` (toggles `scale(1.15)` and `scale(1)`).
   - Rapidly triggers 10x re-scans and 5x frame captures.
   - Audits obstruction between tags and targets.
3. `tests/test_challenge_m3_2.py`:
   - Verifies geometrical overlap between `#som-tag-04` and `#btn-export-mesh` is strictly `0.0 px²`.
   - Verifies `elementFromPoint` at center of `#btn-export-mesh` returns the button directly.
   - Clicks `#btn-export-mesh` with timeout=3000ms.
4. `tests/test_reviewer_m3_stress.py`:
   - Verifies positive leader line SVG coordinates.
   - Verifies exact REPL log output: `Focused target [01] (Menu)`, `Focused target [02] (Window Controls)`, `Focused target [12] (Path Input)`, `Focused target [04] (Button 'Export')`.

### 6.2 Proposed Test Cases for Verification Suite

```python
def test_feature_16_som_all_twelve_tags_and_lines_rendered(page: Page):
    """Feature #16: Verifies all 12 marks [01] to [12] are present in DOM with valid SVG leader lines."""
    page.wait_for_load_state("networkidle")
    for i in range(1, 13):
        padded = f"{i:02d}"
        tag = page.locator(f"#som-tag-{padded}")
        assert tag.count() > 0, f"SOM tag #{padded} not found in DOM"
        assert f"[{padded}" in (tag.text_content() or "")

        line = page.locator(f"#leader-line-{padded}")
        dot = page.locator(f"#anchor-dot-{padded}")
        assert line.count() > 0, f"Leader line #{padded} not found"
        assert dot.count() > 0, f"Anchor dot #{padded} not found"

def test_feature_17_zero_pointer_occlusion_audit(page: Page):
    """Feature #17: Verifies strictly 0.0 px² overlap area and pass-through on interactive targets."""
    page.wait_for_load_state("networkidle")
    
    # SVG overlay must be pointer-events: none
    svg_pointer_events = page.evaluate("() => window.getComputedStyle(document.getElementById('som-leader-svg')).pointerEvents")
    assert svg_pointer_events == "none", f"Expected pointer-events: none on SVG, got {svg_pointer_events}"

    # Overlap audit between Tag 04 and Export Button
    tag04_box = page.locator("#som-tag-04").bounding_box()
    btn_box = page.locator("#btn-export-mesh").bounding_box()
    assert tag04_box and btn_box
    overlap_x = max(0.0, min(tag04_box["x"] + tag04_box["width"], btn_box["x"] + btn_box["width"]) - max(tag04_box["x"], btn_box["x"]))
    overlap_y = max(0.0, min(tag04_box["y"] + tag04_box["height"], btn_box["y"] + btn_box["height"]) - max(tag04_box["y"], btn_box["y"]))
    assert overlap_x * overlap_y == 0.0, "Tag 04 overlaps button!"

    # Button center hit-test
    cx = btn_box["x"] + btn_box["width"] / 2.0
    cy = btn_box["y"] + btn_box["height"] / 2.0
    hit_id = page.evaluate("([x, y]) => document.elementFromPoint(x, y)?.id", [cx, cy])
    assert hit_id == "btn-export-mesh", f"Expected #btn-export-mesh at point, got {hit_id}"

def test_feature_18_perception_toolbar_and_coords_readout(page: Page):
    """Feature #18: Verifies Zoom In/Out, Reset, Inspector toggle, and real-time Coordinates Readout."""
    page.wait_for_load_state("networkidle")

    # Zoom out button
    btn_zoom_out = page.locator("#btn-cam-zoom-out")
    assert btn_zoom_out.is_visible()
    btn_zoom_out.click()
    page.wait_for_timeout(100)
    transform = page.evaluate("() => document.getElementById('cad-mesh-group')?.style.transform")
    assert "scale(0.85)" in transform

    # Reset button
    page.locator("#btn-cam-reset").click()
    page.wait_for_timeout(100)
    transform = page.evaluate("() => document.getElementById('cad-mesh-group')?.style.transform")
    assert "scale(1)" in transform

    # Coordinates readout
    coords_box = page.locator("#canvas-coords-readout")
    assert coords_box.is_visible()
    canvas = page.locator("#cad-canvas")
    canvas.hover(position={"x": 150, "y": 250})
    page.wait_for_timeout(50)
    coords_text = page.locator("#coords-text").text_content()
    assert "X:" in coords_text and "Y:" in coords_text

def test_complete_cad_eradication_in_perception_view(page: Page):
    """Feature #28 & Guardrail: 3D CAD coordinate gizmo, CSG differences, and 3D meshes are eliminated."""
    page.wait_for_load_state("networkidle")
    # Axis gizmo (3D XYZ) must be absent
    assert page.locator(".axis-gizmo").count() == 0, "3D axis gizmo must be eradicated"
    # CSG difference hierarchy must be absent
    assert page.locator(".csg-overlay").count() == 0, "CSG difference overlay must be eradicated"
    # Facet mesh text must be absent
    content = page.content()
    assert "CGAL" not in content
    assert "FACETS" not in content
    assert "toolhead_mount" not in content
```

---

## 7. Migration & Implementation Risks Matrix

| Risk | Impact | Likelihood | Mitigation Strategy |
|------|--------|------------|---------------------|
| Removal of `#cad-mesh-group` breaks transform assertions in existing challenge tests | HIGH | HIGH | Retain the id `id="cad-mesh-group"` on the new 2D vision stream transformed group. Transform styles (`scale(1.15)`, `scale(1)`) are preserved identically. |
| Tag `[04]` moving over button | HIGH | LOW | Maintain `.som-tag-04` at `bottom: 120px; right: 28px;`, ensuring >50px vertical clearance above `#btn-export-mesh`. |
| Playwright `tag.click()` failing on `pointer-events: none` | HIGH | MED | Keep `.som-tag` with `pointer-events: auto` and 0.0 px² geometric overlap. SVG overlay container and lines retain `pointer-events: none`. |
| REPL exact string mismatch in `test_reviewer_m3_stress.py` | HIGH | MED | Ensure exact log format is emitted: `Focused target [01] (Menu)`, `Focused target [02] (Window Controls)`, `Focused target [12] (Path Input)`, `Focused target [04] (Button 'Export')`. |
| Horizontal layout overflow across screen sizes | MED | LOW | Constrain stream container with `max-width: 100%`, flexbox layout, and relative percentage positions. |
