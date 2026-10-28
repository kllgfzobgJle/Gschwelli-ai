## 2026-10-28T16:06:09Z
[Message] timestamp=2026-10-28T16:06:09Z sender=20ee9337-54d2-4ed7-a02f-42aad4232d45 priority=MESSAGE_PRIORITY_HIGH content=You are teamwork_preview_worker for Milestone 2 (Global Shell, Design System & Left Sidebar).
Your working directory is: c:\Users\andym\gschwelli-ai\.agents\teamwork\worker_m2
Your parent is the Project Orchestrator (conversation ID: 20ee9337-54d2-4ed7-a02f-42aad4232d45).

MANDATORY INPUTS (read these before starting work):
- c:\Users\andym\gschwelli-ai\.agents\teamwork\ORIGINAL_REQUEST.md
- c:\Users\andym\gschwelli-ai\PROJECT.md
- Visual Mockup: c:\Users\andym\gschwelli-ai\Inspirations\ui_reference_mockup.png
- Survey 1 Report: c:\Users\andym\gschwelli-ai\.agents\teamwork\spec_miner_survey_1\survey_report.md
- Survey 2 Report: c:\Users\andym\gschwelli-ai\.agents\teamwork\explorer_survey_2\survey_report.md

EXCLUSIVELY OWNED FILES:
- c:\Users\andym\gschwelli-ai\ui\dashboard\index.html

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

YOUR MISSION:
Overhaul ui/dashboard/index.html to implement Milestone 2 per PROJECT.md:
1. Design System & CSS Variables:
   - Deep slate/navy dark void palette (--bg-void: #060a10, --bg-panel: #0b121c, --bg-card: #101a28, --border-subtle: #1b2a3e, --cyan-accent: #00e5ff, --teal-accent: #14b8a6, --amber-warning: #f59e0b, --emerald-success: #10b981, --red-panic: #ef4444).
   - Typography font stacks (Inter / system sans-serif for UI, JetBrains Mono / Cascadia Code / monospace for code and telemetry).
   - Crisp cybernetic styling, subtle glow borders, clean scrollbars, and high-DPI scaling.
2. Layout Grid:
   - Top Navigation Bar (48px height)
   - Left Sidebar (270px width)
   - Center SOM Canvas container (flexible 1fr)
   - Right Sidebar container (360px width)
   - Bottom Human-in-the-Loop Approval Gate dock (44px)
   - Bottom Omnibox Command Bar dock (48px)
3. Top Navigation Bar:
   - Window controls dot cluster: 3 colored dots (Red #ff5f56, Yellow #ffbd2e, Green #27c93f).
   - Brand title: "gschwelli-ai" with pulsing live status dot (emerald green).
   - Centered 4-mode segmented pill switcher: "Mission Control", "Knowledge Studio", "Vision SOM", "Focus Chat".
   - Runtime telemetry badge: "Ollama 7B • 42 tok/s • 4.2GB VRAM".
   - Settings cog trigger button.
4. Left Sidebar:
   - Project / Local Workspace card: "PROJECT / LOCAL WORKSPACE", "Active: 3D Fabrication & Automation", git branch "main / 6 files indexed", and interactive switcher dropdown.
   - Tasks & To-Dos panel: Header with progress counter "TASKS & TO-DOS" | "2 / 4", 4 interactive tasks with checkboxes and agent status badges:
     * Task 1: [x] "Validate mount geometry" (Complete, emerald)
     * Task 2: [x] "Resolve export destination" (Complete, emerald)
     * Task 3: [ ] "Export toolhead mount" (Approval needed, amber)
     * Task 4: [ ] "Run fabrication pipeline" (Queued, muted)
     * "+ Add task" action button.
   - Knowledge Base file tree: Header "KNOWLEDGE BASE" with "+" button, collapsible "📁 fabrication/" folder with 6 files ("workflow.md", "agent_kinematics.py", "toolhead_mount.scad" highlighted, "mount_assembly.step", "pipeline_config.yaml", "safety_protocol.md"), and sync telemetry "Synced 12s ago • 48 chunks".
   - Audio / Wake-Word footer: Mic level indicator ("RØDE NT-USB Mini -42 dB" with animated level bars) and interactive toggle pill ("Listening for Wake-Word").
5. Reactive AppState & Connectivity:
   - Maintain a single reactive AppState store in JavaScript connecting to /ws and /api/state, with rich simulated default state for the 3D Fabrication & Automation scenario so the prototype works immediately without server errors.
   - Multi-tab view switching logic: Switching tabs toggles view containers for all 4 views cleanly.
   - Provide structured scaffolding in Center, Right, and Bottom areas so the entire page renders with zero console errors.
6. Verify your implementation by running:
   uv run --with pytest pytest tests/test_api.py -v
   uv run --with pytest,playwright pytest tests/test_browser_dom.py -v
7. Document changes and test results in handoff.md in your working directory and notify parent with send_message.
