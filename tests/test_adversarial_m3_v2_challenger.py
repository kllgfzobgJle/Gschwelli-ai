"""Empirical Challenger Adversarial Stress Test Suite for Milestone 3 Iteration 2.

Assigned to: challenger_m3_v2_2
Target: ui/dashboard/index.html served by server/api.py

Focus areas:
1. Rapid Viewport Navigation (Tabs 1-4 & Ctrl+1..Ctrl+4 hotkeys).
2. DOM Node Leak Audit during rapid viewport hot-switching.
3. 50/50 Split-Screen Mode Toggle (#btn-split-screen & Alt+S) and dual pane concurrent interactivity.
4. Shell Sandbox & REPL Terminal Streaming (pwsh, bash, sandbox, timestamps, exit code badges, stdout/stderr styling).
5. Quick Telemetry Drawers (Tools, Memory, Cache, Undo) & Escape key priority over safety gate abort.
"""

from __future__ import annotations

import re
import time
import pytest
from playwright.sync_api import Page, expect
from tests.test_browser_dom import server_url, playwright_instance, browser, page


def test_adversarial_viewport_navigation_tabs_and_hotkeys(page: Page) -> None:
    """Stress-test rapid viewport navigation via tab clicks and Ctrl+1..4 hotkeys."""
    page.wait_for_load_state("networkidle")

    viewports = ["1", "2", "3", "4"]

    # 1. Test clicking tab buttons
    for vp in viewports:
        tab_btn = page.locator(f".viewport-tab-btn[data-viewport='{vp}']")
        expect(tab_btn).to_be_visible()
        tab_btn.click()
        page.wait_for_timeout(50)

        # Tab button must be active and aria-selected
        expect(tab_btn).to_have_class(re.compile(r"active"))
        assert tab_btn.get_attribute("aria-selected") == "true"

        # Corresponding viewport panel must be active
        panel = page.locator(f"#viewport-{vp}")
        expect(panel).to_have_class(re.compile(r"active"))

        # Other viewport panels must NOT be active
        for other_vp in viewports:
            if other_vp != vp:
                other_panel = page.locator(f"#viewport-{other_vp}")
                expect(other_panel).not_to_have_class(re.compile(r"\bactive\b"))

    # 2. Test switching via keyboard shortcuts Ctrl+1..Ctrl+4
    for vp in viewports:
        page.keyboard.press(f"Control+{vp}")
        page.wait_for_timeout(50)

        tab_btn = page.locator(f".viewport-tab-btn[data-viewport='{vp}']")
        expect(tab_btn).to_have_class(re.compile(r"active"))
        panel = page.locator(f"#viewport-{vp}")
        expect(panel).to_have_class(re.compile(r"active"))

    # 3. Adversarial Stress: Rapid sequential hotkey cycling (40 transitions)
    for _ in range(10):
        for vp in ["2", "4", "1", "3"]:
            page.keyboard.press(f"Control+{vp}")
        page.wait_for_timeout(20)

    # Return to Viewport 1 and verify integrity
    page.keyboard.press("Control+1")
    page.wait_for_timeout(100)
    expect(page.locator("#viewport-1")).to_have_class(re.compile(r"active"))
    assert len(page._page_errors) == 0, f"Page errors during rapid viewport switching: {page._page_errors}"


def test_adversarial_zero_dom_leak_during_rapid_switching(page: Page) -> None:
    """Empirically verify that rapid viewport switching exhibits zero DOM node memory leaks."""
    page.wait_for_load_state("networkidle")

    # Initial warm-up: visit each viewport once so any lazy-load elements (e.g. DAG path) are created
    for vp in ["1", "2", "3", "4", "1"]:
        page.keyboard.press(f"Control+{vp}")
        page.wait_for_timeout(80)

    # Measure baseline DOM element count
    initial_node_count = page.evaluate("() => document.querySelectorAll('*').length")

    # Perform 50 rapid cycles across all 4 viewports (200 transitions)
    for cycle in range(50):
        vp = str((cycle % 4) + 1)
        page.keyboard.press(f"Control+{vp}")
        if cycle % 10 == 0:
            page.wait_for_timeout(30)

    # Return to baseline Viewport 1
    page.keyboard.press("Control+1")
    page.wait_for_timeout(200)

    # Measure final DOM element count
    final_node_count = page.evaluate("() => document.querySelectorAll('*').length")
    delta = final_node_count - initial_node_count

    print(f"\n[DOM LEAK AUDIT] Baseline: {initial_node_count}, Final: {final_node_count}, Delta: {delta}")
    # Zero node growth is strictly enforced
    assert delta <= 0, f"DOM node leak detected! DOM grew by {delta} elements during viewport switching"
    assert len(page._page_errors) == 0, f"Errors encountered during leak audit: {page._page_errors}"


def test_adversarial_split_screen_toggle_and_dual_pane_interactivity(page: Page) -> None:
    """Empirically test 50/50 Split-Screen toggle and simultaneous dual-pane interactivity."""
    page.wait_for_load_state("networkidle")

    container = page.locator("#stage-viewports-container")
    split_btn = page.locator("#btn-split-screen")
    vp1 = page.locator("#viewport-1")
    vp4 = page.locator("#viewport-4")

    # 1. Toggle Split-Screen ON via Button Click
    split_btn.click()
    page.wait_for_timeout(150)

    expect(container).to_have_class(re.compile(r"split-screen-active"))
    expect(split_btn).to_have_class(re.compile(r"active"))
    expect(vp1).to_have_class(re.compile(r"split-left"))
    expect(vp4).to_have_class(re.compile(r"split-right"))

    # Verify both viewports are simultaneously visible
    expect(vp1).to_be_visible()
    expect(vp4).to_be_visible()

    # Bounding box geometry audit: verify 50/50 dual layout
    box1 = vp1.bounding_box()
    box4 = vp4.bounding_box()
    assert box1 and box4, "Could not retrieve bounding boxes for split panes"
    assert box1["width"] > 300, f"Left pane too narrow: {box1['width']}px"
    assert box4["width"] > 300, f"Right pane too narrow: {box4['width']}px"

    width_diff = abs(box1["width"] - box4["width"])
    print(f"\n[SPLIT SCREEN GEOMETRY] Left width: {box1['width']:.1f}px, Right width: {box4['width']:.1f}px, Diff: {width_diff:.1f}px")
    assert width_diff < 50.0, f"Panes are not 50/50 balanced! Width difference is {width_diff:.1f}px"

    # 2. Left Pane Interactivity: Click SOM tag in Viewport 1
    som_tag = page.locator("#som-tag-02")
    som_tag.click()
    page.wait_for_timeout(100)
    expect(som_tag).to_have_class(re.compile(r"active"))
    expect(page.locator("#repl-logs")).to_contain_text("Focused target [02]")

    # 3. Right Pane Interactivity: Execute command in Terminal Viewport 4
    term_input = page.locator("#terminal-active-input")
    expect(term_input).to_be_visible()
    term_input.fill("echo 'SPLIT_PANE_EXECUTION_CHECK'")
    page.locator("#btn-term-run").click()
    page.wait_for_timeout(200)

    expect(page.locator("#terminal-logs-surface")).to_contain_text("SPLIT_PANE_EXECUTION_CHECK")

    # 4. Switch right pane viewport while in split-screen mode via Ctrl+2
    page.keyboard.press("Control+2")
    page.wait_for_timeout(150)
    vp2 = page.locator("#viewport-2")
    expect(vp1).to_have_class(re.compile(r"split-left"))
    expect(vp2).to_have_class(re.compile(r"split-right"))
    expect(vp2).to_be_visible()

    # 5. Toggle Split-Screen OFF via Alt+S shortcut
    page.keyboard.press("Alt+s")
    page.wait_for_timeout(150)

    expect(container).not_to_have_class(re.compile(r"split-screen-active"))
    expect(split_btn).not_to_have_class(re.compile(r"active"))
    assert len(page._page_errors) == 0


def test_adversarial_repl_terminal_streaming_and_exit_badges(page: Page) -> None:
    """Stress-test REPL streaming, shell tabs, ANSI/color classes, and exit code badge updates."""
    page.wait_for_load_state("networkidle")

    # Navigate to Viewport 4
    page.keyboard.press("Control+4")
    page.wait_for_timeout(100)

    # 1. Test Shell Tabs switching (pwsh, bash, sandbox)
    prompt_label = page.locator("#terminal-prompt-label")

    # Bash tab
    page.locator("#term-tab-bash").click()
    page.wait_for_timeout(80)
    expect(page.locator("#term-tab-bash")).to_have_class(re.compile(r"active"))
    expect(prompt_label).to_contain_text("aether@agent-vm")

    # Sandbox tab
    page.locator("#term-tab-sandbox").click()
    page.wait_for_timeout(80)
    expect(page.locator("#term-tab-sandbox")).to_have_class(re.compile(r"active"))
    expect(prompt_label).to_contain_text("agent-sandbox")

    # Back to pwsh tab
    page.locator("#term-tab-pwsh").click()
    page.wait_for_timeout(80)
    expect(page.locator("#term-tab-pwsh")).to_have_class(re.compile(r"active"))
    expect(prompt_label).to_contain_text("PS C:")

    # 2. Test Success Command & Exit 0 Badge
    term_input = page.locator("#terminal-active-input")
    term_input.fill("Write-Output 'SUCCESS_STREAM_CHECK'")
    page.keyboard.press("Enter")
    page.wait_for_timeout(400)

    # Exit badge checks
    term_exit = page.locator("#terminal-exit-badge")
    repl_exit = page.locator("#repl-exit-badge")
    expect(term_exit).to_contain_text("EXIT 0")
    expect(term_exit).to_have_class(re.compile(r"badge-complete"))
    expect(repl_exit).to_contain_text("EXIT 0")
    expect(repl_exit).to_have_class(re.compile(r"badge-complete"))

    # Timestamp and output in logs surface
    surface = page.locator("#terminal-logs-surface")
    expect(surface).to_contain_text("SUCCESS_STREAM_CHECK")
    expect(surface.locator(".log-ts").last).to_contain_text(re.compile(r"\[\d{2}:\d{2}:\d{2}\]"))

    # 3. Test Failure Command & Exit 1 Badge Transition via actual PowerShell syntax error
    term_input.fill("test-path")  # missing mandatory path parameter -> triggers [PS_ERROR]
    page.keyboard.press("Enter")
    page.wait_for_timeout(400)

    expect(term_exit).to_contain_text("EXIT 1")
    expect(term_exit).to_have_class(re.compile(r"badge-queued"))
    expect(repl_exit).to_contain_text("EXIT 1")
    expect(repl_exit).to_have_class(re.compile(r"badge-queued"))

    # Test stdout vs stderr styling in appendReplLog
    page.evaluate("""() => {
        appendReplLog(null, 'Simulated STDERR Failure', 'error');
        appendReplLog(null, 'Simulated WARNING Action', 'warn');
        appendReplLog(null, 'Simulated SUCCESS Metric', 'success');
    }""")
    page.wait_for_timeout(100)

    expect(surface.locator(".log-stderr").last).to_contain_text("Simulated STDERR Failure")
    expect(surface.locator(".log-warn").last).to_contain_text("Simulated WARNING Action")
    expect(surface.locator(".log-success").last).to_contain_text("Simulated SUCCESS Metric")

    # Restore exit status 0
    page.evaluate("() => ReplEngine.updateExitStatus(0)")
    page.wait_for_timeout(80)
    expect(term_exit).to_contain_text("EXIT 0")
    assert len(page._page_errors) == 0


def test_adversarial_telemetry_drawers_and_escape_priority(page: Page) -> None:
    """Stress-test Telemetry Drawers and verify Escape key closes drawer WITHOUT triggering safety gate abort."""
    page.wait_for_load_state("networkidle")

    drawer_panel = page.locator("#telemetry-drawer-panel")
    drawer_overlay = page.locator("#telemetry-drawer-overlay")
    status_badge = page.locator("#mission-status-badge")
    gate_dock = page.locator("#approval-gate-dock")

    # Ensure Approval Gate is in active PAUSED • APPROVAL state
    page.evaluate("""() => {
        AppState.mission.status = 'PAUSED • APPROVAL';
        AppState.approvalGate.active = true;
        const b = document.getElementById('mission-status-badge');
        if (b) b.textContent = 'PAUSED • APPROVAL';
    }""")
    page.wait_for_timeout(100)
    expect(status_badge).to_contain_text("PAUSED • APPROVAL")

    # 1. Open Tools Drawer via quick drawer button
    btn_tools = page.locator("button[data-drawer='tools']")
    btn_tools.click()
    page.wait_for_timeout(150)

    expect(drawer_panel).to_have_class(re.compile(r"open"))
    expect(drawer_overlay).not_to_have_class(re.compile(r"hidden"))
    expect(page.locator("#drawer-pane-tools")).to_have_class(re.compile(r"active"))

    # 2. Switch tabs inside drawer: Memory, Cache, Undo
    page.locator("#drawer-tab-memory").click()
    page.wait_for_timeout(100)
    expect(page.locator("#drawer-pane-memory")).to_have_class(re.compile(r"active"))

    page.locator("#drawer-tab-cache").click()
    page.wait_for_timeout(100)
    expect(page.locator("#drawer-pane-cache")).to_have_class(re.compile(r"active"))

    page.locator("#drawer-tab-undo").click()
    page.wait_for_timeout(100)
    expect(page.locator("#drawer-pane-undo")).to_have_class(re.compile(r"active"))

    # 3. CRITICAL EMPIRICAL TEST: Press Escape while drawer is OPEN
    # Expected behavior:
    # - Drawer panel must close (lose .open)
    # - Safety Gate must NOT abort (status must remain PAUSED • APPROVAL)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    expect(drawer_panel).not_to_have_class(re.compile(r"open"))
    expect(status_badge).to_contain_text("PAUSED • APPROVAL")
    expect(gate_dock).not_to_have_class(re.compile(r"aborted"))

    # 4. Now press Escape a SECOND time (when drawer is closed)
    # Expected behavior:
    # - Now the Escape key targets the safety gate and triggers Abort
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    expect(status_badge).to_contain_text("ABORTED")
    expect(gate_dock).to_have_class(re.compile(r"aborted"))

    # 5. Test Close Button and Overlay Click
    page.locator("button[data-drawer='tools']").click()
    page.wait_for_timeout(150)
    expect(drawer_panel).to_have_class(re.compile(r"open"))

    # Close via #btn-close-drawer
    page.locator("#btn-close-drawer").click()
    page.wait_for_timeout(150)
    expect(drawer_panel).not_to_have_class(re.compile(r"open"))

    assert len(page._page_errors) == 0, f"Errors in drawer and escape test: {page._page_errors}"
