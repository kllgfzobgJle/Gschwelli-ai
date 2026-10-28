"""Adversarial and behavioral review verification suite for Milestone 3.

Stress tests:
1. Dynamic SOM leader line calculations and coordinate validity.
2. Clicking tags [01, 02, 04, 12] transitions, target highlight rings, and exact REPL logging.
3. Camera navigation controls (orbit, pan, zoom, reset) and SVG transform styling.
4. Toolbar buttons (Re-scan laser sweep, Capture camera flash, Inspect target).
5. OpenSCAD window controls, menu items (Preview F5, Render F6), and Export action.
6. Responsive layout integrity and zero horizontal overflow at 1440x900 and 1024x768.
7. Tab isolation and CSS specificity when switching between Mission Control and other views.
"""

import re
import pytest
from playwright.sync_api import Page, expect
from tests.test_browser_dom import server_url, playwright_instance, browser, page


def test_som_leader_lines_dynamic_coordinates(page: Page) -> None:
    """Verify that updateSomLeaderLines calculates valid dynamic coordinates on load and resize."""
    page.wait_for_load_state("networkidle")

    # Check leader line SVG coordinates are valid numbers and not (0,0,0,0)
    lines_data = page.evaluate("""() => {
        const pairs = ['01', '02', '12', '04'];
        return pairs.map(id => {
            const line = document.getElementById(`leader-line-${id}`);
            const dot = document.getElementById(`anchor-dot-${id}`);
            return {
                id,
                x1: parseFloat(line.getAttribute('x1') || '0'),
                y1: parseFloat(line.getAttribute('y1') || '0'),
                x2: parseFloat(line.getAttribute('x2') || '0'),
                y2: parseFloat(line.getAttribute('y2') || '0'),
                cx: parseFloat(dot.getAttribute('cx') || '0'),
                cy: parseFloat(dot.getAttribute('cy') || '0'),
            };
        });
    }""")

    for line in lines_data:
        assert line["x1"] > 0, f"Leader line {line['id']} x1 is not positive: {line['x1']}"
        assert line["y1"] > 0, f"Leader line {line['id']} y1 is not positive: {line['y1']}"
        assert line["x2"] > 0, f"Leader line {line['id']} x2 is not positive: {line['x2']}"
        assert line["y2"] > 0, f"Leader line {line['id']} y2 is not positive: {line['y2']}"
        assert abs(line["x2"] - line["cx"]) < 0.01, f"Dot cx does not match line x2 for {line['id']}"
        assert abs(line["y2"] - line["cy"]) < 0.01, f"Dot cy does not match line y2 for {line['id']}"


def test_som_tags_click_transitions_and_repl_logging(page: Page) -> None:
    """Verify that clicking tags ([01], [02], [04], [12]) produces clean transitions and REPL logs."""
    page.wait_for_load_state("networkidle")

    tag_cases = [
        ("som-tag-01", "01", "leader-line-01", "anchor-dot-01", "target-menubar", "Focused target [01] (Menu)"),
        ("som-tag-02", "02", "leader-line-02", "anchor-dot-02", "target-window-actions", "Focused target [02] (Window Controls)"),
        ("som-tag-12", "12", "leader-line-12", "anchor-dot-12", "export-path-input", "Focused target [12] (Path Input)"),
        ("som-tag-04", "04", "leader-line-04", "anchor-dot-04", "btn-export-mesh", "Focused target [04] (Button 'Export')"),
    ]

    for tag_id, padded_id, line_id, dot_id, target_id, expected_log in tag_cases:
        tag_el = page.locator(f"#{tag_id}")
        tag_el.click()
        page.wait_for_timeout(100)

        # Check tag is active
        expect(tag_el).to_have_class(re.compile(r"active"))

        # Check line and dot are active
        line_el = page.locator(f"#{line_id}")
        dot_el = page.locator(f"#{dot_id}")
        expect(line_el).to_have_class(re.compile(r"active"))
        expect(dot_el).to_have_class(re.compile(r"active"))

        # Check target has highlight ring
        target_el = page.locator(f"#{target_id}")
        expect(target_el).to_have_class(re.compile(r"target-highlight-ring"))

        # Check REPL has logged the focus event
        repl_logs = page.locator("#repl-logs")
        expect(repl_logs).to_contain_text(expected_log)


def test_camera_navigation_controls_transform(page: Page) -> None:
    """Verify camera controls (Orbit, Pan, Zoom, Reset) manipulate SVG CAD viewport without breaking."""
    page.wait_for_load_state("networkidle")

    mesh_group = page.locator("#cad-mesh-group")
    btn_zoom = page.locator("#btn-cam-zoom")
    btn_reset = page.locator("#btn-cam-reset")
    btn_orbit = page.locator("#btn-cam-orbit")
    btn_pan = page.locator("#btn-cam-pan")

    # Zoom in
    btn_zoom.click()
    page.wait_for_timeout(100)
    transform = mesh_group.evaluate("el => el.style.transform")
    assert "scale(1.15)" in transform, f"Expected zoom scale(1.15), got {transform}"

    # Zoom out (toggle back)
    btn_zoom.click()
    page.wait_for_timeout(100)
    transform = mesh_group.evaluate("el => el.style.transform")
    assert "scale(1)" in transform, f"Expected zoom scale(1), got {transform}"

    # Zoom again then Reset
    btn_zoom.click()
    page.wait_for_timeout(100)
    btn_reset.click()
    page.wait_for_timeout(100)
    transform = mesh_group.evaluate("el => el.style.transform")
    assert "scale(1)" in transform, f"Expected reset scale(1), got {transform}"
    expect(btn_orbit).to_have_class(re.compile(r"active"))

    # Test Pan activation
    btn_pan.click()
    page.wait_for_timeout(100)
    expect(btn_pan).to_have_class(re.compile(r"active"))


def test_toolbar_actions_and_animations(page: Page) -> None:
    """Verify Re-scan SOM laser sweep, Inspect target, and Capture shutter flash animations."""
    page.wait_for_load_state("networkidle")

    # Re-scan SOM
    frame_before = page.locator("#frame-telemetry").inner_text()
    page.click("#btn-rescan-som")
    page.wait_for_timeout(450)
    frame_after = page.locator("#frame-telemetry").inner_text()
    assert frame_before != frame_after, f"Frame telemetry did not increment: {frame_before} vs {frame_after}"
    expect(page.locator("#repl-logs")).to_contain_text("Re-scanning targets")

    # Inspect target
    page.click("#btn-inspect-target")
    page.wait_for_timeout(100)
    expect(page.locator("#repl-logs")).to_contain_text("[INSPECT] Grounded target")

    # Capture frame
    page.click("#btn-capture-frame")
    page.wait_for_timeout(100)
    expect(page.locator("#repl-logs")).to_contain_text("[CAPTURE] Frame")


def test_openscad_window_and_export_dock_interactions(page: Page) -> None:
    """Verify Menu Preview F5, Render F6, Window buttons, and Export held warning."""
    page.wait_for_load_state("networkidle")

    # Menu Preview
    page.click("#btn-menu-preview")
    page.wait_for_timeout(100)
    expect(page.locator("#repl-logs")).to_contain_text("Preview compiled")

    # Menu Render
    page.click("#btn-menu-render")
    page.wait_for_timeout(100)
    expect(page.locator("#repl-logs")).to_contain_text("CGAL 2-manifold render completed")

    # Window close button held in sandbox
    page.click("#win-btn-close")
    page.wait_for_timeout(100)
    expect(page.locator("#repl-logs")).to_contain_text("OpenSCAD viewport locked in sandboxed focus mode")

    # Check export button click with force or check whether som-tag-04 intercepts it
    btn_export = page.locator("#btn-export-mesh")
    # Using dispatch_event or force=True to trigger click listener
    btn_export.dispatch_event("click")
    page.wait_for_timeout(100)
    expect(page.locator("#repl-logs")).to_contain_text("SEC-810: Export held by safety policy")


def test_tab_isolation_and_leader_line_graceful_handling(page: Page) -> None:
    """Verify that switching tabs hides mission control and does not crash leader line calculations."""
    page.wait_for_load_state("networkidle")

    # Switch away to Vision SOM
    page.click('.mode-tab-btn[data-mode="vision_som"]')
    page.wait_for_timeout(200)

    mc_display = page.evaluate("() => window.getComputedStyle(document.getElementById('view-mission-control')).display")
    assert mc_display == "none", f"Expected #view-mission-control to be 'none', got '{mc_display}'"

    # Manually trigger resize while hidden - updateSomLeaderLines should safely return early
    page.evaluate("() => window.dispatchEvent(new Event('resize'))")
    page.wait_for_timeout(100)

    # Switch back to Mission Control
    page.click('.mode-tab-btn[data-mode="mission_control"]')
    page.wait_for_timeout(200)

    mc_display_back = page.evaluate("() => window.getComputedStyle(document.getElementById('view-mission-control')).display")
    assert mc_display_back == "grid", f"Expected #view-mission-control to be 'grid', got '{mc_display_back}'"

    assert len(page._page_errors) == 0, f"Errors during tab switching/leader line update: {page._page_errors}"


@pytest.mark.parametrize("width,height", [
    (1440, 900),
    (1024, 768),
    (1920, 1080),
])
def test_responsive_layout_no_overflow_m3(page: Page, width: int, height: int) -> None:
    """Verify responsive viewport integrity and zero horizontal overflow at baseline and compact sizes."""
    page.set_viewport_size({"width": width, "height": height})
    page.wait_for_timeout(150)

    metrics = page.evaluate("""() => {
        const root = document.documentElement;
        const body = document.body;
        const app = document.getElementById('app-container');
        const canvas = document.getElementById('cad-canvas');
        const frame = document.getElementById('cad-viewport-frame');

        return {
            windowInnerWidth: window.innerWidth,
            windowInnerHeight: window.innerHeight,
            rootScrollWidth: root.scrollWidth,
            rootClientWidth: root.clientWidth,
            bodyScrollWidth: body.scrollWidth,
            bodyClientWidth: body.clientWidth,
            appScrollWidth: app.scrollWidth,
            appClientWidth: app.clientWidth,
            canvasHeight: canvas ? canvas.getBoundingClientRect().height : 0,
            frameHeight: frame ? frame.getBoundingClientRect().height : 0,
        };
    }""")

    assert metrics["rootScrollWidth"] <= metrics["rootClientWidth"], (
        f"Horizontal overflow at {width}x{height}: root scrollWidth {metrics['rootScrollWidth']} > clientWidth {metrics['rootClientWidth']}"
    )
    assert metrics["appScrollWidth"] <= metrics["appClientWidth"], (
        f"Horizontal overflow at {width}x{height}: app scrollWidth {metrics['appScrollWidth']} > clientWidth {metrics['appClientWidth']}"
    )
    assert metrics["canvasHeight"] > 100, f"CAD canvas collapsed at {width}x{height}: height={metrics['canvasHeight']}"
    assert metrics["frameHeight"] > 200, f"CAD frame collapsed at {width}x{height}: height={metrics['frameHeight']}"


def test_som_tags_occlusion_audit(page: Page) -> None:
    """Audit whether SOM callout tags overlap their target elements and intercept pointer clicks."""
    page.wait_for_load_state("networkidle")

    pairs = [
        ("#som-tag-01", "#target-menubar"),
        ("#som-tag-02", "#target-window-actions"),
        ("#som-tag-12", "#export-path-input"),
        ("#som-tag-04", "#btn-export-mesh"),
    ]

    overlaps = {}
    for tag_id, target_id in pairs:
        tag_b = page.locator(tag_id).bounding_box()
        tgt_b = page.locator(target_id).bounding_box()
        overlap_x = max(0, min(tag_b['x'] + tag_b['width'], tgt_b['x'] + tgt_b['width']) - max(tag_b['x'], tgt_b['x']))
        overlap_y = max(0, min(tag_b['y'] + tag_b['height'], tgt_b['y'] + tgt_b['height']) - max(tag_b['y'], tgt_b['y']))
        overlap_area = overlap_x * overlap_y
        overlaps[f"{tag_id} -> {target_id}"] = overlap_area

    # Document the overlapping tags:
    print(f"SOM Tag Overlap Areas: {overlaps}")
    # Following remediation, Tag 04 and Tag 12 float cleanly with 0 overlap on export controls
    assert overlaps["#som-tag-04 -> #btn-export-mesh"] == 0.0, f"Expected 0 overlap on Tag 04, got {overlaps['#som-tag-04 -> #btn-export-mesh']}"
    assert overlaps["#som-tag-12 -> #export-path-input"] == 0.0, f"Expected 0 overlap on Tag 12, got {overlaps['#som-tag-12 -> #export-path-input']}"
