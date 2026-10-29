"""Empirical Challenger Test Suite for Milestone 3 (challenger_m3_v2_1).

Adversarially tests and verifies:
1. Pointer Occlusion & Geometry:
   - Strictly 0.0 px² bounding box overlap between all SOM tags [01]..[12] and #btn-export-mesh / #export-path-input.
   - Multi-resolution verification at 1024x768, 1440x900, and 1920x1080.
2. elementFromPoint Hit-Testing:
   - Center of #btn-export-mesh receives clicks directly without interception.
   - Center of #export-path-input receives clicks directly.
   - Center of camera toolbar buttons (#btn-cam-orbit, #btn-cam-pan, #btn-cam-zoom, #btn-cam-zoom-out, #btn-cam-reset) receive clicks directly.
   - Action buttons (#btn-rescan-som, #btn-inspect-target, #btn-capture-frame) receive clicks directly.
3. SOM Perception & Tags [01] through [12]:
   - All 12 SOM tags [01]..[12] exist and are clickable.
   - Mutual exclusivity: exactly 1 tag active at any time.
   - Rapid sequential and burst clicking across all 12 tags without error or state corruption.
   - Leader line SVG rendering and dynamic coordinate recalculation.
4. Camera Toolbar Navigation & Coordinates HUD:
   - Orbit, Pan, Zoom In, Zoom Out, and Reset buttons.
   - Verification of transform attributes and AppState.canvasScale.
   - Coordinates HUD update on mousemove (e.g. X: 350 px • Y: 220 px) and mouseleave (X: 000 px • Y: 000 px).
5. Multi-Resolution Layout Stability:
   - 1024x768, 1440x900, 1920x1080 viewports.
   - Zero horizontal/vertical layout scroll overflow.
6. Browser Stability:
   - 0 console errors and 0 uncaught page exceptions.
"""

from __future__ import annotations

import math
from pathlib import Path
import socket
import sys
import threading
import time
from typing import Generator, List, Dict, Any

import pytest
import uvicorn
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from server.api import create_app


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def app_server():
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
        raise RuntimeError(f"Server at {url} failed to start within {max_wait}s")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-gpu", "--no-sandbox"])
        yield {"url": url, "port": port, "browser": browser}
        browser.close()

    server.should_exit = True
    thread.join(timeout=2.0)


@pytest.fixture
def fresh_page(app_server) -> Generator[Page, None, None]:
    browser: Browser = app_server["browser"]
    context: BrowserContext = browser.new_context(viewport={"width": 1440, "height": 900})
    page: Page = context.new_page()

    console_errors: List[str] = []
    page_errors: List[str] = []

    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda exc: page_errors.append(str(exc)))

    page.goto(app_server["url"], wait_until="networkidle")
    page.wait_for_timeout(200)

    page._console_errors = console_errors
    page._page_errors = page_errors

    yield page
    context.close()


# ==============================================================================
# 1. POINTER OCCLUSION AUDIT & GEOMETRICAL OVERLAP (STRICTLY 0.0 px²)
# ==============================================================================

@pytest.mark.parametrize("width,height,label", [
    (1024, 768, "1024x768 (Compact)"),
    (1440, 900, "1440x900 (Baseline)"),
    (1920, 1080, "1920x1080 (Full HD)")
])
def test_strictly_zero_pointer_occlusion_across_resolutions(app_server, width: int, height: int, label: str):
    """Adversarially verify that SOM Tag [04] and SOM Tag [12] produce strictly 0.0 px² overlap
    with #btn-export-mesh and #export-path-input across all standard resolutions."""
    browser: Browser = app_server["browser"]
    context = browser.new_context(viewport={"width": width, "height": height})
    page = context.new_page()
    page.goto(app_server["url"], wait_until="networkidle")
    page.wait_for_timeout(200)

    metrics = page.evaluate("""() => {
        function getBox(id) {
            const el = document.getElementById(id);
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return { x: r.left, y: r.top, width: r.width, height: r.height, right: r.right, bottom: r.bottom };
        }
        function overlapArea(b1, b2) {
            if (!b1 || !b2) return 0;
            const ox = Math.max(0.0, Math.min(b1.right, b2.right) - Math.max(b1.x, b2.x));
            const oy = Math.max(0.0, Math.min(b1.bottom, b2.bottom) - Math.max(b1.y, b2.y));
            return ox * oy;
        }

        const tag04 = getBox('som-tag-04');
        const tag12 = getBox('som-tag-12');
        const btnExport = getBox('btn-export-mesh');
        const pathInput = getBox('export-path-input');

        // Also check all 12 SOM tags
        const allTags = [];
        for (let i = 1; i <= 12; i++) {
            const pad = String(i).padStart(2, '0');
            const box = getBox('som-tag-' + pad);
            if (box) {
                allTags.push({
                    tag: 'som-tag-' + pad,
                    box,
                    overlapWithBtn: overlapArea(box, btnExport),
                    overlapWithInput: overlapArea(box, pathInput)
                });
            }
        }

        return {
            tag04,
            tag12,
            btnExport,
            pathInput,
            overlapTag04Btn: overlapArea(tag04, btnExport),
            overlapTag12Input: overlapArea(tag12, pathInput),
            verticalClearance04Btn: btnExport && tag04 ? btnExport.y - tag04.bottom : null,
            verticalClearance12Input: pathInput && tag12 ? pathInput.y - tag12.bottom : null,
            allTags
        };
    }""")

    assert metrics["tag04"] is not None, f"[{label}] som-tag-04 missing"
    assert metrics["btnExport"] is not None, f"[{label}] btn-export-mesh missing"
    assert metrics["tag12"] is not None, f"[{label}] som-tag-12 missing"
    assert metrics["pathInput"] is not None, f"[{label}] export-path-input missing"

    # Strict 0.0 px² verification
    assert metrics["overlapTag04Btn"] == 0.0, (
        f"[{label}] som-tag-04 occludes #btn-export-mesh by {metrics['overlapTag04Btn']:.2f} px²"
    )
    assert metrics["overlapTag12Input"] == 0.0, (
        f"[{label}] som-tag-12 occludes #export-path-input by {metrics['overlapTag12Input']:.2f} px²"
    )

    # Clearance must be at least 15px
    assert metrics["verticalClearance04Btn"] >= 15.0, (
        f"[{label}] Vertical clearance between tag04 and btn-export-mesh insufficient: {metrics['verticalClearance04Btn']} px"
    )
    assert metrics["verticalClearance12Input"] >= 15.0, (
        f"[{label}] Vertical clearance between tag12 and export-path-input insufficient: {metrics['verticalClearance12Input']} px"
    )

    # Audit all 12 tags
    for t in metrics["allTags"]:
        assert t["overlapWithBtn"] == 0.0, (
            f"[{label}] {t['tag']} unexpectedly occludes #btn-export-mesh by {t['overlapWithBtn']:.2f} px²"
        )
        assert t["overlapWithInput"] == 0.0, (
            f"[{label}] {t['tag']} unexpectedly occludes #export-path-input by {t['overlapWithInput']:.2f} px²"
        )

    context.close()


# ==============================================================================
# 2. DOCUMENT.ELEMENTFROMPOINT HIT-TESTING ON INTERACTIVE BUTTONS
# ==============================================================================

def test_element_from_point_at_center_of_interactive_buttons(fresh_page: Page):
    """Verify that document.elementFromPoint at the center of interactive buttons
    returns the button itself (or an internal child), confirming no intercepting overlay."""
    page = fresh_page

    test_targets = [
        "btn-export-mesh",
        "export-path-input",
        "btn-cam-orbit",
        "btn-cam-pan",
        "btn-cam-zoom",
        "btn-cam-zoom-out",
        "btn-cam-reset",
        "btn-inspector-toggle",
        "btn-rescan-som",
        "btn-inspect-target",
        "btn-capture-frame",
        "win-btn-min",
        "win-btn-max",
        "win-btn-close",
        "btn-menu-preview",
        "btn-menu-render",
    ]

    hit_results = page.evaluate("""(targetIds) => {
        return targetIds.map(id => {
            const el = document.getElementById(id);
            if (!el) return { id, error: 'not_found' };
            const r = el.getBoundingClientRect();
            const cx = r.left + r.width / 2;
            const cy = r.top + r.height / 2;
            const hit = document.elementFromPoint(cx, cy);
            const isSelfOrDescendant = hit ? (hit === el || el.contains(hit)) : false;
            return {
                id,
                cx: Math.round(cx),
                cy: Math.round(cy),
                hitId: hit ? hit.id : null,
                hitClass: hit ? hit.className : null,
                hitTag: hit ? hit.tagName : null,
                isDirectHit: isSelfOrDescendant
            };
        });
    }""", test_targets)

    for res in hit_results:
        assert res.get("error") is None, f"Target element #{res['id']} not found in DOM"
        assert res["isDirectHit"], (
            f"INTERCEPTION BUG: #{res['id']} at ({res['cx']}, {res['cy']}) intercepted by "
            f"<{res['hitTag']} id='{res['hitId']}' class='{res['hitClass']}'>"
        )

    # Click directly on #btn-export-mesh without force to confirm Playwright actionability passes
    t0 = time.perf_counter()
    page.locator("#btn-export-mesh").click(timeout=2000)
    latency_ms = (time.perf_counter() - t0) * 1000.0
    assert latency_ms < 150.0, f"Click latency excessive: {latency_ms:.1f}ms"


# ==============================================================================
# 3. SOM TAGS [01] THROUGH [12] RAPID CLICKING & EXCLUSIVITY STRESS
# ==============================================================================

def test_som_tags_01_through_12_mutual_exclusivity(fresh_page: Page):
    """Test clicking each SOM tag from [01] to [12] sequentially.
    Verify clean active toggle and single active tag exclusivity."""
    page = fresh_page

    for i in range(1, 13):
        pad = f"{i:02d}"
        tag_id = f"som-tag-{pad}"
        tag_el = page.locator(f"#{tag_id}")
        assert tag_el.is_visible(), f"SOM tag #{tag_id} is not visible"

        tag_el.click()
        page.wait_for_timeout(30)

        state = page.evaluate("""() => {
            const active = Array.from(document.querySelectorAll('.som-tag.active')).map(e => e.id);
            return {
                active,
                target: typeof AppState !== 'undefined' ? AppState.somFocusedTarget : null
            };
        }""")

        assert state["active"] == [tag_id], f"Expected only #{tag_id} active, got: {state['active']}"
        assert state["target"] == pad, f"AppState.somFocusedTarget mismatch: {state['target']} != {pad}"


def test_som_tags_rapid_burst_clicking_stress(fresh_page: Page):
    """Adversarially stress SOM tags with rapid alternating bursts."""
    page = fresh_page

    burst_sequence = ["01", "12", "04", "07", "02", "11", "06", "03", "10", "08", "09", "05", "04", "12", "01"]
    for mark in burst_sequence:
        page.locator(f"#som-tag-{mark}").click()
        page.wait_for_timeout(20)

    # Final tag clicked was '01'
    final_active = page.evaluate("() => Array.from(document.querySelectorAll('.som-tag.active')).map(e => e.id)")
    assert final_active == ["som-tag-01"], f"Expected single active tag som-tag-01, got {final_active}"
    assert len(page._page_errors) == 0, f"Uncaught page errors: {page._page_errors}"
    assert len(page._console_errors) == 0, f"Console errors: {page._console_errors}"


# ==============================================================================
# 4. CAMERA TOOLBAR (ZOOM, ZOOM-OUT, PAN, RESET) & COORDINATES HUD
# ==============================================================================

def test_camera_toolbar_zoom_pan_reset_and_zoom_out(fresh_page: Page):
    """Test all camera toolbar controls including Zoom In, Zoom Out, Pan, Orbit, and Reset."""
    page = fresh_page

    # Verify initial buttons
    assert page.locator("#btn-cam-orbit").is_visible()
    assert page.locator("#btn-cam-pan").is_visible()
    assert page.locator("#btn-cam-zoom").is_visible()
    assert page.locator("#btn-cam-zoom-out").is_visible()
    assert page.locator("#btn-cam-reset").is_visible()

    # 1. Pan
    page.locator("#btn-cam-pan").click()
    page.wait_for_timeout(30)
    assert page.evaluate("() => document.getElementById('btn-cam-pan').classList.contains('active')")
    logs = page.locator("#repl-logs").inner_text()
    assert "[VIEWPORT] Camera mode: Pan View" in logs

    # 2. Zoom In (toggle 1.15)
    page.locator("#btn-cam-zoom").click()
    page.wait_for_timeout(30)
    transform = page.evaluate("() => document.getElementById('cad-mesh-group')?.style.transform")
    assert transform == "scale(1.15)", f"Expected scale(1.15), got: {transform}"

    # 3. Zoom Out button
    page.locator("#btn-cam-zoom-out").click()
    page.wait_for_timeout(50)
    logs = page.locator("#repl-logs").inner_text()
    assert "[CAMERA] Zoom Out" in logs

    # 4. Reset
    page.locator("#btn-cam-reset").click()
    page.wait_for_timeout(50)
    reset_active = page.evaluate("() => document.getElementById('btn-cam-orbit').classList.contains('active')")
    assert reset_active, "Orbit button should be active after Reset"
    reset_transform = page.evaluate("() => document.getElementById('cad-mesh-group')?.style.transform")
    assert reset_transform == "scale(1)", f"Expected scale(1) after reset, got: {reset_transform}"


def test_coordinates_hud_mousemove_and_mouseleave(fresh_page: Page):
    """Test dynamic coordinates HUD updates on mousemove and mouseleave."""
    page = fresh_page

    coords_el = page.locator("#coords-text")
    assert coords_el.is_visible(), "#coords-text must be visible"

    # Initial text
    initial_text = coords_el.inner_text()
    assert "X:" in initial_text and "Y:" in initial_text

    # Dispatch mousemove on #cad-canvas
    page.evaluate("""() => {
        const canvas = document.getElementById('cad-canvas');
        if (!canvas) return;
        const rect = canvas.getBoundingClientRect();
        const evt = new MouseEvent('mousemove', {
            bubbles: true,
            clientX: rect.left + 350,
            clientY: rect.top + 220
        });
        canvas.dispatchEvent(evt);
    }""")
    page.wait_for_timeout(50)

    updated_text = coords_el.inner_text()
    assert "X: 350 px" in updated_text and "Y: 220 px" in updated_text, (
        f"Expected HUD coords X: 350 px • Y: 220 px, got: '{updated_text}'"
    )

    # Dispatch mouseleave
    page.evaluate("""() => {
        const canvas = document.getElementById('cad-canvas');
        if (!canvas) return;
        canvas.dispatchEvent(new MouseEvent('mouseleave', { bubbles: true }));
    }""")
    page.wait_for_timeout(50)

    leave_text = coords_el.inner_text()
    assert "X: 000 px" in leave_text and "Y: 000 px" in leave_text, (
        f"Expected HUD coords reset to 000 px on mouseleave, got: '{leave_text}'"
    )


# ==============================================================================
# 5. MULTI-RESOLUTION RESPONSIVENESS (1024x768, 1440x900, 1920x1080)
# ==============================================================================

@pytest.mark.parametrize("width,height", [(1024, 768), (1440, 900), (1920, 1080)])
def test_layout_zero_overflow_and_svg_leader_lines(app_server, width: int, height: int):
    """Verify zero layout overflow and mathematically positive SVG leader lines across resolutions."""
    browser: Browser = app_server["browser"]
    context = browser.new_context(viewport={"width": width, "height": height})
    page = context.new_page()
    page.goto(app_server["url"], wait_until="networkidle")
    page.wait_for_timeout(200)

    # 1. Overflow check
    overflows = page.evaluate("""() => ({
        docScrollW: document.documentElement.scrollWidth,
        docClientW: document.documentElement.clientWidth,
        appScrollW: document.getElementById('app-container').scrollWidth,
        appClientW: document.getElementById('app-container').clientWidth,
        appScrollH: document.getElementById('app-container').scrollHeight,
        appClientH: document.getElementById('app-container').clientHeight
    })""")

    assert overflows["docScrollW"] <= width, f"Doc overflow: {overflows['docScrollW']} > {width}"
    assert overflows["appScrollW"] <= width, f"App overflow W: {overflows['appScrollW']} > {width}"
    assert overflows["appScrollH"] <= height, f"App overflow H: {overflows['appScrollH']} > {height}"

    # 2. Leader lines check for [01], [02], [12], [04]
    lines_data = page.evaluate("""() => {
        return ['01', '02', '12', '04'].map(id => {
            const line = document.getElementById('leader-line-' + id);
            const dot = document.getElementById('anchor-dot-' + id);
            return {
                id,
                x1: line ? parseFloat(line.getAttribute('x1')) : NaN,
                y1: line ? parseFloat(line.getAttribute('y1')) : NaN,
                x2: line ? parseFloat(line.getAttribute('x2')) : NaN,
                y2: line ? parseFloat(line.getAttribute('y2')) : NaN,
                cx: dot ? parseFloat(dot.getAttribute('cx')) : NaN,
                cy: dot ? parseFloat(dot.getAttribute('cy')) : NaN
            };
        });
    }""")

    for ld in lines_data:
        assert not math.isnan(ld["x1"]) and ld["x1"] > 0, f"Line {ld['id']} x1 invalid: {ld}"
        assert not math.isnan(ld["y1"]) and ld["y1"] > 0, f"Line {ld['id']} y1 invalid: {ld}"
        assert not math.isnan(ld["x2"]) and ld["x2"] > 0, f"Line {ld['id']} x2 invalid: {ld}"
        assert not math.isnan(ld["y2"]) and ld["y2"] > 0, f"Line {ld['id']} y2 invalid: {ld}"
        assert abs(ld["x2"] - ld["cx"]) < 1.0, f"Line {ld['id']} dot alignment mismatch"
        assert abs(ld["y2"] - ld["cy"]) < 1.0, f"Line {ld['id']} dot alignment mismatch"

    context.close()
