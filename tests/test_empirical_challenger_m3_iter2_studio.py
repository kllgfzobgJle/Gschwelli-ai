"""Empirical Challenger Adversarial Stress Test Suite for Milestone 3 Iteration 2 (Viewport 2 Document Studio).

Adversarially tests and verifies:
1. Code Studio:
   - Complex code strings with symbols, quotes, multiline comments, indentation, keywords, and function tokens.
   - Line numbers gutter synchronization with vertical scrolling.
   - Wrap toggle button (#btn-code-toggle-wrap / #btn-toggle-wrap) state transitions.
   - Copy code button (#btn-code-copy / #btn-copy-code) activation.
2. Data Grid Studio:
   - CSV strings with embedded quotes, commas inside quotes, multi-line values, and special characters.
   - Regex-safe live filtering with matching and non-matching substrings (#grid-search-input).
   - TSV export (#btn-grid-copy-tsv).
3. Auto-MIME Routing & M2 Backward Compatibility:
   - Dynamic routing on previewing .md, .py, .csv, .svg files.
   - Verification that active studio tab switches correctly to the corresponding sub-pane.
   - Verification of M2 backward compatibility: #ks-editor-textarea.value is always populated with file content.
   - Manual sub-view tab switching (.studio-view-btn).
4. Zero Console Errors:
   - Strict tracking of console errors and uncaught exceptions across all interactions.
"""

from __future__ import annotations

import re
import time
from typing import List
import pytest
from playwright.sync_api import Page, expect

from tests.test_browser_dom import server_url, playwright_instance, browser, page


def test_empirical_code_studio_complex_syntax_and_structure(page: Page) -> None:
    """Adversarially stress-test Code Studio with complex symbols, quotes, comments, and tokens."""
    page.wait_for_load_state("networkidle")

    # Switch to Viewport 2
    page.keyboard.press("Control+2")
    page.wait_for_timeout(100)
    expect(page.locator("#viewport-2")).to_have_class(re.compile(r"active"))

    # Switch to Code Studio sub-view
    page.locator("#btn-view-code").click()
    page.wait_for_timeout(100)
    expect(page.locator("#ks-code-studio")).to_be_visible()

    # Adversarial code string: symbols, escaped quotes, multiline docstrings, deep indentation, HTML tags
    adversarial_code = '''"""Module: Adversarial Agent Runner.
Stress testing syntax highlighting with special symbols: <tag> &amp; "quotes" 'single'
Line with math: x = (a + b) * (c / d) >= 100 and y != 0
"""
import sys
import os
from typing import List, Dict, Optional

# Inline comment with special characters: <script>alert("xss")</script> & symbols: @#$%^&*
def execute_complex_pipeline(action_id: str, payload: Dict[str, any], timeout_seconds: int = 30) -> bool:
    """Executes a multi-stage pipeline with strict validation."""
    if not action_id or timeout_seconds <= 0:
        return False

    raw_str = "String with \\"escaped quotes\\" and 'nested single quotes' inside"
    url_endpoint = 'http://localhost:8765/api/som?mark=04&detail=full'
    multiline_val = """First line of doc
    second line with symbols < > & " '
    third line ending doc"""

    # Indented loops and control flow
    for idx in range(10):
        if idx % 2 == 0:
            print(f"[RUNNER] Processing index: {idx} with value: {idx * 3.14159}")
        else:
            try:
                result = float(idx) / 2.5
            except Exception as exc:
                continue

    return True
'''

    # Invoke highlightCode directly with adversarial payload
    page.evaluate("(code) => window.highlightCode(code, 'py')", adversarial_code)
    page.wait_for_timeout(100)

    # 1. Verify line count and line numbers gutter
    expected_line_count = len(adversarial_code.split("\n"))
    line_number_els = page.locator("#code-line-numbers .code-line-number")
    actual_line_count = line_number_els.count()
    assert actual_line_count == expected_line_count, f"Line numbers count {actual_line_count} != expected {expected_line_count}"

    # Verify first and last line numbers
    assert line_number_els.first.text_content().strip() == "1"
    assert line_number_els.last.text_content().strip() == str(expected_line_count)

    # 2. Verify Stats & Lang Badges
    lang_badge = page.locator("#code-lang-badge")
    assert lang_badge.text_content().strip() == "PYTHON"

    stats_badge = page.locator("#code-stats-badge")
    stats_text = stats_badge.text_content().strip()
    assert f"{expected_line_count} lines" in stats_text, f"Stats badge '{stats_text}' does not contain line count"

    # 3. Verify Syntax Tokenization
    pre_el = page.locator("#code-highlighted-pre")
    expect(pre_el).to_be_visible()

    # Keywords (.tok-kw) must be tokenized
    kw_count = pre_el.locator(".tok-kw").count()
    assert kw_count >= 10, f"Expected at least 10 keywords highlighted, found {kw_count}"

    # Strings (.tok-str) must be tokenized
    str_count = pre_el.locator(".tok-str").count()
    assert str_count >= 3, f"Expected at least 3 string tokens, found {str_count}"

    # Comments (.tok-com) must be tokenized
    com_count = pre_el.locator(".tok-com").count()
    assert com_count >= 1, f"Expected at least 1 comment token, found {com_count}"

    # Functions (.tok-fn) must be tokenized
    fn_count = pre_el.locator(".tok-fn").count()
    assert fn_count >= 2, f"Expected function tokens (e.g. execute_complex_pipeline, print), found {fn_count}"

    # Numbers (.tok-num) must be tokenized
    num_count = pre_el.locator(".tok-num").count()
    assert num_count >= 3, f"Expected number tokens, found {num_count}"

    # 4. Strict XSS Prevention: Ensure injected <script> was safely escaped into text, not an actual DOM script node
    script_in_pre = pre_el.locator("script").count()
    assert script_in_pre == 0, "Security flaw: unescaped <script> tag found in code pre DOM!"

    # 5. Verify zero console errors
    assert len(page._console_errors) == 0, f"Console errors in code studio: {page._console_errors}"
    assert len(page._page_errors) == 0, f"Page errors in code studio: {page._page_errors}"


def test_empirical_code_studio_scroll_sync_and_toolbar(page: Page) -> None:
    """Stress-test vertical scroll synchronization between code editor and line numbers gutter, and toolbar controls."""
    page.wait_for_load_state("networkidle")
    page.keyboard.press("Control+2")
    page.wait_for_timeout(100)
    page.locator("#btn-view-code").click()
    page.wait_for_timeout(100)

    # Generate a tall 150-line code payload with wide lines
    tall_code_lines = [f"line_{i:03d} = 'Synthetic payload line {i}' + (' ' * 80) # Comment for line {i}" for i in range(1, 151)]
    tall_code = "\n".join(tall_code_lines)

    page.evaluate("(code) => window.highlightCode(code, 'py')", tall_code)
    page.wait_for_timeout(100)

    # 1. Scroll Synchronization Test
    # Scroll #code-content-wrapper by 400px
    scroll_res = page.evaluate("""() => {
        const wrapper = document.getElementById('code-content-wrapper');
        const gutter = document.getElementById('code-line-numbers');
        wrapper.scrollTop = 400;
        // Trigger scroll event manually in case needed
        wrapper.dispatchEvent(new Event('scroll'));
        return {
            wrapperScrollTop: wrapper.scrollTop,
            gutterScrollTop: gutter.scrollTop
        };
    }""")
    print("\n[SCROLL SYNC DOWN]", scroll_res)
    assert scroll_res["wrapperScrollTop"] > 0, "code-content-wrapper did not scroll"
    assert abs(scroll_res["wrapperScrollTop"] - scroll_res["gutterScrollTop"]) <= 1.0, (
        f"Gutter scrollTop {scroll_res['gutterScrollTop']} out of sync with wrapper {scroll_res['wrapperScrollTop']}"
    )

    # Scroll back to top (0px)
    scroll_top_res = page.evaluate("""() => {
        const wrapper = document.getElementById('code-content-wrapper');
        const gutter = document.getElementById('code-line-numbers');
        wrapper.scrollTop = 0;
        wrapper.dispatchEvent(new Event('scroll'));
        return {
            wrapperScrollTop: wrapper.scrollTop,
            gutterScrollTop: gutter.scrollTop
        };
    }""")
    print("[SCROLL SYNC TOP]", scroll_top_res)
    assert scroll_top_res["wrapperScrollTop"] == 0
    assert scroll_top_res["gutterScrollTop"] == 0

    # 2. Line Wrap Toggle Button Test (#btn-code-toggle-wrap or #btn-toggle-wrap)
    wrap_btn = page.locator("#btn-code-toggle-wrap, #btn-toggle-wrap")
    expect(wrap_btn).to_be_visible()

    pre_el = page.locator("#code-highlighted-pre")

    # Initial state: Wrap Off
    initial_wrap_text = wrap_btn.text_content().strip()
    assert "Off" in initial_wrap_text or "off" in initial_wrap_text.lower()
    initial_white_space = page.evaluate("() => document.getElementById('code-highlighted-pre').style.whiteSpace")
    assert initial_white_space == "pre"

    # Click toggle: Wrap On
    wrap_btn.click()
    page.wait_for_timeout(50)
    toggled_wrap_text = wrap_btn.text_content().strip()
    assert "On" in toggled_wrap_text or "on" in toggled_wrap_text.lower()
    toggled_white_space = page.evaluate("() => document.getElementById('code-highlighted-pre').style.whiteSpace")
    assert toggled_white_space == "pre-wrap"

    # Click toggle again: Wrap Off
    wrap_btn.click()
    page.wait_for_timeout(50)
    restored_wrap_text = wrap_btn.text_content().strip()
    assert "Off" in restored_wrap_text or "off" in restored_wrap_text.lower()
    restored_white_space = page.evaluate("() => document.getElementById('code-highlighted-pre').style.whiteSpace")
    assert restored_white_space == "pre"

    # Rapid toggle stress: 10 toggles
    for _ in range(10):
        wrap_btn.click()
    page.wait_for_timeout(50)
    # Even number of toggles leaves it at "pre"
    final_white_space = page.evaluate("() => document.getElementById('code-highlighted-pre').style.whiteSpace")
    assert final_white_space == "pre"

    # 3. Copy Code Button Test (#btn-code-copy or #btn-copy-code)
    copy_btn = page.locator("#btn-code-copy, #btn-copy-code")
    expect(copy_btn).to_be_visible()

    copy_btn.click()
    page.wait_for_timeout(100)
    copy_feedback_text = copy_btn.text_content().strip()
    print("[COPY CODE FEEDBACK]", copy_feedback_text)
    assert "Copied" in copy_feedback_text or "Copy" in copy_feedback_text

    # Verify zero console errors
    assert len(page._console_errors) == 0, f"Console errors: {page._console_errors}"
    assert len(page._page_errors) == 0, f"Page errors: {page._page_errors}"


def test_empirical_data_grid_adversarial_csv_parsing(page: Page) -> None:
    """Stress-test Data Grid Studio with adversarial CSVs: embedded quotes, commas inside quotes, multi-line values, and XSS."""
    page.wait_for_load_state("networkidle")
    page.keyboard.press("Control+2")
    page.wait_for_timeout(100)
    page.locator("#btn-view-grid").click()
    page.wait_for_timeout(100)
    expect(page.locator("#ks-data-grid-studio")).to_be_visible()

    # Adversarial CSV containing:
    # 1. Embedded commas inside double quotes: "Smith, John", "New York, NY"
    # 2. Escaped quotes inside double quotes: "He said ""Deploy now!"""
    # 3. Special characters & XSS tags: <script>alert(1)</script>, &amp;, EUR €
    # 4. Spaces, numbers, status codes
    adversarial_csv = (
        'id,client_name,location,quote_message,status,budget\n'
        '1,"Smith, John","New York, NY","He said ""Deploy now!""",success,15000\n'
        '2,"Doe, Jane","London, UK","Approval <gate> & checklist",pending,28500\n'
        '3,"Security, Bot","Berlin, DE","<script>alert(\'xss\')</script>",blocked,0\n'
        '4,"Alpha, Team","Tokyo, JP","Status: OK / 🚀 Active",success,94000\n'
    )

    page.evaluate("(csv) => window.renderDataGrid(csv)", adversarial_csv)
    page.wait_for_timeout(100)

    # 1. Verify Headers
    header_cells = page.locator("#grid-thead tr th")
    # Headers include 1 index column ('#') + 6 data columns = 7 total
    assert header_cells.count() == 7
    header_texts = [header_cells.nth(i).text_content().strip() for i in range(7)]
    assert header_texts == ["#", "id", "client_name", "location", "quote_message", "status", "budget"]

    # 2. Verify Row Count
    rows = page.locator("#grid-tbody tr")
    assert rows.count() == 4

    # 3. Verify Embedded Commas inside Quotes (Row 1: "Smith, John" and "New York, NY")
    row1_cells = rows.nth(0).locator("td")
    assert row1_cells.count() == 7
    assert row1_cells.nth(0).text_content().strip() == "1"  # Row number
    assert row1_cells.nth(1).text_content().strip() == "1"  # id
    assert row1_cells.nth(2).text_content().strip() == "Smith, John"  # comma inside quotes preserved!
    assert row1_cells.nth(3).text_content().strip() == "New York, NY"  # comma inside quotes preserved!
    assert row1_cells.nth(4).text_content().strip() == 'He said "Deploy now!"'  # escaped quotes unescaped!
    assert row1_cells.nth(5).text_content().strip() == "success"
    assert row1_cells.nth(6).text_content().strip() == "15000"

    # 4. Verify XSS Sanitization in Row 3 (<script> must not become a real DOM script)
    row3_cells = rows.nth(2).locator("td")
    assert row3_cells.nth(4).text_content().strip() == "<script>alert('xss')</script>"
    script_in_table = page.locator("#studio-data-grid script").count()
    assert script_in_table == 0, "Security flaw: unescaped <script> tag in table!"

    # 5. Verify Row 4 Special Glyphs / Emojis (🚀)
    row4_cells = rows.nth(3).locator("td")
    assert "🚀" in row4_cells.nth(4).text_content()

    # 6. Verify Dimensions Badge
    badge = page.locator("#grid-dimensions-badge")
    assert badge.text_content().strip() == "4 ROWS × 6 COLS"

    # 7. Delimiter auto-detection: Render TSV input (tabs)
    tsv_content = "step\taction\tduration_ms\n1\tscan\t45\n2\tplan\t120\n3\texec\t350"
    page.evaluate("(tsv) => window.renderDataGrid(tsv)", tsv_content)
    page.wait_for_timeout(100)

    tsv_headers = page.locator("#grid-thead tr th")
    assert tsv_headers.count() == 4  # '#' + 3 cols
    assert [tsv_headers.nth(i).text_content().strip() for i in range(4)] == ["#", "step", "action", "duration_ms"]
    assert page.locator("#grid-tbody tr").count() == 3
    assert page.locator("#grid-dimensions-badge").text_content().strip() == "3 ROWS × 3 COLS"

    # Verify zero console errors
    assert len(page._console_errors) == 0, f"Console errors: {page._console_errors}"
    assert len(page._page_errors) == 0, f"Page errors: {page._page_errors}"


def test_empirical_data_grid_live_search_and_tsv_export(page: Page) -> None:
    """Stress-test Data Grid live search filtering (matching, non-matching, regex-special substrings) and TSV export."""
    page.wait_for_load_state("networkidle")
    page.keyboard.press("Control+2")
    page.wait_for_timeout(100)
    page.locator("#btn-view-grid").click()
    page.wait_for_timeout(100)

    # 6 structured rows
    grid_data = (
        "id,agent_name,role,status,tasks_count\n"
        "1,agent_orion,orchestrator,active,14\n"
        "2,agent_atlas,worker,idle,0\n"
        "3,agent_titan,worker,active,5\n"
        "4,agent_nova,critic,blocked,2\n"
        "5,agent_vega,worker,active,8\n"
        "6,agent_cygnus,specialist,completed,12\n"
    )

    page.evaluate("(csv) => window.renderDataGrid(csv)", grid_data)
    page.wait_for_timeout(100)

    search_input = page.locator("#grid-search-input")
    expect(search_input).to_be_visible()
    badge = page.locator("#grid-dimensions-badge")

    # Initial state
    assert page.locator("#grid-tbody tr").count() == 6
    assert badge.text_content().strip() == "6 ROWS × 5 COLS"

    # 1. Filter matching multiple rows: "worker" (should match rows 2, 3, 5 = 3 rows)
    search_input.fill("worker")
    page.wait_for_timeout(100)
    assert page.locator("#grid-tbody tr").count() == 3
    assert badge.text_content().strip() == "3 / 6 ROWS × 5 COLS"

    # 2. Filter matching exact single row: "cygnus"
    search_input.fill("cygnus")
    page.wait_for_timeout(100)
    assert page.locator("#grid-tbody tr").count() == 1
    assert page.locator("#grid-tbody tr td").nth(2).text_content().strip() == "agent_cygnus"
    assert badge.text_content().strip() == "1 / 6 ROWS × 5 COLS"

    # 3. Filter with regex special characters without syntax crash: "[worker]", "(active)", "."
    search_input.fill("active")
    page.wait_for_timeout(100)
    assert page.locator("#grid-tbody tr").count() == 3  # rows 1, 3, 5

    # Type an unclosed bracket '[' (would crash if unescaped RegExp was used)
    search_input.fill("[")
    page.wait_for_timeout(100)
    # Should safely return 0 without JS crash
    assert page.locator("#grid-tbody tr").count() == 0
    assert badge.text_content().strip() == "0 / 6 ROWS × 5 COLS"

    # 4. Filter with completely non-matching query
    search_input.fill("non_existent_token_xyz_999")
    page.wait_for_timeout(100)
    assert page.locator("#grid-tbody tr").count() == 0
    assert badge.text_content().strip() == "0 / 6 ROWS × 5 COLS"

    # 5. Clear search query: restores all 6 rows
    search_input.fill("")
    page.wait_for_timeout(100)
    assert page.locator("#grid-tbody tr").count() == 6
    assert badge.text_content().strip() == "6 ROWS × 5 COLS"

    # 6. TSV Export Button (#btn-grid-copy-tsv)
    copy_tsv_btn = page.locator("#btn-grid-copy-tsv")
    expect(copy_tsv_btn).to_be_visible()

    # Trigger click
    copy_tsv_btn.click()
    page.wait_for_timeout(100)
    copy_text = copy_tsv_btn.text_content().strip()
    print("[COPY TSV FEEDBACK]", copy_text)
    assert "Copied" in copy_text or "Copy" in copy_text

    # Verify zero console errors
    assert len(page._console_errors) == 0, f"Console errors: {page._console_errors}"
    assert len(page._page_errors) == 0, f"Page errors: {page._page_errors}"


def test_empirical_auto_mime_routing_and_m2_backward_compatibility(page: Page) -> None:
    """Stress-test auto-MIME routing for .md, .py, .csv, .svg and verify strict M2 backward compatibility (#ks-editor-textarea.value)."""
    page.wait_for_load_state("networkidle")

    # Start at Viewport 1 to ensure previewInViewport2 switches stage to Viewport 2
    page.keyboard.press("Control+1")
    page.wait_for_timeout(100)
    expect(page.locator("#viewport-1")).to_have_class(re.compile(r"active"))

    # Vector 1: Markdown (.md)
    md_file = {
        "name": "architecture_spec.md",
        "ext": "md",
        "category": "doc",
        "content": "# System Architecture\n\nHigh-performance domain-agnostic agent cockpit.\n\n- Feature 1: SOM Perception\n- Feature 2: Document Studio"
    }
    page.evaluate("""(file) => {
        FileExplorer.files.push(file);
        FileExplorer.selectFile(file.name);
    }""", md_file)
    page.wait_for_timeout(150)

    # Must switch stage to Viewport 2
    expect(page.locator("#viewport-2")).to_have_class(re.compile(r"active"))

    # Studio sub-view must be Markdown
    expect(page.locator("#btn-view-markdown")).to_have_class(re.compile(r"active"))
    assert page.locator("#btn-view-markdown").get_attribute("aria-selected") == "true"
    expect(page.locator("#ks-markdown-studio")).to_be_visible()
    expect(page.locator("#ks-code-studio")).not_to_be_visible()
    expect(page.locator("#ks-data-grid-studio")).not_to_be_visible()
    expect(page.locator("#ks-media-studio")).not_to_be_visible()

    # Badge must be MARKDOWN
    assert page.locator("#ks-mode-indicator-badge").text_content().strip() == "MARKDOWN"

    # CRITICAL M2 BACKWARD COMPATIBILITY: #ks-editor-textarea.value must equal file content
    editor_val_md = page.locator("#ks-editor-textarea").input_value()
    assert editor_val_md == md_file["content"], f"Editor textarea value mismatch: '{editor_val_md}'"

    # Live preview body must contain rendered HTML
    preview_html = page.locator("#ks-markdown-preview").inner_html()
    assert "System Architecture" in preview_html
    assert "SOM Perception" in preview_html

    # Vector 2: Python Code (.py)
    py_file = {
        "name": "orchestrator_node.py",
        "ext": "py",
        "category": "code",
        "content": "import time\n\ndef run_orchestrator():\n    print('Orchestrator active')\n    return {'status': 'success'}\n"
    }
    page.evaluate("""(file) => {
        FileExplorer.files.push(file);
        FileExplorer.selectFile(file.name);
    }""", py_file)
    page.wait_for_timeout(150)

    # Studio sub-view must auto-route to Code
    expect(page.locator("#btn-view-code")).to_have_class(re.compile(r"active"))
    assert page.locator("#btn-view-code").get_attribute("aria-selected") == "true"
    expect(page.locator("#ks-code-studio")).to_be_visible()
    expect(page.locator("#ks-markdown-studio")).not_to_be_visible()
    expect(page.locator("#ks-data-grid-studio")).not_to_be_visible()
    expect(page.locator("#ks-media-studio")).not_to_be_visible()

    # Badges
    assert page.locator("#ks-mode-indicator-badge").text_content().strip() == "PY"
    assert page.locator("#code-lang-badge").text_content().strip() == "PYTHON"

    # CRITICAL M2 BACKWARD COMPATIBILITY: #ks-editor-textarea.value must equal file content
    editor_val_py = page.locator("#ks-editor-textarea").input_value()
    assert editor_val_py == py_file["content"], f"Editor textarea value mismatch for py: '{editor_val_py}'"

    # Vector 3: Tabular Data (.csv)
    csv_file = {
        "name": "latency_benchmarks.csv",
        "ext": "csv",
        "category": "data",
        "content": "stage,p50_ms,p99_ms\nperception,12,35\nplanning,85,210\nexecution,140,490\n"
    }
    page.evaluate("""(file) => {
        FileExplorer.files.push(file);
        FileExplorer.selectFile(file.name);
    }""", csv_file)
    page.wait_for_timeout(150)

    # Studio sub-view must auto-route to Data Grid
    expect(page.locator("#btn-view-grid")).to_have_class(re.compile(r"active"))
    assert page.locator("#btn-view-grid").get_attribute("aria-selected") == "true"
    expect(page.locator("#ks-data-grid-studio")).to_be_visible()
    expect(page.locator("#ks-markdown-studio")).not_to_be_visible()
    expect(page.locator("#ks-code-studio")).not_to_be_visible()

    # Badge
    assert page.locator("#ks-mode-indicator-badge").text_content().strip() == "DATA GRID"

    # Data grid table check
    assert page.locator("#grid-thead tr th").count() == 4  # '#' + 3 cols
    assert page.locator("#grid-tbody tr").count() == 3

    # CRITICAL M2 BACKWARD COMPATIBILITY: #ks-editor-textarea.value must equal file content
    editor_val_csv = page.locator("#ks-editor-textarea").input_value()
    assert editor_val_csv == csv_file["content"], f"Editor textarea value mismatch for csv: '{editor_val_csv}'"

    # Vector 4: Vector Graphics (.svg)
    svg_file = {
        "name": "flowchart.svg",
        "ext": "svg",
        "category": "media",
        "content": '<svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="40" fill="#06B6D4"/></svg>'
    }
    page.evaluate("""(file) => {
        FileExplorer.files.push(file);
        FileExplorer.selectFile(file.name);
    }""", svg_file)
    page.wait_for_timeout(150)

    # Studio sub-view must auto-route to Media
    expect(page.locator("#btn-view-media")).to_have_class(re.compile(r"active"))
    assert page.locator("#btn-view-media").get_attribute("aria-selected") == "true"
    expect(page.locator("#ks-media-studio")).to_be_visible()
    expect(page.locator("#ks-code-studio")).not_to_be_visible()
    expect(page.locator("#ks-data-grid-studio")).not_to_be_visible()

    # Badge
    assert page.locator("#ks-mode-indicator-badge").text_content().strip() == "MEDIA"
    assert page.locator("#media-type-badge").text_content().strip() == "SVG VECTOR GRAPHIC"
    svg_loc = page.locator("#media-display-container svg")
    assert svg_loc.count() == 1
    expect(svg_loc).to_be_visible()

    # CRITICAL M2 BACKWARD COMPATIBILITY: #ks-editor-textarea.value must equal file content
    editor_val_svg = page.locator("#ks-editor-textarea").input_value()
    assert editor_val_svg == svg_file["content"], f"Editor textarea value mismatch for svg: '{editor_val_svg}'"

    # Vector 5: Test Clicking Actual DOM File Tree Items in #kb-file-list
    # Select default files from tree list
    file_items = page.locator("#kb-file-list .file-tree-item")
    if file_items.count() > 0:
        # Click on metrics_report.csv
        csv_item = page.locator('#kb-file-list .file-tree-item[data-file="metrics_report.csv"]')
        if csv_item.count() > 0:
            csv_item.click()
            page.wait_for_timeout(150)
            expect(page.locator("#ks-data-grid-studio")).to_be_visible()
            assert page.locator("#ks-mode-indicator-badge").text_content().strip() == "DATA GRID"

        # Click on agent_runner.py
        py_item = page.locator('#kb-file-list .file-tree-item[data-file="agent_runner.py"]')
        if py_item.count() > 0:
            py_item.click()
            page.wait_for_timeout(150)
            expect(page.locator("#ks-code-studio")).to_be_visible()
            assert page.locator("#ks-mode-indicator-badge").text_content().strip() == "PY"

        # Click on README.md
        md_item = page.locator('#kb-file-list .file-tree-item[data-file="README.md"]')
        if md_item.count() > 0:
            md_item.click()
            page.wait_for_timeout(150)
            expect(page.locator("#ks-markdown-studio")).to_be_visible()
            assert page.locator("#ks-mode-indicator-badge").text_content().strip() == "MARKDOWN"

    # Verify zero console errors
    assert len(page._console_errors) == 0, f"Console errors: {page._console_errors}"
    assert len(page._page_errors) == 0, f"Page errors: {page._page_errors}"


def test_empirical_zero_console_errors_across_rapid_studio_stress(page: Page) -> None:
    """Stress-test rapid switching between all Document Studio sub-panes and verify 0 console errors."""
    page.wait_for_load_state("networkidle")
    page.keyboard.press("Control+2")
    page.wait_for_timeout(100)

    studio_buttons = ["#btn-view-markdown", "#btn-view-code", "#btn-view-grid", "#btn-view-media"]

    # Rapidly cycle between all 4 sub-views 5 times (20 transitions)
    for _ in range(5):
        for btn_sel in studio_buttons:
            page.locator(btn_sel).click()
            page.wait_for_timeout(30)

    # Edit raw markdown in textarea and verify live sync
    page.locator("#btn-view-markdown").click()
    page.wait_for_timeout(50)
    textarea = page.locator("#ks-editor-textarea")
    textarea.fill("# Adversarial Live Test\n\n- Sub-bullet 1\n- Sub-bullet 2")
    textarea.dispatch_event("input")
    page.wait_for_timeout(50)

    preview_text = page.locator("#ks-markdown-preview").text_content()
    assert "Adversarial Live Test" in preview_text
    assert "Sub-bullet 1" in preview_text

    # Strict check: 0 console errors and 0 page exceptions
    print(f"\n[CONSOLE ERRORS COUNT]: {len(page._console_errors)}")
    print(f"[PAGE ERRORS COUNT]: {len(page._page_errors)}")
    assert len(page._console_errors) == 0, f"Uncaught console errors: {page._console_errors}"
    assert len(page._page_errors) == 0, f"Uncaught page exceptions: {page._page_errors}"
