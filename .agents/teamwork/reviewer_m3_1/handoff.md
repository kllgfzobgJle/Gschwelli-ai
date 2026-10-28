# Review & Adversarial Challenge Report: Milestone 3 — Center SOM Canvas & Isometric CAD Viewport

**Reviewer**: `teamwork_preview_reviewer` (reviewer_m3_1)  
**Parent Orchestrator**: `orchestrator_1` (`20ee9337-54d2-4ed7-a02f-42aad4232d45`)  
**Target Code**: `c:\Users\andym\gschwelli-ai\ui\dashboard\index.html`  
**Worker Under Review**: `teamwork_preview_worker` (`worker_m3`)  
**Timestamp**: 2026-10-28T17:37:00Z  

---

## Review Summary

**Verdict**: **REQUEST_CHANGES**

The implementation submitted by `worker_m3` is of high quality:
- A rich isometric 3D CAD mesh SVG for mounting bracket `mount_v3` with realistic gradient shading (`facet-base-top`, `facet-flange-front`, `facet-flange-side`), chamfers, 3 countersunk bolt holes with depth gradients, 2 vertical flange slots, ground perspective grid, dimension callouts (`80.00 mm`, `24.00 mm`), 3D coordinate axes gizmo (Z/Y/X), CSG overlay, and mesh telemetry (`MANIFOLD • 1,248 FACETS`).
- Center Canvas top header with retina icon, `SOM Perception Canvas`, pulsing `LIVE` pill, and `DISPLAY 01 • 1440 × 900`.
- Active mission bar with pulsing amber dot, `M-024 / Export toolhead_mount.stl`, and glowing amber pill `PAUSED • APPROVAL`.
- Interactive Set-of-Marks tags (`[01]`, `[02]`, `[12]`, `[04]`) with dynamic SVG leader lines computing bounding box coordinates across resizes.
- Application export section with folder icon, path input, `Export` button, safety policy warning banner, and render telemetry.
- Action toolbar (`Re-scan SOM` with laser scanline sweep, `Inspect target`, `Capture` with camera shutter flash, `FRAME #8184 • 84ms`) and bottom fusion status bar (`12 targets mapped`, `UIA + VISION FUSION`, `99.2% confidence`).
- All 4 automated test suites run and pass: **45 / 45 tests pass**.

However, adversarial stress testing and visual comparison against `Inspirations/ui_reference_mockup.png` revealed **one Major Usability & Layout Defect** and **one Minor Visual Defect**:
1. **[Major] Pointer Event Interception**: `.som-tag-04` is styled with `bottom: 62px; right: 28px;`, placing it directly over `#btn-export-mesh` (covering ~90% of the button area). When an automated test or user attempts to click `#btn-export-mesh`, the browser fails with `playwright._impl._errors.TimeoutError: <div id="som-tag-04" ...> intercepts pointer events`. In addition, `.som-tag-12` sits directly on top of the left portion of `#export-path-input`. In `ui_reference_mockup.png`, both tags float inside the 3D CAD canvas area *above* the export dock, with leader lines pointing downwards into the dock.
2. **[Minor] Cold-Load Active Line Parity**: On initial page load before user interaction, `#som-tag-04` has the `.active` class, but `#leader-line-04` and `#anchor-dot-04` do not have `.active` in the HTML markup, resulting in a dashed, dim leader line instead of a solid glowing cyan line.

A minimal 2-line CSS adjustment and 1-line HTML update completely fixes both issues, verified via Playwright simulation.

---

## 1. Observation

### Exact File Paths and Lines:
- `c:\Users\andym\gschwelli-ai\ui\dashboard\index.html`:
  - **Lines 1039–1040 (CSS Tag Positioning)**:
    ```css
    .som-tag-12 { bottom: 62px; left: 24px; }
    .som-tag-04 { bottom: 62px; right: 28px; }
    ```
  - **Lines 2136–2148 (Leader Line SVG Overlay)**:
    ```html
    <line class="som-leader-line line-04" id="leader-line-04" x1="0" y1="0" x2="0" y2="0" />
    <circle class="som-anchor-dot dot-04" id="anchor-dot-04" cx="0" cy="0" r="3.5" />
    ```
  - **Lines 2372–2379 (Export Button & Path Input)**:
    ```html
    <div class="export-input-row">
      <span class="export-folder-icon">📁</span>
      <input class="export-path-input" id="export-path-input" value="C:\Fabrication\toolhead_mount.stl" readonly />
      <button class="btn-export" id="btn-export-mesh">
        ...
        Export
      </button>
    </div>
    ```

### Measured Bounding Boxes (Viewport 1440 × 900):
```
Export Dock:        { x: 285.0, y: 624.2, width: 779.0, height: 108.8 }
Export Button:      { x: 963.3, y: 653.2, width: 86.7,  height: 25.0  }
SOM Tag 04:         { x: 889.3, y: 649.2, width: 152.3, height: 22.7  }  <-- OVERLAPS Export Button (x: 963-1041, y: 649-672)
Export Path Input:  { x: 324.9, y: 653.2, width: 630.5, height: 25.0  }
SOM Tag 12:         { x: 309.0, y: 650.0, width: 111.8, height: 21.0  }  <-- OVERLAPS Path Input
```

### Verbatim Playwright Failure on Direct Click:
```
playwright._impl._errors.TimeoutError: Locator.click: Timeout 30000ms exceeded.
Call log:
  - waiting for locator("#btn-export-mesh")
  - attempting click action
    - <div data-mark="4" id="som-tag-04" class="som-tag som-tag-04 active" title="Tag [04: Button 'Export']">[04: Button "Export"]</div> intercepts pointer events
```

### Visual Reference Comparison (`Inspirations/ui_reference_mockup.png`):
- In the reference mockup, `[04: Button "Export"]` is located in the bottom-right corner of the 3D CAD canvas viewport (below `• MANIFOLD • 1,248 FACETS`), well above the export dock.
- A cyan leader line connects downwards from `[04: Button "Export"]` to the `Export` button inside the export dock.
- `[12: Path Input]` is located in the bottom-left of the 3D CAD canvas, and its leader line connects downwards to the path input.

---

## 2. Logic Chain

1. In `index.html`, `#cad-viewport-frame` contains both the CAD canvas (`#cad-canvas`, height ~350px) and the export dock (`#target-export-dock`, height ~109px).
2. The SOM callout tags `.som-tag-12` and `.som-tag-04` are positioned absolutely relative to `#cad-viewport-frame` with `bottom: 62px;`.
3. Because the export dock is 108.8px tall, `bottom: 62px;` positions the tags inside the export dock, exactly at `y = 650px` (where the input row sits at `y = 653px`).
4. Tag `[04: Button "Export"]` (width 152px) spans `x: 889` to `1041`, while `#btn-export-mesh` (width 86.7px) spans `x: 963` to `1050`. The tag directly covers ~90% of the button.
5. Because `.som-tag` has `z-index: 15` (higher than `.btn-export` and inputs), user click actions on `#btn-export-mesh` hit `.som-tag-04` instead of `#btn-export-mesh`, preventing direct invocation of the export action handler.
6. Changing `.som-tag-12` and `.som-tag-04` to `bottom: 125px;` moves them ~16px above the export dock into the 3D CAD canvas, exactly matching `Inspirations/ui_reference_mockup.png`.
7. Once moved to `bottom: 125px;`, `#btn-export-mesh` is completely unobstructed, `page.locator("#btn-export-mesh").click()` succeeds in <100ms, and `updateSomLeaderLines()` draws the leader line downwards into the dock.
8. Similarly, adding `active` to `#leader-line-04` and `#anchor-dot-04` ensures cold-load active state parity with `#som-tag-04`.

---

## 3. Findings

### [Major] Finding 1: `.som-tag-04` Overlaps `#btn-export-mesh`, Intercepting Pointer Clicks; `.som-tag-12` Overlaps `#export-path-input`

- **What**: SOM Tag `[04: Button "Export"]` sits directly on top of the `#btn-export-mesh` button, and SOM Tag `[12: Path Input]` sits directly on top of `#export-path-input`.
- **Where**: `ui/dashboard/index.html`, lines 1039–1040:
  ```css
  .som-tag-12 { bottom: 62px; left: 24px; }
  .som-tag-04 { bottom: 62px; right: 28px; }
  ```
- **Why**: Intercepts pointer events on `#btn-export-mesh`, causing click actions to fail or trigger SOM tag selection rather than the export warning/action. Violates visual reference layout where tags float in the 3D viewport canvas above the dock.
- **Suggested Fix**:
  Update lines 1039–1040 in `ui/dashboard/index.html`:
  ```css
  .som-tag-12 { bottom: 125px; left: 24px; }
  .som-tag-04 { bottom: 125px; right: 28px; }
  ```

### [Minor] Finding 2: Static HTML Lacks `active` Class on `#leader-line-04` and `#anchor-dot-04` on Cold Load

- **What**: `#som-tag-04` has `class="som-tag som-tag-04 active"` in HTML, but `#leader-line-04` and `#anchor-dot-04` lack `active`.
- **Where**: `ui/dashboard/index.html`, lines 2146–2147:
  ```html
  <line class="som-leader-line line-04" id="leader-line-04" x1="0" y1="0" x2="0" y2="0" />
  <circle class="som-anchor-dot dot-04" id="anchor-dot-04" cx="0" cy="0" r="3.5" />
  ```
- **Why**: Causes the active tag to show a dim, dashed leader line and inactive dot on initial page render, before any user click.
- **Suggested Fix**:
  Add `active` class to `#leader-line-04` and `#anchor-dot-04` in lines 2146–2147:
  ```html
  <line class="som-leader-line line-04 active" id="leader-line-04" x1="0" y1="0" x2="0" y2="0" />
  <circle class="som-anchor-dot dot-04 active" id="anchor-dot-04" cx="0" cy="0" r="3.5" />
  ```

---

## 4. Integrity Check Attestation

The implementation was examined for integrity violations:
- **Hardcoded test outputs**: None found.
- **Dummy / facade logic**: None found. Real SVG coordinate math, real CSS keyframes and shutter flashes, real AppState reactivity.
- **Shortcuts / bypassed work**: None found. M3 features are implemented thoroughly.
- **Fabricated verification outputs**: None found. All test runs were executed independently.
- **Verdict on Integrity**: **PASS (NO INTEGRITY VIOLATION)**.

---

## 5. Verified Claims

| Feature / Claim | Verification Method | Status |
|-----------------|---------------------|--------|
| Canvas Top Header (retina icon, "SOM Perception Canvas", LIVE pill pulse, DISPLAY 01 telemetry) | Playwright inspection & DOM styles | PASS |
| Active Mission Status Bar (pulsing amber dot, M-024 label, glowing PAUSED • APPROVAL badge) | Playwright inspection & DOM styles | PASS |
| Simulated OpenSCAD Window (cube icon, title, green dot, min/max/close controls) | Playwright click & REPL log verification | PASS |
| Menubar actions (Preview F5 & Render F6) | Playwright click & render telemetry updates | PASS |
| Isometric 3D CAD Mesh (`mount_v3` gradient faces, wireframes, 3 bolt holes, 2 slots, chamfers, ground grid) | SVG DOM node inspection & visual review | PASS |
| Dimension callouts (80.00 mm along base, 24.00 mm flange height) | SVG text and dimension line inspection | PASS |
| Coordinate axes gizmo (Z cyan up, Y green up-right, X red down-right) | SVG line & marker inspection | PASS |
| CSG overlay (`mount_v3 / difference() / base_plate / mount_wall / bolt_holes × 5`) | DOM text & styling inspection | PASS |
| Camera navigation (Orbit, Pan, Zoom scale 1.15x, Reset) | Playwright click & style transform inspection | PASS |
| Mesh telemetry (`MANIFOLD • 1,248 FACETS`) | DOM node & text inspection | PASS |
| Interactive SOM tags ([01], [02], [12], [04]) & leader lines | Playwright click, active classes, AppState update, REPL log | PASS (interactivity works; layout overlap flagged) |
| Action toolbar (Re-scan laser sweep, Inspect target, Capture shutter flash) | Playwright click, CSS animation classes, REPL logs | PASS |
| Fusion status bar (12 targets, UIA + VISION FUSION, 99.2% confidence) | DOM text & style inspection | PASS |
| Test suite execution (test_api.py, test_browser_dom.py, test_challenge_m2.py, test_adversarial_m2.py) | pytest runs via `uv run` | PASS (45/45) |

---

## 6. Caveats

- `test_api.py` and `test_browser_dom.py` must be run in separate Python processes when using sync Playwright to avoid anyio/asyncio event-loop conflicts.
- Findings 1 and 2 do not require architecture changes; they are clean 2-line CSS and 1-line HTML adjustments.

---

## 7. Conclusion

Milestone 3 is technically comprehensive, visually striking, and functionally rich. However, because `.som-tag-04` physically obstructs clicking `#btn-export-mesh`, and `.som-tag-12` obstructs `#export-path-input`, the verdict is **REQUEST_CHANGES**. Applying the suggested 2-line CSS adjustment (`bottom: 125px`) and 1-line HTML update resolves the pointer interception, brings the layout into 100% conformity with `Inspirations/ui_reference_mockup.png`, and ensures flawless cold-load active styling.

---

## 8. Verification Method

To verify the findings and fix:

1. **Verify Pointer Interception Failure**:
   ```powershell
   $code = @'
   import socket, threading, time, uvicorn
   from playwright.sync_api import sync_playwright
   from server.api import create_app

   port = 8799
   app = create_app()
   server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
   threading.Thread(target=server.run, daemon=True).start()
   time.sleep(1)

   with sync_playwright() as p:
       page = p.chromium.launch(headless=True).new_page(viewport={"width": 1440, "height": 900})
       page.goto(f"http://127.0.0.1:{port}")
       page.locator("#btn-export-mesh").click(timeout=3000)
   server.should_exit = True
   '@
   $code | uv run --with playwright python -
   ```
   *Result*: Fails with `Locator.click: Timeout 3000ms exceeded ... som-tag-04 intercepts pointer events`.

2. **Verify Proposed Fix**:
   With `.som-tag-12, .som-tag-04 { bottom: 125px; }`, the script above completes in <100ms with exit code 0.

3. **Verify All Automated Tests**:
   ```powershell
   uv run --with pytest pytest tests/test_api.py -v
   uv run --with pytest,playwright pytest tests/test_browser_dom.py -v
   uv run --with pytest,playwright pytest tests/test_challenge_m2.py -v
   uv run --with pytest,playwright pytest tests/test_adversarial_m2.py -v
   ```
   *Expected*: All 45 tests pass.
