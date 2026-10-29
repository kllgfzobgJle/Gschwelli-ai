# Milestone 2 Adversarial Stress Testing Handoff Report

## 1. Observation

### Mandated Test Command
```powershell
uv run --with pytest,playwright pytest tests/test_adversarial_m2.py tests/test_browser_dom.py -v
```

### Verbatim Test Execution Output
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\andym\gschwelli-ai
plugins: anyio-4.15.1
collected 44 items

tests/test_adversarial_m2.py::test_zero_console_warnings_and_errors PASSED [  2%]
tests/test_adversarial_m2.py::test_stress_task_checkbox_rapid_toggling PASSED [  4%]
tests/test_adversarial_m2.py::test_add_task_edge_cases PASSED            [  6%]
tests/test_adversarial_m2.py::test_stress_mic_mute_toggling PASSED       [  9%]
tests/test_adversarial_m2.py::test_stress_project_dropdown_workflow PASSED [ 11%]
tests/test_adversarial_m2.py::test_stress_4_tab_switching_rapid PASSED   [ 13%]
tests/test_adversarial_m2.py::test_tab_visibility_and_css_display_leak PASSED [ 15%]
tests/test_adversarial_m2.py::test_tab_switching_shared_state_persistence PASSED [ 18%]
tests/test_adversarial_m2.py::test_dom_node_count_leak_during_tab_switching PASSED [ 20%]
tests/test_adversarial_m2.py::test_modal_stress_rapid_open_and_close_mechanisms FAILED [ 22%]
tests/test_adversarial_m2.py::test_modal_form_validation_empty_and_whitespace FAILED [ 25%]
tests/test_adversarial_m2.py::test_modal_stress_5000_char_string PASSED  [ 27%]
tests/test_adversarial_m2.py::test_multiple_workspace_creation_and_rapid_hot_switching PASSED [ 29%]
tests/test_adversarial_m2.py::test_workspace_localstorage_persistence_across_browser_reload FAILED [ 31%]
tests/test_browser_dom.py::test_zero_console_errors_on_load PASSED       [ 34%]
tests/test_browser_dom.py::test_offline_zero_external_network_requests PASSED [ 36%]
tests/test_browser_dom.py::test_top_nav_visual_structure PASSED          [ 38%]
tests/test_browser_dom.py::test_left_sidebar_structure PASSED            [ 40%]
tests/test_browser_dom.py::test_center_canvas_structure PASSED           [ 43%]
tests/test_browser_dom.py::test_right_sidebar_structure PASSED           [ 45%]
tests/test_browser_dom.py::test_bottom_approval_gate_structure PASSED    [ 47%]
tests/test_browser_dom.py::test_bottom_omnibox_structure PASSED          [ 50%]
tests/test_browser_dom.py::test_workspace_modal_crud_and_switching PASSED [ 52%]
tests/test_browser_dom.py::test_workspace_and_task_persistence_across_reload PASSED [ 54%]
tests/test_browser_dom.py::test_reactive_tasks_inline_creation_and_status_cycles PASSED [ 56%]
tests/test_browser_dom.py::test_task_delegation_toggle_and_progress_metrics PASSED [ 59%]
tests/test_browser_dom.py::test_dynamic_file_explorer_tree_and_category_filtering PASSED [ 61%]
tests/test_browser_dom.py::test_four_polymorphic_viewports_switching PASSED [ 63%]
tests/test_browser_dom.py::test_viewport_1_som_perception_canvas_and_toolbar PASSED [ 65%]
tests/test_browser_dom.py::test_viewport_2_artifact_document_studio_views PASSED [ 68%]
tests/test_browser_dom.py::test_viewport_3_task_reasoning_graph_and_live_variables PASSED [ 70%]
tests/test_browser_dom.py::test_viewport_4_shell_sandbox_multitab_terminal PASSED [ 72%]
tests/test_browser_dom.py::test_split_screen_dual_viewport_layout PASSED [ 75%]
tests/test_browser_dom.py::test_quick_drawers_telemetry_inspection PASSED [ 77%]
tests/test_browser_dom.py::test_keyboard_scope_guard_space_and_esc PASSED [ 79%]
tests/test_browser_dom.py::test_empty_task_title_rejection PASSED        [ 81%]
tests/test_browser_dom.py::test_rapid_status_badge_cycling_stress PASSED [ 84%]
tests/test_browser_dom.py::test_xss_sanitization_across_inputs PASSED    [ 86%]
tests/test_browser_dom.py::test_panic_kill_and_emergency_undo PASSED     [ 88%]
tests/test_browser_dom.py::test_omnibar_slash_autocomplete_and_audio_pill PASSED [ 90%]
tests/test_browser_dom.py::test_multi_resolution_layout_and_som_occlusion_audit[1024-768-Compact / XGA (1024x768)] PASSED [ 93%]
tests/test_browser_dom.py::test_multi_resolution_layout_and_som_occlusion_audit[1440-900-Standard Baseline (1440x900)] PASSED [ 95%]
tests/test_browser_dom.py::test_multi_resolution_layout_and_som_occlusion_audit[1920-1080-Full HD (1920x1080)] PASSED [ 97%]
tests/test_browser_dom.py::test_complete_end_to_end_agent_workflow PASSED [100%]

================================== FAILURES ===================================
______________ test_modal_stress_rapid_open_and_close_mechanisms ______________
    # 1b. Open via #btn-new-workspace, blur focus, close via Escape key
    btn_new_ws.click()
    page.wait_for_timeout(50)
    assert modal_backdrop.evaluate("el => window.getComputedStyle(el).display") != "none"
    page.evaluate("document.activeElement.blur()")
    page.keyboard.press("Escape")
    page.wait_for_timeout(50)
>   assert modal_backdrop.evaluate("el => window.getComputedStyle(el).display") == "none", (
        "Modal failed to close on Escape key when focus was blurred/not inside input! "
        "Global keydown listener omitted #workspace-modal-backdrop."
    )
E   AssertionError: Modal failed to close on Escape key when focus was blurred/not inside input! Global keydown listener omitted #workspace-modal-backdrop.
E   assert 'flex' == 'none'

tests\test_adversarial_m2.py:441: AssertionError

_______________ test_modal_form_validation_empty_and_whitespace _______________
    # 1. Empty form submission
    btn_new_ws.click()
    name_input.fill("")
    submit_btn.click()
    page.wait_for_timeout(100)

    # Modal must remain open, error must be visible in UI
    assert modal_backdrop.evaluate("el => window.getComputedStyle(el).display") != "none", "Modal closed on empty submission"
>   assert error_el.evaluate("el => window.getComputedStyle(el).display") != "none", (
        "Error message container #ws-modal-error not displayed on empty submission! "
        "HTML5 required attribute blocked submit event before custom error handler executed."
    )
E   AssertionError: Error message container #ws-modal-error not displayed on empty submission! HTML5 required attribute blocked submit event before custom error handler executed.
E   assert 'none' != 'none'

tests\test_adversarial_m2.py:503: AssertionError

________ test_workspace_localstorage_persistence_across_browser_reload ________
    # 4. Trigger browser reload (F5)
    page.reload(wait_until="networkidle")

    # 5. Verify restored state after reload
    title_after = page.locator("#active-project-title").inner_text()
>   assert ws_name in title_after, (
        f"Active project title was not restored after reload! Got: '{title_after}'. "
        f"Backend synchronization clobbered newly created workspace on page reload."
    )
E   AssertionError: Active project title was not restored after reload! Got: 'Active: WS_Epsilon_Blackboard'. Backend synchronization clobbered newly created workspace on page reload.
E   assert 'Persistent_Challenger_Lab' in 'Active: WS_Epsilon_Blackboard'

tests\test_adversarial_m2.py:704: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_adversarial_m2.py::test_modal_stress_rapid_open_and_close_mechanisms
FAILED tests/test_adversarial_m2.py::test_modal_form_validation_empty_and_whitespace
FAILED tests/test_adversarial_m2.py::test_workspace_localstorage_persistence_across_browser_reload
=================== 3 failed, 41 passed in 62.09s (0:01:02) ===================
```

### Exact File Paths & Lines of Defective Implementations
1. **State Persistence & Reversion on Reload**:
   - `ui/dashboard/index.html` lines 3907-3929 (`AppState.createWorkspace` does not invoke backend activation for the backend-generated workspace ID).
   - `ui/dashboard/index.html` lines 4010-4028 (`AppState.loadWorkspaces` clobbers `this.activeWorkspaceId` and `localStorage.gschwelli_active_workspace` with the backend's stale active workspace ID returned from `GET /api/workspaces`).
2. **Form Validation Empty Suppression**:
   - `ui/dashboard/index.html` line 3704 (`<form id="form-new-workspace" class="workspace-modal-form" onsubmit="return false;">` lacks `novalidate`).
   - `ui/dashboard/index.html` line 3716 (`<input id="ws-name-input" ... required ... />` triggers native HTML5 constraint validation, suppressing the JavaScript submit listener at lines 4175-4190).
3. **Escape Key Trapping & Approval Gate Abortion Leak**:
   - `ui/dashboard/index.html` lines 4208-4218 (Escape listener attached solely to `div#workspace-modal` which lacks `tabindex` and cannot receive keydown events when focus is blurred).
   - `ui/dashboard/index.html` lines 5920-5932 (`window.addEventListener('keydown', ...)` checks `settingsModal` and `slashMenu`, but omits `workspace-modal-backdrop`).
   - `ui/dashboard/index.html` lines 5934-5944 (When Escape is pressed with blurred focus while the modal is open and the Approval Gate is in `PAUSED • APPROVAL`, it triggers `handleAbort()` in the background).

---

## 2. Logic Chain

### Defect 1: Active Workspace State Reversion on Browser Reload (Requirement R1, Acceptance Criteria)
1. **Observation**: A new workspace (`Persistent_Challenger_Lab`) is created via modal and set as active in `AppState`. In `localStorage`, `gschwelli_workspaces` and `gschwelli_active_workspace` are populated. Upon browser reload (`page.reload()`), `#active-project-title` renders `Active: WS_Epsilon_Blackboard` instead of `Persistent_Challenger_Lab`.
2. **Step 1**: In `AppState.createWorkspace` (`ui/dashboard/index.html`:3888), a temporary client ID `wsId = 'ws-' + ...` is created. `this.switchWorkspace(wsId)` is called, which dispatches `POST /api/workspaces/activate` with `{ id: wsId }`. Because `wsId` does not yet exist on the backend, the backend returns 404, leaving backend `_active_workspace_id` unchanged.
3. **Step 2**: The asynchronous `fetch('/api/workspaces', { method: 'POST', ... })` call resolves, receiving `{ workspace: { id: "ws-xxxx" } }`. The client updates `newWs.id = data.workspace.id` and `this.activeWorkspaceId = data.workspace.id`, but NEVER dispatches `POST /api/workspaces/activate` with the new backend ID. Thus, the backend persistently stores the previous workspace as active.
4. **Step 3**: On page reload, `AppState.loadWorkspaces()` (`ui/dashboard/index.html`:3985) correctly reads `Persistent_Challenger_Lab` from `localStorage`. However, line 4008 executes `await fetch('/api/workspaces')`. The backend responds with `data.active_workspace_id` pointing to the old workspace (`WS_Epsilon_Blackboard`).
5. **Step 4**: Line 4024 executes:
   ```javascript
   if (data.active_workspace_id) {
     this.activeWorkspaceId = data.active_workspace_id;
   }
   this.saveWorkspaces();
   renderWorkspaces();
   ```
   This unconditionally clobbers the active workspace and overwrites `localStorage.gschwelli_active_workspace` with the stale backend ID.
6. **Conclusion**: Newly created workspaces lose their active state immediately upon browser reload. This violates the core acceptance criterion: *"Workspaces und Aufgaben werden nach Browser-Neuladen persistent wiederhergestellt."*

### Defect 2: Modal Form Empty Validation Bypasses Custom Error UI
1. **Observation**: In `test_modal_form_validation_empty_and_whitespace`, clicking `#btn-create-ws` with an empty `#ws-name-input` results in `#ws-modal-error` remaining `display: none`.
2. **Step 1**: Line 3716 defines `<input type="text" id="ws-name-input" name="name" class="ws-form-input" placeholder="..." required autocomplete="off" />` inside `<form id="form-new-workspace">` without a `novalidate` attribute.
3. **Step 2**: When `#btn-create-ws` (`type="submit"`) is clicked, browser HTML5 constraint validation halts the form submission before the DOM `'submit'` event is dispatched.
4. **Step 3**: The JavaScript handler on line 4175 (`form.addEventListener('submit', ...)`) which sets `errEl.style.display = 'block'` is never invoked.
5. **Step 4**: In contrast, when whitespace (e.g., `"   "`) is entered, native validation passes because `value.length > 0`, allowing the JS submit handler to run, trim the input, and display `#ws-modal-error`.
6. **Conclusion**: Form validation is inconsistent and broken. Submitting an empty name fails silently with native tooltip suppression, while whitespace shows the custom styled UI container.

### Defect 3: Escape Key Trapping Failure & Approval Gate Abortion Leak
1. **Observation**: When the modal is open and focus is blurred or on any non-form element (e.g. clicking the modal backdrop or modal header), pressing `Escape` fails to close `#workspace-modal-backdrop`.
2. **Step 1**: The modal Escape listener is registered solely on `div#workspace-modal` (line 4210). Because `div` is not focusable without `tabindex`, it only catches bubbled events from focused children.
3. **Step 2**: When focus is blurred, the `Escape` key event bubbles to `window`.
4. **Step 3**: In the global window keydown listener (line 5920), checks exist for `settingsModal` and `slashMenu`, but `#workspace-modal-backdrop` is missing:
   ```javascript
   if (e.code === 'Escape') {
     const settingsModal = document.getElementById('settings-modal');
     if (settingsModal && settingsModal.style.display !== 'none') { ... }
     if (slashMenu && slashMenu.classList.contains('open')) { ... }
   }
   ```
5. **Step 4**: The event continues to line 5941:
   ```javascript
   if (e.code === 'Escape') {
     e.preventDefault();
     handleAbort();
   }
   ```
6. **Conclusion**: Pressing Escape while viewing the modal with blurred focus leaves the modal open and triggers an unintended background abort of the agent's approval gate.

---

## 3. Caveats

- **Structural DOM Leak vs Terminal Logging**: In `test_multiple_workspace_creation_and_rapid_hot_switching`, structural workspace DOM elements (`*:not(#repl-logs *)`) are 100% invariant (0 diff). The observed growth of 90 nodes across 30 switches is entirely contained within `#repl-logs` via `appendReplLog()`. While `#repl-logs` is bounded by a 500-line ring buffer, callers should be aware that hot-switching generates terminal log records.
- **5,000-Character String Stress**: Verified robust. When submitted with a 5,000-character name and prompt, `#left-sidebar` does not expand horizontally (`width <= 275px`), `#active-project-title` properly truncates with CSS `text-overflow: ellipsis`, and zero horizontal scrollbars are introduced.

---

## 4. Conclusion

### Explicit Verdict: **REQUEST_CHANGES**

The Milestone 2 implementation in `ui/dashboard/index.html` fails 3 critical adversarial stress criteria:
1. **CRITICAL**: Active workspace state loss on browser reload due to asynchronous backend hydration overwriting `localStorage`.
2. **HIGH**: Modal form empty validation fails to display the custom `#ws-modal-error` UI due to HTML5 `required` constraint validation without `novalidate` on `<form id="form-new-workspace">`.
3. **HIGH**: Modal Escape key is not trapped when focus is blurred/on backdrop, failing to close the modal and leaking to the Approval Gate abort handler.

### Recommended Worker Fixes
1. **In `AppState.createWorkspace` (`ui/dashboard/index.html`)**:
   In the `fetch('/api/workspaces')` `.then(data => ...)` handler, after setting `newWs.id = data.workspace.id`, invoke backend activation:
   ```javascript
   fetch('/api/workspaces/activate', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ id: data.workspace.id })
   }).catch(() => {});
   ```
   Additionally, in `AppState.loadWorkspaces()`, if `cached` has a valid active workspace and backend `active_workspace_id` does not match, prefer the client's explicit selection or ensure backend sync has completed before overriding.
2. **In `<form id="form-new-workspace">` (`ui/dashboard/index.html`:3704)**:
   Add `novalidate` to `<form id="form-new-workspace" class="workspace-modal-form" novalidate onsubmit="return false;">` so that the JavaScript submit listener always executes and reliably renders `#ws-modal-error`.
3. **In `window.addEventListener('keydown', ...)` (`ui/dashboard/index.html`:5920)**:
   Include `#workspace-modal-backdrop` in the Escape handler:
   ```javascript
   const wsBackdrop = document.getElementById('workspace-modal-backdrop');
   if (wsBackdrop && wsBackdrop.style.display !== 'none') {
     e.preventDefault();
     closeWorkspaceModal();
     return;
   }
   ```

---

## 5. Verification Method

To independently reproduce all findings and verify fixes:

```powershell
uv run --with pytest,playwright pytest tests/test_adversarial_m2.py tests/test_browser_dom.py -v
```

- **Target Files**:
  * Test Suite: `tests/test_adversarial_m2.py`
  * Implementation: `ui/dashboard/index.html`
- **Pass Criteria for Re-Review**:
  * `test_modal_stress_rapid_open_and_close_mechanisms`: PASSED (closes via Escape even when blurred)
  * `test_modal_form_validation_empty_and_whitespace`: PASSED (`#ws-modal-error` displayed on empty submission)
  * `test_workspace_localstorage_persistence_across_browser_reload`: PASSED (active workspace retained across F5 reload)
  * All 44 tests across `test_adversarial_m2.py` and `test_browser_dom.py` pass cleanly.
