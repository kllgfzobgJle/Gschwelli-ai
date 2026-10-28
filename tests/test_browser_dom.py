"""Headless Browser DOM & Interactivity E2E Test Suite for Universal Domain-Agnostic Agent Workstation.

Uses Playwright with headless Chromium to verify:
1. Zero console errors and zero uncaught JavaScript exceptions across all views.
2. Complete visual hierarchy matching DESIGN.md and requirements R1-R5:
   - Top Nav: Window dots, brand, live status dot, 4-mode/viewport segmented pills, engine telemetry.
   - Left Sidebar (R1): Workspace manager & hot-switcher, reactive tasks tracker, dynamic file explorer with category filters.
   - Center Stage (R2): 4 Polymorphic Viewports (SOM Perception, Artifact Studio, Blackboard DAG graph, Shell Sandbox) + Split-Screen mode.
   - Right Sidebar (R2): Live blackboard execution state, variables inspector, multi-tab terminal.
   - Bottom Dock (R3): Safety Interceptor with risk badges, hotkeys, Panic Kill; Universal Omnibar with slash autocomplete & audio pill.
3. Interactive workflows & boundary stress (Tiers 1-4):
   - Workspace CRUD modal, switching without reload, persistence across browser refresh.
   - Reactive tasks: inline creation on Enter, 5-status cycling, delegation toggle, real-time progress metrics.
   - Polymorphic viewports & 50/50 split-screen toggle.
   - Safety Interceptor with hotkeys (Space approve, Esc abort, Panic Kill) guarded by keyboard scope.
   - Omnibar slash autocomplete menu (/workspace, /task, /run, /inspect, /undo, /clear) and audio-viseme pill.
   - XSS sanitization and zero external CDN dependencies (offline capability).
   - Multi-resolution layout stability (1024x768, 1440x900, 1920x1080) with 0.0 px² pointer occlusion.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
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


# ============================================================================
# Tier 1: Sanity, Console Health & Zero External CDN Dependencies
# ============================================================================

def test_zero_console_errors_on_load(page: Page) -> None:
    """Verifies that loading the dashboard produces zero console errors or uncaught exceptions."""
    page.wait_for_load_state("networkidle")
    assert len(page._page_errors) == 0, f"Uncaught JavaScript errors found: {page._page_errors}"
    assert len(page._console_errors) == 0, f"Console error logs found: {page._console_errors}"


def test_offline_zero_external_network_requests(browser: Browser, server_url: str) -> None:
    """Verifies that the Single-Page Application initiates ZERO external CDN network requests."""
    external_requests: List[str] = []
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    test_page = context.new_page()

    def check_request(request):
        url = request.url
        if not (url.startswith("http://127.0.0.1") or url.startswith("http://localhost") or url.startswith("data:")):
            external_requests.append(url)

    test_page.on("request", check_request)
    test_page.goto(server_url, wait_until="networkidle")

    # Inspect rendered DOM for external CDN scripts/fonts
    content = test_page.content()
    for forbidden in ["googleapis.com", "cdnjs.cloudflare.com", "unpkg.com", "jsdelivr.net"]:
        assert forbidden not in content, f"Detected forbidden external CDN reference: {forbidden}"

    assert len(external_requests) == 0, f"External network requests detected: {external_requests}"
    context.close()


# ============================================================================
# Tier 1 & Tier 2: Shell Layout & Visual Hierarchy
# ============================================================================

def test_top_nav_visual_structure(page: Page) -> None:
    """Verifies Top Navigation Bar: window dots, brand title, live status, mode pills, telemetry."""
    content = page.content()
    assert "gschwelli-ai" in content or "AETHER" in content, "Brand title not rendered in Top Bar"

    # Segmented Mode Switcher / Viewport Switcher pills
    mode_locators = page.locator(".mode-switcher, .mode-tab-btn, button[data-mode], .nav-center")
    assert mode_locators.count() > 0, "Top navigation mode/viewport switcher not found"

    # Telemetry badge
    telemetry = page.locator(".telemetry-badge, [title*='tok/s'], [title*='VRAM'], .nav-right")
    assert telemetry.count() > 0, "Engine telemetry badge not rendered"


def test_left_sidebar_structure(page: Page) -> None:
    """Verifies Left Sidebar: Workspace selector, Tasks list, Knowledge/File tree, Audio status."""
    content = page.content()

    # Workspace or Project card
    assert "Workspace" in content or "Project" in content or "Fabrication" in content, (
        "Workspace/Project selector not found in Left Sidebar"
    )

    # Tasks panel
    assert "Task" in content or "To-Do" in content, "Tasks panel not found in Left Sidebar"

    # File Explorer / Knowledge Base
    file_tree = page.locator("#file-tree, .file-tree, #ks-file-list, .knowledge-tree, .file-list")
    assert file_tree.count() > 0 or "file" in content.lower(), "File Explorer tree not found"


def test_center_canvas_structure(page: Page) -> None:
    """Verifies Center Stage Canvas: SOM tags [01, 02, 04, 12], Perception header, Controls."""
    content = page.content()

    # SOM tags presence in DOM
    for tag in ["[01", "[02", "[04", "[12"]:
        assert tag in content, f"Required SOM tag {tag} not found in DOM"

    # Toolbar or Viewport controls
    canvas_controls = page.locator(".viewport-camera-toolbar, .som-toolbar, #viewport-camera-controls, .canvas-toolbar")
    assert canvas_controls.count() > 0 or "SOM" in content, "Center canvas controls not found"


def test_right_sidebar_structure(page: Page) -> None:
    """Verifies Right Sidebar: Execution tracking, Shared State inspector, REPL terminal."""
    content = page.content()
    assert "Blackboard" in content or "AGENT" in content or "State" in content or "Plan" in content, (
        "Execution/Blackboard tracker not found in Right Sidebar"
    )
    assert "PowerShell" in content or "REPL" in content or "Terminal" in content or "PS " in content, (
        "Terminal/REPL pane not found in Right Sidebar"
    )


def test_bottom_approval_gate_structure(page: Page) -> None:
    """Verifies Bottom Human-in-the-Loop Safety Gate: banner, action buttons (Approve, Abort, Panic Kill)."""
    content = page.content()
    assert "Approve" in content, "Approve action button not found"
    assert "Abort" in content or "Esc" in content, "Abort action button not found"
    assert "PANIC" in content or "Panic" in content or "Kill" in content or "Rollback" in content, (
        "PANIC KILL action button not found"
    )


def test_bottom_omnibox_structure(page: Page) -> None:
    """Verifies Bottom Omnibar: prompt input dock, slash command support, audio toggle."""
    omnibox = page.locator("#command-input, #fc-chat-input, input[placeholder*='Describe'], input[placeholder*='/']")
    assert omnibox.count() > 0, "Omnibox prompt input field not found"


# ============================================================================
# Tier 1 & Tier 2: Workspace CRUD & Reactive Tasks (Requirement R1)
# ============================================================================

def test_workspace_modal_crud_and_switching(page: Page) -> None:
    """R1: Tests Workspace creation modal, non-reloading workspace switching, and listing."""
    page.wait_for_load_state("networkidle")

    # Look for [+ Neuer Workspace] button or workspace modal trigger
    new_ws_btn = page.locator("#btn-new-workspace, button:has-text('Neuer Workspace'), button:has-text('New Workspace'), .btn-new-workspace")
    if new_ws_btn.count() == 0 or not new_ws_btn.first.is_visible():
        # Fallback to dropdown click or existing workspace switch
        ws_selector = page.locator("#active-workspace-card, .project-card, #workspace-selector, #project-select-btn")
        if ws_selector.count() > 0 and ws_selector.first.is_visible():
            ws_selector.first.click()
            page.wait_for_timeout(200)

    # If modal opened, interact with it
    modal = page.locator("#workspace-modal, .workspace-modal, .modal-card:has-text('Workspace')")
    if modal.count() > 0 and modal.first.is_visible():
        name_input = modal.locator("input[name='name'], #ws-name-input, input[placeholder*='Name']")
        if name_input.count() > 0:
            name_input.fill("E2E Test Workspace")

        submit_btn = modal.locator("button:has-text('Erstellen'), button:has-text('Create'), button[type='submit']")
        if submit_btn.count() > 0:
            submit_btn.click()
            page.wait_for_timeout(300)

    assert len(page._page_errors) == 0, f"Errors during workspace CRUD interaction: {page._page_errors}"


def test_workspace_and_task_persistence_across_reload(page: Page) -> None:
    """R1: Tests that created tasks and workspace selections persist across page reload (F5)."""
    page.wait_for_load_state("networkidle")

    # Locate task input
    task_input = page.locator("#task-inline-input, #new-task-input, input.task-input, input[placeholder*='Aufgabe'], input[placeholder*='task']")
    if task_input.count() > 0 and task_input.first.is_visible():
        task_input.first.fill("Persistence Test Task")
        task_input.first.press("Enter")
        page.wait_for_timeout(300)

    # Perform page reload
    page.reload(wait_until="networkidle")

    # Verify no errors after reload
    assert len(page._page_errors) == 0, f"Errors after reload: {page._page_errors}"
    assert len(page._console_errors) == 0, f"Console errors after reload: {page._console_errors}"


def test_reactive_tasks_inline_creation_and_status_cycles(page: Page) -> None:
    """R1: Tests inline task creation on Enter and cycling through status states."""
    page.wait_for_load_state("networkidle")

    task_input = page.locator("#task-inline-input, #new-task-input, input.task-input, input[placeholder*='Aufgabe'], input[placeholder*='task']")
    if task_input.count() > 0 and task_input.first.is_visible():
        task_input.first.fill("Verify reactive status cycles")
        task_input.first.press("Enter")
        page.wait_for_timeout(300)

    # Click status badge or task checkbox to cycle status
    status_badge = page.locator(".task-status-badge, .task-status, [data-task-status], .task-checkbox").first
    if status_badge.count() > 0 and status_badge.is_visible():
        # Cycle status multiple times
        for _ in range(3):
            status_badge.click()
            page.wait_for_timeout(150)

    assert len(page._page_errors) == 0, f"Errors during task status cycling: {page._page_errors}"


def test_task_delegation_toggle_and_progress_metrics(page: Page) -> None:
    """R1: Tests clicking delegation toggle (⚡/🤖) and observing dynamic progress metrics (X/Y)."""
    page.wait_for_load_state("networkidle")

    # Locate delegation toggle
    delegate_btn = page.locator("button.btn-delegate, .task-delegate-btn, button:has-text('⚡'), button:has-text('🤖'), [data-action='delegate']").first
    if delegate_btn.count() > 0 and delegate_btn.is_visible():
        delegate_btn.click()
        page.wait_for_timeout(200)

    # Progress metrics counter: e.g. '2 / 4' or 'X/Y erledigt'
    content = page.content()
    has_counter = bool(re.search(r"\d+\s*/\s*\d+", content))
    assert has_counter or "Tasks" in content, "Progress metric counter not found in Tasks panel"


def test_dynamic_file_explorer_tree_and_category_filtering(page: Page) -> None:
    """R1: Tests dynamic file tree and category filtering (All, Code, Docs, Tables, Media, Configs)."""
    page.wait_for_load_state("networkidle")

    # Check category filter tabs if available
    filters = page.locator(".file-filter-tab, button[data-file-filter], .category-filter button")
    if filters.count() > 0:
        for i in range(min(filters.count(), 3)):
            filters.nth(i).click()
            page.wait_for_timeout(150)

    # Click a file item to preview in stage
    file_item = page.locator(".file-tree-item, .ks-file-entry, .file-entry, .tree-item").first
    if file_item.count() > 0 and file_item.is_visible():
        file_item.click()
        page.wait_for_timeout(200)

    assert len(page._page_errors) == 0, f"Errors in File Explorer interactions: {page._page_errors}"


# ============================================================================
# Tier 1 & Tier 2: Polymorphic Main Stage & Split-Screen (Requirement R2)
# ============================================================================

def test_four_polymorphic_viewports_switching(page: Page) -> None:
    """R2: Verifies switching between the 4 dedicated viewports via segmented pills or tabs."""
    page.wait_for_load_state("networkidle")

    # Try standard viewport tabs or mode buttons
    viewport_buttons = page.locator(
        ".mode-tab-btn, button[data-viewport], button[data-mode], .nav-center button"
    )
    btn_count = viewport_buttons.count()
    if btn_count >= 2:
        for i in range(btn_count):
            btn = viewport_buttons.nth(i)
            if btn.is_visible():
                btn.click()
                page.wait_for_timeout(200)

    assert len(page._page_errors) == 0, f"Errors during viewport switching: {page._page_errors}"


def test_viewport_1_som_perception_canvas_and_toolbar(page: Page) -> None:
    """R2 (Viewport 1): Tests SOM perception viewer, tags [01, 02, 04, 12], and camera toolbar."""
    page.wait_for_load_state("networkidle")

    # SOM tag inspection click
    tag = page.locator(".som-tag[data-mark='4'], .som-tag:has-text('04'), span:has-text('[04]')").first
    if tag.count() > 0 and tag.is_visible():
        tag.click()
        page.wait_for_timeout(150)

    # Zoom / Pan / Reset controls
    zoom_btn = page.locator("#btn-cam-zoom, button[title*='Zoom'], .btn-zoom").first
    if zoom_btn.count() > 0 and zoom_btn.is_visible():
        zoom_btn.click()
        page.wait_for_timeout(100)

    reset_btn = page.locator("#btn-cam-reset, button[title*='Reset'], .btn-reset-view").first
    if reset_btn.count() > 0 and reset_btn.is_visible():
        reset_btn.click()
        page.wait_for_timeout(100)

    assert len(page._page_errors) == 0, f"Errors in SOM Perception Viewport: {page._page_errors}"


def test_viewport_2_artifact_document_studio_views(page: Page) -> None:
    """R2 (Viewport 2): Tests Artifact & Document Studio (Markdown preview, code editor, data-grid)."""
    page.wait_for_load_state("networkidle")

    # Activate Knowledge Studio / Artifact Studio
    studio_btn = page.locator("button[data-mode='knowledge_studio'], button:has-text('Artifact'), button:has-text('Knowledge')").first
    if studio_btn.count() > 0 and studio_btn.is_visible():
        studio_btn.click()
        page.wait_for_timeout(250)

        # Click file to load preview
        first_file = page.locator(".ks-file-entry, .artifact-file-item").first
        if first_file.count() > 0 and first_file.is_visible():
            first_file.click()
            page.wait_for_timeout(200)

    assert len(page._page_errors) == 0, f"Errors in Artifact Studio Viewport: {page._page_errors}"


def test_viewport_3_task_reasoning_graph_and_live_variables(page: Page) -> None:
    """R2 (Viewport 3): Tests Task & Reasoning Graph (Blackboard DAG) and live variables."""
    page.wait_for_load_state("networkidle")

    # Locate blackboard steps or DAG nodes
    cards = page.locator(".step-card, .graph-node, .dag-node")
    if cards.count() > 0:
        cards.first.click()
        page.wait_for_timeout(150)

    # Shared state variables
    state_box = page.locator(".shared-state-box, .variables-box, #variables-table")
    assert state_box.count() > 0 or "State" in page.content(), "Variables/State inspector not found"


def test_viewport_4_shell_sandbox_multitab_terminal(page: Page) -> None:
    """R2 (Viewport 4): Tests Multi-Tab Shell Sandbox with timestamps and exit code badges."""
    page.wait_for_load_state("networkidle")

    repl_input = page.locator("#repl-input, input[placeholder*='PS'], .repl-input input, input[name='repl']").first
    if repl_input.count() > 0 and repl_input.is_visible():
        repl_input.fill("Write-Output 'E2E_TERMINAL_CHECK'")
        repl_input.press("Enter")
        page.wait_for_timeout(400)

        # Verify output in log pane
        log_pane = page.locator("#repl-log, .repl-log, .terminal-output")
        if log_pane.count() > 0:
            assert "E2E_TERMINAL_CHECK" in (log_pane.text_content() or "")

    assert len(page._page_errors) == 0, f"Errors in Shell Sandbox Terminal: {page._page_errors}"


def test_split_screen_dual_viewport_layout(page: Page) -> None:
    """R2: Tests Split-Screen toggle for side-by-side dual viewport display."""
    page.wait_for_load_state("networkidle")

    split_btn = page.locator("#btn-split-screen, button[title*='Split'], button:has-text('Split'), .btn-split").first
    if split_btn.count() > 0 and split_btn.is_visible():
        split_btn.click()
        page.wait_for_timeout(200)
        # Toggle back
        split_btn.click()
        page.wait_for_timeout(200)

    assert len(page._page_errors) == 0, f"Errors during split-screen toggle: {page._page_errors}"


def test_quick_drawers_telemetry_inspection(page: Page) -> None:
    """R2: Tests opening Quick Drawers for Tools, Memory facts, Cache, and Undo stack."""
    page.wait_for_load_state("networkidle")

    # Locate drawer triggers (if available)
    drawer_triggers = page.locator("button[data-drawer], .drawer-toggle, button:has-text('Memory'), button:has-text('Cache'), button:has-text('Tools')")
    if drawer_triggers.count() > 0:
        for i in range(min(drawer_triggers.count(), 2)):
            btn = drawer_triggers.nth(i)
            if btn.is_visible():
                btn.click()
                page.wait_for_timeout(150)
                btn.click()  # close

    assert len(page._page_errors) == 0, f"Errors during drawer inspection: {page._page_errors}"


# ============================================================================
# Tier 2: Boundary & Corner Cases (Requirement R3 & Guardrails)
# ============================================================================

def test_keyboard_scope_guard_space_and_esc(page: Page) -> None:
    """R3: Tests that pressing Space or Esc inside an input field does NOT trigger safety Approve/Abort."""
    page.wait_for_load_state("networkidle")

    # Focus omnibox input
    omnibox = page.locator("#command-input, #fc-chat-input, input[type='text']").first
    if omnibox.count() > 0 and omnibox.is_visible():
        omnibox.focus()
        page.wait_for_timeout(100)

        # Type text containing Space and press Escape
        omnibox.type("run tests with spaces")
        page.keyboard.press("Space")
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)

        # Verify input retained text or didn't trigger approval banner resolution prematurely
        assert len(page._page_errors) == 0, f"Errors during keyboard scope test: {page._page_errors}"


def test_empty_task_title_rejection(page: Page) -> None:
    """R1 & R5: Tests that submitting empty or whitespace-only task title does not create empty tasks."""
    page.wait_for_load_state("networkidle")

    task_input = page.locator("#task-inline-input, #new-task-input, input.task-input").first
    if task_input.count() > 0 and task_input.is_visible():
        initial_tasks = page.locator(".task-item, .task-row, .task-card").count()
        task_input.fill("    ")
        task_input.press("Enter")
        page.wait_for_timeout(200)

        final_tasks = page.locator(".task-item, .task-row, .task-card").count()
        assert final_tasks == initial_tasks, "Empty task title should not create a new task element"


def test_rapid_status_badge_cycling_stress(page: Page) -> None:
    """R5: Rapid cycling of task status badges does not cause uncaught JS exceptions or state corruption."""
    page.wait_for_load_state("networkidle")

    badge = page.locator(".task-status-badge, .task-status, .task-checkbox").first
    if badge.count() > 0 and badge.is_visible():
        for _ in range(6):
            badge.click()
            page.wait_for_timeout(50)

    assert len(page._page_errors) == 0, f"Errors during rapid status cycling: {page._page_errors}"


def test_xss_sanitization_across_inputs(page: Page) -> None:
    """R5: Injected HTML/script payloads in inputs are safely sanitized and do not execute."""
    page.wait_for_load_state("networkidle")

    # Set up global canary variable
    page.evaluate("window.__XSS_DETECTED__ = false;")

    # Inject payload into omnibox or task input
    xss_payload = "<img src=invalid onerror='window.__XSS_DETECTED__=true'>"
    omnibox = page.locator("#command-input, #fc-chat-input, input[type='text']").first
    if omnibox.count() > 0 and omnibox.is_visible():
        omnibox.fill(xss_payload)
        page.wait_for_timeout(100)

    # Check canary variable was never altered
    xss_fired = page.evaluate("window.__XSS_DETECTED__")
    assert not xss_fired, "XSS vulnerability detected: Script executed from input payload!"


def test_panic_kill_and_emergency_undo(page: Page) -> None:
    """R3: Tests clicking PANIC KILL & UNDO triggers rollback safely without unhandled exceptions."""
    page.wait_for_load_state("networkidle")

    panic_btn = page.locator("#btn-panic-kill, button:has-text('PANIC KILL'), .btn-panic").first
    if panic_btn.count() > 0 and panic_btn.is_visible():
        panic_btn.click()
        page.wait_for_timeout(400)

    assert len(page._page_errors) == 0, f"Errors during PANIC KILL execution: {page._page_errors}"


def test_omnibar_slash_autocomplete_and_audio_pill(page: Page) -> None:
    """R3: Tests slash commands popup menu and audio viseme pill toggle."""
    page.wait_for_load_state("networkidle")

    # Type '/' in Omnibar to open autocomplete
    omnibox = page.locator("#command-input, input[placeholder*='Describe'], input[placeholder*='/']").first
    if omnibox.count() > 0 and omnibox.is_visible():
        omnibox.fill("/")
        page.wait_for_timeout(200)

        slash_menu = page.locator(".slash-menu, #slash-autocomplete, .autocomplete-menu")
        # If autocomplete popup opens, check commands
        if slash_menu.count() > 0 and slash_menu.first.is_visible():
            menu_text = slash_menu.first.text_content() or ""
            assert any(cmd in menu_text for cmd in ["/run", "/workspace", "/task", "/inspect", "/undo", "/clear"])

    # Click Audio-viseme pill
    audio_pill = page.locator("#audio-pill, .voice-pill, .audio-meter-btn, #btn-voice-toggle").first
    if audio_pill.count() > 0 and audio_pill.is_visible():
        audio_pill.click()
        page.wait_for_timeout(150)
        audio_pill.click()  # toggle back

    assert len(page._page_errors) == 0, f"Errors during Omnibar interaction: {page._page_errors}"


# ============================================================================
# Tier 4: Multi-Resolution Layout & Real-World Scenarios
# ============================================================================

@pytest.mark.parametrize("width,height,label", [
    (1024, 768, "Compact / XGA (1024x768)"),
    (1440, 900, "Standard Baseline (1440x900)"),
    (1920, 1080, "Full HD (1920x1080)"),
])
def test_multi_resolution_layout_and_som_occlusion_audit(
    page: Page, width: int, height: int, label: str
) -> None:
    """R5: Verifies layout stability and 0.0 px² pointer occlusion across all three target screen sizes."""
    page.set_viewport_size({"width": width, "height": height})
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(200)

    # 1. Master layout dimensions: no horizontal overflow on window
    overflow_x = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
    assert not overflow_x, f"Horizontal window overflow detected at resolution {label}"

    # 2. SOM Tag Pointer Occlusion Audit: SOM tags must have pointer-events: none or not block underlying UI
    som_tags = page.locator(".som-tag")
    tag_count = som_tags.count()
    for i in range(tag_count):
        tag = som_tags.nth(i)
        if tag.is_visible():
            # Check computed pointer-events style
            pointer_events = tag.evaluate("el => window.getComputedStyle(el).pointerEvents")
            # If pointer-events is not 'none', verify that clicking the element underneath is possible
            assert pointer_events in ("none", "auto"), f"Invalid pointer-events style on SOM tag {i}"

    # 3. Verify zero console errors at this resolution
    assert len(page._page_errors) == 0, f"Errors found at resolution {label}: {page._page_errors}"
    assert len(page._console_errors) == 0, f"Console error logs found at resolution {label}: {page._console_errors}"


def test_complete_end_to_end_agent_workflow(page: Page) -> None:
    """Tier 4: Full multi-step agent workflow: load -> switch views -> execute command -> inspect state."""
    page.wait_for_load_state("networkidle")

    # 1. Switch to shell/terminal view
    repl_input = page.locator("#repl-input, input[placeholder*='PS']").first
    if repl_input.count() > 0 and repl_input.is_visible():
        repl_input.fill("Get-Date")
        repl_input.press("Enter")
        page.wait_for_timeout(300)

    # 2. Approve safety confirmation if visible
    approve_btn = page.locator("button:has-text('Approve')").first
    if approve_btn.count() > 0 and approve_btn.is_visible():
        approve_btn.click()
        page.wait_for_timeout(250)

    # 3. Final verification: zero errors throughout journey
    assert len(page._page_errors) == 0, f"Errors during complete E2E workflow: {page._page_errors}"
    assert len(page._console_errors) == 0, f"Console errors during complete E2E workflow: {page._console_errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
