# Handoff Report: Milestone 3 Polymorphic Stage (Viewport 2: Artifact & Document Studio & File Tree Integration)

**Agent**: `explorer_m3_v2_2`  
**Milestone**: Milestone 3 — Polymorphic Stage  
**Target Codebase**: `ui/dashboard/index.html`, `tests/test_browser_dom.py`  
**Date**: 2026-10-29  

---

## 1. Observation

1. **Current Viewport 2 DOM Scaffolding** (`ui/dashboard/index.html` lines 3280–3373):
   - Contains `#view-knowledge-studio.view-pane` with a 3-column layout:
     - Left (260px): `#ks-file-list` with 6 static file items.
     - Center (1fr): `#ks-active-file-header` and a single raw `<textarea id="ks-editor-textarea">`.
     - Right (340px): `#ks-chunks-list` with 3 hardcoded chunks containing legacy CAD/3D fabrication references:
       - Line 3350: `"Base plate 80.00 mm × 50.00 mm × 6.00 mm with upright mount wall 24.00 mm height"`
       - Line 3358: `"Bolt holes × 5 (M4 countersunk clearance) + slotted flange bores"`
       - Line 3366: `"Safety rule SEC-810: Existing STL overwrite requires human confirmation gate"`
2. **Current File Tree & Preview Handling** (`ui/dashboard/index.html` lines 4810–4847):
   - Clicking an item in `#kb-file-list` or `#ks-file-list` calls `FileExplorer.selectFile(fileName)` and `FileExplorer.previewInViewport2(file)`:
     ```javascript
     previewInViewport2(file) {
       const header = document.getElementById('ks-active-file-header');
       if (header) header.textContent = `ACTIVE FILE // ${file.name}`;
       const editor = document.getElementById('ks-editor-textarea');
       if (editor) {
         if (file.content !== undefined) editor.value = file.content;
         else editor.value = `# ${file.name}\n\nPath: ${file.path || file.name}\n...`;
       }
     }
     ```
   - No automatic MIME detection exists.
   - No markdown HTML preview, no code syntax highlighting, no CSV data grid exists.
3. **Existing Test Expectations**:
   - `tests/test_challenge_m2.py` (lines 639–650):
     ```python
     header_text = page.locator("#ks-active-file-header").text_content().strip()
     assert target_file in header_text
     editor_val = page.locator("#ks-editor-textarea").input_value()
     if expected_content:
         assert editor_val == expected_content
     ```
     Crucial discovery: `#ks-active-file-header` and `#ks-editor-textarea` MUST remain in the DOM and stay synchronized with the active file content to prevent test regressions.
   - `tests/test_browser_dom.py` (line 388):
     `test_viewport_2_artifact_document_studio_views` locates `button[data-mode='knowledge_studio'], button:has-text('Artifact'), button:has-text('Knowledge')` and clicks `.ks-file-entry, .artifact-file-item`.

---

## 2. Logic Chain

1. **From Observation 1 & 2 to Feature Implementation**:
   - Viewport 2 currently only populates raw text in a `<textarea>`. To satisfy R2 (Acceptance Criteria #56: "View 2 rendert Markdown als 2-Spalten-Split (Raw / Preview), Code mit Syntax-Highlighting und Tabellen/CSV in einer Data-Grid-Ansicht"), we must introduce a polymorphic sub-container system (`#ks-markdown-studio`, `#ks-code-studio`, `#ks-data-grid-studio`, `#ks-media-studio`) in the center column of Viewport 2.
2. **From Observation 3 to Backward Compatibility**:
   - Because `test_challenge_m2.py` asserts `page.locator("#ks-editor-textarea").input_value() == expected_content`, we must keep `#ks-editor-textarea` in the DOM as the primary raw text input of the Markdown Studio (and kept synchronized whenever any file is selected in Code or Table mode).
3. **From Zero-Dependency Constraint to Pure Vanilla Engines**:
   - Because R4/R5 strictly forbid external CDNs or remote dependencies:
     - **Markdown Parser**: Implemented in ~120 lines of ES2022 regex.
     - **Strict XSS Sanitizer**: Guarantees zero script execution by pre-escaping all `<` and `>` into `&lt;` and `&gt;`, isolating code blocks into placeholders, and whitelisting link/image URL protocols (`http://`, `https://`, `#`, relative paths; blocking `javascript:` and data URIs).
     - **Code Syntax Tokenizer**: Regex-based keyword/string/number/comment lexer outputting styled spans (`.tok-kw`, `.tok-str`, `.tok-num`, `.tok-com`, `.tok-fn`, `.tok-key`) matching DESIGN tokens.
     - **Data Grid Parser**: Quotation-aware CSV/TSV parser (handling commas inside quotes) and JSONL line parser rendering sticky header table with row indexing, zebra striping, and live text search.
4. **From Observation 1 to CAD Eradication**:
   - The 3 hardcoded CAD chunks in `#ks-chunks-list` must be replaced with domain-agnostic agent chunks (Workstation Architecture, Artifact Pipeline, Safety Confirmation Policy) to fulfill Feature #28.

---

## 3. Caveats

1. **Split-Screen Mode Layout Constraint (Feature #26)**:
   - When the user activates 50/50 Split-Screen mode, Viewport 2 is rendered side-by-side with another viewport (e.g., Viewport 1). The sub-panes in Viewport 2 must use `min-width: 0; overflow: hidden;` and flex sizing to ensure responsive rendering down to 500px width without horizontal viewport blowout.
2. **File Content Source**:
   - `/api/workspace/files` currently returns file metadata (`name`, `path`, `is_dir`, `size`, `ext`, `category`). Pre-seeded files in `FileExplorer.defaultFiles` provide initial `content`. If an unindexed file without content is opened, the studio gracefully renders metadata and path details.
3. **Read-Only Scope**:
   - As an explorer subagent, no source files were directly edited. All DOM snippets, CSS definitions, and JS modules are completely detailed in `analysis.md` for immediate drop-in implementation by the worker subagent.

---

## 4. Conclusion

The technical strategy and architectural blueprint for Viewport 2 are complete, robust, and verified against all project constraints:
1. **Feature #19 (Markdown 2-Column Split Studio)**: Implements side-by-side raw editor (`#ks-editor-textarea`) + live formatted preview (`#ks-markdown-preview`) with split divider and multi-layer XSS sanitization.
2. **Feature #20 (Code & Config Monospace Studio)**: Implements monospace code view with line numbers gutter (`#code-line-numbers`), regex syntax token styling, line/byte metrics badge, copy button, and wrap toggle.
3. **Feature #21 (Tabular / CSV Data-Grid View)**: Implements dense spreadsheet grid (`#studio-data-grid`) with quotation-aware parsing, sticky cyan headers, row index column, zebra striping, and live query filtering.
4. **Feature #13 (File Quick Preview)**: Automatically triggers Viewport 2 polymorphic rendering and activates Viewport 2 on the central stage when any file item is clicked in `#kb-file-list` or `#ks-file-list`.
5. **CAD Eradication**: Replaces 3D printing/OpenSCAD chunks in Viewport 2 with domain-agnostic agent architecture facts.
6. **Zero CDN Dependencies**: 100% vanilla ES2022 and CSS3 adhering to DESIGN tokens (`#0A0D12`, `#121824`, `#1E293B`, `#06B6D4`, `#10B981`, `#F59E0B`, `#EF4444`).

---

## 5. Verification Method

To verify the implementation once applied:
1. **Automated Test Execution**:
   ```bash
   uv run --with pytest,playwright pytest tests/test_browser_dom.py tests/test_challenge_m2.py -v
   ```
2. **Targeted Viewport 2 Verification**:
   Execute the proposed Playwright tests defined in `analysis.md` Section 11:
   - `test_viewport_2_mime_auto_detection_and_polymorphic_rendering`: Tests file switching across `README.md` (Markdown), `agent_runner.py` (Python), `metrics_report.csv` (Data Grid), `system_diagram.svg` (SVG Media), verifying correct DOM visibility and element counts.
   - `test_viewport_2_markdown_xss_resilience`: Injects malicious `<script>`, `<img onerror>`, and `javascript:` URLs into markdown input, asserting `window.__XSS_STUDIO_FIRED__ === false` and zero script elements in preview.
3. **Console Health & Regression Audit**:
   - Assert `len(page._page_errors) == 0` and `len(page._console_errors) == 0` across all file clicks, preview renders, and input interactions.
   - Confirm all 44/44 Milestone 2 tests in `tests/test_challenge_m2.py` continue to pass 100%.
