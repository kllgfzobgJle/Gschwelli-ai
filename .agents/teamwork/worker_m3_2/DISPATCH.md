# Dispatch Assignment: Milestone 3 Remediation Worker (worker_m3_2)
Working directory: c:\Users\andym\gschwelli-ai\.agents\teamwork\worker_m3_2
Identity: teamwork_preview_worker
Parent: orchestrator_1 (20ee9337-54d2-4ed7-a02f-42aad4232d45)
Scope: Remediate SOM tag placement and cold-load active class in ui/dashboard/index.html based on unanimous Gate 3 findings.

EXCLUSIVELY OWNED FILES:
- c:\Users\andym\gschwelli-ai\ui\dashboard\index.html

MANDATORY INPUTS (read these before starting work):
- c:\Users\andym\gschwelli-ai\.agents\teamwork\ORIGINAL_REQUEST.md
- c:\Users\andym\gschwelli-ai\PROJECT.md
- Visual Mockup: c:\Users\andym\gschwelli-ai\Inspirations\ui_reference_mockup.png
- Reviewer 1 Handoff: c:\Users\andym\gschwelli-ai\.agents\teamwork\reviewer_m3_1\handoff.md
- Reviewer 2 Handoff: c:\Users\andym\gschwelli-ai\.agents\teamwork\reviewer_m3_2\handoff.md
- Challenger 1 Handoff: c:\Users\andym\gschwelli-ai\.agents\teamwork\challenger_m3_1\handoff.md
- Challenger 2 Handoff: c:\Users\andym\gschwelli-ai\.agents\teamwork\challenger_m3_2\handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

REMEDIATION TASKS:
1. In `ui/dashboard/index.html` (CSS around lines 1036–1040):
   Reposition SOM callout tags so they float in the 3D CAD canvas margin above the export dock, matching Inspirations/ui_reference_mockup.png:
   ```css
   .som-tag-01 { top: 10px; left: 16px; }
   .som-tag-02 { top: 6px; right: 88px; }
   .som-tag-12 { bottom: 120px; left: 24px; }
   .som-tag-04 { bottom: 120px; right: 28px; }
   ```
   This clears `#btn-export-mesh` and `#export-path-input` 100%, resolving pointer event interception while allowing leader lines to point down to their targets.
2. In `ui/dashboard/index.html` (HTML around lines 2146–2147):
   Add the `active` class to `#leader-line-04` and `#anchor-dot-04` in the static HTML markup to match `#som-tag-04.active` on cold load:
   ```html
   <line class="som-leader-line line-04 active" id="leader-line-04" x1="0" y1="0" x2="0" y2="0" />
   <circle class="som-anchor-dot dot-04 active" id="anchor-dot-04" cx="0" cy="0" r="3.5" />
   ```
3. Verification:
   Run all test suites and confirm 100% pass:
   - `uv run --with pytest pytest tests/test_api.py -v`
   - `uv run --with pytest,playwright pytest tests/test_browser_dom.py -v`
   - `uv run --with pytest,playwright pytest tests/test_challenge_m3_1.py -v`
   - `uv run --with pytest,playwright pytest tests/test_challenge_m3_2.py -v`
   - `uv run --with pytest,playwright pytest tests/test_challenge_m2.py -v`
   - `uv run --with pytest,playwright pytest tests/test_adversarial_m2.py -v`
4. Write handoff.md with verification commands and output, and notify orchestrator_1.
