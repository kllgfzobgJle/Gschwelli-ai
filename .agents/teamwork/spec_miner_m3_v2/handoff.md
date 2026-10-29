# Specification Mining Handoff Report: Milestone 3 — Polymorphic Stage

**Agent ID:** `spec_miner_m3_v2` (teamwork_spec_miner subagent)  
**Parent Agent:** `db3d98a0-f6a4-45e7-9dea-32dceda77cf0`  
**Milestone:** Milestone 3 (Polymorphic Stage: 4 Viewports, Split-Screen Mode, Quick Telemetry Drawers, and Center Stage CAD Eradication)  
**Date:** 2026-10-29  
**Deliverable Document:** `c:\Users\andym\gschwelli-ai\.agents\teamwork\spec_miner_m3_v2\analysis.md`  

---

## 1. Observation

1. **Authoritative Specification & Mandate (`ORIGINAL_REQUEST.md` & `PROJECT.md`)**:
   - `ORIGINAL_REQUEST.md` (lines 5, 17–24, 53–60):
     > "Transformiere das bestehende Web-Cockpit in eine universelle, domain-agnostische Agent-Workstation (Operating Canvas) für autonome Agenten ohne Bindung an spezifische Domänen oder vordefinierte Spezial-Szenarien (keine hardcodierten CAD- oder 3D-Druck-Elemente)."  
     > "Umschaltbarer Viewport-Container (per Tab oder Shortcut) mit vier universellen Viewport-Typen:  
     > 1. Screen & Vision Stream (Set-of-Marks Perception)  
     > 2. Artifact & Document Studio  
     > 3. Task & Reasoning Graph (Blackboard Visualizer)  
     > 4. Shell & Execution Sandbox  
     > Split-Screen-Layout für zwei parallele Ansichten sowie beibehaltene Quick-Drawers / Inspektoren für Tools, Memory-Facts (/api/memory), Tier-0-Cache (/api/cache) und Undo-Stack (/api/undo)."
   - `PROJECT.md` Feature Inventory (lines 50–63):
     * Feature #15: Polymorphic 4-Viewport Container (M3)
     * Feature #22: Task & Reasoning Graph (Blackboard) (M3)
     * Feature #23: Live Variables & Memory State (M3)
     * Feature #24: Multi-Tab Shell Sandbox (M3)
     * Feature #25: REPL Execution & Log Styling (M3)
     * Feature #26: Split-Screen Canvas Mode (M3)
     * Feature #27: Quick Telemetry Drawers (M3)
     * Feature #28: Center Stage CAD Removal (M3)

2. **Existing Implementation Status in `ui/dashboard/index.html`**:
   - In lines 2801–3116, the center stage is currently occupied by `#center-canvas-container` containing `#cad-viewport-frame`, `#cad-canvas`, `#cad-mesh-svg` with 3D bracket isometric geometry `#cad-mesh-group` (shaded polygons `#facet-base-top`, bolt hole ellipses, slotted rects, dimension lines `80.00 mm`, `24.00 mm`), axis gizmo `#axis-gizmo`, CSG overlay `.csg-overlay`, OpenSCAD window header `#target-window-header` with title `"OpenSCAD — toolhead_mount.scad"`, menubar actions `"▷ Preview F5"` and `"⚙ Render F6"`, and `#target-export-dock` (`STL (binary) • 62.4 KB`, `#export-path-input`, `#btn-export-mesh`).
   - In lines 3218–3271, the terminal is a single-tab PowerShell REPL in the right sidebar (`#repl-pane`, `#repl-logs`, `#repl-input`), without tab switching for Bash or Sandbox.
   - In lines 3199–3215, shared state displays static `$target_dir` and `$exit_code`, without integration with `/api/memory`.
   - In lines 3530–3565, quick drawers exist only as static cards inside Viewport 4 (Focus Chat), rather than slide-out panels accessible globally.
   - Neither `#btn-split-screen` nor `Ctrl+1..4` viewport switching are currently implemented.

3. **Backend API Readiness (`server/api.py`)**:
   - `GET /api/state` returns all required system keys (`system`, `workspaces`, `tasks`, `tools`, `cache`, `memory`, `undo`, `pending_confirmation`, `history`, `voice`).
   - `POST /api/repl` (lines 467–474) executes commands via `ps_repl.run`, returning `{"command": cmd, "output": out, "exit_code": exit_code}`.
   - `GET /api/som` (lines 476–609) returns 12 universal application marks (`[01]`–`[12]`) with `Window::` selectors and zero CAD tokens.
   - `POST /api/memory` and `DELETE /api/memory/{key}` (lines 424–433) support CRUD operations on persistent memory.
   - `DELETE /api/cache` (lines 434–438) and `POST /api/undo` (lines 414–418) support cache flush and rollback.

4. **Automated Test Results**:
   - `uv run --with pytest pytest tests/test_api.py -v`: 22 passed in 14.87s.
   - `uv run --with pytest,playwright pytest tests/test_browser_dom.py -v`: 30 passed in 34.30s.

---

## 2. Logic Chain

1. **Authoritative Mandate Derivation**:
   - Per `ORIGINAL_REQUEST.md` R2, the center stage must provide a polymorphic 4-viewport system (Vision Stream, Document Studio, Reasoning Graph, Shell Sandbox) with 50/50 split-screen mode and slide-out quick drawers.
   - Per `PROJECT.md` Feature #28 and `ORIGINAL_REQUEST.md` R1/R5, all hardcoded CAD elements (OpenSCAD title bar, 3D mesh polygon rendering, CSG difference snippets, STL export docks, and 3D printing widgets) must be 100% eradicated from the center stage.

2. **Analysis of Legacy Elements vs Target Design**:
   - Currently, `#cad-viewport-frame` houses 3D CAD vectors and OpenSCAD titles. This directly violates R1/R5 domain-agnostic requirements.
   - To achieve Feature #15, `#center-canvas-container` must be refactored into a `#stage-viewports-container` hosting four `.viewport-panel` containers (`#viewport-1` to `#viewport-4`), controlled by segmented tabs (`.viewport-tab-btn[data-viewport="1..4"]`) and keyboard hotkeys (`Ctrl+1..4`).
   - To achieve Feature #22 and #23, Viewport 3 must host the DAG Blackboard (`Goal ➔ Sub-Tasks ➔ Gates ➔ Artifacts`) and the Live Variables & Memory State Inspector panel synced with `/api/memory`.
   - To achieve Features #24 and #25, Viewport 4 must host a multi-tab terminal (`PowerShell`, `Bash`, `Sandbox`) calling `POST /api/repl` with color-coded stdout/stderr streams, timestamps, and exit code indicators.
   - To achieve Feature #26, a `#btn-split-screen` button toggles a 50/50 CSS Grid layout (`grid-template-columns: 1fr 1fr`), rendering two viewports side-by-side with independent event routing.
   - To achieve Feature #27, a fixed slide-out panel `#telemetry-drawer-panel` must provide slide-out access to Tools (`/api/tool`), Memory (`/api/memory`), Cache (`/api/cache`), and Undo (`/api/undo`), dismissible via backdrop click or `Escape` key without triggering the global Safety Interceptor abort.

3. **Validation Against Anti-Cheat & Zero-Dependency Constraints**:
   - Zero external CDNs: All icons are inline SVG, fonts are system monospace/sans stacks, and layout math is pure CSS3/ES2022.
   - Keyboard Scope Guard: `Ctrl+1..4` switches viewports cleanly without corrupting active input text. `Escape` inside an open drawer closes the drawer without resolving the safety confirmation gate.

---

## 3. Caveats

1. **Viewport 1 & Viewport 2 Exploration Synergy**:
   - Viewport 1 (Screen & Vision Stream SOM) and Viewport 2 (Artifact & Document Studio) are explored concurrently by `explorer_m3_v2_1` and `explorer_m3_v2_2`. This blueprint establishes the master container contracts (`#viewport-1`, `#viewport-2`, `#stage-viewports-container`, and hotkeys) so their component implementations drop in seamlessly.
2. **Backward Compatibility with Existing Selectors**:
   - Existing tests in `test_browser_dom.py` expect selectors such as `.mode-tab-btn`, `.shared-state-box`, `#repl-input`, and `#btn-split-screen`. The blueprint retains these IDs and CSS classes as semantic aliases.
3. **No Code Written**:
   - In accordance with the Read-Only constraint for specification miners, no source files were edited.

---

## 4. Conclusion

The specification blueprint in `c:\Users\andym\gschwelli-ai\.agents\teamwork\spec_miner_m3_v2\analysis.md` provides an exhaustive, actionable, and verified architecture for all 7 Milestone 3 features:
1. Feature #15 (Polymorphic 4-Viewport Container with `Ctrl+1..4` hotkeys).
2. Feature #22 (Task & Reasoning Graph / Blackboard DAG Visualizer).
3. Feature #23 (Live Variables & Memory State Inspector calling `/api/memory`).
4. Features #24 & #25 (Multi-Tab Shell Sandbox & REPL with exit codes and stream styling).
5. Feature #26 (Split-Screen Canvas Mode with 50/50 side-by-side layout).
6. Feature #27 (Quick Telemetry Drawers for Tools, Memory, Cache, Undo).
7. Feature #28 (100% Center Stage CAD Eradication with zero remaining forbidden tokens).

All technical requirements, data contracts, DOM structures, CSS tokens, and edge cases are thoroughly documented and ready for worker implementation.

---

## 5. Verification Method

To independently reproduce and verify this specification:

1. **Inspect Analysis Report**:
   ```powershell
   Get-Content c:\Users\andym\gschwelli-ai\.agents\teamwork\spec_miner_m3_v2\analysis.md
   ```
   *Expected:* Complete document with Features Discovered and Edge Cases tables, DOM templates, CSS variables, and event handling logic.

2. **Verify Backend Contract Baseline**:
   ```powershell
   uv run --with pytest pytest tests/test_api.py -v
   ```
   *Expected:* 22 passed.

3. **Verify DOM Interactivity Baseline**:
   ```powershell
   uv run --with pytest,playwright pytest tests/test_browser_dom.py -v
   ```
   *Expected:* 30 passed.

4. **Verify CAD Token Eradication Target Locations**:
   ```powershell
   rg -i "openscad|cad-mesh|csg-overlay|toolhead" ui/dashboard/index.html
   ```
   *Expected:* Matches found only in legacy center stage lines (to be replaced by worker during M3 implementation).
