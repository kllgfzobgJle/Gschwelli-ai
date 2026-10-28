"""Empirical Adversarial Challenge Suite for Milestone 3 (Center SOM Canvas & Isometric CAD Viewport).

Empirically tests:
1. Rapid and concurrent clicks across all SOM tags ([01], [02], [04], [12]):
   - Active classes toggle cleanly (exactly one active tag at a time).
   - Dynamic SVG leader lines and anchor dots update active states synchronously.
   - Target highlight rings apply to respective DOM elements.
   - REPL logs receive expected formatted entries without duplicate logs or errors.
   - Concurrency stress: rapid sequential and parallel click dispatch.

2. Camera control toolbar:
   - Orbit, Pan, Zoom, and Reset buttons.
   - Transforms on #cad-mesh-group toggle between scale(1.15) and scale(1).
   - Reset cleanly returns camera mode to Orbit and scale to 1.
   - REPL logs record camera actions accurately.
   - Stress cycling camera toolbar actions.

3. Action Toolbar stress:
   - "Re-scan SOM" clicked 10 times rapidly:
     - Laser scanline class (.scanning) toggles cleanly without leaving phantom scanlines.
     - Frame telemetry increments exactly 10 times (e.g., from #8184 to #8194).
     - REPL logs record scan actions and detection results.
   - "Capture" clicked 5 times rapidly:
     - Shutter flash class (.flashing) triggers and fades cleanly.
     - REPL logs record capture entries.
   - "Inspect target" correctly grounds currently focused mark.

4. Multi-resolution layout and geometry verification:
   - Tested at 1024x768, 1440x900, and 1920x1080 viewports.
   - Zero layout overflows (docScrollWidth <= width, appScrollWidth <= width, appScrollHeight <= height).
   - Positive leader line bounding box dimensions (x1, y1, x2, y2 > 0, length > 0, coordinates within frame).
   - Dynamic resize responsiveness: coordinates recompute on viewport resize.

5. Tab Switching & State Preservation:
   - Leader lines and CAD canvas persist correctly when navigating between modes.
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

from server.api import create_app


def find_free_port() -> int:
    """Find a random available TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def challenge_env():
    """Starts the FastAPI dashboard server in a background thread for the module."""
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

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-gpu", "--no-sandbox"])
        yield {"url": url, "port": port, "browser": browser}
        browser.close()

    server.should_exit = True
    thread.join(timeout=2.0)


@pytest.fixture
def fresh_page(challenge_env) -> Generator[Page, None, None]:
    """Provides a fresh browser Page for each test, capturing console errors and exceptions."""
    browser: Browser = challenge_env["browser"]
    context: BrowserContext = browser.new_context(viewport={"width": 1440, "height": 900})
    page: Page = context.new_page()

    console_errors: List[str] = []
    page_errors: List[str] = []

    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda exc: page_errors.append(str(exc)))

    page.goto(challenge_env["url"], wait_until="networkidle")
    page.wait_for_timeout(200)

    page._console_errors = console_errors
    page._page_errors = page_errors

    yield page
    context.close()


# ==============================================================================
# 1. RAPID AND CONCURRENT SOM TAG CLICKS
# ==============================================================================

def test_som_tags_initial_state(fresh_page: Page):
    """Verify initial state of SOM tags: Tag [04] is active by default, others inactive."""
    page = fresh_page
    
    # Check tag elements exist
    for tag_id in ["som-tag-01", "som-tag-02", "som-tag-12", "som-tag-04"]:
        assert page.locator(f"#{tag_id}").is_visible(), f"SOM tag #{tag_id} is not visible"

    # Default active mark in AppState is '04'
    active_tag = page.evaluate("""() => {
        const activeTags = Array.from(document.querySelectorAll('.som-tag.active')).map(el => el.id);
        return {
            activeTags,
            somFocusedTarget: typeof AppState !== 'undefined' ? AppState.somFocusedTarget : null,
            missionTarget: typeof AppState !== 'undefined' ? AppState.mission?.focusedTarget : null
        };
    }""")
    assert "som-tag-04" in active_tag["activeTags"], "Initial active tag should be som-tag-04"
    assert len(active_tag["activeTags"]) == 1, f"Expected exactly 1 active tag, got {active_tag['activeTags']}"
    assert len(page._page_errors) == 0, f"Uncaught page errors: {page._page_errors}"


def test_som_tags_sequential_clean_toggling(fresh_page: Page):
    """Test clicking each SOM tag sequentially: verify active class exclusivity, leader lines, and REPL logs."""
    page = fresh_page

    tags_info = [
        ("som-tag-01", "01", "leader-line-01", "anchor-dot-01", "target-menubar", "Menu"),
        ("som-tag-02", "02", "leader-line-02", "anchor-dot-02", "target-window-actions", "Window Controls"),
        ("som-tag-12", "12", "leader-line-12", "anchor-dot-12", "export-path-input", "Path Input"),
        ("som-tag-04", "04", "leader-line-04", "anchor-dot-04", "btn-export-mesh", "Button 'Export'"),
    ]

    for tag_id, mark_num, line_id, dot_id, target_el_id, desc in tags_info:
        # Click tag
        page.locator(f"#{tag_id}").click()
        page.wait_for_timeout(100)

        # 1. Verify exactly one active tag, one active line, one active dot
        state = page.evaluate("""() => {
            const activeTags = Array.from(document.querySelectorAll('.som-tag.active')).map(e => e.id);
            const activeLines = Array.from(document.querySelectorAll('.som-leader-line.active')).map(e => e.id);
            const activeDots = Array.from(document.querySelectorAll('.som-anchor-dot.active')).map(e => e.id);
            const ringElements = Array.from(document.querySelectorAll('.target-highlight-ring')).map(e => e.id);
            return {
                activeTags,
                activeLines,
                activeDots,
                ringElements,
                appStateTarget: typeof AppState !== 'undefined' ? AppState.somFocusedTarget : null,
                missionTarget: typeof AppState !== 'undefined' ? AppState.mission?.focusedTarget : null
            };
        }""")

        assert state["activeTags"] == [tag_id], f"Expected only {tag_id} to be active, got {state['activeTags']}"
        assert state["activeLines"] == [line_id], f"Expected only {line_id} to be active, got {state['activeLines']}"
        assert state["activeDots"] == [dot_id], f"Expected only {dot_id} to be active, got {state['activeDots']}"
        assert target_el_id in state["ringElements"], f"Target element {target_el_id} missing highlight ring"
        assert state["appStateTarget"] == mark_num, f"AppState.somFocusedTarget mismatch: expected {mark_num}, got {state['appStateTarget']}"
        assert state["missionTarget"] == mark_num, f"AppState.mission.focusedTarget mismatch: expected {mark_num}, got {state['missionTarget']}"

        # 2. Verify REPL log entry exists
        expected_log = f"Focused target [{mark_num}] ({desc})"
        logs_text = page.locator("#repl-logs").inner_text()
        assert expected_log in logs_text, f"Expected REPL log '{expected_log}' not found in logs: {logs_text}"

    assert len(page._page_errors) == 0, f"Uncaught page errors: {page._page_errors}"
    assert len(page._console_errors) == 0, f"Console errors: {page._console_errors}"


def test_som_tags_rapid_and_concurrent_clicks(fresh_page: Page):
    """Stress-test SOM tags under rapid alternating clicks and simulated concurrent dispatch."""
    page = fresh_page

    initial_log_count = page.evaluate("() => document.querySelectorAll('#repl-logs .log-line').length")

    # Rapid sequence of 12 clicks across all 4 tags
    sequence = ["01", "02", "12", "04", "02", "01", "04", "12", "01", "04", "02", "12"]
    for mark in sequence:
        page.locator(f"#som-tag-{mark}").click()
        page.wait_for_timeout(30)

    # After sequence, tag 12 must be the sole active tag
    final_state = page.evaluate("""() => {
        return {
            activeTags: Array.from(document.querySelectorAll('.som-tag.active')).map(e => e.id),
            activeLines: Array.from(document.querySelectorAll('.som-leader-line.active')).map(e => e.id),
            activeDots: Array.from(document.querySelectorAll('.som-anchor-dot.active')).map(e => e.id),
            appTarget: typeof AppState !== 'undefined' ? AppState.somFocusedTarget : null,
            totalLogs: document.querySelectorAll('#repl-logs .log-line').length
        };
    }""")

    assert final_state["activeTags"] == ["som-tag-12"], f"Expected only som-tag-12 active, got {final_state['activeTags']}"
    assert final_state["activeLines"] == ["leader-line-12"], f"Expected only leader-line-12 active, got {final_state['activeLines']}"
    assert final_state["activeDots"] == ["anchor-dot-12"], f"Expected only anchor-dot-12 active, got {final_state['activeDots']}"
    assert final_state["appTarget"] == "12"
    # Exactly 12 new logs added
    assert final_state["totalLogs"] == initial_log_count + len(sequence)

    # Concurrent dispatch stress: fire click events in same JavaScript turn
    page.evaluate("""() => {
        const ids = ['01', '04', '02', '12', '01'];
        ids.forEach(id => {
            const el = document.getElementById('som-tag-' + id);
            if (el) el.click();
        });
    }""")
    page.wait_for_timeout(150)

    # Last clicked in concurrent burst was '01'
    concurrent_state = page.evaluate("""() => ({
        activeTags: Array.from(document.querySelectorAll('.som-tag.active')).map(e => e.id),
        activeLines: Array.from(document.querySelectorAll('.som-leader-line.active')).map(e => e.id),
        activeDots: Array.from(document.querySelectorAll('.som-anchor-dot.active')).map(e => e.id),
        appTarget: typeof AppState !== 'undefined' ? AppState.somFocusedTarget : null
    })""")

    assert concurrent_state["activeTags"] == ["som-tag-01"]
    assert concurrent_state["activeLines"] == ["leader-line-01"]
    assert concurrent_state["activeDots"] == ["anchor-dot-01"]
    assert concurrent_state["appTarget"] == "01"

    assert len(page._page_errors) == 0, f"Uncaught page errors: {page._page_errors}"
    assert len(page._console_errors) == 0, f"Console errors: {page._console_errors}"


# ==============================================================================
# 2. CAMERA CONTROL TOOLBAR
# ==============================================================================

def test_camera_toolbar_transform_and_reset(fresh_page: Page):
    """Test camera control toolbar: Orbit, Pan, Zoom toggling, and Reset restoring scale(1)."""
    page = fresh_page

    # Verify buttons exist
    cam_buttons = ["btn-cam-orbit", "btn-cam-pan", "btn-cam-zoom", "btn-cam-reset"]
    for btn_id in cam_buttons:
        assert page.locator(f"#{btn_id}").is_visible(), f"Camera button #{btn_id} is not visible"

    # Default state
    mesh_transform = page.evaluate("() => document.getElementById('cad-mesh-group')?.style.transform || ''")
    assert mesh_transform in ("", "scale(1)"), f"Initial mesh transform unexpected: {mesh_transform}"

    # 1. Click Orbit
    page.locator("#btn-cam-orbit").click()
    page.wait_for_timeout(50)
    orbit_state = page.evaluate("""() => ({
        activeBtn: document.querySelector('.cam-btn.active')?.id,
        transform: document.getElementById('cad-mesh-group')?.style.transform || ''
    })""")
    assert orbit_state["activeBtn"] == "btn-cam-orbit"
    logs = page.locator("#repl-logs").inner_text()
    assert "[VIEWPORT] Camera mode: Orbit / 3D Rotate" in logs

    # 2. Click Pan
    page.locator("#btn-cam-pan").click()
    page.wait_for_timeout(50)
    pan_state = page.evaluate("""() => ({
        activeBtn: document.querySelector('.cam-btn.active')?.id
    })""")
    assert pan_state["activeBtn"] == "btn-cam-pan"
    logs = page.locator("#repl-logs").inner_text()
    assert "[VIEWPORT] Camera mode: Pan View" in logs

    # 3. Click Zoom (Toggle 1: zoom in to 115%)
    page.locator("#btn-cam-zoom").click()
    page.wait_for_timeout(50)
    zoom1_state = page.evaluate("""() => ({
        activeBtn: document.querySelector('.cam-btn.active')?.id,
        transform: document.getElementById('cad-mesh-group')?.style.transform
    })""")
    assert zoom1_state["activeBtn"] == "btn-cam-zoom"
    assert zoom1_state["transform"] == "scale(1.15)"
    logs = page.locator("#repl-logs").inner_text()
    assert "[VIEWPORT] Camera zoom: 115%" in logs

    # 4. Click Zoom (Toggle 2: zoom out back to 100%)
    page.locator("#btn-cam-zoom").click()
    page.wait_for_timeout(50)
    zoom2_state = page.evaluate("""() => ({
        transform: document.getElementById('cad-mesh-group')?.style.transform
    })""")
    assert zoom2_state["transform"] == "scale(1)"
    logs = page.locator("#repl-logs").inner_text()
    assert "[VIEWPORT] Camera zoom: 100%" in logs

    # 5. Click Zoom (Toggle 3: back to 115%) then Reset
    page.locator("#btn-cam-zoom").click()
    page.wait_for_timeout(50)
    assert page.evaluate("() => document.getElementById('cad-mesh-group')?.style.transform") == "scale(1.15)"

    # Click Reset
    page.locator("#btn-cam-reset").click()
    page.wait_for_timeout(50)
    reset_state = page.evaluate("""() => ({
        activeBtn: document.querySelector('.cam-btn.active')?.id,
        transform: document.getElementById('cad-mesh-group')?.style.transform
    })""")
    assert reset_state["activeBtn"] == "btn-cam-orbit", "Reset should restore active camera button to Orbit"
    assert reset_state["transform"] == "scale(1)", "Reset should restore scale to scale(1)"
    logs = page.locator("#repl-logs").inner_text()
    assert "[VIEWPORT] Camera reset to default isometric angle" in logs


def test_camera_toolbar_rapid_cycling_stress(fresh_page: Page):
    """Stress-test camera buttons under rapid cycling and ensure reset is idempotent and leaves no invalid state."""
    page = fresh_page

    # Rapid clicks across camera controls
    for _ in range(5):
        page.locator("#btn-cam-orbit").click()
        page.locator("#btn-cam-pan").click()
        page.locator("#btn-cam-zoom").click()
        page.locator("#btn-cam-zoom").click()
        page.locator("#btn-cam-reset").click()

    final_state = page.evaluate("""() => ({
        activeBtn: document.querySelector('.cam-btn.active')?.id,
        transform: document.getElementById('cad-mesh-group')?.style.transform
    })""")
    assert final_state["activeBtn"] == "btn-cam-orbit"
    assert final_state["transform"] == "scale(1)"
    assert len(page._page_errors) == 0, f"Uncaught page errors: {page._page_errors}"
    assert len(page._console_errors) == 0, f"Console errors: {page._console_errors}"


# ==============================================================================
# 3. ACTION TOOLBAR STRESS (RE-SCAN 10X & CAPTURE 5X)
# ==============================================================================

def test_action_toolbar_rapid_rescan_som_10x(fresh_page: Page):
    """Click 'Re-scan SOM' 10 times rapidly: verify laser scanline cleans up, telemetry increments, and no phantom scanlines."""
    page = fresh_page

    initial_frame = page.evaluate("() => (typeof AppState !== 'undefined' ? AppState.mission?.frameNumber : 8184) || 8184")
    btn_rescan = page.locator("#btn-rescan-som")
    assert btn_rescan.is_visible(), "#btn-rescan-som is not visible"

    # Rapid click 10 times
    for _ in range(10):
        btn_rescan.click()
        # Tight delay between clicks to stress race conditions
        page.wait_for_timeout(20)

    # Verify frame number incremented by exactly 10 in AppState
    current_frame = page.evaluate("() => typeof AppState !== 'undefined' ? AppState.mission?.frameNumber : null")
    expected_frame = initial_frame + 10
    assert current_frame == expected_frame, f"Expected frame {expected_frame}, got {current_frame}"

    # Verify UI frame telemetry text contains updated frame number
    telemetry_text = page.locator("#frame-telemetry").inner_text()
    assert f"FRAME #{expected_frame}" in telemetry_text, f"Telemetry text '{telemetry_text}' missing FRAME #{expected_frame}"

    # During scan, scanning class is present
    scan_line = page.locator("#som-scan-line")
    assert scan_line.count() == 1, "#som-scan-line not found in DOM"

    # Wait for the scanline CSS animation & timeout to cleanly finish (800ms animation + 400ms margin)
    page.wait_for_timeout(1200)

    # Verify class 'scanning' is completely removed (no phantom scanlines)
    is_scanning = page.evaluate("() => document.getElementById('som-scan-line')?.classList.contains('scanning')")
    assert not is_scanning, "Laser scanline retained .scanning class after timeout expired (phantom scanline bug)"

    # Verify REPL logs received scan telemetry
    repl_logs = page.locator("#repl-logs").inner_text()
    assert "[SOM] Re-scanning targets via UIA + Vision Fusion..." in repl_logs
    assert f"12 targets detected • Frame #{expected_frame}" in repl_logs

    assert len(page._page_errors) == 0, f"Uncaught page errors: {page._page_errors}"
    assert len(page._console_errors) == 0, f"Console errors: {page._console_errors}"


def test_action_toolbar_rapid_capture_5x(fresh_page: Page):
    """Click 'Capture' 5 times rapidly: verify shutter flash triggers and fades cleanly."""
    page = fresh_page

    btn_capture = page.locator("#btn-capture-frame")
    assert btn_capture.is_visible(), "#btn-capture-frame is not visible"

    # Click Capture 5 times
    for _ in range(5):
        btn_capture.click()
        page.wait_for_timeout(30)

    # Wait for flash animation and timeout to finish (250ms duration + 200ms margin)
    page.wait_for_timeout(500)

    # Verify class 'flashing' is completely removed
    is_flashing = page.evaluate("() => document.getElementById('viewport-shutter-flash')?.classList.contains('flashing')")
    assert not is_flashing, "Shutter flash retained .flashing class (phantom flash bug)"

    # Verify REPL logs contain capture confirmation
    repl_logs = page.locator("#repl-logs").inner_text()
    assert "[CAPTURE]" in repl_logs
    assert "captured (1440 × 900 PNG • 84ms)" in repl_logs

    assert len(page._page_errors) == 0, f"Uncaught page errors: {page._page_errors}"
    assert len(page._console_errors) == 0, f"Console errors: {page._console_errors}"


def test_action_toolbar_inspect_target(fresh_page: Page):
    """Click 'Inspect target' button: verifies focusing and logging grounding telemetry for active mark."""
    page = fresh_page

    # First focus tag 01
    page.locator("#som-tag-01").click()
    page.wait_for_timeout(50)

    # Click Inspect Target
    page.locator("#btn-inspect-target").click()
    page.wait_for_timeout(50)

    repl_logs = page.locator("#repl-logs").inner_text()
    assert "[INSPECT] Grounded target [01]" in repl_logs
    assert "BoundingBox" in repl_logs
    assert "Confidence: 99.2%" in repl_logs


# ==============================================================================
# 4. MULTI-RESOLUTION LAYOUT AND LEADER LINE GEOMETRY
# ==============================================================================

RESOLUTIONS = [
    (1024, 768, "1024x768 (Compact / XGA)"),
    (1440, 900, "1440x900 (Baseline)"),
    (1920, 1080, "1920x1080 (Full HD)"),
]


@pytest.mark.parametrize("width,height,label", RESOLUTIONS)
def test_multiresolution_layout_and_leader_lines(challenge_env, width: int, height: int, label: str):
    """Verify zero layout overflow and mathematically positive, bounded leader line geometry across resolutions."""
    browser: Browser = challenge_env["browser"]
    context = browser.new_context(viewport={"width": width, "height": height})
    page = context.new_page()

    uncaught_errors: List[str] = []
    page.on("pageerror", lambda err: uncaught_errors.append(str(err)))

    page.goto(challenge_env["url"], wait_until="networkidle")
    page.wait_for_timeout(300)

    assert len(uncaught_errors) == 0, f"[{label}] Uncaught page errors on load: {uncaught_errors}"

    # 1. Zero Root / App-Container Overflows
    overflow_metrics = page.evaluate("""() => ({
        docScrollWidth: document.documentElement.scrollWidth,
        docClientWidth: document.documentElement.clientWidth,
        appScrollWidth: document.getElementById('app-container').scrollWidth,
        appClientWidth: document.getElementById('app-container').clientWidth,
        appScrollHeight: document.getElementById('app-container').scrollHeight,
        appClientHeight: document.getElementById('app-container').clientHeight
    })""")

    assert overflow_metrics["docScrollWidth"] <= width, f"[{label}] Horizontal scroll on document: {overflow_metrics['docScrollWidth']} > {width}"
    assert overflow_metrics["appScrollWidth"] <= width, f"[{label}] Horizontal overflow on #app-container: {overflow_metrics['appScrollWidth']} > {width}"
    assert overflow_metrics["appScrollHeight"] <= height, f"[{label}] Vertical overflow on #app-container: {overflow_metrics['appScrollHeight']} > {height}"

    # 2. Viewport Frame and Leader Line SVG geometry
    frame_metrics = page.evaluate("""() => {
        const frame = document.getElementById('cad-viewport-frame');
        const svg = document.getElementById('som-leader-svg');
        const fRect = frame ? frame.getBoundingClientRect() : null;
        const sRect = svg ? svg.getBoundingClientRect() : null;

        const lines = ['01', '02', '12', '04'].map(id => {
            const el = document.getElementById('leader-line-' + id);
            const dot = document.getElementById('anchor-dot-' + id);
            const tag = document.getElementById('som-tag-' + id);
            const tagRect = tag ? tag.getBoundingClientRect() : null;

            return {
                id,
                x1: el ? parseFloat(el.getAttribute('x1')) : NaN,
                y1: el ? parseFloat(el.getAttribute('y1')) : NaN,
                x2: el ? parseFloat(el.getAttribute('x2')) : NaN,
                y2: el ? parseFloat(el.getAttribute('y2')) : NaN,
                dot_cx: dot ? parseFloat(dot.getAttribute('cx')) : NaN,
                dot_cy: dot ? parseFloat(dot.getAttribute('cy')) : NaN,
                dot_r: dot ? parseFloat(dot.getAttribute('r')) : NaN,
                tag_w: tagRect ? tagRect.width : 0,
                tag_h: tagRect ? tagRect.height : 0
            };
        });

        return {
            frameWidth: fRect ? fRect.width : 0,
            frameHeight: fRect ? fRect.height : 0,
            svgWidth: sRect ? sRect.width : 0,
            svgHeight: sRect ? sRect.height : 0,
            lines
        };
    }""")

    # Frame and SVG overlay must have positive dimensions
    assert frame_metrics["frameWidth"] > 200, f"[{label}] CAD viewport frame width too small: {frame_metrics['frameWidth']}"
    assert frame_metrics["frameHeight"] > 200, f"[{label}] CAD viewport frame height too small: {frame_metrics['frameHeight']}"
    assert frame_metrics["svgWidth"] > 0, f"[{label}] Leader SVG overlay width zero"
    assert frame_metrics["svgHeight"] > 0, f"[{label}] Leader SVG overlay height zero"

    # 3. Leader Line Coordinates Verification
    frame_w = frame_metrics["frameWidth"]
    frame_h = frame_metrics["frameHeight"]

    for line in frame_metrics["lines"]:
        lid = line["id"]
        x1, y1, x2, y2 = line["x1"], line["y1"], line["x2"], line["y2"]

        # Coordinates must be valid finite non-NaN numbers
        assert not (math.isnan(x1) or math.isnan(y1) or math.isnan(x2) or math.isnan(y2)), f"[{label}] Line {lid} has NaN coordinate: {line}"

        # Coordinates must be positive
        assert x1 >= 0 and y1 >= 0, f"[{label}] Line {lid} origin (x1, y1) is negative: ({x1}, {y1})"
        assert x2 >= 0 and y2 >= 0, f"[{label}] Line {lid} target (x2, y2) is negative: ({x2}, {y2})"

        # Coordinates must be bounded within frame bounds
        assert x1 <= frame_w and y1 <= frame_h, f"[{label}] Line {lid} origin ({x1}, {y1}) exceeds frame bounds ({frame_w}, {frame_h})"
        assert x2 <= frame_w and y2 <= frame_h, f"[{label}] Line {lid} target ({x2}, {y2}) exceeds frame bounds ({frame_w}, {frame_h})"

        # Line must have positive mathematical length (not collapsed to a single point)
        length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        assert length > 10.0, f"[{label}] Line {lid} length too short or collapsed: {length}px"

        # Anchor dot must match line end point (x2, y2)
        assert abs(line["dot_cx"] - x2) < 1.0, f"[{label}] Dot cx {line['dot_cx']} does not match line x2 {x2}"
        assert abs(line["dot_cy"] - y2) < 1.0, f"[{label}] Dot cy {line['dot_cy']} does not match line y2 {y2}"
        assert line["dot_r"] > 0, f"[{label}] Dot radius is non-positive: {line['dot_r']}"

        # Tag must have positive dimensions
        assert line["tag_w"] > 20 and line["tag_h"] > 10, f"[{label}] Tag {lid} bounding box too small: {line['tag_w']}x{line['tag_h']}"

    context.close()


def test_leader_lines_dynamic_viewport_resize(fresh_page: Page):
    """Test dynamic window resize: verify updateSomLeaderLines automatically recalculates line coordinates."""
    page = fresh_page

    # Coordinates at 1440x900
    initial_coords = page.evaluate("""() => {
        return ['01', '02', '12', '04'].map(id => {
            const el = document.getElementById('leader-line-' + id);
            return {
                id,
                x1: parseFloat(el.getAttribute('x1')),
                x2: parseFloat(el.getAttribute('x2')),
                y1: parseFloat(el.getAttribute('y1')),
                y2: parseFloat(el.getAttribute('y2'))
            };
        });
    }""")

    # Resize page to 1024x768
    page.set_viewport_size({"width": 1024, "height": 768})
    page.wait_for_timeout(200)

    # Coordinates after resize
    resized_coords = page.evaluate("""() => {
        return ['01', '02', '12', '04'].map(id => {
            const el = document.getElementById('leader-line-' + id);
            return {
                id,
                x1: parseFloat(el.getAttribute('x1')),
                x2: parseFloat(el.getAttribute('x2')),
                y1: parseFloat(el.getAttribute('y1')),
                y2: parseFloat(el.getAttribute('y2'))
            };
        });
    }""")

    # Verify that the coordinates adapted to the new geometry
    for init_c, res_c in zip(initial_coords, resized_coords):
        lid = init_c["id"]
        # All resized coords must be positive
        assert res_c["x1"] > 0 and res_c["y1"] > 0
        assert res_c["x2"] > 0 and res_c["y2"] > 0
        # Line 04 connects to export button at right edge, which moves on resize
        if lid in ("04", "02"):
            assert init_c["x2"] != res_c["x2"], f"Line {lid} x2 should adapt on resize (was {init_c['x2']}, now {res_c['x2']})"

    # Resize back to 1440x900
    page.set_viewport_size({"width": 1440, "height": 900})
    page.wait_for_timeout(200)

    restored_coords = page.evaluate("""() => {
        return ['01', '02', '12', '04'].map(id => {
            const el = document.getElementById('leader-line-' + id);
            return {
                id,
                x1: parseFloat(el.getAttribute('x1')),
                x2: parseFloat(el.getAttribute('x2'))
            };
        });
    }""")

    for init_c, rest_c in zip(initial_coords, restored_coords):
        assert abs(init_c["x2"] - rest_c["x2"]) < 2.0, f"Line {init_c['id']} x2 did not restore after resizing back"


# ==============================================================================
# 5. TAB SWITCHING & SOM CANVAS PRESERVATION
# ==============================================================================

def test_tab_switching_preserves_som_canvas(fresh_page: Page):
    """Switch away to Vision SOM and Focus Chat, then back to Mission Control: verify canvas and leader lines remain healthy."""
    page = fresh_page

    # Click tag 02
    page.locator("#som-tag-02").click()
    page.wait_for_timeout(50)

    # Switch to Vision SOM
    page.locator("button:has-text('Vision SOM')").click()
    page.wait_for_timeout(100)

    # Switch to Focus Chat
    page.locator("button:has-text('Focus Chat')").click()
    page.wait_for_timeout(100)

    # Switch back to Mission Control
    page.locator("button:has-text('Mission Control')").click()
    page.wait_for_timeout(200)

    # Verify Tag 02 remains active, leader lines are rendered with valid coordinates
    state = page.evaluate("""() => {
        const activeTag = document.querySelector('.som-tag.active')?.id;
        const line02 = document.getElementById('leader-line-02');
        return {
            activeTag,
            line02_x1: parseFloat(line02.getAttribute('x1')),
            line02_x2: parseFloat(line02.getAttribute('x2')),
            line02_active: line02.classList.contains('active')
        };
    }""")

    assert state["activeTag"] == "som-tag-02"
    assert state["line02_active"] is True
    assert state["line02_x1"] > 0
    assert state["line02_x2"] > 0

    assert len(page._page_errors) == 0, f"Uncaught page errors: {page._page_errors}"
    assert len(page._console_errors) == 0, f"Console errors: {page._console_errors}"


# ==============================================================================
# 6. ADVERSARIAL OVERLAY & POINTER EVENT INTERCEPTION CHALLENGE
# ==============================================================================

def test_som_tag_04_interception_of_export_button(fresh_page: Page):
    """Adversarial stress-test: verify whether SOM tag [04] physically intercepts pointer events to #btn-export-mesh.
    
    If .som-tag-04 overlaps #btn-export-mesh directly, clicking #btn-export-mesh fails or is intercepted.
    """
    page = fresh_page

    overlap_info = page.evaluate("""() => {
        const tag04 = document.getElementById('som-tag-04');
        const btnExport = document.getElementById('btn-export-mesh');
        if (!tag04 || !btnExport) return null;

        const rTag = tag04.getBoundingClientRect();
        const rBtn = btnExport.getBoundingClientRect();

        const overlaps = !(
            rTag.right < rBtn.left ||
            rTag.left > rBtn.right ||
            rTag.bottom < rBtn.top ||
            rTag.top > rBtn.bottom
        );

        // Check which element receives pointer event at center of export button
        const btnCenterX = rBtn.left + rBtn.width / 2;
        const btnCenterY = rBtn.top + rBtn.height / 2;
        const topEl = document.elementFromPoint(btnCenterX, btnCenterY);

        return {
            rTag: { left: rTag.left, top: rTag.top, right: rTag.right, bottom: rTag.bottom, width: rTag.width, height: rTag.height },
            rBtn: { left: rBtn.left, top: rBtn.top, right: rBtn.right, bottom: rBtn.bottom, width: rBtn.width, height: rBtn.height },
            overlaps,
            topElId: topEl ? topEl.id : null,
            topElClass: topEl ? topEl.className : null
        };
    }""")

    print("\nOVERLAP INFO:", overlap_info)

    # Attempt to click #btn-export-mesh with standard Playwright actionability checks
    # If intercepted by som-tag-04, this raises playwright TimeoutError
    try:
        page.locator("#btn-export-mesh").click(timeout=3000)
        clicked = True
    except Exception as e:
        clicked = False
        error_msg = str(e)

    assert clicked, f"CRITICAL UI BUG: #btn-export-mesh cannot be clicked because pointer events are intercepted by SOM overlay! Details: {overlap_info}, Error: {error_msg if not clicked else ''}"


def test_som_tag_12_interception_of_path_input(fresh_page: Page):
    """Adversarial stress-test: verify whether SOM tag [12] overlaps and intercepts pointer events to #export-path-input."""
    page = fresh_page

    overlap_info = page.evaluate("""() => {
        const tag12 = document.getElementById('som-tag-12');
        const input = document.getElementById('export-path-input');
        if (!tag12 || !input) return null;

        const rTag = tag12.getBoundingClientRect();
        const rInp = input.getBoundingClientRect();

        const overlaps = !(
            rTag.right < rInp.left ||
            rTag.left > rInp.right ||
            rTag.bottom < rInp.top ||
            rTag.top > rInp.bottom
        );

        // Check element at left side of input where som-tag-12 sits
        const inpLeftX = rInp.left + 20;
        const inpCenterY = rInp.top + rInp.height / 2;
        const topEl = document.elementFromPoint(inpLeftX, inpCenterY);

        return {
            rTag: { left: rTag.left, top: rTag.top, right: rTag.right, bottom: rTag.bottom, width: rTag.width },
            rInp: { left: rInp.left, top: rInp.top, right: rInp.right, bottom: rInp.bottom, width: rInp.width },
            overlaps,
            topElId: topEl ? topEl.id : null
        };
    }""")

    print("\nTAG 12 OVERLAP INFO:", overlap_info)
    assert not overlap_info["overlaps"], f"Tag [12] overlaps #export-path-input: {overlap_info}"


def test_som_tags_all_four_geometry_and_obstruction_audit(fresh_page: Page):
    """Audit all 4 SOM tags against their target elements to catalog exact geometric obstructions."""
    page = fresh_page

    audit = page.evaluate("""() => {
        const pairs = [
            { tagId: 'som-tag-01', targetId: 'target-menubar', desc: 'Menu Bar' },
            { tagId: 'som-tag-02', targetId: 'target-window-actions', desc: 'Window Controls' },
            { tagId: 'som-tag-12', targetId: 'export-path-input', desc: 'Path Input' },
            { tagId: 'som-tag-04', targetId: 'btn-export-mesh', desc: 'Export Button' }
        ];

        return pairs.map(p => {
            const tag = document.getElementById(p.tagId);
            const target = document.getElementById(p.targetId);
            if (!tag || !target) return { desc: p.desc, error: 'Element missing' };

            const rTag = tag.getBoundingClientRect();
            const rTgt = target.getBoundingClientRect();

            const overlaps = !(
                rTag.right < rTgt.left ||
                rTag.left > rTgt.right ||
                rTag.bottom < rTgt.top ||
                rTag.top > rTgt.bottom
            );

            return {
                tag: p.tagId,
                target: p.targetId,
                desc: p.desc,
                rTag: { left: Math.round(rTag.left), top: Math.round(rTag.top), right: Math.round(rTag.right), bottom: Math.round(rTag.bottom) },
                rTgt: { left: Math.round(rTgt.left), top: Math.round(rTgt.top), right: Math.round(rTgt.right), bottom: Math.round(rTgt.bottom) },
                overlaps
            };
        });
    }""")

    print("\n=== SOM TAG GEOMETRIC OBSTRUCTION AUDIT ===")
    for item in audit:
        print(item)
    print("===========================================\n")



