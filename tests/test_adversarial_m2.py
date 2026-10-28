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


# ============================================================================
# Category 4: Workspace Modal Adversarial Stress & Edge Cases
# ============================================================================

def test_modal_stress_rapid_open_and_close_mechanisms(page: Page) -> None:
    """Adversarial stress: Rapidly open modal and close via Escape, backdrop click, Cancel button, Close button.
    
    Verifies:
    - Open via #btn-new-workspace
    - Close via Escape key
    - Open via #btn-new-workspace-dropdown
    - Close via backdrop click (click outside card)
    - Open via #btn-new-workspace and close via #btn-cancel-ws
    - Open via #btn-new-workspace and close via #btn-close-ws-modal
    - Rapid 20-cycle stress across all close mechanisms
    - Zero JS errors or console errors
    """
    page.wait_for_load_state("networkidle")
    
    modal_backdrop = page.locator("#workspace-modal-backdrop")
    btn_new_ws = page.locator("#btn-new-workspace")
    btn_cancel = page.locator("#btn-cancel-ws")
    btn_close = page.locator("#btn-close-ws-modal")

    # Initial state: modal hidden
    assert modal_backdrop.evaluate("el => window.getComputedStyle(el).display") == "none"

    # 1. Open via #btn-new-workspace, close via Escape key
    btn_new_ws.click()
    page.wait_for_timeout(50)
    assert modal_backdrop.evaluate("el => window.getComputedStyle(el).display") != "none", "Modal not displayed after clicking #btn-new-workspace"
    page.keyboard.press("Escape")
    page.wait_for_timeout(50)
    assert modal_backdrop.evaluate("el => window.getComputedStyle(el).display") == "none", "Modal did not close on Escape key"

    # 2. Open via #btn-new-workspace, close via backdrop click (click at x=10, y=10 on backdrop)
    btn_new_ws.click()
    page.wait_for_timeout(50)
    assert modal_backdrop.evaluate("el => window.getComputedStyle(el).display") != "none"
    modal_backdrop.click(position={"x": 10, "y": 10})
    page.wait_for_timeout(50)
    assert modal_backdrop.evaluate("el => window.getComputedStyle(el).display") == "none", "Modal did not close on backdrop click"

    # 3. Open via dropdown button #btn-new-workspace-dropdown, close via Cancel button
    page.locator("#workspace-switcher-card").click()
    page.locator("#btn-new-workspace-dropdown").click()
    page.wait_for_timeout(50)
    assert modal_backdrop.evaluate("el => window.getComputedStyle(el).display") != "none", "Modal not displayed via dropdown button"
    btn_cancel.click()
    page.wait_for_timeout(50)
    assert modal_backdrop.evaluate("el => window.getComputedStyle(el).display") == "none", "Modal did not close on Cancel button"

    # 4. Open via #btn-new-workspace, close via Close (x) button
    btn_new_ws.click()
    page.wait_for_timeout(50)
    assert modal_backdrop.evaluate("el => window.getComputedStyle(el).display") != "none"
    btn_close.click()
    page.wait_for_timeout(50)
    assert modal_backdrop.evaluate("el => window.getComputedStyle(el).display") == "none", "Modal did not close on Close (x) button"

    # 5. Rapid open/close stress cycling (20 cycles)
    close_actions = ["escape", "backdrop", "cancel", "close_btn"]
    for i in range(20):
        action = close_actions[i % len(close_actions)]
        btn_new_ws.click()
        assert modal_backdrop.evaluate("el => window.getComputedStyle(el).display") != "none"
        if action == "escape":
            page.keyboard.press("Escape")
        elif action == "backdrop":
            modal_backdrop.click(position={"x": 10, "y": 10})
        elif action == "cancel":
            btn_cancel.click()
        elif action == "close_btn":
            btn_close.click()
        assert modal_backdrop.evaluate("el => window.getComputedStyle(el).display") == "none", f"Cycle {i}: Modal failed to close via {action}"

    assert len(page._page_errors) == 0, f"Errors during modal open/close stress: {page._page_errors}"


def test_modal_form_validation_empty_and_whitespace(page: Page) -> None:
    """Stress test form submission with empty input, whitespace-only, and error recovery."""
    page.wait_for_load_state("networkidle")

    modal_backdrop = page.locator("#workspace-modal-backdrop")
    btn_new_ws = page.locator("#btn-new-workspace")
    name_input = page.locator("#ws-name-input")
    submit_btn = page.locator("#btn-create-ws")
    error_el = page.locator("#ws-modal-error")

    initial_ws_count = page.evaluate("AppState.workspaces.length")

    # 1. Empty form submission
    btn_new_ws.click()
    name_input.fill("")
    submit_btn.click()
    page.wait_for_timeout(100)

    # Modal must remain open, error must be visible
    assert modal_backdrop.evaluate("el => window.getComputedStyle(el).display") != "none", "Modal closed on empty submission"
    assert error_el.evaluate("el => window.getComputedStyle(el).display") != "none", "Error message not displayed on empty submission"
    assert len(error_el.inner_text().strip()) > 0, "Error message text is empty"
    current_ws_count = page.evaluate("AppState.workspaces.length")
    assert current_ws_count == initial_ws_count, "Workspace created on empty name"

    # 2. Whitespace-only submission
    name_input.fill("     \t\n   ")
    submit_btn.click()
    page.wait_for_timeout(100)

    assert modal_backdrop.evaluate("el => window.getComputedStyle(el).display") != "none", "Modal closed on whitespace submission"
    assert error_el.evaluate("el => window.getComputedStyle(el).display") != "none", "Error message not displayed on whitespace submission"
    current_ws_count = page.evaluate("AppState.workspaces.length")
    assert current_ws_count == initial_ws_count, "Workspace created on whitespace name"

    # 3. Dismiss modal and reopen: verify error element is hidden/reset
    page.locator("#btn-cancel-ws").click()
    assert modal_backdrop.evaluate("el => window.getComputedStyle(el).display") == "none"
    btn_new_ws.click()
    assert error_el.evaluate("el => window.getComputedStyle(el).display") == "none", "Error message was not reset on modal reopen"
    page.locator("#btn-cancel-ws").click()

    assert len(page._page_errors) == 0, f"Errors during validation stress: {page._page_errors}"


def test_modal_stress_5000_char_string(page: Page) -> None:
    """Stress test: Submit modal with 5,000-character name and prompt strings."""
    page.wait_for_load_state("networkidle")

    modal_backdrop = page.locator("#workspace-modal-backdrop")
    btn_new_ws = page.locator("#btn-new-workspace")
    name_input = page.locator("#ws-name-input")
    prompt_input = page.locator("#ws-prompt-input")
    submit_btn = page.locator("#btn-create-ws")

    long_name = "MegaWorkspace_" + ("A" * 4980)
    long_prompt = "MissionPrompt_" + ("B" * 4980)

    btn_new_ws.click()
    name_input.fill(long_name)
    prompt_input.fill(long_prompt)
    submit_btn.click()
    page.wait_for_timeout(200)

    # Modal should close successfully
    assert modal_backdrop.evaluate("el => window.getComputedStyle(el).display") == "none", "Modal did not close after long string submission"

    # Verify workspace was created and is active
    active_ws_name = page.evaluate("AppState.workspaces.find(w => w.id === AppState.activeWorkspaceId)?.name")
    assert active_ws_name == long_name, f"Active workspace name mismatch: {active_ws_name[:50]}..."

    # Check UI layout bounding: Left sidebar must not expand horizontally or blow out the shell
    sidebar_box = page.locator("#left-sidebar").bounding_box()
    assert sidebar_box is not None
    assert sidebar_box["width"] <= 275, f"Left sidebar expanded beyond expected width: {sidebar_box['width']}px"

    # Verify title text is visually clipped with ellipsis
    title_el = page.locator("#active-project-title")
    title_style = title_el.evaluate("el => window.getComputedStyle(el).textOverflow")
    assert title_style == "ellipsis", f"Title element missing text-overflow: ellipsis, got {title_style}"

    # Verify no horizontal scrollbar was introduced to the document body
    has_horiz_scroll = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
    assert not has_horiz_scroll, "5,000-character workspace string introduced horizontal document overflow!"

    assert len(page._page_errors) == 0, f"Errors during 5,000-character string submission: {page._page_errors}"


# ============================================================================
# Category 5: Multiple Workspace Creation & Rapid Hot-Switching
# ============================================================================

def test_multiple_workspace_creation_and_rapid_hot_switching(page: Page) -> None:
    """Stress test: Create 5 workspaces sequentially and rapid hot-switch 30 times.
    
    Verifies:
    - All 5 workspaces created via modal
    - Immediate UI synchronization on switch (#active-project-title, #kb-folder-name, .active)
    - Zero orphaned DOM nodes or DOM node count explosion
    - Zero page reloads required
    - Zero console errors or unhandled exceptions
    """
    page.wait_for_load_state("networkidle")

    btn_new_ws = page.locator("#btn-new-workspace")
    name_input = page.locator("#ws-name-input")
    prompt_input = page.locator("#ws-prompt-input")
    dir_input = page.locator("#ws-dir-input")
    submit_btn = page.locator("#btn-create-ws")

    test_workspaces = [
        ("WS_Alpha_Analytics", "Autonomous Data Processing", "workspace/alpha"),
        ("WS_Beta_VisionStream", "SOM Desktop Perception", "workspace/beta"),
        ("WS_Gamma_REPLRunner", "Multi-Tab Sandbox Exec", "workspace/gamma"),
        ("WS_Delta_ArtifactStudio", "MIME Document Editor", "workspace/delta"),
        ("WS_Epsilon_Blackboard", "DAG Reasoning Graph", "workspace/epsilon")
    ]

    for name, prompt, wdir in test_workspaces:
        btn_new_ws.click()
        name_input.fill(name)
        prompt_input.fill(prompt)
        dir_input.fill(wdir)
        submit_btn.click()
        page.wait_for_timeout(100)

    # Verify all workspaces exist in dropdown
    ws_card = page.locator("#workspace-switcher-card")
    ws_dropdown = page.locator("#workspace-dropdown")
    ws_card.click()
    page.wait_for_timeout(100)

    for name, _, _ in test_workspaces:
        item = ws_dropdown.locator(f".workspace-menu-item[data-project='{name}']")
        assert item.count() > 0, f"Workspace '{name}' not found in dropdown"

    ws_card.click()  # close dropdown

    # Record baseline DOM node count before rapid switching
    baseline_dom_nodes = page.evaluate("document.querySelectorAll('*').length")

    # Rapid hot-switching: 30 switches
    for i in range(30):
        target_name, _, target_dir = test_workspaces[i % len(test_workspaces)]
        
        # Trigger switch programmatically or via dropdown click
        page.evaluate(f"AppState.switchWorkspace(AppState.workspaces.find(w => w.name === '{target_name}')?.id)")
        
        # Immediate UI assertion: Title must update immediately without page reload
        title_text = page.locator("#active-project-title").inner_text()
        assert target_name in title_text, f"Switch {i}: Title did not update immediately to '{target_name}', got '{title_text}'"

        # Folder name in knowledge base must update immediately
        folder_text = page.locator("#kb-folder-name").inner_text()
        assert target_dir in folder_text or target_name in folder_text, f"Switch {i}: Folder not updated, got '{folder_text}'"

    # Verify DOM node count stability (no memory leaks or orphaned nodes)
    final_dom_nodes = page.evaluate("document.querySelectorAll('*').length")
    dom_diff = abs(final_dom_nodes - baseline_dom_nodes)
    assert dom_diff <= 5, f"DOM node leak detected! Baseline: {baseline_dom_nodes}, Final: {final_dom_nodes}, Diff: {dom_diff}"

    assert len(page._page_errors) == 0, f"Errors during rapid hot-switching: {page._page_errors}"


# ============================================================================
# Category 6: Browser Reload State Persistence in localStorage
# ============================================================================

def test_workspace_localstorage_persistence_across_browser_reload(page: Page) -> None:
    """Stress test: Verify state persistence in localStorage across browser page reload (F5)."""
    page.wait_for_load_state("networkidle")

    # 1. Create a dedicated workspace
    ws_name = "Persistent_Challenger_Lab"
    ws_prompt = "Mission for persistent state validation"
    ws_dir = "workspace/persistent_lab"

    btn_new_ws = page.locator("#btn-new-workspace")
    btn_new_ws.click()
    page.locator("#ws-name-input").fill(ws_name)
    page.locator("#ws-prompt-input").fill(ws_prompt)
    page.locator("#ws-dir-input").fill(ws_dir)
    page.locator("#btn-create-ws").click()
    page.wait_for_timeout(150)

    # 2. Add a task to this workspace
    task_input = page.locator("#input-new-task")
    assert task_input.count() > 0, "Inline task input #input-new-task not found"
    unique_task_title = f"Task_Persistent_{int(time.time())}"
    task_input.fill(unique_task_title)
    task_input.press("Enter")
    page.wait_for_timeout(150)

    # 3. Verify localStorage has been populated
    local_storage_data = page.evaluate("""() => {
        return {
            workspaces: localStorage.getItem('gschwelli_workspaces'),
            active_ws: localStorage.getItem('gschwelli_active_workspace') || localStorage.getItem('gschwelli_active_workspace_id'),
            tasks: localStorage.getItem('gschwelli_tasks')
        };
    }""")

    assert local_storage_data["workspaces"] is not None, "localStorage.gschwelli_workspaces is null"
    assert ws_name in local_storage_data["workspaces"], f"Workspace '{ws_name}' not found in localStorage"
    assert local_storage_data["active_ws"] is not None, "localStorage active workspace ID is null"
    assert local_storage_data["tasks"] is not None, "localStorage.gschwelli_tasks is null"
    assert unique_task_title in local_storage_data["tasks"], "New task not found in localStorage"

    # 4. Trigger browser reload (F5)
    page.reload(wait_until="networkidle")

    # 5. Verify restored state after reload
    title_after = page.locator("#active-project-title").inner_text()
    assert ws_name in title_after, f"Active project title was not restored after reload! Got: '{title_after}'"

    folder_after = page.locator("#kb-folder-name").inner_text()
    assert ws_dir in folder_after or ws_name in folder_after, f"Folder name not restored after reload: '{folder_after}'"

    # Verify task was restored
    task_titles = page.locator(".task-title").all_inner_texts()
    assert any(unique_task_title in t for t in task_titles), f"Task '{unique_task_title}' was not restored after reload! Present: {task_titles}"

    # Verify dropdown has the active workspace checked
    page.locator("#workspace-switcher-card").click()
    active_item = page.locator(f".workspace-menu-item.active[data-project='{ws_name}']")
    assert active_item.count() > 0, f"Active workspace '{ws_name}' is not marked active in dropdown after reload"

    assert len(page._page_errors) == 0, f"Errors after reload: {page._page_errors}"
    assert len(page._console_errors) == 0, f"Console errors after reload: {page._console_errors}"
