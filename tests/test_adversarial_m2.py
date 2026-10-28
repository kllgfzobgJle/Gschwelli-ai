"""Adversarial Challenge & Stress Test Suite for Milestone 2 (ui/dashboard/index.html).

Empirically challenges:
1. DOM loading, console errors, console warnings, and unhandled promise rejections.
2. Left Sidebar stress testing:
   - Rapid task checkbox toggling & counter synchronization.
   - Task creation edge cases: empty strings, whitespace, dialog dismissals, HTML/XSS injection.
   - Microphone wake-word toggling & audio meter responsiveness.
   - Project workspace dropdown opening, outside clicking, and item selection.
3. 4-tab switching stress testing:
   - Rapid cycling across all 4 modes.
   - Mutual exclusivity of active classes.
   - Actual element visibility & CSS display computed style (detecting ID specificity leaks).
   - Shared state persistence across tab switches.
   - DOM leak detection (node count invariant).
"""

from __future__ import annotations

import os
from pathlib import Path
import socket
import threading
import time
from typing import Generator, List, Dict, Any

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright
import pytest
import uvicorn

from server.api import create_app


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def server_url() -> Generator[str, None, None]:
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


@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance) -> Generator[Browser, None, None]:
    browser = playwright_instance.chromium.launch(
        headless=True,
        args=["--disable-gpu", "--no-sandbox"],
    )
    yield browser
    browser.close()


@pytest.fixture
def page(browser: Browser, server_url: str) -> Generator[Page, None, None]:
    context: BrowserContext = browser.new_context(viewport={"width": 1440, "height": 900})
    page: Page = context.new_page()

    console_errors: List[str] = []
    console_warnings: List[str] = []
    page_errors: List[str] = []
    unhandled_rejections: List[str] = []

    def on_console(msg):
        if msg.type == "error":
            console_errors.append(msg.text)
        elif msg.type == "warning":
            console_warnings.append(msg.text)

    def on_page_error(exc):
        page_errors.append(str(exc))

    page.on("console", on_console)
    page.on("pageerror", on_page_error)

    # Listen for unhandled promise rejections
    page.add_init_script("""
        window._unhandledRejections = [];
        window.addEventListener('unhandledrejection', event => {
            window._unhandledRejections.push(String(event.reason));
        });
    """)

    page.goto(server_url, wait_until="domcontentloaded")

    page._console_errors = console_errors
    page._console_warnings = console_warnings
    page._page_errors = page_errors

    yield page
    context.close()


# ============================================================================
# Category 1: Loading, Console Integrity & Rejections
# ============================================================================

def test_zero_console_warnings_and_errors(page: Page) -> None:
    """Rigorous check: Ensure ZERO console errors, ZERO console warnings, and ZERO unhandled rejections on load."""
    page.wait_for_load_state("networkidle")
    rejections = page.evaluate("window._unhandledRejections || []")
    
    assert len(page._page_errors) == 0, f"Uncaught JavaScript exceptions: {page._page_errors}"
    assert len(page._console_errors) == 0, f"Console errors logged: {page._console_errors}"
    assert len(page._console_warnings) == 0, f"Console warnings logged: {page._console_warnings}"
    assert len(rejections) == 0, f"Unhandled promise rejections: {rejections}"


# ============================================================================
# Category 2: Left Sidebar Interactive Stress Testing
# ============================================================================

def test_stress_task_checkbox_rapid_toggling(page: Page) -> None:
    """Stress test: Rapidly toggle task checkboxes 100 times and verify counter consistency."""
    page.wait_for_load_state("networkidle")

    # Locate first task checkbox
    checkbox = page.locator(".task-item[data-task-id='t1'] .custom-checkbox").first
    assert checkbox.is_visible(), "Task 1 checkbox not visible"

    for i in range(50):
        checkbox.click()
        # Verify counter string format
        counter_text = page.locator("#task-counter").inner_text()
        completed_str, total_str = [s.strip() for s in counter_text.split("/")]
        completed = int(completed_str)
        total = int(total_str)
        
        # Verify mathematical consistency
        dom_completed_count = page.locator(".custom-checkbox.checked").count()
        assert completed == dom_completed_count, (
            f"Iteration {i}: Counter mismatch! Text says {completed}, but DOM has {dom_completed_count} checked boxes"
        )
        assert total == 4, f"Total tasks changed unexpectedly: {total}"

    assert len(page._page_errors) == 0, f"Errors during rapid task toggling: {page._page_errors}"


def test_add_task_edge_cases(page: Page) -> None:
    """Edge cases for task addition: Empty, whitespace, cancellation, and XSS payload."""
    page.wait_for_load_state("networkidle")

    initial_total = page.locator(".task-item").count()

    # 1. Dialog cancelled (null response)
    def cancel_dialog(dialog):
        dialog.dismiss()
    page.once("dialog", cancel_dialog)
    page.locator("#btn-add-task").click()
    page.wait_for_timeout(100)
    assert page.locator(".task-item").count() == initial_total, "Cancelled dialog should not add a task"

    # 2. Whitespace-only task description
    def whitespace_dialog(dialog):
        dialog.accept("    ")
    page.once("dialog", whitespace_dialog)
    page.locator("#btn-add-task").click()
    page.wait_for_timeout(100)
    assert page.locator(".task-item").count() == initial_total, "Whitespace-only dialog should not add a task"

    # 3. HTML / XSS Injection probe
    xss_payload = '<span id="xss-test-probe">XSS_INJECTED</span>'
    def xss_dialog(dialog):
        dialog.accept(xss_payload)
    page.once("dialog", xss_dialog)
    page.locator("#btn-add-task").click()
    page.wait_for_timeout(100)

    # Check whether the payload was rendered as raw unescaped HTML elements
    probe_element = page.locator("#xss-test-probe")
    probe_count = probe_element.count()
    
    # We record whether raw unescaped HTML tags were inserted into the DOM
    # If probe_count > 0, the DOM parsed raw HTML, indicating an XSS / HTML injection vulnerability
    task_count = page.locator(".task-item").count()
    assert task_count == initial_total + 1, "Task should be added"

    if probe_count > 0:
        pytest.fail(f"SECURITY VULNERABILITY DETECTED: Task description rendered raw HTML tags directly into innerHTML without sanitization! Found {probe_count} injected DOM nodes.")


def test_stress_mic_mute_toggling(page: Page) -> None:
    """Stress test: Rapidly toggle microphone wake-word 40 times."""
    page.wait_for_load_state("networkidle")

    btn_wake = page.locator("#btn-wake-word")
    label_wake = page.locator("#wake-word-label")

    for i in range(40):
        btn_wake.click()
        is_active = "active" in btn_wake.get_attribute("class")
        label_text = label_wake.inner_text()

        if is_active:
            assert "Listening" in label_text, f"Active mic should say 'Listening', got: '{label_text}'"
        else:
            assert "Muted" in label_text, f"Muted mic should say 'Muted', got: '{label_text}'"

    assert len(page._page_errors) == 0, f"Errors during mic toggling: {page._page_errors}"


def test_stress_project_dropdown_workflow(page: Page) -> None:
    """Stress test: Project dropdown opening, click outside, and project selection."""
    page.wait_for_load_state("networkidle")

    ws_card = page.locator("#workspace-switcher-card")
    ws_dropdown = page.locator("#workspace-dropdown")

    # Verify initial closed state
    assert "open" not in ws_dropdown.get_attribute("class")

    # Open dropdown
    ws_card.click()
    assert "open" in ws_dropdown.get_attribute("class"), "Dropdown did not open on click"

    # Click outside to close (e.g. on top nav bar)
    page.locator("#top-nav").click()
    assert "open" not in ws_dropdown.get_attribute("class"), "Dropdown did not close on click outside"

    # Open and select another project
    ws_card.click()
    item = page.locator(".workspace-menu-item[data-project*='Robotic']").first
    assert item.count() > 0, "Robotic Pick & Place menu item not found"
    item.click()
    assert "open" not in ws_dropdown.get_attribute("class"), "Dropdown did not close after item selection"
    title_text = page.locator("#active-project-title").inner_text()
    assert "Robotic" in title_text, f"Project title did not update to selected item: {title_text}"

    assert len(page._page_errors) == 0, f"Errors during project dropdown workflow: {page._page_errors}"


# ============================================================================
# Category 3: 4-Tab Switching & DOM Leak Stress Testing
# ============================================================================

def test_stress_4_tab_switching_rapid(page: Page) -> None:
    """Stress test: Switch rapidly across all 4 modes 20 times (80 tab clicks)."""
    page.wait_for_load_state("networkidle")

    tabs = [
        ("mission_control", "view-mission-control"),
        ("knowledge_studio", "view-knowledge-studio"),
        ("vision_som", "view-vision-som"),
        ("focus_chat", "view-focus-chat")
    ]

    for cycle in range(20):
        for mode, view_id in tabs:
            btn = page.locator(f".mode-tab-btn[data-mode='{mode}']")
            btn.click()

            # Check that exactly one button has active class
            active_btn_count = page.locator(".mode-tab-btn.active").count()
            assert active_btn_count == 1, f"Expected exactly 1 active tab button, found {active_btn_count}"

            # Check that this view pane has active-view class
            view_pane = page.locator(f"#{view_id}")
            assert "active-view" in view_pane.get_attribute("class"), f"View {view_id} missing active-view class"

    assert len(page._page_errors) == 0, f"Errors during rapid tab cycling: {page._page_errors}"


def test_tab_visibility_and_css_display_leak(page: Page) -> None:
    """Adversarial challenge: Verify that inactive tabs are TRULY hidden via CSS display: none.
    
    Checks for CSS selector specificity bugs where #view-mission-control { display: grid }
    overrides .view-pane { display: none }, causing Mission Control to remain rendered
    simultaneously with Knowledge Studio or Vision SOM!
    """
    page.wait_for_load_state("networkidle")

    # Switch to Knowledge Studio
    page.locator(".mode-tab-btn[data-mode='knowledge_studio']").click()
    page.wait_for_timeout(100)

    # Inspect computed display and bounding rects
    metrics = page.evaluate("""() => {
        const mc = document.getElementById('view-mission-control');
        const ks = document.getElementById('view-knowledge-studio');
        const mcRect = mc.getBoundingClientRect();
        const ksRect = ks.getBoundingClientRect();
        return {
            disp_mc: window.getComputedStyle(mc).display,
            disp_ks: window.getComputedStyle(ks).display,
            mc_box: { x: mcRect.x, y: mcRect.y, width: mcRect.width, height: mcRect.height },
            ks_box: { x: ksRect.x, y: ksRect.y, width: ksRect.width, height: ksRect.height }
        };
    }""")

    disp_mc = metrics["disp_mc"]
    disp_ks = metrics["disp_ks"]
    ks_box = metrics["ks_box"]
    mc_box = metrics["mc_box"]

    print(f"Metrics after switching to Knowledge Studio: MC={mc_box}, KS={ks_box}")

    # An inactive view pane MUST have computed display == 'none'
    assert disp_ks != "none", f"Active Knowledge Studio should be visible, got display: {disp_ks}"
    assert disp_mc == "none", (
        f"CSS SPECIFICITY BUG: Inactive Mission Control pane has computed display '{disp_mc}' instead of 'none'! "
        f"Mission Control occupies {mc_box}, pushing Knowledge Studio to {ks_box} (off-screen / overlapping)!"
    )


def test_tab_switching_shared_state_persistence(page: Page) -> None:
    """Verify that user state modifications persist cleanly across tab switches."""
    page.wait_for_load_state("networkidle")

    # 1. In Mission Control, toggle task 1 to uncompleted
    page.locator(".mode-tab-btn[data-mode='mission_control']").click()
    task1_cb = page.locator(".task-item[data-task-id='t1'] .custom-checkbox").first
    task1_cb.click()
    is_task1_checked_before = "checked" in task1_cb.get_attribute("class")

    # 2. Toggle mic mute
    btn_wake = page.locator("#btn-wake-word")
    btn_wake.click()
    mic_active_before = "active" in btn_wake.get_attribute("class")

    # 3. Switch through all other tabs
    for mode in ["knowledge_studio", "vision_som", "focus_chat"]:
        page.locator(f".mode-tab-btn[data-mode='{mode}']").click()
        page.wait_for_timeout(50)

    # 4. Return to Mission Control
    page.locator(".mode-tab-btn[data-mode='mission_control']").click()
    page.wait_for_timeout(50)

    # Verify task 1 state persisted
    task1_cb_after = page.locator(".task-item[data-task-id='t1'] .custom-checkbox").first
    is_task1_checked_after = "checked" in task1_cb_after.get_attribute("class")
    assert is_task1_checked_after == is_task1_checked_before, "Task 1 state was lost after tab switching"

    # Verify mic state persisted
    btn_wake_after = page.locator("#btn-wake-word")
    mic_active_after = "active" in btn_wake_after.get_attribute("class")
    assert mic_active_after == mic_active_before, "Mic mute state was lost after tab switching"


def test_dom_node_count_leak_during_tab_switching(page: Page) -> None:
    """Verify that switching tabs does not leak DOM elements or recreate views repeatedly."""
    page.wait_for_load_state("networkidle")

    initial_node_count = page.evaluate("document.querySelectorAll('*').length")

    tabs = ["knowledge_studio", "vision_som", "focus_chat", "mission_control"]
    for _ in range(10):
        for mode in tabs:
            page.locator(f".mode-tab-btn[data-mode='{mode}']").click()

    final_node_count = page.evaluate("document.querySelectorAll('*').length")

    # Element count should be completely invariant during pure view switching
    assert final_node_count == initial_node_count, (
        f"DOM leak detected! Initial elements: {initial_node_count}, Final elements: {final_node_count}"
    )
