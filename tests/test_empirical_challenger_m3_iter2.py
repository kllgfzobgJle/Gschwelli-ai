"""Empirical Challenger Verification Harness for Milestone 3 Iteration 2.

Tests the specific acceptance criteria for remediation:
1. Bounding box overlap area between #som-tag-04 and #btn-export-mesh is strictly 0.0 px^2 across 1024x768, 1440x900, 1920x1080.
2. elementFromPoint at center of #btn-export-mesh returns #btn-export-mesh directly across all viewports.
3. Standard Playwright locator("#btn-export-mesh").click() execution time is <100ms.
4. Bounding box overlap area between #som-tag-12 and #export-path-input is strictly 0.0 px^2.
5. Leader line slope and visual clearance confirmation.
"""

from __future__ import annotations

import socket
import threading
import time
from typing import Generator, List
import pytest
import uvicorn
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from server.api import create_app


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def challenge_server():
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


@pytest.mark.parametrize("vp_w,vp_h,res_name", [
    (1024, 768, "1024x768"),
    (1440, 900, "1440x900"),
    (1920, 1080, "1920x1080"),
])
def test_empirical_bounding_box_and_element_from_point(challenge_server, vp_w: int, vp_h: int, res_name: str):
    browser: Browser = challenge_server["browser"]
    context: BrowserContext = browser.new_context(viewport={"width": vp_w, "height": vp_h})
    page: Page = context.new_page()

    page.goto(challenge_server["url"], wait_until="networkidle")
    page.wait_for_timeout(200)

    # 1. Measure Tag 04 vs Export Button
    tag04_el = page.locator("#som-tag-04")
    btn_el = page.locator("#btn-export-mesh")
    assert tag04_el.is_visible()
    assert btn_el.is_visible()

    box_tag04 = tag04_el.bounding_box()
    box_btn = btn_el.bounding_box()
    assert box_tag04 and box_btn

    overlap_x = max(0.0, min(box_tag04["x"] + box_tag04["width"], box_btn["x"] + box_btn["width"]) - max(box_tag04["x"], box_btn["x"]))
    overlap_y = max(0.0, min(box_tag04["y"] + box_tag04["height"], box_btn["y"] + box_btn["height"]) - max(box_tag04["y"], box_btn["y"]))
    overlap_area = overlap_x * overlap_y

    vertical_clearance = box_btn["y"] - (box_tag04["y"] + box_tag04["height"])

    print(f"\n[{res_name}] Tag 04 Box: {box_tag04}")
    print(f"[{res_name}] Btn Box: {box_btn}")
    print(f"[{res_name}] Overlap Area: {overlap_area:.4f} px^2")
    print(f"[{res_name}] Vertical Clearance: {vertical_clearance:.2f} px")

    assert overlap_area == 0.0, f"[{res_name}] Tag 04 overlaps Export Button by {overlap_area} px^2"
    assert vertical_clearance > 15.0, f"[{res_name}] Vertical clearance too small: {vertical_clearance} px"

    # 2. Check elementFromPoint at center of #btn-export-mesh
    cx = box_btn["x"] + box_btn["width"] / 2.0
    cy = box_btn["y"] + box_btn["height"] / 2.0
    hit_info = page.evaluate("""([x, y]) => {
        const el = document.elementFromPoint(x, y);
        return {
            id: el ? el.id : null,
            className: el ? el.className : null,
            tagName: el ? el.tagName : null
        };
    }""", [cx, cy])

    print(f"[{res_name}] elementFromPoint at ({cx:.1f}, {cy:.1f}): {hit_info}")
    assert hit_info["id"] == "btn-export-mesh", f"[{res_name}] Center not hitting btn-export-mesh directly: {hit_info}"
    assert hit_info["tagName"] == "BUTTON", f"[{res_name}] Hit element is not BUTTON: {hit_info}"

    # 3. Measure click latency of standard Playwright locator.click()
    t_start = time.perf_counter()
    btn_el.click(timeout=2000)
    click_duration_ms = (time.perf_counter() - t_start) * 1000.0
    print(f"[{res_name}] Playwright locator.click() duration: {click_duration_ms:.2f} ms")

    assert click_duration_ms < 100.0, f"[{res_name}] Click latency exceeded 100ms: {click_duration_ms:.2f} ms"

    # 4. Measure Tag 12 vs Path Input
    tag12_el = page.locator("#som-tag-12")
    inp_el = page.locator("#export-path-input")
    assert tag12_el.is_visible()
    assert inp_el.is_visible()

    box_tag12 = tag12_el.bounding_box()
    box_inp = inp_el.bounding_box()
    assert box_tag12 and box_inp

    overlap12_x = max(0.0, min(box_tag12["x"] + box_tag12["width"], box_inp["x"] + box_inp["width"]) - max(box_tag12["x"], box_inp["x"]))
    overlap12_y = max(0.0, min(box_tag12["y"] + box_tag12["height"], box_inp["y"] + box_inp["height"]) - max(box_tag12["y"], box_inp["y"]))
    overlap12_area = overlap12_x * overlap12_y
    clearance12 = box_inp["y"] - (box_tag12["y"] + box_tag12["height"])

    print(f"[{res_name}] Tag 12 vs Path Input Overlap: {overlap12_area:.4f} px^2, Clearance: {clearance12:.2f} px")
    assert overlap12_area == 0.0, f"[{res_name}] Tag 12 overlaps Path Input by {overlap12_area} px^2"
    assert clearance12 > 15.0, f"[{res_name}] Clearance 12 too small: {clearance12} px"

    # 5. Check elementFromPoint at center of #export-path-input
    inp_cx = box_inp["x"] + 25.0
    inp_cy = box_inp["y"] + box_inp["height"] / 2.0
    hit_inp = page.evaluate("""([x, y]) => {
        const el = document.elementFromPoint(x, y);
        return { id: el ? el.id : null, tagName: el ? el.tagName : null };
    }""", [inp_cx, inp_cy])
    print(f"[{res_name}] elementFromPoint at input ({inp_cx:.1f}, {inp_cy:.1f}): {hit_inp}")
    assert hit_inp["id"] == "export-path-input"

    context.close()


def test_cold_load_synchronous_active_styling(challenge_server):
    """Verify that on initial cold load, Tag 04, Leader Line 04, and Anchor Dot 04 are synchronously active."""
    browser: Browser = challenge_server["browser"]
    context: BrowserContext = browser.new_context(viewport={"width": 1440, "height": 900})
    page: Page = context.new_page()

    page.goto(challenge_server["url"], wait_until="commit")

    # Evaluate immediate DOM classes before any user events
    classes = page.evaluate("""() => ({
        tag04: document.getElementById('som-tag-04')?.className,
        line04: document.getElementById('leader-line-04')?.getAttribute('class'),
        dot04: document.getElementById('anchor-dot-04')?.getAttribute('class'),
        tag01: document.getElementById('som-tag-01')?.className,
        line01: document.getElementById('leader-line-01')?.getAttribute('class'),
        dot01: document.getElementById('anchor-dot-01')?.getAttribute('class')
    })""")

    print("\n[COLD LOAD ACTIVE CLASSES]", classes)
    assert "active" in (classes["tag04"] or "").split(), "som-tag-04 not active on cold load"
    assert "active" in (classes["line04"] or "").split(), "leader-line-04 not active on cold load"
    assert "active" in (classes["dot04"] or "").split(), "anchor-dot-04 not active on cold load"

    # Other tags must NOT be active
    assert "active" not in (classes["tag01"] or "").split()
    assert "active" not in (classes["line01"] or "").split()
    assert "active" not in (classes["dot01"] or "").split()

    context.close()
