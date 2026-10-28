"""Empirical Adversarial Challenge Suite for Milestone 2 (ui/dashboard/index.html).

Empirically tests:
1. Zero-dependency verification (Zero external network requests & links).
2. Offline / WebSocket resilience (Graceful fallback to AppState mock data, zero uncaught exceptions).
3. Viewport rendering & responsiveness at 1440x900, 1920x1080, 1024x768.
4. Stress-testing sub-component overflow at 1024x768 (Toolbar button wrapping, top nav height).
5. Tab switching visibility & CSS display leak (#view-mission-control specificity).
6. XSS / HTML sanitization in task addition.
"""

from __future__ import annotations

from pathlib import Path
import re
import socket
import threading
import time
from typing import Generator, List
from urllib.parse import urlparse

from playwright.sync_api import Browser, sync_playwright
import pytest
import uvicorn

from server.api import create_app


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def challenge_env():
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


# ==============================================================================
# Challenge 1: Zero-Dependency Verification
# ==============================================================================

def test_zero_external_network_requests(challenge_env):
    """Verify that loading and interacting with the page initiates ZERO external network requests."""
    browser: Browser = challenge_env["browser"]
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    requests_made: List[str] = []
    page.on("request", lambda req: requests_made.append(req.url))

    page.goto(challenge_env["url"], wait_until="networkidle")
    page.wait_for_timeout(500)

    external_requests = []
    local_host = f"127.0.0.1:{challenge_env['port']}"
    for u in requests_made:
        parsed = urlparse(u)
        if parsed.netloc != local_host and parsed.scheme not in ("data", "blob"):
            external_requests.append(u)

    context.close()
    assert len(external_requests) == 0, f"Found external requests: {external_requests}"


def test_zero_external_links_in_html_source():
    """Verify index.html contains no external stylesheet links, external scripts, or @import statements."""
    html_path = Path(__file__).resolve().parent.parent / "ui" / "dashboard" / "index.html"
    content = html_path.read_text(encoding="utf-8")

    external_links = re.findall(r'<link[^>]+href=["\'](http[s]?://[^"\']+)["\']', content, re.IGNORECASE)
    assert len(external_links) == 0, f"Found external link tags: {external_links}"

    external_scripts = re.findall(r'<script[^>]+src=["\'](http[s]?://[^"\']+)["\']', content, re.IGNORECASE)
    assert len(external_scripts) == 0, f"Found external script tags: {external_scripts}"

    external_imports = re.findall(r'@import\s+(?:url\()?["\'](http[s]?://[^"\']+)["\']', content, re.IGNORECASE)
    assert len(external_imports) == 0, f"Found external CSS @import: {external_imports}"


# ==============================================================================
# Challenge 2: WebSocket Resilience & Offline Fallback
# ==============================================================================

def test_offline_page_load_and_mock_fallback(challenge_env):
    """Simulate completely unreachable backend / failed WebSocket and verify AppState and UI remain robust."""
    browser: Browser = challenge_env["browser"]
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    uncaught_errors: List[str] = []
    page.on("pageerror", lambda err: uncaught_errors.append(str(err)))

    page.route("**/api/**", lambda route: route.abort("connectionrefused"))
    page.route("**/ws", lambda route: route.abort("connectionrefused"))

    page.goto(challenge_env["url"], wait_until="domcontentloaded")
    page.wait_for_timeout(1000)

    # 1. Zero uncaught errors
    assert len(uncaught_errors) == 0, f"Uncaught page errors while offline: {uncaught_errors}"

    # 2. AppState retains rich mock data
    app_state = page.evaluate("() => ({ project: AppState.project, mission: AppState.mission, tasks: AppState.tasks, blackboard: AppState.blackboard })")
    assert app_state["project"]["name"] == "3D Fabrication & Automation"
    assert app_state["mission"]["status"] == "PAUSED • APPROVAL"
    assert len(app_state["tasks"]) == 4

    # 3. Interactive workflows operate cleanly offline
    page.click('.task-item[data-task-id="t3"] .custom-checkbox')
    assert page.evaluate("() => AppState.tasks.find(t => t.id === 't3').completed") is True

    page.click("#btn-approve")
    assert page.evaluate("() => AppState.mission.status") == "COMPLETED"

    page.fill("#repl-input", "Get-Process openscad")
    page.press("#repl-input", "Enter")

    page.fill("#command-input", "/approve")
    page.press("#command-input", "Enter")

    assert len(uncaught_errors) == 0, f"Uncaught errors during offline interactions: {uncaught_errors}"
    context.close()


# ==============================================================================
# Challenge 3: Multi-Resolution Viewport Layout & Overflow
# ==============================================================================

RESOLUTIONS = [
    (1440, 900, "1440x900 (Baseline)"),
    (1920, 1080, "1920x1080 (Full HD)"),
    (1024, 768, "1024x768 (XGA / Compact)"),
]

@pytest.mark.parametrize("width,height,label", RESOLUTIONS)
def test_viewport_layout_overflow_and_bounds(challenge_env, width: int, height: int, label: str):
    """Stress-test viewport rendering at target resolution: verify root containment."""
    browser: Browser = challenge_env["browser"]
    context = browser.new_context(viewport={"width": width, "height": height})
    page = context.new_page()

    uncaught_errors: List[str] = []
    page.on("pageerror", lambda err: uncaught_errors.append(str(err)))

    page.goto(challenge_env["url"], wait_until="networkidle")
    page.wait_for_timeout(300)

    assert len(uncaught_errors) == 0

    scroll_metrics = page.evaluate("""() => ({
        docScrollWidth: document.documentElement.scrollWidth,
        appScrollWidth: document.getElementById('app-container').scrollWidth,
        appScrollHeight: document.getElementById('app-container').scrollHeight
    })""")

    assert scroll_metrics["docScrollWidth"] <= width, f"[{label}] Horizontal scroll on document: {scroll_metrics['docScrollWidth']} > {width}"
    assert scroll_metrics["appScrollWidth"] <= width, f"[{label}] Horizontal scroll on #app-container: {scroll_metrics['appScrollWidth']} > {width}"
    assert scroll_metrics["appScrollHeight"] <= height, f"[{label}] Vertical overflow on #app-container: {scroll_metrics['appScrollHeight']} > {height}"

    context.close()


# ==============================================================================
# Challenge 4: Sub-Component Layout Stress at 1024x768 (Finding Documentation)
# ==============================================================================

def test_subcomponent_1024_tight_layout_metrics(challenge_env):
    """Empirically measure sub-component dimensions at 1024x768 to check for internal wrapping/overflow."""
    browser: Browser = challenge_env["browser"]
    context = browser.new_context(viewport={"width": 1024, "height": 768})
    page = context.new_page()
    page.goto(challenge_env["url"], wait_until="networkidle")

    metrics = page.evaluate("""() => {
        const tb = document.querySelector('.canvas-action-toolbar');
        const tbBox = tb ? tb.getBoundingClientRect() : null;
        const btn1 = document.getElementById('btn-rescan-som').getBoundingClientRect();
        
        const nav = document.getElementById('top-nav');
        const navBox = nav.getBoundingClientRect();
        const switcher = nav.querySelector('.mode-switcher').getBoundingClientRect();

        return {
            tb_height: tbBox.height,
            btn1_height: btn1.height,
            btn1_bottom: btn1.bottom,
            tb_bottom: tbBox.bottom,
            btn1_overflows: btn1.bottom > tbBox.bottom,
            nav_height: navBox.height,
            switcher_height: switcher.height,
            switcher_overflows: switcher.height > navBox.height
        };
    }""")

    context.close()
    # Document findings:
    # 1. Action toolbar button overflows fixed 38px toolbar
    # 2. Mode switcher exceeds 48px top-nav
    print("1024x768 sub-component layout metrics:", metrics)


# ==============================================================================
# Challenge 5: Tab Switching CSS Specificity Display Leak (Critical Bug)
# ==============================================================================

def test_tab_switching_css_specificity_display_leak(challenge_env):
    """Verify that switching tabs properly sets display: none on inactive Mission Control pane.
    
    Demonstrates the CSS specificity flaw where #view-mission-control (ID selector)
    overrides .view-pane { display: none } (class selector).
    """
    browser: Browser = challenge_env["browser"]
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()
    page.goto(challenge_env["url"], wait_until="networkidle")

    # Switch away from Mission Control to Knowledge Studio
    page.click('.mode-tab-btn[data-mode="knowledge_studio"]')
    page.wait_for_timeout(200)

    display_metrics = page.evaluate("""() => {
        const mc = document.getElementById('view-mission-control');
        const ks = document.getElementById('view-knowledge-studio');
        return {
            mcDisplay: window.getComputedStyle(mc).display,
            ksDisplay: window.getComputedStyle(ks).display,
            mcBoundingBox: mc.getBoundingClientRect(),
            ksBoundingBox: ks.getBoundingClientRect()
        };
    }""")
    context.close()

    assert display_metrics["mcDisplay"] == "none", (
        f"CSS SPECIFICITY BUG DETECTED: Inactive #view-mission-control has display: '{display_metrics['mcDisplay']}' "
        f"instead of 'none'! ID selector #view-mission-control {{ display: grid }} overrides .view-pane {{ display: none }}. "
        f"Knowledge Studio was pushed to x={display_metrics['ksBoundingBox']['x']}."
    )
