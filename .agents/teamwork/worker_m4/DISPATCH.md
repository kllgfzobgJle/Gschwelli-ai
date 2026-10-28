## 2026-10-28T18:13:07Z
You are worker_m4.
Your working directory is: c:\Users\andym\gschwelli-ai\.agents\teamwork\worker_m4
Your parent agent is: orchestrator_1 (id: 20ee9337-54d2-4ed7-a02f-42aad4232d45).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY INSTRUCTION: You MUST read ORIGINAL_REQUEST.md before starting work:
c:\Users\andym\gschwelli-ai\.agents\teamwork\ORIGINAL_REQUEST.md

You MUST also read the handoff reports from the Milestone 4 exploration panel:
1. c:\Users\andym\gschwelli-ai\.agents\teamwork\spec_miner_m4\handoff.md
2. c:\Users\andym\gschwelli-ai\.agents\teamwork\explorer_m4_1\handoff.md
3. c:\Users\andym\gschwelli-ai\.agents\teamwork\explorer_m4_2\handoff.md
And reference files:
- c:\Users\andym\gschwelli-ai\PROJECT.md (Features 25-39, Milestone 4)
- c:\Users\andym\gschwelli-ai\Inspirations\ui_reference_mockup.png

FILE OWNERSHIP:
You have exclusive write ownership of:
c:\Users\andym\gschwelli-ai\ui\dashboard\index.html
DO NOT modify server/api.py or existing test files.

TASK SCOPE: Implement Milestone 4 (Blackboard, PowerShell REPL, Approval Gate & Omnibox):
1. Right Sidebar (Features 25–30):
   - Blackboard Header with AGENT-01 badge.
   - Pipeline breadcrumb tracker: [Plan] -> [UIA Detect] -> [Verify] -> [Execute] with status-aware color tokens.
   - Blackboard Step Cards: 4 step cards with status badges (COMPLETE, BLOCKED, etc.), AGENT-01 assignment, step descriptions, details.
   - Shared State Inspector: table showing $target_dir, $exit_code, checkpoint #018.
   - PowerShell REPL Terminal: dark monospace console with EXIT 0 badge, timestamped log lines, 5-color syntax classifier (.log-cmd, .log-info, .log-success, .log-warn, .log-error), and interactive PS C:\Fabrication> command input with command history buffer (ArrowUp/ArrowDown), execution calling POST /api/repl with fallback for offline commands, and clear / cls handling.
   - REPL status footer: pulsing green dot, pwsh 7.4.2, and SANDBOX * I/O GUARDED.
   - Reactive renderer: renderBlackboard() driven by AppState.blackboard.

2. Bottom Docks (Features 31–39):
   - Approval Gate Banner: 44px amber safety dock with shield icon, 2-line title/detail group ("HUMAN-IN-THE-LOOP APPROVAL NEEDED", "Overwrite toolhead_mount.stl * backup saved * SEC-810"), and buttons:
     * #btn-approve ("✓ Approve (Space)")
     * #btn-edit ("✏ Edit") -> unlocks #export-path-input for editing, updates gate detail
     * #btn-abort ("Abort (Esc)") -> halts execution safely, marks ABORTED, updates $exit_code to 1
     * #btn-panic ("🚫 PANIC KILL & UNDO") -> emergency halt, calls /api/undo
   - Omnibox Command Bar: 48px dock with:
     * #btn-attach ("+") -> inserts context reference into prompt
     * #chip-slash ("/run...") -> toggles slash autocomplete menu
     * #command-input -> natural language / slash input
     * #slash-menu -> autocomplete popup with 7 commands (/run, /scan, /approve, /abort, /undo, /mode, /clear) with ArrowUp/ArrowDown navigation
     * #btn-voice-toggle -> VOICE pill, synchronized with sidebar wake-word button and /api/voice
     * #model-router-select -> dropdown (Auto-Route: Ollama/Gemini) updating active routing tier
     * #btn-submit-cmd -> circular cyan send button
   - Global Keyboard Shortcuts: Space for Approve, Esc for Abort when approval gate is active, with strict typing focus guard (must NOT trigger when user is typing in inputs or textareas, and Esc closes open menus/modals first).
   - Cross-Panel State Synchronization: Resolving safety gate updates Mission Header, Left Sidebar Tasks (Task 3 checked, counter 2/4 -> 3/4), Blackboard [Execute] card & breadcrumb, REPL logs, and backend endpoints (/api/confirm, /api/undo).

VERIFICATION REQUIREMENTS:
After implementing in ui/dashboard/index.html, you MUST run tests using run_command:
1. uv run --with pytest pytest tests/test_api.py -v
2. uv run --with pytest,playwright pytest tests/test_browser_dom.py -v
3. uv run --with pytest,playwright pytest tests/test_challenge_m3_1.py -v
4. uv run --with pytest,playwright pytest tests/test_challenge_m3_2.py -v
All tests must pass with 0 failures and 0 console errors.

Deliver your detailed report in:
c:\Users\andym\gschwelli-ai\.agents\teamwork\worker_m4\handoff.md
And notify parent orchestrator via send_message.
