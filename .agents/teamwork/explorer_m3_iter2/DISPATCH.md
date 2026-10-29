## 2026-10-29T10:24:15Z
You are explorer_m3_iter2, a teamwork_explorer subagent investigating the remediation strategy for Milestone 3 (Polymorphic Stage: 4 Viewports & Split-Screen) following Iteration 1 Gate Failure.

MANDATORY INTEGRITY DIRECTIVE:
Milestone 3 Iteration 1 failed due to:
1. FORENSIC AUDIT INTEGRITY VIOLATION from auditor_m3_v2 (36 forbidden CAD tokens found in ui/dashboard/index.html).
2. REVIEWER INTEGRITY VIOLATION from reviewer_m3_v2_1 (Viewport 2 contains dummy facade implementations: Features #20 and #21 had empty HTML markup but zero JavaScript logic to populate code syntax tokens, line numbers, or CSV table rows, and interactive buttons lacked event listeners).

YOU MUST READ:
1. The authoritative user request at:
   c:\Users\andym\gschwelli-ai\.agents\teamwork\ORIGINAL_REQUEST.md
   and the project plan at:
   c:\Users\andym\gschwelli-ai\PROJECT.md
2. The FULL AUDIT EVIDENCE REPORT (NON-NEGOTIABLE):
   c:\Users\andym\gschwelli-ai\.agents\teamwork\auditor_m3_v2\handoff.md
3. The REVIEWER EVIDENCE REPORT:
   c:\Users\andym\gschwelli-ai\.agents\teamwork\reviewer_m3_v2_1\handoff.md
4. The worker's previous implementation in:
   c:\Users\andym\gschwelli-ai\ui\dashboard\index.html
5. The challenge test files:
   `tests/test_challenge_m3_2.py`, `tests/test_reviewer_m3_stress.py`, `tests/test_browser_dom.py`.

YOUR MISSION:
Develop an exact, comprehensive, step-by-step remediation strategy for worker_m3_iter2:

PART A: 100% CAD TOKEN ERADICATION
- Analyze all 36 occurrences of forbidden CAD tokens cited by the auditor:
  * `openscad` (9 occurrences): replace with domain-agnostic desktop stream diagnostics (e.g. `[STREAM]`, `Workspace Process`).
  * `toolhead_mount` (19 occurrences): replace in Center Stage (`#active-mission-label`, `#export-path-input`, etc.) with generic paths (`workspace/default/action_target.py` or `artifact_output.dat`).
  * `cgal` (5 occurrences): replace with `2D Surface Mesh` or generic verification.
  * `bolt holes` (1 occurrence): replace placeholder with `Search files or content...`.
  * `csg-overlay` (1 occurrence): remove legacy CSS rule.
  * `axis-gizmo` (1 occurrence): remove legacy CSS rule.
- Analyze the legacy challenge test assertions in `tests/test_challenge_m3_2.py` and `tests/test_reviewer_m3_stress.py` that caused the worker to retain these strings. Determine exact modifications needed in the tests to assert domain-agnostic strings instead of hardcoded CAD names.

PART B: GENUINE VIEWPORT 2 (DOCUMENT STUDIO) IMPLEMENTATION
- Feature #20 (Monospace Code Studio):
  * Design exact JavaScript logic to split file content by newline, generate line numbers in `#code-line-numbers`, and highlight code tokens (spans with classes .tok-kw, .tok-str, .tok-num, .tok-com, .tok-fn) in `#code-highlighted-pre`.
  * Design event handlers for `#btn-code-copy` (clipboard copy with visual confirmation) and `#btn-code-toggle-wrap` (toggle pre vs pre-wrap).
- Feature #21 (Tabular / CSV Data-Grid View):
  * Design quotation-aware CSV/TSV parser generating sticky headers in `#grid-thead` and rows in `#grid-tbody` with row numbering and zebra striping.
  * Design live filter handler on `#grid-search-input` filtering table rows dynamically.
  * Design export handler on `#btn-grid-copy-tsv`.
- Feature #13 (Auto-MIME File Preview Routing):
  * Update `FileExplorer.previewInViewport2(file)` / `FileExplorer.selectFile(fileName)` to automatically detect file extension and activate the appropriate studio sub-pane (`#ks-markdown-studio` for .md, `#ks-code-studio` for .py/.js/.json/.yaml, `#ks-data-grid-studio` for .csv/.tsv, `#ks-media-studio` for .svg/.png).
  * Ensure backward compatibility: keep `#ks-active-file-header` and `#ks-editor-textarea` synchronized so existing tests pass.

OUTPUT:
Write your complete technical analysis and remediation plan to:
c:\Users\andym\gschwelli-ai\.agents\teamwork\explorer_m3_iter2\analysis.md
and a structured handoff to:
c:\Users\andym\gschwelli-ai\.agents\teamwork\explorer_m3_iter2\handoff.md
Send a completion message when done.
