# Test Infrastructure Specification: Universal Domain-Agnostic Agent Workstation E2E Suite

**Document Version**: 2.0.0  
**Target Project**: `gschwelli-ai` (Universal Domain-Agnostic Agent Workstation / Operating Canvas)  
**Author**: E2E Test Writer (`teamwork_test_writer_e2e_v2`)  
**Scope**: Full-stack opaque-box automated verification across Tiers 1–4  

---

## 1. Testing Philosophy & Guardrails

The `gschwelli-ai` test infrastructure adheres to five fundamental tenets:

1. **Opaque-Box Requirement Verification**:
   Tests interact strictly via public interfaces:
   - Backend: HTTP REST endpoints (`fastapi.testclient.TestClient`) and WebSocket streams.
   - Frontend: Headless browser automation (`playwright`) querying DOM nodes, styles, attributes, and user interaction events.
   No internal private variables or implementation shims are accessed.

2. **Authoritative Expected Output Derivation**:
   Every expected value is derived directly from:
   - `ORIGINAL_REQUEST.md` (Requirements R1–R5 and Acceptance Criteria).
   - `PROJECT.md` (Architecture, 40 Features, Interface Contracts, Design Tokens).
   - `DESIGN.md` (Color tokens `#0A0D12`, `#121824`, `#1E293B`, `#06B6D4`, `#F59E0B`, `#EF4444`).

3. **Zero-Facade Integrity Mandate**:
   Tests must never be written as facades or dummy passes:
   - API tests verify status codes, exact JSON schema keys, value types, and persistence/side-effects.
   - DOM tests assert that required elements are present, visible, contain exact reference text, respond to click/keyboard events, and trigger state transitions without browser console errors.

4. **Progressive Testability & Tiered Coverage**:
   - **Tier 1 (Feature Coverage & Sanity)**: Baseline server launch, HTML delivery (`200 OK`), zero CDN dependencies, Workspace CRUD modal, Reactive Tasks, Dynamic File Explorer, 4 Polymorphic Viewports, Split-Screen mode, Quick Drawers, Safety Interceptor, Universal Omnibar.
   - **Tier 2 (Boundary & Corner Cases)**: Keyboard scope guards (`Space` and `Esc` isolated from inputs), empty task title rejection, rapid status badge cycling, XSS injection prevention, empty undo stack panic kill handling.
   - **Tier 3 (Cross-Feature Combinations)**: Workspace switch -> task list changes -> file preview in Viewport 2; task creation -> delegation toggle -> progress counter/bar update; Omnibar slash command execution -> stage transitions.
   - **Tier 4 (Real-World Application Scenarios & Responsiveness)**: Complete multi-step agent workflow; multi-resolution layout checks (`1024x768`, `1440x900`, `1920x1080`) with zero console errors and 0.0 px² pointer occlusion.

5. **Deterministic & Isolated Execution**:
   Each test establishes its own prerequisites. Conftest-level Playwright proxying allows clean, re-entrant browser execution across session, module, and function-scoped test files without asyncio event loop collisions.

---

## 2. Feature Inventory Tier Coverage Matrix

| # | Feature Name | Milestone | Test File & Function | Tier | Verifiable Assertion |
|---|--------------|-----------|----------------------|------|----------------------|
| 1 | Backend Domain-Agnostic Endpoints | M1 | `tests/test_api.py::test_som_endpoint_catalogue`, `test_scenario_reset_endpoint` | Tier 1, 2 | 12 SOM targets mapped, tags `[01, 02, 04, 12]`, generic reset response |
| 2 | Backend Workspace & Task REST | M1 | `tests/test_api.py::test_workspaces_crud_endpoints`, `test_tasks_crud_lifecycle_and_statuses`, `test_workspace_files_listing_and_categories` | Tier 2, 3 | Full CRUD operations for workspaces and tasks with 5 statuses and categorized file listing |
| 3 | Workspace Creation Modal | M2 | `tests/test_browser_dom.py::test_workspace_modal_crud_and_switching` | Tier 1 | Modal triggers, accepts name/prompt/dir, adds workspace |
| 4 | Workspace Hot-Switcher | M2 | `tests/test_browser_dom.py::test_workspace_modal_crud_and_switching` | Tier 1, 3 | Switches workspace without full page reload |
| 5 | Workspace State Persistence | M2 | `tests/test_browser_dom.py::test_workspace_and_task_persistence_across_reload` | Tier 1 | Workspaces and tasks survive browser reload (`page.reload()`) |
| 6 | Universal Task Object Model | M2 | `tests/test_api.py::test_tasks_crud_lifecycle_and_statuses` | Tier 2 | Task conforms to `{id, title, status, priority, delegated, meta}` |
| 7 | Fast Inline Task Creation | M2 | `tests/test_browser_dom.py::test_reactive_tasks_inline_creation_and_status_cycles` | Tier 1 | Typing in input and pressing `Enter` creates task immediately |
| 8 | Task Status Lifecycle | M2 | `tests/test_browser_dom.py::test_reactive_tasks_inline_creation_and_status_cycles` | Tier 1, 2 | Cycles across `backlog`, `in_progress`, `agent_delegated`, `blocked`, `done` |
| 9 | Agent Delegation Toggle | M2 | `tests/test_browser_dom.py::test_task_delegation_toggle_and_progress_metrics` | Tier 1 | Quick toggle button (⚡ / 🤖) updates delegated state |
| 10 | Reactive Progress Metrics | M2 | `tests/test_browser_dom.py::test_task_delegation_toggle_and_progress_metrics` | Tier 1, 3 | Dynamic counter (`X/Y erledigt`) and visual progress bar update |
| 11 | Dynamic Workspace File Tree | M2 | `tests/test_browser_dom.py::test_dynamic_file_explorer_tree_and_category_filtering` | Tier 1 | Displays active workspace files in dynamic tree |
| 12 | File Type Filtering | M2 | `tests/test_browser_dom.py::test_dynamic_file_explorer_tree_and_category_filtering` | Tier 1 | Filters tree by categories (`All`, `Code`, `Docs`, `Tables`, `Media`, `Configs`) |
| 13 | File Quick Preview | M2 | `tests/test_browser_dom.py::test_dynamic_file_explorer_tree_and_category_filtering` | Tier 1, 3 | Clicking tree item loads preview in central Viewport 2 |
| 14 | Left Sidebar CAD Eradication | M2 | `tests/test_browser_dom.py::test_left_sidebar_structure` | Tier 2 | Zero CAD references in left sidebar |
| 15 | Polymorphic 4-Viewport Container | M3 | `tests/test_browser_dom.py::test_four_polymorphic_viewports_switching` | Tier 1 | Clean switching across all 4 viewports |
| 16 | Screen & Vision Stream (SOM) | M3 | `tests/test_browser_dom.py::test_viewport_1_som_perception_canvas_and_toolbar` | Tier 1 | Perception viewer with tags `[01]`-`[12]` |
| 17 | SOM Non-Occluding Pointer Events | M3 | `tests/test_browser_dom.py::test_multi_resolution_layout_and_som_occlusion_audit` | Tier 2, 4 | Pointer-events pass-through (0.0 px² pointer occlusion) |
| 18 | Perception Toolbar Controls | M3 | `tests/test_browser_dom.py::test_viewport_1_som_perception_canvas_and_toolbar` | Tier 1 | Zoom In/Out, Pan, and Reset actions |
| 19 | Markdown 2-Column Split Studio | M3 | `tests/test_browser_dom.py::test_viewport_2_artifact_document_studio_views` | Tier 1 | 2-column split (raw editor + live preview) |
| 20 | Code Monospace Studio | M3 | `tests/test_browser_dom.py::test_viewport_2_artifact_document_studio_views` | Tier 1 | Monospace code viewer with syntax highlighting |
| 21 | Tabular / CSV Data-Grid | M3 | `tests/test_browser_dom.py::test_viewport_2_artifact_document_studio_views` | Tier 1 | Spreadsheet-style grid view for tabular data |
| 22 | Task & Reasoning Graph (Blackboard)| M3 | `tests/test_browser_dom.py::test_viewport_3_task_reasoning_graph_and_live_variables` | Tier 1 | Visual execution path DAG (Goal → Subtasks → Gates → Artifacts) |
| 23 | Live Variables & Memory State | M3 | `tests/test_browser_dom.py::test_viewport_3_task_reasoning_graph_and_live_variables` | Tier 1 | Variables table and memory facts inspector |
| 24 | Multi-Tab Shell Sandbox | M3 | `tests/test_browser_dom.py::test_viewport_4_shell_sandbox_multitab_terminal` | Tier 1 | Monospace terminal with tab switching |
| 25 | REPL Execution & Log Styling | M3 | `tests/test_browser_dom.py::test_viewport_4_shell_sandbox_multitab_terminal`, `tests/test_api.py::test_repl_endpoint_execution` | Tier 1, 2 | Executes commands with timestamps and exit code badges |
| 26 | Split-Screen Canvas Mode | M3 | `tests/test_browser_dom.py::test_split_screen_dual_viewport_layout` | Tier 1 | Parallel side-by-side dual viewport display |
| 27 | Quick Telemetry Drawers | M3 | `tests/test_browser_dom.py::test_quick_drawers_telemetry_inspection` | Tier 1 | Drawers for Tools, Memory facts, Cache, Undo stack |
| 28 | Center Stage CAD Eradication | M3 | `tests/test_browser_dom.py::test_center_canvas_structure` | Tier 2 | Zero CAD-specific blockers in main stage |
| 29 | Safety Interceptor Banner & Badges| M4 | `tests/test_browser_dom.py::test_bottom_approval_gate_structure` | Tier 1 | Risk badge display (`Info`, `Moderate`, `Critical`) |
| 30 | Safety Action Buttons | M4 | `tests/test_browser_dom.py::test_bottom_approval_gate_structure` | Tier 1 | `Approve (Space)`, `Edit`, `Abort (Esc)` buttons |
| 31 | PANIC KILL & Emergency Rollback | M4 | `tests/test_browser_dom.py::test_panic_kill_and_emergency_undo`, `tests/test_api.py::test_post_undo_and_empty_history` | Tier 1, 2 | Emergency stop halts agent and triggers `/api/undo` |
| 32 | Keyboard Scope Guard | M4 | `tests/test_browser_dom.py::test_keyboard_scope_guard_space_and_esc` | Tier 2 | `Space` and `Esc` isolated when typing in inputs/textareas |
| 33 | Universal Input Omnibar | M4 | `tests/test_browser_dom.py::test_bottom_omnibox_structure` | Tier 1 | Natural language prompt submission on `Enter` |
| 34 | Slash Commands Autocomplete | M4 | `tests/test_browser_dom.py::test_omnibar_slash_autocomplete_and_audio_pill` | Tier 1 | Popup menu for `/workspace`, `/task`, `/run`, `/inspect`, `/undo`, `/clear` |
| 35 | Audio-Viseme Pill | M4 | `tests/test_browser_dom.py::test_omnibar_slash_autocomplete_and_audio_pill` | Tier 1 | Pill toggling listening mode vs muted |
| 36 | XSS Input Sanitization | M4 | `tests/test_browser_dom.py::test_xss_sanitization_across_inputs`, `tests/test_api.py::test_post_route_xss_and_special_characters` | Tier 2 | Sanitizes script tags and onerror vectors |
| 37 | Zero-Dependency Offline SPA | M4 | `tests/test_browser_dom.py::test_offline_zero_external_network_requests` | Tier 1 | Zero external network calls (no CDNs, remote fonts, scripts) |
| 38 | DESIGN Tokens & Responsiveness | M4 | `tests/test_browser_dom.py::test_multi_resolution_layout_and_som_occlusion_audit` | Tier 4 | Stability across `1024x768`, `1440x900`, `1920x1080` |
| 39 | Automated E2E Test Suite | E2E | `tests/test_api.py`, `tests/test_browser_dom.py` | Tier 1–4 | 52 automated tests executed via `uv run` |
| 40 | 100% E2E Pass & Hardening | M5 | Full suite execution | Tier 1–4 | 100% test pass on core test harness |

---

## 3. Test Execution Instructions

### 3.1 Backend API Suite
```powershell
uv run --with pytest pytest tests/test_api.py -v
```

### 3.2 Browser DOM E2E Suite
```powershell
uv run --with pytest,playwright pytest tests/test_browser_dom.py -v
```

### 3.3 Core E2E Verification Harness (Combined)
```powershell
uv run --with pytest,playwright pytest tests/test_api.py tests/test_browser_dom.py -v
```

### 3.4 Full Project Test Suite
```powershell
uv run --with pytest,playwright pytest tests/ -v
```

---

## 4. Quality Thresholds & Escalation

1. **Pass Rate Threshold**: 100% of applicable tests must pass without failures or errors.
2. **Console Error Threshold**: Exactly 0 `console.error` and 0 unhandled exceptions across all test runs.
3. **Escalation Protocol**: If an implementation defect in `server/api.py` or `ui/dashboard/index.html` causes a failure, it is documented with exact reproduction command, file location, and line numbers, and escalated to the responsible worker agent.
