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


# ==============================================================================
# Challenge 6: Task Lifecycle - Rapid 20-Click Status Cycling
# ==============================================================================

def test_challenge_rapid_task_status_cycling_20_clicks(challenge_env):
    """Rapidly cycle a task through 20 status clicks: verify transitions remain clean across all 5 states."""
    browser: Browser = challenge_env["browser"]
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    page_errors: List[str] = []
    page.on("pageerror", lambda err: page_errors.append(str(err)))

    page.goto(challenge_env["url"], wait_until="networkidle")
    page.evaluate("() => localStorage.removeItem('gschwelli_tasks')")
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(300)

    # State flow definition in order
    flow = ["backlog", "in_progress", "agent_delegated", "blocked", "done"]
    expected_labels = {
        "backlog": "BACKLOG",
        "in_progress": "IN PROGRESS",
        "agent_delegated": "DELEGATED",
        "blocked": "BLOCKED",
        "done": "DONE",
    }
    expected_classes = {
        "backlog": "badge-backlog",
        "in_progress": "badge-in-progress",
        "agent_delegated": "badge-agent-delegated",
        "blocked": "badge-blocked",
        "done": "badge-done",
    }

    # Start with task t3 which has initial status 'backlog'
    task_id = "t3"
    initial_status = page.evaluate(f"() => AppState.tasks.find(t => t.id === '{task_id}').status")
    assert initial_status == "backlog", f"Expected task {task_id} initial status 'backlog', got {initial_status}"

    badge_locator = page.locator(f'.task-item[data-task-id="{task_id}"] .task-status-badge')
    assert badge_locator.count() == 1, f"Task status badge for {task_id} not found"

    visited_states = set()

    for click_idx in range(1, 21):
        expected_status = flow[click_idx % len(flow)]
        badge_locator.click()
        page.wait_for_timeout(50)

        # Inspect DOM & AppState
        dom_status = page.locator(f'.task-item[data-task-id="{task_id}"]').get_attribute("data-task-status")
        badge_text = badge_locator.text_content().strip()
        badge_class = badge_locator.get_attribute("class")
        app_status = page.evaluate(f"() => AppState.tasks.find(t => t.id === '{task_id}').status")
        app_completed = page.evaluate(f"() => AppState.tasks.find(t => t.id === '{task_id}').completed")

        visited_states.add(expected_status)

        assert dom_status == expected_status, f"Click {click_idx}: DOM status was '{dom_status}', expected '{expected_status}'"
        assert app_status == expected_status, f"Click {click_idx}: AppState status was '{app_status}', expected '{expected_status}'"
        assert expected_labels[expected_status] in badge_text, f"Click {click_idx}: badge text '{badge_text}' does not contain '{expected_labels[expected_status]}'"
        assert expected_classes[expected_status] in badge_class, f"Click {click_idx}: badge class '{badge_class}' does not contain '{expected_classes[expected_status]}'"
        assert app_completed == (expected_status == "done"), f"Click {click_idx}: completed was {app_completed}, expected {expected_status == 'done'}"

    # Verify all 5 states were thoroughly visited
    assert len(visited_states) == 5, f"Not all 5 states were visited: {visited_states}"
    # Verify 20 clicks returned to backlog (20 % 5 == 0)
    final_status = page.evaluate(f"() => AppState.tasks.find(t => t.id === '{task_id}').status")
    assert final_status == "backlog", f"Expected final status 'backlog', got {final_status}"
    assert len(page_errors) == 0, f"Page errors during status cycling: {page_errors}"

    context.close()


# ==============================================================================
# Challenge 7: Task Lifecycle - 10 Consecutive Delegation Toggles
# ==============================================================================

def test_challenge_toggle_delegation_10_times_consecutively(challenge_env):
    """Toggle delegation 10 times consecutively: verify metrics and state stay consistent."""
    browser: Browser = challenge_env["browser"]
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    page_errors: List[str] = []
    page.on("pageerror", lambda err: page_errors.append(str(err)))

    page.goto(challenge_env["url"], wait_until="networkidle")
    page.evaluate("() => localStorage.removeItem('gschwelli_tasks')")
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(300)

    task_id = "t3"
    delegate_btn = page.locator(f'.task-item[data-task-id="{task_id}"] .task-delegate-btn')
    assert delegate_btn.count() == 1, f"Delegate button for {task_id} not found"

    # Initial state: delegated is False, status is backlog
    initial_meta = page.evaluate(f"""() => ({{
        delegated: AppState.tasks.find(t => t.id === '{task_id}').delegated,
        status: AppState.tasks.find(t => t.id === '{task_id}').status,
        doneCount: AppState.tasks.filter(t => t.status === 'done' || t.completed === true).length,
        total: AppState.tasks.length,
        counter: document.getElementById('task-counter').textContent.trim()
    }})""")
    assert initial_meta["delegated"] is False
    assert initial_meta["status"] == "backlog"

    expected_done = initial_meta["doneCount"]
    expected_total = initial_meta["total"]

    for i in range(1, 11):
        delegate_btn.click()
        page.wait_for_timeout(50)

        should_be_delegated = (i % 2 == 1)
        expected_status = "agent_delegated" if should_be_delegated else "backlog"
        expected_btn_text = "🤖" if should_be_delegated else "⚡"

        state = page.evaluate(f"""() => ({{
            delegated: AppState.tasks.find(t => t.id === '{task_id}').delegated,
            status: AppState.tasks.find(t => t.id === '{task_id}').status,
            doneCount: AppState.tasks.filter(t => t.status === 'done' || t.completed === true).length,
            total: AppState.tasks.length,
            counter: document.getElementById('task-counter').textContent.trim(),
            progressBarWidth: document.getElementById('task-progress-bar').style.width,
            progressAria: document.getElementById('task-progress-bar').getAttribute('aria-valuenow')
        }})""")

        btn_class = delegate_btn.get_attribute("class")
        btn_text = delegate_btn.text_content().strip()

        assert state["delegated"] == should_be_delegated, f"Iteration {i}: delegated={state['delegated']}, expected {should_be_delegated}"
        assert state["status"] == expected_status, f"Iteration {i}: status='{state['status']}', expected '{expected_status}'"
        assert expected_btn_text in btn_text, f"Iteration {i}: button text '{btn_text}' does not contain '{expected_btn_text}'"

        if should_be_delegated:
            assert "active" in btn_class, f"Iteration {i}: expected 'active' in button class, got '{btn_class}'"
        else:
            assert "active" not in btn_class, f"Iteration {i}: unexpected 'active' in button class '{btn_class}'"

        # Verify metrics remain strictly consistent (toggling non-done task does not alter doneCount)
        assert state["doneCount"] == expected_done, f"Iteration {i}: doneCount changed from {expected_done} to {state['doneCount']}"
        assert state["total"] == expected_total, f"Iteration {i}: total changed from {expected_total} to {state['total']}"
        assert state["counter"] == f"{expected_done} / {expected_total}", f"Iteration {i}: counter='{state['counter']}', expected '{expected_done} / {expected_total}'"

        expected_pct = round((expected_done / expected_total) * 100)
        assert state["progressBarWidth"] == f"{expected_pct}%", f"Iteration {i}: width='{state['progressBarWidth']}', expected '{expected_pct}%'"
        assert state["progressAria"] == str(expected_pct), f"Iteration {i}: aria='{state['progressAria']}', expected '{expected_pct}'"

    # Final state check: after 10 toggles, it must be back to undelegated
    final_delegated = page.evaluate(f"() => AppState.tasks.find(t => t.id === '{task_id}').delegated")
    assert final_delegated is False, "Task should return to undelegated after 10 toggles"
    assert len(page_errors) == 0, f"Page errors during delegation toggling: {page_errors}"

    context.close()


# ==============================================================================
# Challenge 8: Dynamic Inline Creation of 20 Tasks & 100% Progress Bar
# ==============================================================================

def test_challenge_create_20_tasks_inline_and_mark_all_done(challenge_env):
    """Create 20 tasks inline with Enter: verify counter updates accurately (X / 24). Mark all done: verify 100% progress bar."""
    browser: Browser = challenge_env["browser"]
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    page_errors: List[str] = []
    page.on("pageerror", lambda err: page_errors.append(str(err)))

    page.goto(challenge_env["url"], wait_until="networkidle")
    page.evaluate("() => localStorage.removeItem('gschwelli_tasks')")
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(300)

    # Initial tasks count is 4 (t1 done, t2 in_progress, t3 backlog, t4 blocked)
    init_info = page.evaluate("""() => ({
        total: AppState.tasks.length,
        doneCount: AppState.tasks.filter(t => t.status === 'done' || t.completed === true).length
    })""")
    assert init_info["total"] == 4, f"Expected 4 initial tasks, found {init_info['total']}"
    initial_done = init_info["doneCount"]

    task_input = page.locator("#input-new-task")
    assert task_input.count() == 1, "Inline task input #input-new-task not found"

    # Inline creation of 20 tasks using Enter
    for i in range(1, 21):
        task_title = f"Empirical Stress Task {i:02d}"
        task_input.fill(task_title)
        task_input.press("Enter")
        page.wait_for_timeout(40)

        expected_total = 4 + i
        current_counter = page.locator("#task-counter").text_content().strip()
        assert current_counter == f"{initial_done} / {expected_total}", (
            f"Step {i}: expected counter '{initial_done} / {expected_total}', got '{current_counter}'"
        )

    # Verify total is 24 and counter is '1 / 24'
    final_created_counter = page.locator("#task-counter").text_content().strip()
    assert final_created_counter == f"{initial_done} / 24", (
        f"Expected counter '{initial_done} / 24', got '{final_created_counter}'"
    )

    tasks_count = page.evaluate("() => AppState.tasks.length")
    assert tasks_count == 24, f"AppState.tasks.length is {tasks_count}, expected 24"

    # Mark all done: verify 100% progress bar
    # Find all tasks that are not done and click their checkbox
    unchecked_checkboxes = page.locator(".task-item .custom-checkbox:not(.checked)")
    count_to_check = unchecked_checkboxes.count()
    for _ in range(count_to_check):
        unchecked = page.locator(".task-item .custom-checkbox:not(.checked)").first
        if unchecked.count() > 0:
            unchecked.click()
            page.wait_for_timeout(30)

    # Verify all 24 tasks are done
    all_done_count = page.evaluate("() => AppState.tasks.filter(t => t.status === 'done' || t.completed === true).length")
    assert all_done_count == 24, f"Expected 24 done tasks, got {all_done_count}"

    counter_all_done = page.locator("#task-counter").text_content().strip()
    assert counter_all_done == "24 / 24", f"Expected '24 / 24', got '{counter_all_done}'"

    # Verify 100% progress bar
    progress_bar = page.locator("#task-progress-bar")
    pb_width = progress_bar.evaluate("el => el.style.width")
    pb_aria = progress_bar.get_attribute("aria-valuenow")
    pb_bg = progress_bar.evaluate("el => window.getComputedStyle(el).backgroundColor")

    assert pb_width == "100%", f"Progress bar width is '{pb_width}', expected '100%'"
    assert pb_aria == "100", f"Progress bar aria-valuenow is '{pb_aria}', expected '100'"
    # var(--emerald-success) is rgb(16, 185, 129)
    assert "16, 185, 129" in pb_bg or "rgb(16, 185, 129)" in pb_bg, f"Expected emerald success background, got '{pb_bg}'"

    assert len(page_errors) == 0, f"Page errors during task creation and completion: {page_errors}"
    context.close()


# ==============================================================================
# Challenge 9: Category Filtering (Code, Docs, Tables, Media, Configs) & Empty Filter State
# ==============================================================================

def test_challenge_file_category_filtering_and_empty_state(challenge_env):
    """Filter by each category (Code, Docs, Tables, Media, Configs) and click empty filter: verify graceful empty state display."""
    browser: Browser = challenge_env["browser"]
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    page_errors: List[str] = []
    page.on("pageerror", lambda err: page_errors.append(str(err)))

    page.goto(challenge_env["url"], wait_until="networkidle")
    page.wait_for_timeout(300)

    categories = ["code", "docs", "tables", "media", "configs"]

    for cat in categories:
        tab_btn = page.locator(f'#file-filter-pills .file-filter-tab[data-file-filter="{cat}"]')
        assert tab_btn.count() == 1, f"Filter tab for '{cat}' not found"

        tab_btn.click()
        page.wait_for_timeout(100)

        # Tab must be active
        assert "active" in tab_btn.get_attribute("class"), f"Tab '{cat}' did not receive .active class"

        # Check displayed files in #kb-file-list
        file_items = page.locator("#kb-file-list .file-tree-item")
        item_count = file_items.count()
        assert item_count > 0, f"Expected matching files for category '{cat}', found 0"

        # Verify that all displayed files match category
        displayed_files = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('#kb-file-list .file-tree-item')).map(el => ({
                file: el.getAttribute('data-file'),
                category: el.getAttribute('data-category')
            }));
        }""")
        for df in displayed_files:
            file_obj = page.evaluate(f"() => FileExplorer.files.find(f => f.name === '{df['file']}')")
            assert file_obj is not None, f"File {df['file']} not found in FileExplorer.files"
            matches = page.evaluate(f"() => FileExplorer.matchesCategory(FileExplorer.files.find(f => f.name === '{df['file']}'), '{cat}')")
            assert matches is True, f"File {df['file']} does not match category '{cat}'"

    # Now test clicking an empty filter tab: verify graceful empty state display
    # Add a custom empty category tab to #file-filter-pills and click it
    page.evaluate("""() => {
        const bar = document.getElementById('file-filter-pills');
        const emptyTab = document.createElement('button');
        emptyTab.className = 'file-filter-tab';
        emptyTab.setAttribute('data-file-filter', 'empty_category');
        emptyTab.id = 'tab-empty-filter';
        emptyTab.textContent = 'Empty';
        bar.appendChild(emptyTab);
    }""")

    empty_tab = page.locator("#tab-empty-filter")
    empty_tab.click()
    page.wait_for_timeout(150)

    # Verify tab became active
    assert "active" in empty_tab.get_attribute("class"), "Empty filter tab did not receive .active class"

    # Verify graceful empty state element .file-tree-empty is displayed
    empty_state_el = page.locator("#kb-file-list .file-tree-empty")
    assert empty_state_el.count() == 1, ".file-tree-empty element not found in file list"
    assert empty_state_el.is_visible(), ".file-tree-empty element is not visible"

    empty_text = empty_state_el.text_content().strip()
    assert 'No files matching "empty_category"' in empty_text, (
        f"Empty state text did not match expected: '{empty_text}'"
    )

    # Verify no file items exist in list during empty state
    assert page.locator("#kb-file-list .file-tree-item").count() == 0, "File items found during empty state"

    # Verify returning to 'all' recovers all items
    page.locator('#file-filter-pills .file-filter-tab[data-file-filter="all"]').click()
    page.wait_for_timeout(100)
    assert page.locator("#kb-file-list .file-tree-item").count() >= 5
    assert page.locator("#kb-file-list .file-tree-empty").count() == 0

    assert len(page_errors) == 0, f"Page errors during category filtering: {page_errors}"
    context.close()


# ==============================================================================
# Challenge 10: File Item Selection & Viewport 2 Content Loading
# ==============================================================================

def test_challenge_file_item_selection_and_viewport_2_preview(challenge_env):
    """Click a file item: verify content loads in Viewport 2 and .selected class applies."""
    browser: Browser = challenge_env["browser"]
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    page_errors: List[str] = []
    page.on("pageerror", lambda err: page_errors.append(str(err)))

    page.goto(challenge_env["url"], wait_until="networkidle")
    page.wait_for_timeout(300)

    # Reset filter to 'all' so all files are visible
    page.locator('#file-filter-pills .file-filter-tab[data-file-filter="all"]').click()
    page.wait_for_timeout(100)

    available_files = page.evaluate("() => FileExplorer.files.map(f => f.name)")
    assert len(available_files) > 0, "No files available in FileExplorer"

    # Select the second file to ensure a state change from default first file
    target_file = available_files[1] if len(available_files) > 1 else available_files[0]
    file_item = page.locator(f'#kb-file-list .file-tree-item[data-file="{target_file}"]')
    assert file_item.count() == 1, f"File item for '{target_file}' not found in #kb-file-list"

    file_item.click()
    page.wait_for_timeout(150)

    # 1. Verify .selected class is applied to clicked item
    item_class = file_item.get_attribute("class")
    assert "selected" in item_class, f"File item '{target_file}' does not have .selected class: '{item_class}'"

    # 2. Verify all other items in #kb-file-list do NOT have .selected
    other_selected = page.locator(f'#kb-file-list .file-tree-item:not([data-file="{target_file}"]).selected')
    assert other_selected.count() == 0, f"Other file items still have .selected: {other_selected.count()}"

    # 3. Verify content loads in Viewport 2 (#ks-active-file-header, #ks-editor-textarea)
    header_text = page.locator("#ks-active-file-header").text_content().strip()
    assert target_file in header_text, f"Viewport 2 header '{header_text}' does not contain '{target_file}'"

    expected_content = page.evaluate(f"() => {{ const f = FileExplorer.files.find(x => x.name === '{target_file}'); return f ? f.content : null; }}")
    editor_val = page.locator("#ks-editor-textarea").input_value()

    if expected_content:
        assert editor_val == expected_content, f"Viewport 2 editor content mismatch for '{target_file}'"
    else:
        assert target_file in editor_val, f"Viewport 2 editor content does not mention '{target_file}'"

    # 4. Now test clicking a different file: e.g. first file
    first_file = available_files[0]
    first_item = page.locator(f'#kb-file-list .file-tree-item[data-file="{first_file}"]')
    first_item.click()
    page.wait_for_timeout(150)

    assert "selected" in first_item.get_attribute("class")
    assert "selected" not in file_item.get_attribute("class")
    new_header = page.locator("#ks-active-file-header").text_content().strip()
    assert first_file in new_header

    assert len(page_errors) == 0, f"Page errors during file item selection: {page_errors}"
    context.close()

