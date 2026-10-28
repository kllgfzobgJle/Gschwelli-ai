"""Empirical Challenger Deep Verification Script for Milestone 2 Iteration 2.

Tests:
1. Tab Isolation: Bounding boxes of inactive views across all transitions:
   MC -> KS -> VS -> FC -> MC, plus non-linear transitions.
2. XSS Payloads: Multiple injection vectors in task addition.
3. Button Layouts: Geometry and wrapping checks at 1024x768 and 1440x900.
"""

from __future__ import annotations

import json
from pathlib import Path
import socket
import sys
import threading
import time
from typing import Dict, Any, List
from urllib.parse import urlparse

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uvicorn
from playwright.sync_api import sync_playwright

from server.api import create_app


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def run_challenger_verification():
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

    results: Dict[str, Any] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-gpu", "--no-sandbox"])

        # =========================================================================
        # 1. TAB ISOLATION DEEP TEST (1440x900)
        # =========================================================================
        print("\n=== RUNNING 1. TAB ISOLATION DEEP TEST ===")
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(url, wait_until="networkidle")

        panes = [
            ("mission_control", "view-mission-control"),
            ("knowledge_studio", "view-knowledge-studio"),
            ("vision_som", "view-vision-som"),
            ("focus_chat", "view-focus-chat"),
        ]

        def get_all_pane_metrics():
            return page.evaluate("""() => {
                const ids = ['view-mission-control', 'view-knowledge-studio', 'view-vision-som', 'view-focus-chat'];
                const res = {};
                for (const id of ids) {
                    const el = document.getElementById(id);
                    if (!el) {
                        res[id] = { exists: false };
                        continue;
                    }
                    const style = window.getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    res[id] = {
                        exists: true,
                        display: style.display,
                        width: rect.width,
                        height: rect.height,
                        top: rect.top,
                        left: rect.left,
                        classes: Array.from(el.classList)
                    };
                }
                return res;
            }""")

        transitions = [
            # Standard sequence
            ("mission_control", "initial"),
            ("knowledge_studio", "MC -> KS"),
            ("vision_som", "KS -> VS"),
            ("focus_chat", "VS -> FC"),
            ("mission_control", "FC -> MC"),
            # Non-linear transitions
            ("vision_som", "MC -> VS"),
            ("knowledge_studio", "VS -> KS"),
            ("focus_chat", "KS -> FC"),
            ("mission_control", "FC -> MC"),
        ]

        tab_isolation_log = []
        tab_isolation_clean = True

        for mode, label in transitions:
            if label != "initial":
                page.locator(f".mode-tab-btn[data-mode='{mode}']").click()
                page.wait_for_timeout(100)

            metrics = get_all_pane_metrics()
            active_id = f"view-{mode.replace('_', '-')}"

            step_summary = {"transition": label, "active_mode": mode, "panes": {}}

            for pane_id, m in metrics.items():
                is_active = (pane_id == active_id)
                if is_active:
                    expected_disp = "grid" if pane_id == "view-mission-control" else "flex"
                    if m["display"] != expected_disp:
                        tab_isolation_clean = False
                        print(f"FAIL: Active pane {pane_id} display is '{m['display']}' (expected '{expected_disp}')")
                    if m["width"] <= 0 or m["height"] <= 0:
                        tab_isolation_clean = False
                        print(f"FAIL: Active pane {pane_id} bounding box zero: {m['width']}x{m['height']}")
                else:
                    if m["display"] != "none":
                        tab_isolation_clean = False
                        print(f"FAIL: Inactive pane {pane_id} display is '{m['display']}' (expected 'none') during {label}")
                    if m["width"] != 0 or m["height"] != 0:
                        tab_isolation_clean = False
                        print(f"FAIL: Inactive pane {pane_id} occupies space: {m['width']}x{m['height']} during {label}")

                step_summary["panes"][pane_id] = {
                    "is_active": is_active,
                    "display": m["display"],
                    "box": f"{m['width']}x{m['height']}"
                }

            tab_isolation_log.append(step_summary)

        results["tab_isolation"] = {
            "clean": tab_isolation_clean,
            "steps_tested": len(transitions),
            "log": tab_isolation_log
        }
        print(f"Tab isolation verified clean: {tab_isolation_clean} across {len(transitions)} transitions")
        page.close()

        # =========================================================================
        # 2. XSS INJECTION ATTACK IN TASK ADDITION
        # =========================================================================
        print("\n=== RUNNING 2. XSS INJECTION ATTACK SUITE ===")
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(url, wait_until="networkidle")

        xss_payloads = [
            ('<script id="xss1">window.__xss1=1;</script>', "xss1", "__xss1"),
            ('<img src="invalid_img.png" id="xss2" onerror="window.__xss2=1;" />', "xss2", "__xss2"),
            ('<svg id="xss3" onload="window.__xss3=1;"><circle r="5"/></svg>', "xss3", "__xss3"),
            ('<span id="xss4" onclick="window.__xss4=1;">Clickme</span>', "xss4", "__xss4"),
            ('"><iframe id="xss5" src="about:blank"></iframe>', "xss5", "__xss5"),
            ('<a id="xss6" href="javascript:window.__xss6=1">Link</a>', "xss6", "__xss6"),
            ('<style id="xss7">body{color:red;}</style>', "xss7", None),
        ]

        xss_results = []
        all_xss_blocked = True

        for payload, dom_id, global_var in xss_payloads:
            def handle_dialog(dialog):
                dialog.accept(payload)
            page.once("dialog", handle_dialog)
            page.locator("#btn-add-task").click()
            page.wait_for_timeout(100)

            # Check if element exists in DOM
            dom_element_present = page.locator(f"#{dom_id}").count() > 0

            # Check if global variable was set
            var_set = False
            if global_var:
                var_set = page.evaluate(f"() => typeof window.{global_var} !== 'undefined'")

            # Check raw innerHTML vs escaped representation in task items
            task_texts = page.evaluate("""() => {
                const items = document.querySelectorAll('.task-item .task-text');
                return Array.from(items).map(i => ({
                    textContent: i.textContent,
                    innerHTML: i.innerHTML
                }));
            }""")

            last_task = task_texts[-1] if task_texts else {}
            escaped_correctly = ("<" not in last_task.get("innerHTML", "") or "&lt;" in last_task.get("innerHTML", ""))

            passed = (not dom_element_present) and (not var_set) and escaped_correctly

            if not passed:
                all_xss_blocked = False
                print(f"XSS FAILURE on payload: {payload} -> dom_element={dom_element_present}, var_set={var_set}")

            xss_results.append({
                "payload": payload,
                "dom_id": dom_id,
                "dom_element_injected": dom_element_present,
                "code_executed": var_set,
                "innerHTML": last_task.get("innerHTML"),
                "textContent": last_task.get("textContent"),
                "passed": passed
            })

        results["xss_injection"] = {
            "all_blocked": all_xss_blocked,
            "tests": xss_results
        }
        print(f"All XSS payloads blocked: {all_xss_blocked} ({len(xss_payloads)} tested)")
        page.close()

        # =========================================================================
        # 3. BUTTON LAYOUTS & OVERFLOW AT 1024x768 AND 1440x900
        # =========================================================================
        print("\n=== RUNNING 3. BUTTON LAYOUTS & OVERFLOW STRESS TEST ===")
        resolutions = [(1024, 768), (1440, 900)]
        layout_results = {}

        for w, h in resolutions:
            res_key = f"{w}x{h}"
            page = browser.new_page(viewport={"width": w, "height": h})
            page.goto(url, wait_until="networkidle")

            metrics = page.evaluate("""() => {
                // Top nav and tabs
                const topNav = document.getElementById('top-nav');
                const topNavRect = topNav.getBoundingClientRect();
                const tabs = Array.from(document.querySelectorAll('.mode-tab-btn')).map(b => {
                    const r = b.getBoundingClientRect();
                    return { text: b.textContent.trim(), top: r.top, bottom: r.bottom, height: r.height, right: r.right };
                });
                // Check if all tabs on same horizontal line
                const tabTops = new Set(tabs.map(t => Math.round(t.top)));
                const tabsWrapped = tabTops.size > 1;

                // Action toolbar buttons
                const toolbar = document.querySelector('.canvas-action-toolbar');
                const tbRect = toolbar.getBoundingClientRect();
                const tbButtons = Array.from(toolbar.querySelectorAll('button')).map(b => {
                    const r = b.getBoundingClientRect();
                    return {
                        id: b.id || b.textContent.trim(),
                        top: r.top,
                        bottom: r.bottom,
                        height: r.height,
                        overflows_bottom: r.bottom > tbRect.bottom + 1
                    };
                });
                const tbAnyOverflow = tbButtons.some(b => b.overflows_bottom);

                // Approval Gate buttons
                const gate = document.getElementById('approval-gate-dock');
                const gateRect = gate.getBoundingClientRect();
                const gateButtons = Array.from(gate.querySelectorAll('button')).map(b => {
                    const r = b.getBoundingClientRect();
                    return {
                        id: b.id || b.textContent.trim(),
                        top: r.top,
                        bottom: r.bottom,
                        height: r.height,
                        overflows_bottom: r.bottom > gateRect.bottom + 1
                    };
                });
                const gateAnyOverflow = gateButtons.some(b => b.overflows_bottom);

                // Omnibox controls
                const omnibox = document.getElementById('omnibox-dock');
                const omniRect = omnibox.getBoundingClientRect();
                const omniAnyOverflow = omniRect.height > 52; // should be 48px

                // Root scrollbars
                const docScrollW = document.documentElement.scrollWidth;
                const docScrollH = document.documentElement.scrollHeight;
                const appScrollW = document.getElementById('app-container').scrollWidth;
                const appScrollH = document.getElementById('app-container').scrollHeight;

                return {
                    topNavHeight: topNavRect.height,
                    tabsWrapped: tabsWrapped,
                    tabCount: tabs.length,
                    toolbarHeight: tbRect.height,
                    tbAnyOverflow: tbAnyOverflow,
                    tbButtons: tbButtons,
                    gateHeight: gateRect.height,
                    gateAnyOverflow: gateAnyOverflow,
                    gateButtons: gateButtons,
                    omniHeight: omniRect.height,
                    omniAnyOverflow: omniAnyOverflow,
                    docScrollW: docScrollW,
                    docScrollH: docScrollH,
                    appScrollW: appScrollW,
                    appScrollH: appScrollH,
                    hasHorizontalScroll: (docScrollW > window.innerWidth || appScrollW > window.innerWidth),
                    hasVerticalScroll: (docScrollH > window.innerHeight || appScrollH > window.innerHeight)
                };
            }""")

            layout_results[res_key] = metrics
            print(f"[{res_key}] TopNavHeight={metrics['topNavHeight']}, TabsWrapped={metrics['tabsWrapped']}, "
                  f"ToolbarOverflow={metrics['tbAnyOverflow']}, GateOverflow={metrics['gateAnyOverflow']}, "
                  f"HorizScroll={metrics['hasHorizontalScroll']}, VertScroll={metrics['hasVerticalScroll']}")
            page.close()

        results["layout_stress"] = layout_results
        browser.close()

    server.should_exit = True
    thread.join(timeout=2.0)

    # Save summary report to JSON
    with open("challenger_empirical_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\nEmpirical Challenger Execution Finished.")
    print("Results saved to challenger_empirical_results.json")
    return results


if __name__ == "__main__":
    run_challenger_verification()
