## 2026-10-28T15:44:37Z
You are teamwork_preview_worker for Milestone 1 (Backend Endpoints & Workspace Fixtures).
Your working directory is: c:\Users\andym\gschwelli-ai\.agents\teamwork\worker_m1
Your parent is the Project Orchestrator (conversation ID: 20ee9337-54d2-4ed7-a02f-42aad4232d45).

MANDATORY INPUTS (read these before starting work):
- c:\Users\andym\gschwelli-ai\.agents\teamwork\ORIGINAL_REQUEST.md
- c:\Users\andym\gschwelli-ai\PROJECT.md
- Survey 3 Report: c:\Users\andym\gschwelli-ai\.agents\teamwork\explorer_survey_3\survey_report.md

EXCLUSIVELY OWNED FILES:
- c:\Users\andym\gschwelli-ai\server\api.py
- c:\Users\andym\gschwelli-ai\workspace\fabrication/*

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

YOUR MISSION:
Implement Milestone 1 per PROJECT.md:
1. In c:\Users\andym\gschwelli-ai\server\api.py:
   - Add POST /api/scenario/reset: resets and seeds the 3D Fabrication & Automation scenario, invoking core.confirm.request_confirmation with key "overwrite_stl", title "Overwrite toolhead_mount.stl", detail "backup saved • SEC-810".
   - Add POST /api/repl: accepts {"command": str}, executes through executors.ps_repl.ps_repl.run (via asyncio.to_thread), returns {"command": str, "output": str, "exit_code": int}.
   - Add GET /api/som: returns the 12 mapped targets metadata dictionary (resolution, fusion_confidence, marks list with [01], [02], [04], [12], etc.).
   - Ensure all existing endpoints and server entrypoints (create_app, start_background_server) remain fully functional and backward-compatible.
2. Create workspace/fabrication/ directory with genuine realistic content:
   - workspace/fabrication/workflow.md
   - workspace/fabrication/agent_kinematics.py
   - workspace/fabrication/toolhead_mount.scad
   - workspace/fabrication/mount_assembly.step
   - workspace/fabrication/pipeline_config.yaml
   - workspace/fabrication/safety_protocol.md
3. Run verification to confirm server creates cleanly and endpoints return 200 OK.
4. Write your changes and test results into handoff.md in your working directory.
5. Notify parent (20ee9337-54d2-4ed7-a02f-42aad4232d45) with send_message.
