## 2026-10-29T10:40:31Z
You are worker_m3_iter2_2, a teamwork_worker implementing the Milestone 3 Iteration 2 Remediation for the Agent Workstation project.

## Working Directory
Your working directory is: `c:\Users\andym\gschwelli-ai\.agents\teamwork\worker_m3_iter2_2`
Store all your internal metadata (progress.md, handoff.md, etc.) in this folder.
Never write code or tests in .agents/teamwork/.

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Mandatory Inputs & References
You MUST read these files first:
1. `c:\Users\andym\gschwelli-ai\.agents\teamwork\ORIGINAL_REQUEST.md` (authoritative user request)
2. `c:\Users\andym\gschwelli-ai\PROJECT.md` (architecture & feature specifications)
3. `c:\Users\andym\gschwelli-ai\.agents\teamwork\explorer_m3_iter2\handoff.md` (remediation summary & plan)
4. `c:\Users\andym\gschwelli-ai\.agents\teamwork\explorer_m3_iter2\analysis.md` (detailed line-by-line blueprint, replacement tables, and JS code snippets)
5. `c:\Users\andym\gschwelli-ai\.agents\teamwork\auditor_m3_v2\handoff.md` (full audit evidence of 36 CAD tokens)
6. `c:\Users\andym\gschwelli-ai\.agents\teamwork\reviewer_m3_v2_1\handoff.md` (full reviewer change requests for Viewport 2)

## Write Ownership
You have exclusive write access to:
- `ui/dashboard/index.html`
- `tests/test_challenge_m3_2.py`
- `tests/test_reviewer_m3_stress.py`

## Implementation Tasks

### Part A: 100% CAD Token Eradication & Test Harmonization
1. In `ui/dashboard/index.html`:
   - Replace all 36 occurrences of forbidden CAD tokens (`openscad`, `toolhead_mount`, `cgal`, `bolt holes`, `csg-overlay`, `axis-gizmo`) per the exact mapping in `explorer_m3_iter2/analysis.md § 2.1`.
   - Specifically:
     - Replace `M-024 / Export toolhead_mount.stl` with `M-024 / Execute action_target.py` (line 3679).
     - Replace `C:\Fabrication\toolhead_mount.stl` with `c:\workspace\action_target.py` in `#export-path-input` (line 3894).
     - In `#repl-logs` default content and REPL simulation: replace `[OpenSCAD]` with `[STREAM]`, `CGAL 2-manifold render completed` with `2D Surface Mesh analysis completed`, `bolt holes` with `anchors`.
     - Delete obsolete `.csg-overlay` and `.axis-gizmo` CSS blocks or replace with generic canvas classes.
2. In `tests/test_challenge_m3_2.py`:
   - Line 196: Harmonize assertion to expect `action_target.py` (instead of `toolhead_mount.stl`).
   - Line 203: Change new_path to `c:\workspace\adversarial_action_target_v99.py`.
   - Line 317: Harmonize assertion to expect `[STREAM] DOM structure analysis completed` (instead of `[OpenSCAD] Preview compiled`).
   - Line 333: Harmonize assertion to expect `[STREAM] 2D Surface Mesh analysis completed` (instead of `[OpenSCAD] CGAL 2-manifold render completed`).
3. In `tests/test_reviewer_m3_stress.py`:
   - Line 156: Expect `2D Surface Mesh analysis completed` (instead of `CGAL 2-manifold render completed`).
   - Line 161: Expect `DOM inspector viewport locked in sandboxed focus mode` (instead of `OpenSCAD viewport locked in sandboxed focus mode`).

### Part B: Genuine Viewport 2 Document Studio Implementation
In `ui/dashboard/index.html`:
1. HTML Structure:
   - Ensure the Studio Sub-Navigation includes buttons with class `studio-view-btn` for Markdown (`#btn-view-markdown`), Code (`#btn-view-code`), Data Grid (`#btn-view-grid`), and Media (`#btn-view-media`).
   - Ensure `#code-highlighted-pre` and `#code-line-numbers` exist inside `#code-view-container`.
   - Ensure `#studio-data-grid` has `#grid-thead` and `#grid-tbody`, and toolbar has `#grid-search-input` and `#btn-grid-copy-tsv`.
2. JavaScript Logic:
   - Implement `highlightCode(code, lang)`:
     - XSS-escapes code first.
     - Tokenizes keywords (`def`, `class`, `import`, `return`, `const`, `function`, etc. -> `<span class="tok-kw">...</span>`), strings (`<span class="tok-str">...</span>`), numbers (`<span class="tok-num">...</span>`), comments (`<span class="tok-com">...</span>`), functions (`<span class="tok-fn">...</span>`).
     - Generates line numbers in `#code-line-numbers` (`1\n2\n...`).
     - Sets `#code-highlighted-pre.innerHTML`.
     - Synchronizes vertical scrolling between `#code-editor-textarea` (or container) and `#code-line-numbers`.
   - Implement `parseCsv(text, delimiter)`:
     - Quote-aware and newline-aware CSV/TSV parser.
     - Populates `#grid-thead` with column headers.
     - Populates `#grid-tbody` with zebra rows and row number column `#`.
     - Binds real-time search filtering on `#grid-search-input` (`keyup`/`input`) to hide/show rows.
     - Binds `#btn-grid-copy-tsv` click handler to export grid rows as TSV to clipboard (wrapped in try/catch with temporary "Copied!" feedback).
   - Event Handlers:
     - Bind `#btn-code-toggle-wrap` to toggle `white-space: pre` vs `pre-wrap`.
     - Bind `#btn-code-copy` to copy code to clipboard with "Copied!" feedback.
     - Bind `.studio-view-btn` click handlers to manually switch sub-views (`markdown`, `code`, `grid`, `media`).
   - Auto-MIME Routing in `FileExplorer`:
     - Update `FileExplorer.previewInViewport2(file)` or `renderArtifactStudio(fileName, content)`:
       - Detect extension: `.md` -> Markdown Studio; `.py`, `.js`, `.json`, `.yaml`, `.sh` -> Code Studio; `.csv`, `.tsv` -> Data Grid; `.svg`, `.png` -> Media Studio.
       - CRITICAL BACKWARD COMPATIBILITY: ALWAYS set `#ks-editor-textarea.value = file.content` so that `test_challenge_m2.py` line 644 continues to pass!
       - If Code: call `highlightCode(file.content, lang)`.
       - If CSV: call `renderDataGrid(file.content)`.
       - If Markdown: set `#ks-editor-textarea.value = file.content` and render `#ks-markdown-preview`.
       - Switch stage to Viewport 2 (`switchViewport(2)`).

## Verification Requirements
Before delivering your handoff, you must run and document:
1. CAD Token Scan:
   Scan `ui/dashboard/index.html` for: `openscad`, `toolhead_mount`, `cgal`, `facet-base`, `bolt holes`, `csg-overlay`, `axis-gizmo`. Must return 0 matches.
2. Full Test Verification:
   - `uv run --with pytest,playwright pytest tests/test_browser_dom.py tests/test_api.py -v`
   - `uv run --with pytest,playwright pytest tests/test_challenge_m3_1.py tests/test_challenge_m3_2.py tests/test_reviewer_m3_stress.py -v`
   - `uv run --with pytest,playwright pytest tests/test_challenge_m2.py tests/test_adversarial_m2.py -v`
3. Write `handoff.md` with:
   - Exact files modified and lines changed.
   - Command output showing 0 CAD tokens.
   - Full pytest execution results.
4. Send completion message back to parent orchestrator.
