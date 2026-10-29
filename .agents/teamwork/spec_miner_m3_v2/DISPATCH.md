## 2026-10-29T09:17:15Z
[Message] timestamp=2026-10-29T09:17:15Z sender=db3d98a0-f6a4-45e7-9dea-32dceda77cf0 priority=MESSAGE_PRIORITY_HIGH content=You are spec_miner_m3_v2, a teamwork_spec_miner subagent investigating Milestone 3: Polymorphic Stage (Viewports 3 & 4, Split-Screen Mode, Quick Telemetry Drawers, and Center Stage CAD Eradication).

MANDATORY REQUIREMENTS:
1. You MUST read the authoritative user request at:
   c:\Users\andym\gschwelli-ai\.agents\teamwork\ORIGINAL_REQUEST.md
   and the project specification at:
   c:\Users\andym\gschwelli-ai\PROJECT.md
2. You are a READ-ONLY specification mining and exploration agent. DO NOT write or edit source code files. You write ONLY to your designated working directory:
   c:\Users\andym\gschwelli-ai\.agents\teamwork\spec_miner_m3_v2\

YOUR MISSION:
Investigate and specify the technical blueprint for:
1. Feature #15 (Polymorphic 4-Viewport Container):
   - Switchable viewport system (Viewport 1: Vision Stream, Viewport 2: Document Studio, Viewport 3: Reasoning Graph, Viewport 4: Shell Sandbox).
   - Viewport selector tabs and keyboard hotkeys (Ctrl+1, Ctrl+2, Ctrl+3, Ctrl+4).
2. Feature #22 (Task & Reasoning Graph / Blackboard):
   - DAG visualizer showing node flow: Goal ➔ Sub-Tasks ➔ Gates ➔ Artifacts.
   - Status indicators on nodes (pending, in_progress, done, blocked).
3. Feature #23 (Live Variables & Memory State):
   - Inspector panel displaying agent context variables (e.g., $workspace, $exit_code, $current_task) and memory key-values fetched from /api/memory.
4. Feature #24 & #25 (Multi-Tab Shell Sandbox & REPL):
   - Monospace terminal with tab switching (PowerShell, Bash, Sandbox).
   - Interactive input calling /api/repl, showing command timestamps, exit codes, and colored stdout/stderr streams.
5. Feature #26 (Split-Screen Canvas Mode):
   - 50/50 side-by-side layout button/toggle enabling two viewports simultaneously (e.g., Vision Stream on left, Shell Sandbox or Studio on right).
6. Feature #27 (Quick Telemetry Drawers):
   - Slide-out quick panels for Tools (/api/tool), Memory (/api/memory), Cache (/api/cache), and Undo Stack (/api/undo).
7. Feature #28 (Center Stage CAD Eradication):
   - Identify every remaining trace of OpenSCAD, 3D mesh rendering, STL export docks, CSG snippets, and 3D printing widgets on the main stage and ensure 100% removal.

OUTPUT:
Write your detailed specification and architecture report to:
c:\Users\andym\gschwelli-ai\.agents\teamwork\spec_miner_m3_v2\analysis.md
and a structured handoff to:
c:\Users\andym\gschwelli-ai\.agents\teamwork\spec_miner_m3_v2\handoff.md
Send a completion message when done.
