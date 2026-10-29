## 2026-10-29T10:34:18Z
You are worker_m3_iter2, a teamwork_worker subagent assigned to remediate Milestone 3 (Polymorphic Stage) in ui/dashboard/index.html.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY REQUIREMENTS & REFERENCES:
1. You MUST read the authoritative user request at:
   c:\Users\andym\gschwelli-ai\.agents\teamwork\ORIGINAL_REQUEST.md
   and the project plan at:
   c:\Users\andym\gschwelli-ai\PROJECT.md
2. You MUST read the full audit evidence report from auditor_m3_v2:
   c:\Users\andym\gschwelli-ai\.agents\teamwork\auditor_m3_v2\handoff.md
3. You MUST read the reviewer evidence report from reviewer_m3_v2_1:
   c:\Users\andym\gschwelli-ai\.agents\teamwork\reviewer_m3_v2_1\handoff.md
4. You MUST read the remediation blueprint prepared by explorer_m3_iter2:
   c:\Users\andym\gschwelli-ai\.agents\teamwork\explorer_m3_iter2\analysis.md
   c:\Users\andym\gschwelli-ai\.agents\teamwork\explorer_m3_iter2\handoff.md
5. File write ownership:
   - Primary: `ui/dashboard/index.html`
   - Test alignment: You are authorized to edit `tests/test_challenge_m3_2.py` and `tests/test_reviewer_m3_stress.py` ONLY to update legacy CAD assertions to domain-agnostic assertions as specified in Part A.2 of the remediation blueprint.
   - DO NOT edit `server/api.py`.
6. Working directory: Write your coordination metadata, progress, and handoff report to:
   c:\Users\andym\gschwelli-ai\.agents\teamwork\worker_m3_iter2\

YOUR MISSION:
Execute the remediation blueprint exactly as detailed in `explorer_m3_iter2/analysis.md`:

1. PART A: 100% CAD TOKEN ERADICATION
   - Replace all 36 occurrences of forbidden CAD tokens in `ui/dashboard/index.html` across all 6 token types (`openscad`, `toolhead_mount`, `cgal`, `bolt holes`, `csg-overlay`, `axis-gizmo`) using the exact replacements specified in Section 2.1 of `explorer_m3_iter2/analysis.md`.
   - Update `#active-mission-label` to `M-024 / Run action_target.py` and `#export-path-input` to `workspace/default/action_target.py`.
   - Delete dead legacy CSS rules `.csg-overlay` and `.axis-gizmo`.
   - In `tests/test_challenge_m3_2.py` and `tests/test_reviewer_m3_stress.py`, harmonize assertions with the new domain-agnostic strings (e.g. check for `action_target.py` instead of `toolhead_mount.stl`, check for `[STREAM] DOM structure analysis completed` instead of `[OpenSCAD] CGAL 2-manifold render completed`).

2. PART B: GENUINE VIEWPORT 2 (DOCUMENT STUDIO) IMPLEMENTATION
   - Feature #20 (Monospace Code Studio): Implement `highlightCode(code, lang)` with HTML escaping and semantic classes (`.tok-kw`, `.tok-str`, `.tok-num`, `.tok-com`, `.tok-fn`), generate line numbers in `#code-line-numbers` with vertical scroll synchronization, and bind active handlers for `#btn-code-copy` and `#btn-code-toggle-wrap`.
   - Feature #21 (Tabular Data Grid): Implement `parseCsv(text, delimiter)` with quotation-awareness, render sticky headers in `#grid-thead`, zebra rows in `#grid-tbody`, bind real-time row filtering on `#grid-search-input`, and bind TSV clipboard export on `#btn-grid-copy-tsv`.
   - Feature #13 (Auto-MIME Routing): Update `FileExplorer.previewInViewport2(file)` and `renderArtifactStudio(fileName, content)` to auto-activate matching sub-panes (`#ks-markdown-studio`, `#ks-code-studio`, `#ks-data-grid-studio`, `#ks-media-studio`), update `#ks-mode-indicator-badge`, and crucially maintain `#ks-editor-textarea.value = file.content` to preserve Milestone 2 backward compatibility.
   - Add `.studio-view-btn` buttons to the HTML studio header and wire event listeners to eliminate all dead/unbound elements.

VERIFICATION:
- Verify 0 CAD tokens remain via:
  `$tokens = @("openscad", "toolhead_mount", "cgal", "facet-base", "bolt holes", "csg-overlay", "axis-gizmo"); foreach ($t in $tokens) { Select-String -Path ui/dashboard/index.html -Pattern $t -CaseSensitive:$false }` (Must be 0 matches).
- Run full test suites:
  `uv run --with pytest,playwright pytest tests/test_browser_dom.py tests/test_api.py -v`
  `uv run --with pytest,playwright pytest tests/test_challenge_m3_1.py tests/test_challenge_m3_2.py tests/test_reviewer_m3_stress.py -v`
  `uv run --with pytest,playwright pytest tests/test_challenge_m2.py tests/test_adversarial_m2.py -v`
- Ensure 100% pass, zero console errors, zero uncaught exceptions.

OUTPUT:
Write your step-by-step progress to `progress.md` and complete handoff report to:
c:\Users\andym\gschwelli-ai\.agents\teamwork\worker_m3_iter2\handoff.md
Send a completion message when done with test results and CAD scan output.
