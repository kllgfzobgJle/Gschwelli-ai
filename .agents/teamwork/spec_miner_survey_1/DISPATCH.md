## 2026-10-28T15:30:15Z
You are teamwork_preview_spec_miner for Survey 1.
Your working directory is: c:\Users\andym\gschwelli-ai\.agents\teamwork\spec_miner_survey_1
Your parent is the Project Orchestrator (conversation ID: 20ee9337-54d2-4ed7-a02f-42aad4232d45).

MANDATORY INPUT:
Read the authoritative user request at:
c:\Users\andym\gschwelli-ai\.agents\teamwork\ORIGINAL_REQUEST.md

Also inspect the Visual Reference Mockup at:
c:\Users\andym\gschwelli-ai\Inspirations\ui_reference_mockup.png
(Note: You can use view_file to view the image file or inspect any accompanying materials).

YOUR MISSION:
Mine and document the exhaustive functional and visual specifications for the gschwelli-ai UI prototype.
Specifically investigate and detail:
1. Exact visual tokens: Palette (backgrounds, cyan/teal accents, amber warning/approval, emerald status), typography, layout dimensions, header, sidebars, dock.
2. Complete inventory of elements across the 4 views:
   - Mission Control: Top Nav bar (dot cluster, brand, status, 4 mode buttons, telemetry badge, settings trigger), Left Sidebar (Project selector, Tasks & To-Dos 2/4 with checkboxes and badges, Knowledge Base tree with sync telemetry, Audio/Wake-word mic footer), Center SOM Canvas (LIVE badge, display/resolution, active mission status M-024, OpenSCAD CAD viewport, CSG snippet, axis gizmo, camera controls, SOM cyan tags [01, 02, 04, 12], export path bar, safety banner, action toolbar, fusion status bar), Right Sidebar (Blackboard AGENT-01 with breadcrumbs [Plan]->[UIA Detect]->[Verify]->[Execute], step status cards, shared state inspector, PowerShell REPL with logs and PS C:\Fabrication> input), Bottom Approval Gate (amber banner, buttons Approve, Edit, Abort, PANIC KILL & UNDO), Bottom Omnibox Command Bar (+ button, /run... prefix chip, input, autocomplete, voice toggle, model router selector, submit button).
   - Knowledge Studio view: File inspector, chunk embeddings/metadata, file content viewer/editor, re-indexing action.
   - Vision SOM view: Expanded SOM & UIA tree inspector, target filtering [01]-[12], element attributes/coords/confidence, simulated highlight/click.
   - Focus Chat view: Conversational agent timeline, step reasoning/Blackboard trace cards, inline approval gates, tool/memory/cache quick inspectors.
3. Interactive state machine and workflows:
   - Approval gate state changes (PAUSED -> APPROVED / ABORTED / KILLED), effects on Blackboard, Tasks, REPL, backend calls.
   - SOM tag clicks and actions (Re-scan, Inspect, Capture).
   - Omnibox commands and slash menu.
   - Hotkeys (Space for Approve, Esc for Abort).

OUTPUT:
Write your complete structured report to:
c:\Users\andym\gschwelli-ai\.agents\teamwork\spec_miner_survey_1\survey_report.md
Also write a self-contained handoff.md in your working directory.
When finished, send a message back to parent (20ee9337-54d2-4ed7-a02f-42aad4232d45) with a summary and link to your report.
