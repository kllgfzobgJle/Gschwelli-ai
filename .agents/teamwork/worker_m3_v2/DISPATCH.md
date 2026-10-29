## 2026-10-29T09:29:17Z
You are worker_m3_v2, a teamwork_worker subagent assigned to implement Milestone 3: Polymorphic Stage (4 Viewports & Split-Screen) in ui/dashboard/index.html.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY CONSTRAINTS & REFERENCES:
1. You MUST read the authoritative user request at:
   c:\Users\andym\gschwelli-ai\.agents\teamwork\ORIGINAL_REQUEST.md
   and the project plan at:
   c:\Users\andym\gschwelli-ai\PROJECT.md
2. You MUST read the technical blueprints prepared by the 3 exploration subagents:
   - Viewport 1 (Vision Stream & SOM): c:\Users\andym\gschwelli-ai\.agents\teamwork\explorer_m3_v2_1\analysis.md
   - Viewport 2 (Artifact & Document Studio): c:\Users\andym\gschwelli-ai\.agents\teamwork\explorer_m3_v2_2\analysis.md
   - Viewports 3-4, Split-Screen & CAD Clean: c:\Users\andym\gschwelli-ai\.agents\teamwork\spec_miner_m3_v2\analysis.md
3. File write ownership: You exclusively own `ui/dashboard/index.html`. DO NOT edit `server/api.py` or any files in `tests/`.
4. Working directory: Write your coordination metadata, progress, and handoff to:
   c:\Users\andym\gschwelli-ai\.agents\teamwork\worker_m3_v2\

YOUR MISSION:
Implement all 14 features of Milestone 3 directly in `ui/dashboard/index.html`:

1. Feature #15 (Polymorphic 4-Viewport Container):
   - Switchable main stage hosting Viewport 1 (Vision Stream), Viewport 2 (Document Studio), Viewport 3 (Reasoning Graph), Viewport 4 (Shell Sandbox).
   - Mode tabs (.mode-tab-btn / .viewport-tab-btn) and hotkeys `Ctrl+1..4` to switch viewports cleanly with state preservation.
2. Feature #16 (Screen & Vision Stream with SOM [01]–[12]):
   - All 12 SOM mark tags `[01]` to `[12]` rendered with SVG leader lines and anchor dots.
3. Feature #17 (SOM Non-Occluding Pointer Events):
   - Guaranteed 0.0 px² pointer occlusion; leader lines/SVG overlays have `pointer-events: none`; tags in safe peripheral coordinates with `pointer-events: auto`.
4. Feature #18 (Perception Toolbar Controls):
   - Zoom In (`#btn-cam-zoom`), Zoom Out (`#btn-cam-zoom-out`), Pan (`#btn-cam-pan`), Reset (`#btn-cam-reset`), Element Inspector Toggle (`#btn-inspector-toggle`).
   - Real-time 2D coordinates readout HUD (`#canvas-coords-readout`, `#coords-text`) updating on mousemove and resetting on mouseleave.
5. Feature #19 (Markdown 2-Column Split Studio):
   - Left raw editor (`#ks-editor-textarea`), right live HTML preview (`#ks-markdown-preview`) with split divider and strict multi-layer XSS sanitization (0 external CDNs).
6. Feature #20 (Code & Config Monospace Studio):
   - Monospace code viewer/editor with line numbers gutter (`#code-line-numbers`), regex syntax token styling, line/byte count badges, and copy button.
7. Feature #21 (Tabular / CSV Data-Grid View):
   - Dense spreadsheet grid (`#studio-data-grid`) with quotation-aware CSV/TSV parsing, sticky headers, row index column, zebra striping, and live search filter.
8. Feature #13 (File Quick Preview Integration):
   - Clicking any file in the workspace file tree automatically triggers Viewport 2 polymorphic rendering and activates Viewport 2.
9. Feature #22 (Task & Reasoning Graph / Blackboard):
   - Interactive DAG visualizer showing `Goal ➔ Sub-Tasks ➔ Gates ➔ Artifacts` with SVG connectors and node status indicators (`pending`, `in_progress`, `done`, `blocked`).
10. Feature #23 (Live Variables & Memory State):
    - Inspector panel in Viewport 3 displaying `$workspace`, `$exit_code`, `$current_task`, and persistent memory facts from `/api/memory` with click-to-REPL insertion and inline CRUD.
11. Features #24 & #25 (Multi-Tab Shell Sandbox & REPL):
    - Monospace terminal with `PowerShell`, `Bash`, `Sandbox` tabs calling `POST /api/repl`, colored stdout/stderr streams, timestamps, and exit code indicators.
12. Feature #26 (Split-Screen Canvas Mode):
    - 50/50 dual layout (`#btn-split-screen`) rendering two viewports side-by-side with independent scroll.
13. Feature #27 (Quick Telemetry Drawers):
    - Slide-out quick panels for Tools (`/api/tool`), Memory (`/api/memory`), Cache (`/api/cache`), and Undo (`/api/undo`) with `Esc` priority close (preventing safety abort trigger).
14. Feature #28 (100% Center Stage CAD Eradication):
    - Eradicate `.axis-gizmo`, `.csg-overlay`, 3D bracket isometric mesh, OpenSCAD window headers, and STL export dock.
    - Replace CAD chunks in `#ks-chunks-list` with domain-agnostic agent architecture facts.
    - PRESERVE critical backward-compatibility DOM IDs: `#cad-viewport-frame`, `#cad-canvas`, `#cad-mesh-group`, `#btn-export-mesh`, `#export-path-input`, `#ks-active-file-header`, `#ks-editor-textarea`, `#repl-input`, `#repl-logs`.
    - PRESERVE exact REPL log strings: `Focused target [01] (Menu)`, `Focused target [02] (Window Controls)`, `Focused target [12] (Path Input)`, `Focused target [04] (Button 'Export')`.
