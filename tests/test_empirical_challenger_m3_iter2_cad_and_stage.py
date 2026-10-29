"""Empirical Challenger Verification & Adversarial Stress Suite for Milestone 3 Iteration 2.

Focuses on:
1. Rigorous static empirical scan of ui/dashboard/index.html and server/api.py for forbidden CAD tokens
   ('openscad', 'toolhead_mount', 'cgal', 'facet-base', 'bolt holes', 'csg-overlay', 'axis-gizmo') -> strictly 0 occurrences.
2. Viewport 1 Set-of-Marks (SoM) perception:
   - Full mark set [01]–[12] presence and visibility.
   - Strictly 0.0 px² pointer occlusion against interactive controls across 1024x768, 1440x900, 1920x1080.
   - elementFromPoint pass-through verification for critical UI elements.
   - Camera toolbar controls (zoom in, zoom out, pan, orbit, focus/inspector toggle, reset) functioning without console errors.
   - Direct tag clicking activating target states without console errors.
3. Split-Screen rapid toggle stress harness:
   - Sequential and random switching between Viewport 1, 2, 3, 4.
   - Split-screen 50/50 activation and right-pane switching.
   - Rapid-fire switching stress loop ensuring 0 DOM crashes, 0 page errors, and active listeners.
   - Post-stress verification that interactive elements remain responsive.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Generator, List

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, expect

from tests.test_browser_dom import browser, page, playwright_instance, server_url


# ==============================================================================
# SECTION 1: EMPIRICAL SCAN FOR FORBIDDEN CAD TOKENS
# ==============================================================================

FORBIDDEN_CAD_TOKENS = [
    "openscad",
    "toolhead_mount",
    "cgal",
    "facet-base",
    "bolt holes",
    "csg-overlay",
    "axis-gizmo",
]


@pytest.mark.parametrize("rel_path", [
    "ui/dashboard/index.html",
    "server/api.py",
])
def test_empirical_scan_zero_cad_tokens(rel_path: str):
    """Empirically verify 0 occurrences of forbidden CAD tokens in source files."""
    file_path = Path(__file__).resolve().parent.parent / rel_path
    assert file_path.exists(), f"Target file does not exist: {file_path}"

    content = file_path.read_text(encoding="utf-8").lower()
    token_counts = {token: content.count(token) for token in FORBIDDEN_CAD_TOKENS}
    total_tokens = sum(token_counts.values())

    print(f"\n[CAD TOKEN SCAN] {rel_path}: {token_counts} (Total: {total_tokens})")
    assert total_tokens == 0, (
        f"Forbidden CAD tokens detected in {rel_path}: "
        f"{ {k: v for k, v in token_counts.items() if v > 0} }"
    )


# ==============================================================================
# SECTION 2: VIEWPORT 1 SET-OF-MARKS (SoM) PERCEPTION & NON-OCCLUSION
# ==============================================================================

@pytest.mark.parametrize("width,height,res_name", [
    (1024, 768, "1024x768"),
    (1440, 900, "1440x900"),
    (1920, 1080, "1920x1080"),
])
def test_som_marks_presence_and_zero_pointer_occlusion(browser: Browser, server_url: str, width: int, height: int, res_name: str):
    """Verify all 12 marks [01]–[12] exist, are visible in Viewport 1, and have 0.0 px² pointer occlusion."""
    context: BrowserContext = browser.new_context(viewport={"width": width, "height": height})
    p: Page = context.new_page()

    console_errors: List[str] = []
    page_errors: List[str] = []
    p.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    p.on("pageerror", lambda exc: page_errors.append(str(exc)))

    p.goto(server_url, wait_until="networkidle")
    p.wait_for_timeout(200)

    # 1. Verify Viewport 1 is active
    vp1 = p.locator("#viewport-1")
    expect(vp1).to_be_visible()

    # 2. Verify all 12 tags exist and are visible
    for i in range(1, 13):
        tag_id = f"som-tag-{i:02d}"
        tag_el = p.locator(f"#{tag_id}")
        assert tag_el.is_visible(), f"[{res_name}] Tag #{tag_id} is not visible in Viewport 1"
        text = tag_el.inner_text()
        assert f"[{i:02d}" in text, f"[{res_name}] Tag #{tag_id} text '{text}' does not contain '[{i:02d}'"

    # 3. Geometric Bounding Box & Pointer Occlusion Check
    occlusion_metrics = p.evaluate("""() => {
        function getBox(id) {
            const el = document.getElementById(id);
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return { x: r.left, y: r.top, width: r.width, height: r.height, right: r.right, bottom: r.bottom };
        }
        function overlapArea(b1, b2) {
            if (!b1 || !b2) return 0.0;
            const ox = Math.max(0.0, Math.min(b1.right, b2.right) - Math.max(b1.x, b2.x));
            const oy = Math.max(0.0, Math.min(b1.bottom, b2.bottom) - Math.max(b1.y, b2.y));
            return ox * oy;
        }

        const btnExport = getBox('btn-export-mesh');
        const pathInput = getBox('export-path-input');
        const menubar = getBox('target-menubar');

        const tagBoxes = {};
        const overlaps = {};

        for (let i = 1; i <= 12; i++) {
            const id = 'som-tag-' + String(i).padStart(2, '0');
            const box = getBox(id);
            tagBoxes[id] = box;
            overlaps[id] = {
                btnOverlap: overlapArea(box, btnExport),
                inputOverlap: overlapArea(box, pathInput),
                menubarOverlap: overlapArea(box, menubar)
            };
        }

        return {
            btnExport,
            pathInput,
            menubar,
            tagBoxes,
            overlaps
        };
    }""")

    assert occlusion_metrics["btnExport"] is not None, f"[{res_name}] #btn-export-mesh not found in DOM"
    assert occlusion_metrics["pathInput"] is not None, f"[{res_name}] #export-path-input not found in DOM"
    assert occlusion_metrics["menubar"] is not None, f"[{res_name}] #target-menubar not found in DOM"

    # Verify strictly 0.0 px² pointer occlusion for every tag against interactive targets
    for tag_id, ov in occlusion_metrics["overlaps"].items():
        assert ov["btnOverlap"] == 0.0, (
            f"[{res_name}] {tag_id} occludes #btn-export-mesh by {ov['btnOverlap']:.2f} px²"
        )
        assert ov["inputOverlap"] == 0.0, (
            f"[{res_name}] {tag_id} occludes #export-path-input by {ov['inputOverlap']:.2f} px²"
        )
        assert ov["menubarOverlap"] == 0.0, (
            f"[{res_name}] {tag_id} occludes #target-menubar by {ov['menubarOverlap']:.2f} px²"
        )

    # 4. elementFromPoint Direct Hit Verification
    pt_checks = p.evaluate("""() => {
        function getHitId(id) {
            const el = document.getElementById(id);
            if (!el) return null;
            const r = el.getBoundingClientRect();
            const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
            return hit ? (hit.id || hit.tagName) : null;
        }
        return {
            btnHit: getHitId('btn-export-mesh'),
            inputHit: getHitId('export-path-input')
        };
    }""")

    assert pt_checks["btnHit"] in ["btn-export-mesh", "svg", "polygon"], (
        f"[{res_name}] elementFromPoint at center of #btn-export-mesh intercepted by '{pt_checks['btnHit']}'"
    )
    assert pt_checks["inputHit"] == "export-path-input", (
        f"[{res_name}] elementFromPoint at center of #export-path-input intercepted by '{pt_checks['inputHit']}'"
    )

    # Check console errors
    assert len(console_errors) == 0, f"[{res_name}] Console errors: {console_errors}"
    assert len(page_errors) == 0, f"[{res_name}] Page errors: {page_errors}"
    context.close()


def test_camera_toolbar_controls_and_tag_focus(page: Page):
    """Verify camera toolbar controls (orbit, pan, zoom, zoom-out, focus/inspector, reset) and tag click focus."""
    page.wait_for_load_state("networkidle")

    # 1. Camera Zoom In
    btn_zoom = page.locator("#btn-cam-zoom")
    btn_zoom.click()
    page.wait_for_timeout(100)
    transform_after_zoom = page.evaluate("() => document.getElementById('cad-mesh-group')?.style.transform")
    assert "scale" in (transform_after_zoom or ""), f"Expected scale transform after zoom in, got: {transform_after_zoom}"

    # 2. Camera Zoom Out
    btn_zoom_out = page.locator("#btn-cam-zoom-out")
    btn_zoom_out.click()
    page.wait_for_timeout(100)
    # AppState scale or group transform updated without error

    # 3. Camera Pan
    btn_pan = page.locator("#btn-cam-pan")
    btn_pan.click()
    page.wait_for_timeout(100)
    expect(btn_pan).to_have_class(re.compile(r"active"))

    # 4. Camera Orbit
    btn_orbit = page.locator("#btn-cam-orbit")
    btn_orbit.click()
    page.wait_for_timeout(100)
    expect(btn_orbit).to_have_class(re.compile(r"active"))

    # 5. Inspector / Focus Toggle
    btn_inspector = page.locator("#btn-inspector-toggle")
    btn_inspector.click()
    page.wait_for_timeout(100)
    frame = page.locator("#cad-viewport-frame")
    expect(frame).to_have_class(re.compile(r"inspection-mode"))
    # Toggle back
    btn_inspector.click()
    page.wait_for_timeout(100)
    expect(frame).not_to_have_class(re.compile(r"inspection-mode"))

    # 6. Camera Reset
    btn_reset = page.locator("#btn-cam-reset")
    btn_reset.click()
    page.wait_for_timeout(100)
    expect(btn_orbit).to_have_class(re.compile(r"active"))
    transform_after_reset = page.evaluate("() => document.getElementById('cad-mesh-group')?.style.transform")
    assert "scale(1)" in (transform_after_reset or ""), f"Expected scale(1) after reset, got: {transform_after_reset}"

    # 7. Focus SoM Targets [01] to [12]
    for i in range(1, 13):
        tag_id = f"som-tag-{i:02d}"
        tag_el = page.locator(f"#{tag_id}")
        tag_el.click()
        page.wait_for_timeout(50)
        expect(tag_el).to_have_class(re.compile(r"active"))
        # Active tag count must be exactly 1
        active_count = page.evaluate("() => document.querySelectorAll('.som-tag.active').length")
        assert active_count == 1, f"Expected exactly 1 active som-tag after clicking {tag_id}, got {active_count}"

    # Verify zero console errors
    assert len(page._console_errors) == 0, f"Console errors during camera controls: {page._console_errors}"
    assert len(page._page_errors) == 0, f"Page errors during camera controls: {page._page_errors}"


# ==============================================================================
# SECTION 3: SPLIT-SCREEN & POLYMORPHIC VIEWPORTS RAPID TOGGLE STRESS
# ==============================================================================

def test_split_screen_and_viewports_rapid_toggle_stress(page: Page):
    """Stress-test rapid viewport switching (1->2->3->4) and split-screen toggling.
    Verifies no DOM exceptions, no detached listeners, and correct post-stress state.
    """
    page.wait_for_load_state("networkidle")

    # A. Sequential tab switching 1 -> 2 -> 3 -> 4 -> 1
    for vp in ["2", "3", "4", "1"]:
        tab_btn = page.locator(f".viewport-tab-btn[data-viewport='{vp}']")
        tab_btn.click()
        page.wait_for_timeout(80)
        panel = page.locator(f"#viewport-{vp}")
        expect(panel).to_have_class(re.compile(r"active"))

    # B. Split-Screen Toggle ON
    split_btn = page.locator("#btn-split-screen")
    split_btn.click()
    page.wait_for_timeout(100)

    container = page.locator("#stage-viewports-container")
    expect(container).to_have_class(re.compile(r"split-screen-active"))
    expect(page.locator("#viewport-1")).to_have_class(re.compile(r"split-left"))

    # While in split-screen mode, switch right pane across viewports 2, 3, 4
    for vp in ["2", "3", "4"]:
        page.locator(f".viewport-tab-btn[data-viewport='{vp}']").click()
        page.wait_for_timeout(60)
        expect(page.locator(f"#viewport-{vp}")).to_have_class(re.compile(r"split-right"))

    # Toggle Split-Screen OFF
    split_btn.click()
    page.wait_for_timeout(100)
    expect(container).not_to_have_class(re.compile(r"split-screen-active"))

    # C. Adversarial Rapid Toggle Stress Loop (30 rapid transitions)
    # Alternate between viewports and split-screen states
    import random
    random.seed(42)

    for step in range(30):
        action = random.choice(["switch_vp", "toggle_split"])
        if action == "switch_vp":
            vp_target = random.choice(["1", "2", "3", "4"])
            page.locator(f".viewport-tab-btn[data-viewport='{vp_target}']").click()
        else:
            split_btn.click()
        page.wait_for_timeout(30)

    # D. Recovery & Post-Stress Verification
    # Ensure split-screen is OFF and we are on Viewport 1
    is_split = page.evaluate("() => document.getElementById('stage-viewports-container')?.classList.contains('split-screen-active')")
    if is_split:
        split_btn.click()
        page.wait_for_timeout(100)

    page.locator(".viewport-tab-btn[data-viewport='1']").click()
    page.wait_for_timeout(100)

    # 1. Viewport 1 SoM tags still responsive
    tag_04 = page.locator("#som-tag-04")
    tag_04.click()
    page.wait_for_timeout(50)
    expect(tag_04).to_have_class(re.compile(r"active"))

    # 2. Viewport 2 Document Studio still responsive
    page.locator(".viewport-tab-btn[data-viewport='2']").click()
    page.wait_for_timeout(100)
    # Check that studio sub-views work
    btn_code = page.locator("#btn-view-code")
    btn_code.click()
    page.wait_for_timeout(50)
    expect(page.locator("#ks-code-studio")).to_be_visible()

    btn_grid = page.locator("#btn-view-grid")
    btn_grid.click()
    page.wait_for_timeout(50)
    expect(page.locator("#ks-data-grid-studio")).to_be_visible()

    # 3. Viewport 4 Terminal still responsive
    page.locator(".viewport-tab-btn[data-viewport='4']").click()
    page.wait_for_timeout(100)
    term_input = page.locator("#terminal-active-input")
    expect(term_input).to_be_visible()
    term_input.fill("echo test_post_stress")
    term_input.press("Enter")
    page.wait_for_timeout(100)

    # Verify zero console errors and zero uncaught exceptions during the entire stress run
    assert len(page._console_errors) == 0, f"Console errors during rapid toggle stress: {page._console_errors}"
    assert len(page._page_errors) == 0, f"Page errors during rapid toggle stress: {page._page_errors}"
