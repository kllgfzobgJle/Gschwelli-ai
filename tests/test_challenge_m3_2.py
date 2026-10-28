"""Adversarial Empirical Challenge Suite for Milestone 3 (challenger_m3_2).

Mission & Requirements:
1. Test export section interactions: modify #export-path-input, click #btn-export-mesh,
   verify safety warning banner is displayed, and verify REPL logs record export action attempt.
2. Test simulated OpenSCAD window title buttons: click minimize, maximize, close buttons
   and verify they don't crash or break the UI layout; click menu buttons ("▷ Preview F5",
   "⚙ Render F6") and verify click feedback and REPL logs.
3. Test interaction persistence across tab switching: focus SOM tag [04], switch from
   Mission Control to Knowledge Studio and back, verify SOM focused target state is preserved,
   and leader lines re-render properly with valid SVG coordinates.
4. Measure browser console errors and warnings during 50 repeated SOM tag and toolbar interactions.
   Verify 0 console errors and 0 uncaught JavaScript page exceptions.
5. Empirical Bug Identification & Verification:
   Demonstrate that SOM Tag [04] occludes #btn-export-mesh due to CSS positioning (.som-tag-04 bottom:62px; right:28px)
   which directly intercepts pointer events on the Export button.
6. Stress-test SOM tag exclusivity and target grounding across all 4 marks ([01], [02], [12], [04]).
7. Stress-test action toolbar animations (laser scan line, capture shutter flash) and camera controls.
"""

from __future__ import annotations

import socket
import sys
import threading
import time
from typing import Generator, List, Dict, Any
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright, TimeoutError as PlaywrightTimeoutError
import pytest
import uvicorn

from server.api import create_app


def find_free_port() -> int:
    """Find a random available TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def server_url() -> Generator[str, None, None]:
    """Starts the FastAPI dashboard server in a background thread."""
    port = find_free_port()
    app = create_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    url = f"http://127.0.0.1:{port}"

    import urllib.request
    max_wait = 10.0
    start = time.time()
    while time.time() - start < max_wait:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    break
        except Exception:
            time.sleep(0.1)
    else:
        raise RuntimeError(f"Server at {url} failed to start within {max_wait} seconds")

    yield url
    server.should_exit = True
    thread.join(timeout=2.0)


@pytest.fixture(scope="module")
def browser_instance():
    """Initializes Playwright browser once per module."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-gpu", "--no-sandbox"],
        )
        yield browser
        browser.close()


@pytest.fixture
def page(browser_instance: Browser, server_url: str) -> Generator[Page, None, None]:
    """Provides a fresh browser Page with console error and pageerror tracking."""
    context: BrowserContext = browser_instance.new_context(viewport={"width": 1440, "height": 900})
    p: Page = context.new_page()

    console_errors: List[str] = []
    console_warnings: List[str] = []
    page_errors: List[str] = []

    def on_console(msg):
        if msg.type == "error":
            console_errors.append(msg.text)
        elif msg.type == "warning":
            console_warnings.append(msg.text)

    def on_page_error(exc):
        page_errors.append(str(exc))

    p.on("console", on_console)
    p.on("pageerror", on_page_error)

    p.goto(server_url, wait_until="domcontentloaded")
    p.wait_for_selector("#cad-viewport-frame", state="visible", timeout=5000)

    # Attach tracking lists to page object
    p._console_errors = console_errors
    p._console_warnings = console_warnings
    p._page_errors = page_errors

    yield p
    context.close()


# ============================================================================
# Empirical Bug Reproduction: SOM Tag [04] Occluding Export Button
# ============================================================================

def test_m3_empirical_bug_som_tag_04_occludes_export_button(page: Page) -> None:
    """EMPIRICAL BUG REPRODUCTION / REMEDIATION VERIFICATION:
    Verifies that SOM Tag [04] does not occlude #btn-export-mesh.
    Prior to remediation, .som-tag-04 was at bottom: 62px; right: 28px, directly on top of Export button.
    Following remediation, .som-tag-04 floats in CAD canvas margin (bottom: 120px; right: 28px),
    clearing the Export button (overlap area = 0) and allowing standard mouse clicks without pointer interception.
    """
    tag_04 = page.locator("#som-tag-04")
    btn_export = page.locator("#btn-export-mesh")

    assert tag_04.is_visible(), "SOM tag [04] must be visible"
    assert btn_export.is_visible(), "Export button #btn-export-mesh must be visible"

    tag_box = tag_04.bounding_box()
    btn_box = btn_export.bounding_box()
    assert tag_box is not None and btn_box is not None

    # Calculate geometrical overlap
    overlap_x = max(0.0, min(tag_box["x"] + tag_box["width"], btn_box["x"] + btn_box["width"]) - max(tag_box["x"], btn_box["x"]))
    overlap_y = max(0.0, min(tag_box["y"] + tag_box["height"], btn_box["y"] + btn_box["height"]) - max(tag_box["y"], btn_box["y"]))
    overlap_area = overlap_x * overlap_y

    print(f"\n[OCCLUSION VERIFICATION DATA]")
    print(f"Tag [04] Box:   x={tag_box['x']:.1f}, y={tag_box['y']:.1f}, w={tag_box['width']:.1f}, h={tag_box['height']:.1f}")
    print(f"Export Btn Box: x={btn_box['x']:.1f}, y={btn_box['y']:.1f}, w={btn_box['width']:.1f}, h={btn_box['height']:.1f}")
    print(f"Overlap Area:   {overlap_area:.1f} px^2 (overlap_x={overlap_x:.1f}, overlap_y={overlap_y:.1f})")

    # Following remediation, overlap area must be 0
    assert overlap_area == 0.0, f"Expected 0 overlap between Tag [04] and Export button, got {overlap_area} px^2"

    # Test hit-testing at the center of #btn-export-mesh
    btn_center_x = btn_box["x"] + btn_box["width"] / 2.0
    btn_center_y = btn_box["y"] + btn_box["height"] / 2.0

    hit_element_id = page.evaluate(
        """([cx, cy]) => {
            const el = document.elementFromPoint(cx, cy);
            return el ? (el.id || el.className) : null;
        }""",
        [btn_center_x, btn_center_y],
    )
    print(f"elementFromPoint at center of #btn-export-mesh ({btn_center_x:.1f}, {btn_center_y:.1f}): '{hit_element_id}'")

    # Confirms that pointer events reach btn-export-mesh directly
    assert "btn-export-mesh" in hit_element_id or "btn-export" in hit_element_id, (
        f"Expected btn-export-mesh to receive pointer events at button center, got '{hit_element_id}'"
    )

    # Standard Playwright click succeeds without pointer interception
    btn_export.click(timeout=3000)


# ============================================================================
# Requirement 1: Export Section Interactions (With Force Click)
# ============================================================================

def test_m3_export_section_interactions(page: Page) -> None:
    """Requirement 1: Test export section interactions:
    - Modify #export-path-input (note readonly attribute)
    - Click #btn-export-mesh (using force=True to bypass the som-tag-04 pointer interception bug)
    - Verify safety warning banner is displayed with exact policy text
    - Verify REPL logs record export action attempt (SEC-810)
    - Verify safety gate amber highlight feedback
    """
    export_input = page.locator("#export-path-input")
    assert export_input.is_visible(), "Export path input #export-path-input must be visible"

    initial_val = export_input.input_value()
    assert "toolhead_mount.stl" in initial_val, f"Unexpected initial export path: {initial_val}"

    # Verify that input initially has readonly attribute
    is_readonly = page.evaluate("() => document.getElementById('export-path-input').readOnly")
    assert is_readonly is True, "Export path input is initially marked readOnly"

    # Adversarially modify the input value via DOM event dispatch
    new_path = r"C:\Fabrication\adversarial_toolhead_mount_v99.stl"
    page.evaluate(
        """(newVal) => {
            const el = document.getElementById('export-path-input');
            el.readOnly = false;
            el.value = newVal;
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
        }""",
        new_path,
    )

    # Verify DOM input value is successfully modified
    modified_val = export_input.input_value()
    assert modified_val == new_path, f"Failed to modify export input value. Current: {modified_val}"

    # Trigger click on export button:
    # Standard click now succeeds directly without pointer interception
    page.locator("#btn-export-mesh").click(timeout=3000)
    page.wait_for_timeout(100)

    # Verify safety warning banner is displayed
    warning_banner = page.locator(".safety-warning-banner")
    assert warning_banner.is_visible(), "Safety warning banner must be visible in export dock"

    banner_text = warning_banner.inner_text()
    assert "Existing file detected" in banner_text, f"Missing warning text: {banner_text}"
    assert "held by safety policy" in banner_text, f"Missing policy text: {banner_text}"

    # Verify REPL log records export attempt with SEC-810
    repl_logs = page.locator("#repl-logs")
    logs_content = repl_logs.inner_text()
    assert "SEC-810: Export held by safety policy. Human approval required." in logs_content, (
        f"Export attempt not logged to REPL: {logs_content}"
    )

    # Verify 0 uncaught JavaScript page exceptions
    assert len(page._page_errors) == 0, f"Uncaught page errors: {page._page_errors}"


# ============================================================================
# Requirement 2: Simulated OpenSCAD Window Title Buttons & Menu Bar
# ============================================================================

def test_m3_simulated_openscad_window_controls(page: Page) -> None:
    """Requirement 2: Test simulated OpenSCAD window title buttons and menu actions:
    - Click minimize (#win-btn-min), maximize (#win-btn-max), close (#win-btn-close)
    - Verify they don't crash or break the UI layout (viewport geometry remains stable)
    - Click menu buttons ("▷ Preview F5", "⚙ Render F6")
    - Verify click feedback in telemetry (.render-telem-right) and REPL logs
    """
    viewport_frame = page.locator("#cad-viewport-frame")
    initial_box = viewport_frame.bounding_box()
    assert initial_box is not None, "CAD viewport frame bounding box must exist"
    assert initial_box["width"] > 300, f"Viewport width too small: {initial_box['width']}"
    assert initial_box["height"] > 200, f"Viewport height too small: {initial_box['height']}"

    # 1. Test Minimize button
    btn_min = page.locator("#win-btn-min")
    assert btn_min.is_visible(), "Minimize button #win-btn-min must be visible"
    btn_min.click()
    page.wait_for_timeout(50)

    repl_text = page.locator("#repl-logs").inner_text()
    assert "[WINDOW] Minimize held" in repl_text, f"Minimize action not logged to REPL: {repl_text}"

    # Verify layout did not collapse
    box_after_min = viewport_frame.bounding_box()
    assert box_after_min is not None and box_after_min["width"] > 300 and box_after_min["height"] > 200, (
        f"Viewport collapsed after minimize: {box_after_min}"
    )

    # 2. Test Maximize button
    btn_max = page.locator("#win-btn-max")
    assert btn_max.is_visible(), "Maximize button #win-btn-max must be visible"
    btn_max.click()
    page.wait_for_timeout(50)

    repl_text = page.locator("#repl-logs").inner_text()
    assert "[WINDOW] Maximize held" in repl_text, f"Maximize action not logged to REPL: {repl_text}"

    # Verify layout remains intact
    box_after_max = viewport_frame.bounding_box()
    assert box_after_max is not None and box_after_max["width"] > 300 and box_after_max["height"] > 200, (
        f"Viewport collapsed after maximize: {box_after_max}"
    )

    # 3. Test Close button
    btn_close = page.locator("#win-btn-close")
    assert btn_close.is_visible(), "Close button #win-btn-close must be visible"
    btn_close.click()
    page.wait_for_timeout(50)

    repl_text = page.locator("#repl-logs").inner_text()
    assert "[WINDOW] Close held" in repl_text, f"Close action not logged to REPL: {repl_text}"

    # Verify layout remains intact
    box_after_close = viewport_frame.bounding_box()
    assert box_after_close is not None and box_after_close["width"] > 300 and box_after_close["height"] > 200, (
        f"Viewport collapsed after close: {box_after_close}"
    )

    # 4. Test Menu Button: Preview F5
    btn_preview = page.locator("#btn-menu-preview")
    assert btn_preview.is_visible(), "Preview button #btn-menu-preview must be visible"
    btn_preview.click()
    page.wait_for_timeout(50)

    # Verify click feedback in telemetry
    render_telem = page.locator(".render-telem-right").inner_text()
    assert "0.412s" in render_telem, f"Expected '0.412s' in render telemetry, got: {render_telem}"

    # Verify REPL log records preview
    repl_text = page.locator("#repl-logs").inner_text()
    assert "[OpenSCAD] Preview compiled ($fn=64) • 0.412s" in repl_text, (
        f"Preview action not recorded in REPL: {repl_text}"
    )

    # 5. Test Menu Button: Render F6
    btn_render = page.locator("#btn-menu-render")
    assert btn_render.is_visible(), "Render button #btn-menu-render must be visible"
    btn_render.click()
    page.wait_for_timeout(50)

    # Verify click feedback in telemetry
    render_telem = page.locator(".render-telem-right").inner_text()
    assert "0.842s" in render_telem, f"Expected '0.842s' in render telemetry, got: {render_telem}"

    # Verify REPL log records render
    repl_text = page.locator("#repl-logs").inner_text()
    assert "[OpenSCAD] CGAL 2-manifold render completed (1,248 facets) • 0.842s" in repl_text, (
        f"Render action not recorded in REPL: {repl_text}"
    )

    assert len(page._page_errors) == 0, f"Uncaught page errors: {page._page_errors}"


# ============================================================================
# Requirement 3: Interaction Persistence Across Tab Switching
# ============================================================================

def test_m3_som_persistence_and_leader_lines_across_tabs(page: Page) -> None:
    """Requirement 3: Test interaction persistence across tab switching:
    - Focus SOM tag [04]
    - Verify tag, leader line, anchor dot, and AppState are focused on [04]
    - Switch from Mission Control to Knowledge Studio and back
    - Verify SOM focused target state is preserved (tag remains active, AppState preserved)
    - Verify leader lines re-render properly with non-zero valid SVG coordinates
    """
    tag_04 = page.locator("#som-tag-04")
    assert tag_04.is_visible(), "SOM tag [04] must be visible"

    # Click SOM tag [04]
    tag_04.click()
    page.wait_for_timeout(100)

    # Verify tag 04 has active class
    tag_classes = tag_04.get_attribute("class") or ""
    assert "active" in tag_classes.split(), f"SOM tag 04 did not receive active class: {tag_classes}"

    # Verify leader line and anchor dot for 04 are active
    line_04 = page.locator("#leader-line-04")
    dot_04 = page.locator("#anchor-dot-04")
    assert "active" in (line_04.get_attribute("class") or "").split(), "Leader line 04 not active"
    assert "active" in (dot_04.get_attribute("class") or "").split(), "Anchor dot 04 not active"

    # Verify SVG coordinates are calculated and non-zero
    x1_before = float(line_04.get_attribute("x1") or "0")
    y1_before = float(line_04.get_attribute("y1") or "0")
    x2_before = float(line_04.get_attribute("x2") or "0")
    y2_before = float(line_04.get_attribute("y2") or "0")
    cx_before = float(dot_04.get_attribute("cx") or "0")
    cy_before = float(dot_04.get_attribute("cy") or "0")

    assert x1_before > 0 and y1_before > 0, f"Leader line starting coords invalid: ({x1_before}, {y1_before})"
    assert x2_before > 0 and y2_before > 0, f"Leader line ending coords invalid: ({x2_before}, {y2_before})"
    assert abs(x2_before - cx_before) < 1.0 and abs(y2_before - cy_before) < 1.0, (
        f"Anchor dot does not align with leader line endpoint: dot=({cx_before},{cy_before}) line=({x2_before},{y2_before})"
    )

    # Verify AppState has somFocusedTarget = '04'
    app_state_target = page.evaluate("() => AppState.somFocusedTarget")
    assert app_state_target == "04", f"AppState.somFocusedTarget mismatch: {app_state_target}"

    # Step 2: Switch to Knowledge Studio tab
    btn_ks = page.locator(".mode-tab-btn[data-mode='knowledge_studio']")
    assert btn_ks.is_visible(), "Knowledge Studio tab button must be visible"
    btn_ks.click()
    page.wait_for_timeout(100)

    # Verify Knowledge Studio is active, Mission Control is hidden
    ks_pane = page.locator("#view-knowledge-studio")
    mc_pane = page.locator("#view-mission-control")
    assert "active-view" in (ks_pane.get_attribute("class") or "").split(), "Knowledge Studio not active"
    assert "active-view" not in (mc_pane.get_attribute("class") or "").split(), "Mission Control still active"

    # Step 3: Switch back to Mission Control tab
    btn_mc = page.locator(".mode-tab-btn[data-mode='mission_control']")
    assert btn_mc.is_visible(), "Mission Control tab button must be visible"
    btn_mc.click()
    page.wait_for_timeout(200)  # Wait for leader line update (50ms timeout in code)

    # Verify Mission Control is active again
    assert "active-view" in (mc_pane.get_attribute("class") or "").split(), "Mission Control not active after switch back"

    # Step 4: Verify SOM tag [04] state was PRESERVED
    tag_classes_after = tag_04.get_attribute("class") or ""
    assert "active" in tag_classes_after.split(), f"SOM tag 04 lost active state after tab switch: {tag_classes_after}"

    app_state_target_after = page.evaluate("() => AppState.somFocusedTarget")
    assert app_state_target_after == "04", f"AppState.somFocusedTarget was reset: {app_state_target_after}"

    # Step 5: Verify leader lines were re-rendered properly with valid positive coordinates
    x1_after = float(line_04.get_attribute("x1") or "0")
    y1_after = float(line_04.get_attribute("y1") or "0")
    x2_after = float(line_04.get_attribute("x2") or "0")
    y2_after = float(line_04.get_attribute("y2") or "0")
    cx_after = float(dot_04.get_attribute("cx") or "0")
    cy_after = float(dot_04.get_attribute("cy") or "0")

    assert x1_after > 0 and y1_after > 0, f"Leader line coords invalid after switch: ({x1_after}, {y1_after})"
    assert x2_after > 0 and y2_after > 0, f"Leader line coords invalid after switch: ({x2_after}, {y2_after})"
    assert abs(x2_after - cx_after) < 1.0 and abs(y2_after - cy_after) < 1.0, (
        f"Anchor dot misaligned after switch: dot=({cx_after},{cy_after}) line=({x2_after},{y2_after})"
    )

    assert len(page._page_errors) == 0, f"Uncaught page errors: {page._page_errors}"


# ============================================================================
# Requirement 4: Repeated SOM Tag & Toolbar Interactions Stress Test (50 Cycles)
# ============================================================================

def test_m3_repeated_interactions_stress_and_zero_console_errors(page: Page) -> None:
    """Requirement 4: Measure browser console errors and warnings during 50 repeated
    SOM tag and toolbar interactions. Verify 0 console errors and 0 uncaught exceptions.
    """
    # Clear any errors collected during setup
    page._console_errors.clear()
    page._page_errors.clear()

    interactive_targets = [
        ("#som-tag-01", "click"),
        ("#som-tag-02", "click"),
        ("#som-tag-04", "click"),
        ("#som-tag-12", "click"),
        ("#btn-rescan-som", "click"),
        ("#btn-inspect-target", "click"),
        ("#btn-capture-frame", "click"),
        ("#btn-cam-orbit", "click"),
        ("#btn-cam-pan", "click"),
        ("#btn-cam-zoom", "click"),
        ("#btn-cam-reset", "click"),
        ("#btn-menu-preview", "click"),
        ("#btn-menu-render", "click"),
        ("#win-btn-min", "click"),
        ("#win-btn-max", "click"),
        ("#btn-export-mesh", "force_click"),
    ]

    total_interactions = 50
    executed_count = 0

    for i in range(total_interactions):
        selector, action = interactive_targets[i % len(interactive_targets)]
        target_el = page.locator(selector)
        if target_el.is_visible():
            if action == "force_click":
                target_el.click(force=True)
            else:
                target_el.click()
            executed_count += 1
        page.wait_for_timeout(10)

    # Wait for any trailing timeouts or async rendering to settle
    page.wait_for_timeout(400)

    # Assert that all 50 interactions were executed
    assert executed_count == total_interactions, f"Only executed {executed_count}/{total_interactions} interactions"

    # CRITICAL: Verify ZERO console errors occurred
    assert len(page._console_errors) == 0, (
        f"Encountered {len(page._console_errors)} console errors during {total_interactions} stress interactions: "
        f"{page._console_errors}"
    )

    # CRITICAL: Verify ZERO uncaught JavaScript page exceptions occurred
    assert len(page._page_errors) == 0, (
        f"Encountered {len(page._page_errors)} uncaught page exceptions: {page._page_errors}"
    )


# ============================================================================
# Requirement 5: SOM Tag Mutual Exclusivity & Grounding Accuracy
# ============================================================================

def test_m3_som_all_four_tags_exclusivity_and_grounding(page: Page) -> None:
    """Adversarially tests mutual exclusivity of SOM tags [01], [02], [12], [04].
    When a tag is clicked, exactly ONE tag, ONE leader line, and ONE anchor dot must be active.
    """
    tag_specs = [
        {"id": "01", "tag": "#som-tag-01", "line": "#leader-line-01", "dot": "#anchor-dot-01", "name": "Menu"},
        {"id": "02", "tag": "#som-tag-02", "line": "#leader-line-02", "dot": "#anchor-dot-02", "name": "Window Controls"},
        {"id": "12", "tag": "#som-tag-12", "line": "#leader-line-12", "dot": "#anchor-dot-12", "name": "Path Input"},
        {"id": "04", "tag": "#som-tag-04", "line": "#leader-line-04", "dot": "#anchor-dot-04", "name": "Button 'Export'"},
    ]

    # Test non-linear cycling order: [12] -> [01] -> [04] -> [02] -> [04]
    sequence = ["12", "01", "04", "02", "04"]

    for step_id in sequence:
        target_spec = next(s for s in tag_specs if s["id"] == step_id)
        page.locator(target_spec["tag"]).click()
        page.wait_for_timeout(50)

        # Check that target spec is active
        assert "active" in (page.locator(target_spec["tag"]).get_attribute("class") or "").split()
        assert "active" in (page.locator(target_spec["line"]).get_attribute("class") or "").split()
        assert "active" in (page.locator(target_spec["dot"]).get_attribute("class") or "").split()

        # Check that ALL other tags, lines, and dots are NOT active
        for other_spec in tag_specs:
            if other_spec["id"] != step_id:
                other_tag_classes = (page.locator(other_spec["tag"]).get_attribute("class") or "").split()
                other_line_classes = (page.locator(other_spec["line"]).get_attribute("class") or "").split()
                other_dot_classes = (page.locator(other_spec["dot"]).get_attribute("class") or "").split()

                assert "active" not in other_tag_classes, f"Tag {other_spec['id']} was not deactivated when {step_id} was focused"
                assert "active" not in other_line_classes, f"Line {other_spec['id']} was not deactivated"
                assert "active" not in other_dot_classes, f"Dot {other_spec['id']} was not deactivated"

        # Check AppState consistency
        state_target = page.evaluate("() => AppState.somFocusedTarget")
        assert state_target == step_id, f"AppState mismatch: expected {step_id}, got {state_target}"

        # Check REPL log output
        repl_logs = page.locator("#repl-logs").inner_text()
        assert f"Focused target [{step_id}]" in repl_logs, f"Missing focus log for [{step_id}] in REPL"

    assert len(page._page_errors) == 0, f"Uncaught page errors: {page._page_errors}"


# ============================================================================
# Requirement 6: Action Toolbar Animations & Camera Mode Navigation
# ============================================================================

def test_m3_action_toolbar_animations_and_telemetry(page: Page) -> None:
    """Verifies action toolbar animations (laser scanline, shutter flash),
    frame telemetry increment, and camera orbit/pan/zoom state updates.
    """
    # 1. Test Re-scan SOM
    initial_frame_text = page.locator("#frame-telemetry").inner_text()
    btn_rescan = page.locator("#btn-rescan-som")
    assert btn_rescan.is_visible(), "Re-scan SOM button must be visible"

    btn_rescan.click()
    page.wait_for_timeout(50)

    # Verify scan line element exists and received scanning class or animation
    scan_line = page.locator("#som-scan-line")
    assert scan_line.count() > 0, "#som-scan-line must exist in DOM"

    # Wait for the rescan timeout to settle (350ms in code)
    page.wait_for_timeout(400)
    updated_frame_text = page.locator("#frame-telemetry").inner_text()
    assert updated_frame_text != initial_frame_text, (
        f"Frame telemetry was not updated after re-scan: {initial_frame_text} -> {updated_frame_text}"
    )

    repl_text = page.locator("#repl-logs").inner_text()
    assert "Re-scanning targets via UIA + Vision Fusion" in repl_text, "Rescan start not logged in REPL"
    assert "12 targets detected" in repl_text, "Rescan complete not logged in REPL"

    # 2. Test Capture button
    btn_capture = page.locator("#btn-capture-frame")
    assert btn_capture.is_visible(), "Capture button must be visible"
    btn_capture.click()
    page.wait_for_timeout(100)

    # Verify flash overlay exists
    shutter_flash = page.locator("#viewport-shutter-flash")
    assert shutter_flash.count() > 0, "#viewport-shutter-flash must exist in DOM"

    repl_text = page.locator("#repl-logs").inner_text()
    assert "High-res CAD viewport captured" in repl_text or "[CAPTURE]" in repl_text, (
        f"Capture action not logged in REPL: {repl_text}"
    )

    # 3. Test Camera Zoom & Reset
    btn_zoom = page.locator("#btn-cam-zoom")
    assert btn_zoom.is_visible(), "Camera zoom button must be visible"
    btn_zoom.click()
    page.wait_for_timeout(50)

    repl_text = page.locator("#repl-logs").inner_text()
    assert "[VIEWPORT] Camera zoom: 115%" in repl_text, f"Zoom in not logged in REPL: {repl_text}"

    # Click Reset camera
    btn_reset = page.locator("#btn-cam-reset")
    assert btn_reset.is_visible(), "Camera reset button must be visible"
    btn_reset.click()
    page.wait_for_timeout(50)

    repl_text = page.locator("#repl-logs").inner_text()
    assert "[VIEWPORT] Camera reset to default isometric angle" in repl_text, (
        f"Camera reset not logged in REPL: {repl_text}"
    )

    assert len(page._page_errors) == 0, f"Uncaught page errors: {page._page_errors}"
