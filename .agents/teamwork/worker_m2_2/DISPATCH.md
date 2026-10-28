## 2026-10-28T16:39:37Z
You are teamwork_preview_worker for Milestone 2 Remediation (Iteration 2).
Your working directory is: c:\Users\andym\gschwelli-ai\.agents\teamwork\worker_m2_2
Your parent is the Project Orchestrator (conversation ID: 20ee9337-54d2-4ed7-a02f-42aad4232d45).

MANDATORY INPUTS (read these before starting work):
- c:\Users\andym\gschwelli-ai\.agents\teamwork\ORIGINAL_REQUEST.md
- c:\Users\andym\gschwelli-ai\PROJECT.md
- Reviewer 1 Handoff: c:\Users\andym\gschwelli-ai\.agents\teamwork\reviewer_m2_1\handoff.md
- Challenger 1 Handoff: c:\Users\andym\gschwelli-ai\.agents\teamwork\challenger_m2_1\handoff.md
- Challenger 2 Handoff: c:\Users\andym\gschwelli-ai\.agents\teamwork\challenger_m2_2\handoff.md

EXCLUSIVELY OWNED FILES:
- c:\Users\andym\gschwelli-ai\ui\dashboard\index.html

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

YOUR MISSION:
Remediate the 4 specific findings from the Milestone 2 Gate:
1. Fix the CSS specificity bug on #view-mission-control (lines ~287-296 of ui/dashboard/index.html):
   Change:
   #view-mission-control {
     grid-template-columns: var(--left-sidebar-width) 1fr var(--right-sidebar-width);
     width: 100%;
     height: 100%;
     overflow: hidden;
   }
   #view-mission-control.active-view {
     display: grid;
   }
   Ensure #view-mission-control does NOT have unconditional display: grid, so when inactive it inherits .view-pane { display: none; } and does not leak into other tab views.
2. Fix XSS/HTML injection in task rendering (around line 2169 of ui/dashboard/index.html):
   Implement escapeHtml(str) utility and sanitize task.title before setting innerHTML in renderTasks().
3. Add white-space: nowrap to .mode-pill and .canvas-action-toolbar button so labels don't wrap at narrow viewports (e.g. 1024x768).
4. Wire click listeners:
   - #kb-folder-toggle: toggles display of #kb-file-list (collapsing/expanding folder).
   - #btn-settings: opens a settings modal/drawer or displays settings dialog.
   - Format VRAM in syncBackendState() with Number(data.system.ram_used_gb || 4.2).toFixed(1).
5. Verify your fixes:
   Run all tests:
   uv run --with pytest pytest tests/test_api.py -v
   uv run --with pytest,playwright pytest tests/test_browser_dom.py -v
   uv run --with pytest,playwright pytest tests/ -v
   Also run Playwright test to verify #view-mission-control is hidden (display: none) when switching to Knowledge Studio.
6. Write handoff.md with verified results and notify parent with send_message.
