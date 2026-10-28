# Review & Adversarial Challenge Report: Milestone 3 — Center SOM Canvas & Isometric CAD Viewport

**Reviewer Agent**: `teamwork_preview_reviewer` (`reviewer_m3_2`)  
**Parent Orchestrator**: `orchestrator_1` (`20ee9337-54d2-4ed7-a02f-42aad4232d45`)  
**Target Code**: `c:\Users\andym\gschwelli-ai\ui\dashboard\index.html`  
**Worker Under Review**: `teamwork_preview_worker` (`worker_m3`)  
**Timestamp**: 2026-10-28T17:38:00Z  

---

## Review Summary

**Verdict**: **REQUEST_CHANGES**

Worker M3 has produced exceptional, high-fidelity work implementing the Center SOM Canvas and Isometric CAD Viewport in `ui/dashboard/index.html`:
- The hand-crafted SVG isometric 3D CAD mesh for `mount_v3` features gradient-shaded faces (`#143c5e`, `#1e5280`), crisp cyan wireframe edges, 3 countersunk holes, 2 vertical slots, dimension callouts (`80.00 mm`, `24.00 mm`), 3D coordinate axes gizmo (Z/Y/X), and the CSG overlay tree.
- Dynamic SVG leader line calculations (`updateSomLeaderLines`) compute precise client rect offsets and update seamlessly across window resize events.
- Toolbar actions (`Re-scan SOM` laser scan sweep, `Capture` shutter flash, `Inspect target`) and camera controls (Orbit, Pan, Zoom, Reset) animate and transform cleanly without errors.
- Tab isolation hides `#view-mission-control` cleanly, and layout responsiveness across 1440x900, 1024x768, and 1920x1080 produces zero horizontal scrollbars or clipping.
- All automated backend tests (`tests/test_api.py`: 16 passed) and DOM tests (`tests/test_browser_dom.py`: 12 passed) pass with zero console errors. No integrity violations or facade stubs were detected.

However, an **adversarial DOM pointer-event stress test** revealed a **Major CSS Placement Defect**:
The Set-of-Marks callout tag `.som-tag-04` (`[04: Button "Export"]`) is positioned at `bottom: 62px; right: 28px;` with `z-index: 15`. This places the callout tag **directly on top of the primary `#btn-export-mesh` button** (overlap area: 1,459.5 px²). Because `.som-tag-04` intercepts all mouse clicks (`document.elementFromPoint` returns `.som-tag-04`), real users and automated browsers cannot click the "Export" button (Playwright's `page.click('#btn-export-mesh')` times out with `intercepts pointer events`). Furthermore, because the tag sits directly over the button, the cyan dashed leader line is collapsed to near-zero length, defeating the visual purpose of Set-of-Marks leader line callouts. Similarly, `.som-tag-12` occludes `#export-path-input`, and `.som-tag-01` occludes `#target-menubar`.

A straightforward 3-line CSS coordinate adjustment completely eliminates all occlusion, restores full mouse clickability to `#btn-export-mesh`, and allows the leader lines to extend gracefully with clear directional vectors.

---

## Findings

### [Major] Finding 1: SOM Tag [04] Directly Occludes `#btn-export-mesh`, Intercepting Pointer Clicks & Collapsing Leader Lines

- **What**: The Set-of-Marks callout tag `.som-tag-04` (`[04: Button "Export"]`) directly covers `#btn-export-mesh`. When a user or browser tries to click the Export button, the click is intercepted by `<div id="som-tag-04">` (`z-index: 15`). In standard Playwright testing, `page.click("#btn-export-mesh")` times out after 30 seconds. In addition, because the tag sits on top of the button, leader line `#leader-line-04` is collapsed to near-zero length, obscuring the anchor dot. Similarly, `.som-tag-12` overlaps `#export-path-input` (overlap area 1,706.5 px²) and `.som-tag-01` overlaps `#target-menubar` (overlap area 995.7 px²).
- **Where**: `ui/dashboard/index.html`, lines 1037–1040:
  ```css
  /* Position SOM Tags cleanly */
  .som-tag-01 { top: 22px; left: 16px; }
  .som-tag-02 { top: 6px; right: 88px; }
  .som-tag-12 { bottom: 62px; left: 24px; }
  .som-tag-04 { bottom: 62px; right: 28px; }
  ```
- **Why**: The export dock (`#target-export-dock`) is located at the bottom of `#cad-viewport-frame` occupying approximately the bottom 100px. Positioning `.som-tag-04` and `.som-tag-12` at `bottom: 62px` places them inside the export dock directly over the input controls rather than floating in the 3D CAD canvas above the dock.
- **Proof of Failure (Playwright Interrogation & elementFromPoint)**:
  - Bounding Box Tag [04]: `x=889.3, y=649.2, w=152.3, h=22.7`
  - Bounding Box Export Button: `x=963.3, y=653.2, w=86.7, h=25.0`
  - Overlap Area: `1,459.5 px²` (almost entire button surface covered)
  - `document.elementFromPoint(btnCenterX, btnCenterY)` returns `<div id="som-tag-04" class="som-tag som-tag-04 active">`
  - Standard Playwright click: `page.click("#btn-export-mesh")` throws:
    `TimeoutError: <div data-mark="4" id="som-tag-04" ...> intercepts pointer events`
- **Suggested Fix**: Adjust the coordinates in `ui/dashboard/index.html` (lines 1037–1040) so the tags float in the 3D viewport canvas margins:
  ```css
  /* Position SOM Tags cleanly in 3D viewport canvas margins */
  .som-tag-01 { top: 58px; left: 16px; }
  .som-tag-02 { top: 6px; right: 88px; }
  .som-tag-12 { bottom: 110px; left: 24px; }
  .som-tag-04 { bottom: 110px; right: 28px; }
  ```
- **Proof of Resolution**: When `.som-tag-04` is placed at `bottom: 110px`, `page.click("#btn-export-mesh")` succeeds instantly without interception, REPL appends `'SEC-810: Export held by safety policy'`, and leader line 04 extends clearly (`y1: 532.5 -> y2: 537.7`, length 42px).

---

### [Minor] Finding 2: Defense-in-Depth for Inactive Mission Control Tab Isolation

- **What**: Worker M3 handoff reported that `#view-mission-control:not(.active-view)` remains `display: none !important`. In the code, `#view-mission-control` relies on `.view-pane { display: none; }` and `#view-mission-control.active-view { display: grid; }`.
- **Where**: `ui/dashboard/index.html`, lines 291–299.
- **Why**: While `getComputedStyle(mc).display` correctly resolves to `'none'` when inactive, declaring `#view-mission-control:not(.active-view) { display: none !important; }` explicitly guarantees defense-in-depth against future ID-level CSS additions.
- **Suggested Fix**: Add the explicit rule:
  ```css
  #view-mission-control:not(.active-view) {
    display: none !important;
  }
  ```

---

## Verified Claims

| Feature / Claim | Verification Method | Status | Notes |
|---|---|---|---|
| Backend tests pass (16/16) | `uv run --with pytest pytest tests/test_api.py -v` | **PASS** | 16 passed, 33 warnings in 6.92s |
| Browser DOM tests pass (12/12) | `uv run --with pytest,playwright pytest tests/test_browser_dom.py -v` | **PASS** | 12 passed in 10.18s |
| Zero console errors on load | Page event listener on `console` and `pageerror` | **PASS** | 0 uncaught errors or exceptions |
| Isometric 3D CAD Mesh | DOM inspection of `#cad-mesh-svg` | **PASS** | Shaded gradients, chamfers, bolt holes, slots, dimensions |
| Dynamic leader line coordinates | `test_som_leader_lines_dynamic_coordinates` | **PASS** | Valid positive coordinates, x2/y2 matches dot cx/cy |
| Tag click transitions & REPL logs | `test_som_tags_click_transitions_and_repl_logging` | **PASS** | Active class toggling, target highlight ring, exact logs |
| Camera navigation controls | `test_camera_navigation_controls_transform` | **PASS** | Zoom scales to 1.15, toggles back to 1.0, reset restores orbit |
| Action toolbar animations | `test_toolbar_actions_and_animations` | **PASS** | Laser scan sweep, frame increment, shutter flash |
| Responsive layout (1024 to 1920) | `test_responsive_layout_no_overflow_m3` | **PASS** | 0 horizontal overflow; canvas remains well-dimensioned |
| Tab isolation | `test_tab_isolation_and_leader_line_graceful_handling` | **PASS** | Inactive view resolves to `display: none`; resize handled |
| Export button pointer clickability | `test_som_tags_occlusion_audit` & Playwright click | **FAIL** | Intercepted by `.som-tag-04` due to CSS placement (Finding 1) |

---

## Adversarial Challenge & Stress-Testing

### Stress Suite Summary
We implemented and ran `tests/test_reviewer_m3_stress.py` containing 10 automated test cases.

1. **SOM Leader Line Math & Bounds**:
   - Tested rapid window resizes (1024x768 -> 1440x900 -> 1920x1080 -> 1024x768).
   - *Result*: Pass. `updateSomLeaderLines()` calculates valid floating-point SVG coordinates across all viewports without infinite reflow loops.
2. **Hidden Tab Resize Resilience**:
   - Dispatched window resize events while `view-mission-control` was hidden.
   - *Result*: Pass. `if (!frame || frame.offsetParent === null) return;` safely aborts calculation on hidden elements, avoiding zero-dimension rect corruptions.
3. **Camera Toolbar Cycling**:
   - Repeatedly toggled Zoom (1.15x -> 1.0x -> 1.15x) followed by Reset.
   - *Result*: Pass. SVG transform stays clamped to valid scale without viewport clipping or geometry distortion.
4. **Pointer Hit-Testing & Occlusion**:
   - Tested mouse clickability on `#btn-export-mesh`, `#export-path-input`, and `#target-menubar`.
   - *Result*: **FAILED**. Tag [04] occludes `#btn-export-mesh` (1,459.5 px² overlap), causing pointer click interception.

---

## 5-Component Handoff Report

### 1. Observation
- `ui/dashboard/index.html:1037-1040`:
  ```css
  .som-tag-01 { top: 22px; left: 16px; }
  .som-tag-02 { top: 6px; right: 88px; }
  .som-tag-12 { bottom: 62px; left: 24px; }
  .som-tag-04 { bottom: 62px; right: 28px; }
  ```
- When rendered at 1440x900:
  - `#som-tag-04`: `x=889.3, y=649.2, width=152.3, height=22.7`
  - `#btn-export-mesh`: `x=963.3, y=653.2, width=86.7, height=25.0`
  - Overlap: `1,459.5 px²`. `document.elementFromPoint(963.3 + 43, 653.2 + 12)` returns `<div id="som-tag-04">`.
  - Calling `page.click('#btn-export-mesh')` in Playwright times out with error:
    `TimeoutError: <div data-mark="4" id="som-tag-04" class="som-tag som-tag-04 active" title="Tag [04: Button 'Export']">[04: Button "Export"]</div> intercepts pointer events`.

### 2. Logic Chain
1. SOM callouts are meant to be floating labels with leader lines pointing to interface elements, not opaque overlays covering the elements themselves.
2. Placing `.som-tag-04` at `bottom: 62px; right: 28px;` puts it directly inside the export dock over the Export button.
3. Because `.som-tag` has `z-index: 15`, it blocks any user from directly clicking the Export button.
4. Furthermore, because the tag sits on top of the button, the cyan leader line length is under 10px, hiding the anchor dot and ruining the visual Set-of-Marks effect.
5. Moving `.som-tag-04` and `.som-tag-12` up to `bottom: 110px` moves them cleanly into the lower margin of the 3D viewport canvas. This gives the leader line 45px of visible travel, exposes the anchor dot, and allows `#btn-export-mesh` to receive direct mouse clicks without interception.

### 3. Caveats
- No caveats. All center canvas components, SVG geometry, JS event handlers, REPL logs, camera transformations, and toolbar animations were tested and verified.

### 4. Conclusion
Milestone 3 is 95% complete with outstanding visual and architectural quality. However, because Finding 1 prevents mouse clicks on the primary Export button and collapses leader line aesthetics, the verdict is **REQUEST_CHANGES**. Applying the 3-line CSS fix will make Milestone 3 100% complete and fully operable.

### 5. Verification Method
1. In `ui/dashboard/index.html`, update lines 1037–1040:
   ```css
   .som-tag-01 { top: 58px; left: 16px; }
   .som-tag-02 { top: 6px; right: 88px; }
   .som-tag-12 { bottom: 110px; left: 24px; }
   .som-tag-04 { bottom: 110px; right: 28px; }
   ```
2. Verify direct pointer clickability without occlusion:
   ```powershell
   uv run --with playwright python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(headless=True); page = b.new_page(viewport={'width': 1440, 'height': 900}); import uvicorn, threading, time, sys; sys.path.insert(0, '.'); from server.api import create_app; server = uvicorn.Server(uvicorn.Config(create_app(), host='127.0.0.1', port=8779, log_level='error')); t = threading.Thread(target=server.run, daemon=True); t.start(); time.sleep(1); page.goto('http://127.0.0.1:8779'); page.click('#btn-export-mesh'); repl = page.locator('#repl-logs').inner_text(); assert 'SEC-810' in repl; print('FIX VERIFIED: Button clicked cleanly!'); b.close(); p.stop(); server.should_exit = True"
   ```
3. Run test suites:
   ```powershell
   uv run --with pytest pytest tests/test_api.py -v
   uv run --with pytest,playwright pytest tests/test_browser_dom.py -v
   uv run --with pytest,playwright pytest tests/test_reviewer_m3_stress.py -v
   ```
