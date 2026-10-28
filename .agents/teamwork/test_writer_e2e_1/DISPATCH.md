# Dispatch Assignment: E2E Test Writer
Working directory: c:\Users\andym\gschwelli-ai\.agents\teamwork\test_writer_e2e_1
Identity: teamwork_preview_test_writer
Parent: orchestrator_1 (20ee9337-54d2-4ed7-a02f-42aad4232d45)
Scope: Create TEST_INFRA.md, comprehensive tests in tests/ (test_api.py and test_browser_dom.py), and publish TEST_READY.md.
Exclusively owned files: TEST_INFRA.md, TEST_READY.md, tests/*

## 2026-10-28T15:44:36Z
Sender: 20ee9337-54d2-4ed7-a02f-42aad4232d45
Priority: MESSAGE_PRIORITY_HIGH
Content:
You are teamwork_preview_test_writer for the E2E Testing Track.
Your working directory is: c:\Users\andym\gschwelli-ai\.agents\teamwork\test_writer_e2e_1
Your parent is the Project Orchestrator (conversation ID: 20ee9337-54d2-4ed7-a02f-42aad4232d45).

MANDATORY INPUTS (read these before starting work):
- c:\Users\andym\gschwelli-ai\.agents\teamwork\ORIGINAL_REQUEST.md
- c:\Users\andym\gschwelli-ai\PROJECT.md
- Visual Mockup: c:\Users\andym\gschwelli-ai\Inspirations\ui_reference_mockup.png
- Survey 3 Report: c:\Users\andym\gschwelli-ai\.agents\teamwork\explorer_survey_3\survey_report.md

EXCLUSIVELY OWNED FILES:
- c:\Users\andym\gschwelli-ai\TEST_INFRA.md
- c:\Users\andym\gschwelli-ai\TEST_READY.md
- c:\Users\andym\gschwelli-ai\tests/*

YOUR MISSION:
Design and build the comprehensive, requirement-driven, opaque-box E2E test suite covering all features in PROJECT.md § Feature Inventory across Tiers 1-4.
1. Create c:\Users\andym\gschwelli-ai\TEST_INFRA.md following the orchestrator TEST_INFRA.md template:
   - Test philosophy, feature inventory with tier coverage, test architecture, and thresholds.
2. Implement tests/test_api.py using fastapi.testclient.TestClient covering all backend endpoints:
   - GET / (serves HTML, 200 OK)
   - GET /api/state (all 8 keys valid)
   - POST /api/route (instruction execution)
   - POST /api/confirm (approve=true and approve=false)
   - POST /api/undo (rollback)
   - POST /api/tool (tool execution)
   - POST & DELETE /api/memory (memory CRUD)
   - DELETE /api/cache (cache clear)
   - POST /api/voice (voice settings toggle)
   - WebSocket /ws (connection & broadcast)
   - POST /api/scenario/reset, POST /api/repl, GET /api/som
3. Implement tests/test_browser_dom.py using Playwright (playwright.sync_api or async_api) running against the FastAPI server:
   - Starts or connects to the FastAPI test server.
   - Launches headless Chromium (pre-installed at C:\Users\andym\AppData\Local\ms-playwright\chromium-1248).
   - Verifies zero console errors and zero uncaught exceptions.
   - Tests visual structure: Top Nav (brand, status dot, 4 mode pills, telemetry), Left Sidebar (project selector, tasks 2/4, knowledge base tree, mic meter), Center Canvas (SOM perception header, mission status M-024, OpenSCAD CAD viewport, SOM tags [01, 02, 04, 12], toolbar, fusion status), Right Sidebar (Blackboard cards, shared state, PowerShell REPL with prompt and exit 0), Bottom Approval Gate (amber banner, buttons Approve, Edit, Abort, PANIC KILL), Bottom Omnibox (/run chip, input, voice, router selector).
   - Tests interactive workflows: Tab switching (Mission Control, Knowledge Studio, Vision SOM, Focus Chat), clicking Approve (Space) and Abort (Esc), clicking SOM tags, submitting REPL commands, selecting Knowledge Base files, Omnibox input.
4. Verify by running:
   uv run --with pytest pytest tests/test_api.py -v
5. When complete, publish c:\Users\andym\gschwelli-ai\TEST_READY.md at project root per the template.
6. Write your handoff.md in your working directory and notify parent (20ee9337-54d2-4ed7-a02f-42aad4232d45) with send_message.
