# Dispatch Assignment: Worker Milestone 3 (Center SOM Canvas & Isometric CAD Viewport)
Working directory: c:\Users\andym\gschwelli-ai\.agents\teamwork\worker_m3
Identity: teamwork_preview_worker
Parent: orchestrator_1 (20ee9337-54d2-4ed7-a02f-42aad4232d45)
Scope: Implement Center SOM Perception Canvas, simulated OpenSCAD window, isometric 3D CAD mesh SVG/Canvas, CSG snippet, coordinate axis gizmo, camera controls, interactive SOM tags [01, 02, 04, 12] with leader lines, export path bar with safety warning, action toolbar, and fusion status bar in ui/dashboard/index.html per PROJECT.md M3.
Exclusively owned files: ui/dashboard/index.html

## 2026-10-28T17:10:01Z
You are teamwork_preview_worker for Milestone 3 (Center SOM Canvas & Isometric CAD Viewport).
Your working directory is: c:\Users\andym\gschwelli-ai\.agents\teamwork\worker_m3
Your parent is the Project Orchestrator (conversation ID: 20ee9337-54d2-4ed7-a02f-42aad4232d45).

MANDATORY INPUTS (read these before starting work):
- c:\Users\andym\gschwelli-ai\.agents\teamwork\ORIGINAL_REQUEST.md
- c:\Users\andym\gschwelli-ai\PROJECT.md
- Visual Mockup: c:\Users\andym\gschwelli-ai\Inspirations\ui_reference_mockup.png
- Survey 1 Report: c:\Users\andym\gschwelli-ai\.agents\teamwork\spec_miner_survey_1\survey_report.md
- Survey 2 Report: c:\Users\andym\gschwelli-ai\.agents\teamwork\explorer_survey_2\survey_report.md

EXCLUSIVELY OWNED FILES:
- c:\Users\andym\gschwelli-ai\ui\dashboard\index.html

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

YOUR MISSION:
Implement Milestone 3 in ui/dashboard/index.html with pixel-level fidelity to Inspirations/ui_reference_mockup.png:
1. Canvas Top Header:
   - Perception retina/eye icon + text "SOM Perception Canvas" + cyan badge "LIVE" (with subtle pulse).
   - Right: Telemetry label "DISPLAY 01 • 1440 × 900".
2. Active Mission Status Bar:
   - Amber status dot + "M-024 / Export toolhead_mount.stl".
   - Right badge: glowing amber pill "PAUSED • APPROVAL".
3. Target Application Viewport ("OpenSCAD — toolhead_mount.scad"):
   - Window Title Bar: 3D cube icon + "OpenSCAD — toolhead_mount.scad" + green status dot + window actions "— 🗖 ✕".
   - Application Menu Bar: "File  Edit  Design  View  Help" | "▷ Preview F5" | "⚙ Render F6".
   - Interactive 3D CAD Mesh Viewport:
     * Render the isometric 3D CAD mesh of the toolhead mounting bracket ("mount_v3") using SVG/Canvas with shaded polygon faces (dark teal tones) and crisp cyan wireframe edges.
     * Geometry: L-bracket base plate with bolt holes, vertical mounting flange with slotted holes, chamfers.
     * Dimension callouts: "80.00 mm" along base, "24.00 mm" flange height.
     * Coordinate axes gizmo: 3D coordinate axes in bottom-left corner (Z cyan/blue, Y green, X red).
     * CSG code snippet overlay (top-left of CAD area):
       mount_v3
         difference()
           base_plate
           mount_wall
           bolt_holes × 5
     * Viewport camera navigation icons (Orbit, Pan, Zoom, Reset) on the right edge.
     * Mesh quality telemetry: green dot + "MANIFOLD • 1,248 FACETS".
   - Interactive Set-of-Marks (SOM) Cyan Tags:
     * Tag [01: Menu] with leader line pointing to the OpenSCAD menu bar.
     * Tag [02: Window Controls] with leader line pointing to the window control buttons.
     * Tag [12: Path Input] with leader line pointing to the file export path input.
     * Tag [04: Button "Export"] with leader line pointing to the Export button.
     * Clicking any tag triggers a bright cyan highlight glow, updates target telemetry in AppState and REPL log ("Focused target [04] (Button 'Export')").
   - Application Export Section:
     * Label: "EXPORT MODEL" (left) | "STL (binary) • millimeters • 62.4 KB" (right).
     * Input box with folder icon + "C:\Fabrication\toolhead_mount.stl" + cyan "Export" button.
     * Safety warning banner: "Existing file detected. Write operation held by safety policy."
     * Render telemetry: "Perspective • $fn=64 • CGAL ready" | "Last render 0.842s".
4. Action Toolbar:
   - Buttons: "[⛶] Re-scan SOM" (triggers scanning line animation and updates frame telemetry), "[↖] Inspect target", "[📷] Capture" (shutter flash effect and REPL log).
   - Telemetry: "FRAME #8184 • 84ms".
5. Fusion Status Bar:
   - Left: cyan dot + "12 targets mapped".
   - Center: "UIA + VISION FUSION".
   - Right: "99.2% confidence" (cyan).
6. Preserve all existing M2 features and fixes (clean tab switching, modal, HTML escaping, left sidebar).
7. Verification:
   Run all tests:
   uv run --with pytest pytest tests/test_api.py -v
   uv run --with pytest,playwright pytest tests/test_browser_dom.py -v
   uv run --with pytest,playwright pytest tests/ -v
8. Write handoff.md with verified results and notify parent with send_message.
