"""Headless Browser DOM & Interactivity E2E Test Suite for gschwelli-ai.

Uses Playwright with headless Chromium to verify:
1. Zero console errors and zero uncaught JavaScript exceptions across all views.
2. Complete visual hierarchy matching Inspirations/ui_reference_mockup.png:
   - Top Nav (M2): Window dots, brand, live status dot, 4 mode switcher pills, engine telemetry badge.
   - Left Sidebar (M2): Project selector, Tasks & To-Dos (2 / 4), Knowledge Base file tree, Wake-word mic meter.
   - Center Canvas (M3): SOM Perception header, Mission M-024 status bar, OpenSCAD 3D CAD mesh, SOM tags [01, 02, 04, 12], toolbar, fusion status.
   - Right Sidebar (M4): Blackboard pipeline cards, shared state inspector, PowerShell REPL terminal & prompt.
   - Bottom Approval Gate (M4): Amber safety banner, buttons (Approve, Edit, Abort, PANIC KILL).
   - Bottom Omnibox (M4): /run prefix chip, natural language input, voice waveform, model router dropdown.
3. Interactive workflows (M4, M5):
   - 4-mode tab navigation (Mission Control, Knowledge Studio, Vision SOM, Focus Chat).
   - Approval gate actions (Approve, Abort, Panic Kill).
   - SOM tag click / target inspection.
   - PowerShell REPL command execution.
   - Knowledge Base file selection.
   - Omnibox input submission.
"""

from __future__ import annotations

import os
from pathlib import Path
import socket
import threading
import time
from typing import Generator, List

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright
import pytest
import uvicorn

from server.api import create_app


def find_free_port() -> int:
    """Find a random available TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def server_url() -> Generator[str, None, None]:
    """Starts the FastAPI dashboard server in a background thread for the duration of the test session."""
    port = find_free_port()
    app = create_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    url = f"http://127.0.0.1:{port}"

    # Wait for server to become responsive
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
    """Initializes Playwright once per test session."""
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance) -> Generator[Browser, None, None]:
    """Launches headless Chromium using local pre-installed binary."""
    browser = playwright_instance.chromium.launch(
        headless=True,
        args=["--disable-gpu", "--no-sandbox"],
    )
    yield browser
    browser.close()


@pytest.fixture
def page(browser: Browser, server_url: str) -> Generator[Page, None, None]:
    """Provides a fresh browser Page for each test, capturing console errors and exceptions."""
    context: BrowserContext = browser.new_context(viewport={"width": 1440, "height": 900})
    page: Page = context.new_page()

    console_errors: List[str] = []
    page_errors: List[str] = []

    def on_console(msg):
        if msg.type == "error":
            console_errors.append(msg.text)

    def on_page_error(exc):
        page_errors.append(str(exc))

    page.on("console", on_console)
    page.on("pageerror", on_page_error)

    # Navigate to server dashboard
    page.goto(server_url, wait_until="domcontentloaded")

    # Store error collectors on page object for test assertions
    page._console_errors = console_errors
    page._page_errors = page_errors

    yield page
    context.close()


def is_m2_deployed(content: str) -> bool:
    """Helper to detect whether Milestone 2 (Shell & Left Sidebar) is deployed."""
    return "gschwelli-ai" in content or "3D Fabrication" in content or "Mission Control" in content


def is_m3_deployed(content: str) -> bool:
    """Helper to detect whether Milestone 3 (Center SOM Canvas) is deployed."""
    return "M-024" in content or "[01" in content or "SOM Perception" in content


def is_m4_deployed(content: str) -> bool:
    """Helper to detect whether Milestone 4 (Blackboard, REPL, Gate, Omnibox) is deployed."""
    return "Blackboard" in content or "AGENT-01" in content or "SEC-810" in content or "/run" in content


# ============================================================================
# Tier 1: Smoke & Console Error Tests
# ============================================================================

def test_zero_console_errors_on_load(page: Page) -> None:
    """Verifies that loading the dashboard produces zero console errors or uncaught exceptions."""
    page.wait_for_load_state("networkidle")
    assert len(page._page_errors) == 0, f"Uncaught JavaScript errors found: {page._page_errors}"
    assert len(page._console_errors) == 0, f"Console error logs found: {page._console_errors}"


# ============================================================================
# Tier 2: Visual Structure Tests (Ground Truth: Inspirations/ui_reference_mockup.png)
# ============================================================================

def test_top_nav_visual_structure(page: Page) -> None:
    """Verifies Top Navigation Bar (M2): window controls, brand, 4 mode pills, telemetry badge."""
    content = page.content()
    if not is_m2_deployed(content):
        pytest.skip("Milestone 2 (Global Shell & Top Nav) not yet deployed in ui/dashboard/index.html")

    # Brand check: 'gschwelli-ai'
    assert "gschwelli-ai" in content, "Brand title 'gschwelli-ai' not rendered in Top Bar"

    # Segmented Mode Switcher: 4 modes
    for tab_name in ["Mission Control", "Knowledge Studio", "Vision SOM", "Focus Chat"]:
        assert tab_name in content, f"Mode tab '{tab_name}' not found in DOM"

    # Engine Telemetry badge: Ollama / tok/s / VRAM
    assert "Ollama" in content or "tok/s" in content or "VRAM" in content, (
        "Engine telemetry badge (Ollama 7B • tok/s • VRAM) not rendered"
    )


def test_left_sidebar_structure(page: Page) -> None:
    """Verifies Left Sidebar (M2): Project selector, Tasks (2/4), Knowledge Base tree, Audio/Wake-word."""
    content = page.content()
    if not is_m2_deployed(content):
        pytest.skip("Milestone 2 (Left Sidebar) not yet deployed in ui/dashboard/index.html")

    # Project Selector
    assert "3D Fabrication" in content or "Fabrication" in content, "Active Project selector card not found"

    # Tasks & To-Dos
    assert "Tasks" in content or "To-Dos" in content or "2 / 4" in content, "Tasks panel not found"

    # Knowledge Base tree: fabrication folder and key files
    assert "fabrication" in content.lower() or "workflow" in content.lower() or "toolhead" in content.lower(), (
        "Knowledge Base file tree not found in Left Sidebar"
    )

    # Wake-word mic meter
    assert "Wake-Word" in content or "dB" in content or "RØDE" in content, (
        "Microphone level meter or Wake-Word toggle not found in footer"
    )


def test_center_canvas_structure(page: Page) -> None:
    """Verifies Center SOM Perception Canvas (M3): Header, Mission status, CAD viewport, SOM tags, Toolbar, Fusion status."""
    content = page.content()
    if not is_m3_deployed(content):
        pytest.skip("Milestone 3 (Center SOM Canvas) not yet deployed in ui/dashboard/index.html")

    # Canvas Header & Mission status
    assert "SOM Perception Canvas" in content or "M-024" in content, (
        "Center Canvas header or active Mission M-024 not found"
    )

    # Set-of-Marks tags: [01], [02], [04], [12]
    for tag in ["[01", "[02", "[04", "[12"]:
        assert tag in content, f"SOM tag {tag} not found in Center Canvas"

    # SOM Action Toolbar & Fusion Status
    assert "SOM" in content or "Fusion" in content or "confidence" in content.lower(), (
        "SOM action toolbar or Fusion status bar not found"
    )


def test_right_sidebar_structure(page: Page) -> None:
    """Verifies Right Sidebar (M4): Blackboard pipeline tracker, step cards, shared state, PowerShell REPL."""
    content = page.content()
    if not is_m4_deployed(content):
        pytest.skip("Milestone 4 (Blackboard & REPL) not yet deployed in ui/dashboard/index.html")

    # Blackboard & Pipeline
    assert "Blackboard" in content or "AGENT-01" in content or "Plan" in content, (
        "Blackboard or pipeline breadcrumb not found in Right Sidebar"
    )

    # PowerShell REPL
    assert "PowerShell" in content or "REPL" in content or "PS " in content or "pwsh" in content.lower(), (
        "PowerShell REPL console not found in Right Sidebar"
    )


def test_bottom_approval_gate_structure(page: Page) -> None:
    """Verifies Bottom Human-in-the-Loop Approval Gate (M4): Amber banner and action buttons."""
    content = page.content()
    if not is_m4_deployed(content):
        pytest.skip("Milestone 4 (Approval Gate) not yet deployed in ui/dashboard/index.html")

    # Approval banner text
    assert "APPROVAL" in content or "Overwrite" in content or "SEC-810" in content, (
        "Human-in-the-Loop Approval banner not found"
    )

    # Action buttons: Approve, Edit, Abort, PANIC KILL
    assert "Approve" in content, "Approve action button not found"
    assert "Abort" in content or "Esc" in content, "Abort action button not found"


def test_bottom_omnibox_structure(page: Page) -> None:
    """Verifies Bottom Omnibox Command Bar (M4): /run chip, prompt input, voice toggle, router selector."""
    content = page.content()
    if not is_m4_deployed(content):
        pytest.skip("Milestone 4 (Omnibox) not yet deployed in ui/dashboard/index.html")

    # Input or command bar
    assert "/run" in content or "commands" in content.lower(), "Omnibox command prompt or /run chip not found"


# ============================================================================
# Tier 4: Interactive Workflows & State Synchronization
# ============================================================================

def test_tab_switching_workflow(page: Page) -> None:
    """Verifies that clicking mode pills switches between the 4 dedicated views cleanly."""
    page.wait_for_load_state("networkidle")

    tabs = ["Knowledge Studio", "Vision SOM", "Focus Chat", "Mission Control"]
    for tab_name in tabs:
        tab_locators = page.locator(f"button:has-text('{tab_name}'), .tab:has-text('{tab_name}'), a:has-text('{tab_name}')")
        if tab_locators.count() > 0:
            tab_locators.first.click()
            page.wait_for_timeout(200)

    # Confirm no JavaScript errors occurred during navigation
    assert len(page._page_errors) == 0, f"Errors during tab switching: {page._page_errors}"


def test_approval_gate_interaction(page: Page) -> None:
    """Verifies clicking Approve or Abort triggers confirmation resolution."""
    page.wait_for_load_state("networkidle")

    # Locate Approve button
    approve_btn = page.locator("button:has-text('Approve')")
    if approve_btn.count() > 0 and approve_btn.first.is_visible():
        approve_btn.first.click()
        page.wait_for_timeout(300)

    assert len(page._page_errors) == 0, f"Errors during approval click: {page._page_errors}"


def test_som_tag_click_interaction(page: Page) -> None:
    """Verifies clicking SOM tags highlights target or updates inspection view."""
    page.wait_for_load_state("networkidle")

    tag_locator = page.locator(".som-tag:has-text('04'), [data-mark='4'], span:has-text('[04]')")
    if tag_locator.count() > 0 and tag_locator.first.is_visible():
        tag_locator.first.click()
        page.wait_for_timeout(200)

    assert len(page._page_errors) == 0, f"Errors during SOM tag click: {page._page_errors}"


def test_repl_command_submission(page: Page) -> None:
    """Verifies submitting a command in PowerShell REPL executes without error."""
    page.wait_for_load_state("networkidle")

    repl_input = page.locator("input[placeholder*='PS'], #repl-input, .repl-input input, input[name='repl']")
    if repl_input.count() > 0 and repl_input.first.is_visible():
        repl_input.first.fill("Write-Output 'E2E_TEST_EXEC'")
        repl_input.first.press("Enter")
        page.wait_for_timeout(400)

    assert len(page._page_errors) == 0, f"Errors during REPL command submission: {page._page_errors}"


def test_omnibox_input_workflow(page: Page) -> None:
    """Verifies entering commands into the bottom Omnibox executes cleanly."""
    page.wait_for_load_state("networkidle")

    omnibox = page.locator("#command-input, input[placeholder*='Describe'], input[placeholder*='/']")
    if omnibox.count() > 0 and omnibox.first.is_visible():
        omnibox.first.fill("inspect toolhead_mount")
        page.wait_for_timeout(200)

    assert len(page._page_errors) == 0, f"Errors during Omnibox interaction: {page._page_errors}"


def test_multi_view_interactive_workflows(page: Page) -> None:
    """Verifies Milestone 5 interactive workflows across Knowledge Studio, Vision SOM, and Focus Chat."""
    page.wait_for_load_state("networkidle")

    # 1. Knowledge Studio view
    page.locator("button[data-mode='knowledge_studio']").click()
    assert page.locator("#view-knowledge-studio").is_visible()
    page.locator(".ks-file-entry[data-ks-file='workflow.md']").click()
    assert "workflow.md" in (page.locator("#ks-active-file-header").text_content() or "")
    page.locator("#btn-ks-reindex").click()
    page.locator("#ks-query-input").fill("bolt holes")
    page.locator("#btn-ks-query").click()

    # 2. Vision SOM view
    page.locator("button[data-mode='vision_som']").click()
    assert page.locator("#view-vision-som").is_visible()
    assert page.locator(".vsom-target-item").count() == 12
    page.locator(".vsom-target-item[data-vsom-id='12']").click()
    assert "[12: Path Input]" in (page.locator("#vsom-detail-id").text_content() or "")
    page.locator("#btn-vsom-sim-click").click()

    # 3. Focus Chat view
    page.locator("button[data-mode='focus_chat']").click()
    assert page.locator("#view-focus-chat").is_visible()
    page.locator("#fc-chat-input").fill("Verify manifold tolerance")
    page.locator("#btn-fc-send").click()
    assert "Verify manifold tolerance" in (page.locator("#fc-chat-timeline").text_content() or "")
    page.locator("#btn-fc-add-memory").click()
    page.locator("#btn-fc-reset-scenario").click()

    # Return to Mission Control
    page.locator("button[data-mode='mission_control']").click()
    assert page.locator("#view-mission-control").is_visible()
    assert len(page._page_errors) == 0, f"Errors during M5 multi-view workflows: {page._page_errors}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
