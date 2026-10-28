# Empirical Adversarial Challenge Report — Milestone 2 Frontend DOM

## 1. Observation

### Verification Suite Executed
- Test Suite: `tests/test_adversarial_m2.py`
- Execution Command: `uv run --with pytest,playwright pytest tests/test_adversarial_m2.py -v`
- Execution Summary: **7 passed, 2 failed, 2 warnings in 19.52s**

### Verbatim Test Execution Logs
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\andym\gschwelli-ai
plugins: anyio-4.15.1
collected 9 items

tests/test_adversarial_m2.py::test_zero_console_warnings_and_errors PASSED [ 11%]
tests/test_adversarial_m2.py::test_stress_task_checkbox_rapid_toggling PASSED [ 22%]
tests/test_adversarial_m2.py::test_add_task_edge_cases FAILED            [ 33%]
tests/test_adversarial_m2.py::test_stress_mic_mute_toggling PASSED       [ 44%]
tests/test_adversarial_m2.py::test_stress_project_dropdown_workflow PASSED [ 55%]
tests/test_adversarial_m2.py::test_stress_4_tab_switching_rapid PASSED   [ 66%]
tests/test_adversarial_m2.py::test_tab_visibility_and_css_display_leak FAILED [ 77%]
tests/test_adversarial_m2.py::test_tab_switching_shared_state_persistence PASSED [ 88%]
tests/test_adversarial_m2.py::test_dom_node_count_leak_during_tab_switching PASSED [100%]
```

### Observation 1: Tab Visibility Leak & CSS Selector Specificity Bug
In `ui/dashboard/index.html` lines 276-293:
```css
    /* Global View Switching Container */
    .view-pane {
      display: none;
      width: 100%;
      height: 100%;
      overflow: hidden;
    }
    .view-pane.active-view {
      display: flex;
    }

    /* Mission Control 3-Column Cockpit Grid */
    #view-mission-control {
      display: grid;
      grid-template-columns: var(--left-sidebar-width) 1fr var(--right-sidebar-width);
      width: 100%;
      height: 100%;
      overflow: hidden;
    }
```
When navigating to Knowledge Studio via `renderModeView('knowledge_studio')` (line 2194), the class `active-view` is removed from `#view-mission-control` and added to `#view-knowledge-studio`.
However, because `#view-mission-control` has ID selector specificity `(1, 0, 0)`, its `display: grid` declaration overrides `.view-pane` specificity `(0, 1, 0)`.
In headless Chromium, `window.getComputedStyle(document.getElementById('view-mission-control')).display` was evaluated after switching to Knowledge Studio:
```
Metrics after switching to Knowledge Studio:
MC = {'x': 0, 'y': 48, 'width': 720, 'height': 760}
KS = {'x': 720, 'y': 48, 'width': 720, 'height': 760}
```
Failure output from `test_tab_visibility_and_css_display_leak`:
```
AssertionError: CSS SPECIFICITY BUG: Inactive Mission Control pane has computed display 'grid' instead of 'none'!
Mission Control occupies {'x': 0, 'y': 48, 'width': 720, 'height': 760}, pushing Knowledge Studio to {'x': 720, 'y': 48, 'width': 720, 'height': 760} (off-screen / overlapping)!
assert 'grid' == 'none'
  - none
  + grid
```

### Observation 2: Raw HTML / XSS Injection in Left Sidebar Task Addition
In `ui/dashboard/index.html` lines 2161-2177 and 2492-2503:
```javascript
      const btnAddTask = document.getElementById('btn-add-task');
      if (btnAddTask) {
        btnAddTask.addEventListener('click', () => {
          const title = prompt('Enter new task description:', 'Verify toolpath clearance');
          if (title && title.trim()) {
            AppState.tasks.push({
              id: 't' + (AppState.tasks.length + 1),
              title: title.trim(),
              completed: false,
              badge: 'Queued',
              badgeType: 'queued'
            });
            renderTasks();
          }
        });
      }
```
And inside `renderTasks()`:
```javascript
      container.innerHTML = AppState.tasks.map(task => {
        ...
        return `
          <div class="task-item" data-task-id="${task.id}">
            <div class="task-left">
              <div class="custom-checkbox ${checkboxClass}" onclick="toggleTask('${task.id}')">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
              </div>
              <span class="task-text ${task.completed ? 'completed' : ''}">${task.title}</span>
            </div>
            ...
          </div>
        `;
      }).join('');
```
`task.title` is concatenated directly into `container.innerHTML` without escaping HTML entities.
In `test_add_task_edge_cases`, entering payload `<span id="xss-test-probe">XSS_INJECTED</span>` resulted in an active probe node instantiated directly in the DOM tree:
```
Failed: SECURITY VULNERABILITY DETECTED: Task description rendered raw HTML tags directly into innerHTML without sanitization! Found 1 injected DOM nodes.
```

### Observation 3: Passed Stress Verifications
- **DOM Loading**: 0 console errors, 0 console warnings, 0 unhandled promise rejections on load via Playwright.
- **Task Toggling**: 50 rapid checkbox clicks kept `#task-counter` and DOM checked count in exact lockstep (`completed / total`).
- **Mic Mute Toggle**: 40 rapid clicks kept `#btn-wake-word.active` and `#wake-word-label` ("Listening for Wake-Word" vs "Wake-Word Muted") synchronized without leaking interval animations.
- **Project Dropdown**: Open, click outside to close, and item selection ("Robotic Pick & Place") functioned cleanly.
- **Tab State Persistence**: Mutations to tasks, mic state, and project persisted across 20 cycles of 4-tab switching.
- **DOM Stability**: DOM element count before (1,061) and after (1,061) 80 tab switches remained completely identical (zero node accumulation / leaks).

---

## 2. Logic Chain

1. **Premise 1**: Requirement R3 and Acceptance Criteria in `PROJECT.md` require four distinct, dedicated top-level view modes (`Mission Control`, `Knowledge Studio`, `Vision SOM`, `Focus Chat`) where switching between tabs presents each dedicated view cleanly in full screen.
2. **Premise 2**: `#workspace-container` is styled as a flex container (`display: flex; flex: 1; overflow: hidden;`).
3. **Inference from Obs 1**: Because `#view-mission-control` is defined with selector `#view-mission-control { display: grid; }`, CSS rule specificity `(1, 0, 0)` overrides the class selector `.view-pane { display: none; }` `(0, 1, 0)`. Therefore, `#view-mission-control` never resolves to `display: none` when the user switches to other tabs.
4. **Impact 1**: When `Knowledge Studio`, `Vision SOM`, or `Focus Chat` is clicked, `#view-mission-control` remains rendered at `width: 720px` (50% of the viewport), while the newly selected view is forced into the remaining `720px` (50% of the viewport). The two panes render side-by-side simultaneously, corrupting the layout and breaking the single-cockpit user experience.
5. **Inference from Obs 2**: In `renderTasks()`, `task.title` is inserted into `container.innerHTML` without HTML entity encoding or using `textContent`.
6. **Impact 2**: If task descriptions contain special characters or `<img src=x onerror=...>`, arbitrary markup and script execution occur directly in the browser DOM.

---

## 3. Caveats

- Backend WebSocket reconnection behavior under interrupted networking was verified via unit tests in `tests/test_api.py`, but network disconnect simulations in headless browser were out of scope for Milestone 2 frontend review.
- No other security vulnerabilities or styling defects were identified in the top navigation bar or left sidebar components.

---

## 4. Conclusion

**Verdict**: `CHALLENGE_REJECT`

Milestone 2 cannot be approved in its current state due to two confirmed empirical failures:
1. **Critical Layout / Specificity Defect**: `#view-mission-control` does not hide when switching to the other 3 tabs, resulting in a broken 50/50 horizontal split between Mission Control and the newly active tab.
   - *Recommended Fix*: Update CSS line 287 to `#view-mission-control.active-view { display: grid; ... }` (or add `#view-mission-control:not(.active-view) { display: none; }`).
2. **Input Sanitization Vulnerability**: Left sidebar task description input is evaluated directly as raw HTML in `container.innerHTML`.
   - *Recommended Fix*: Sanitize `task.title` using textContent assignment or HTML escaping (`task.title.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))`).

---

## 5. Verification Method

To independently reproduce both issues:
```powershell
uv run --with pytest,playwright pytest tests/test_adversarial_m2.py -v
```

Expected failures:
1. `tests/test_adversarial_m2.py::test_tab_visibility_and_css_display_leak` fails with `AssertionError: CSS SPECIFICITY BUG: Inactive Mission Control pane has computed display 'grid' instead of 'none'! Mission Control occupies {'x': 0, 'y': 48, 'width': 720, 'height': 760}, pushing Knowledge Studio to {'x': 720, 'y': 48, 'width': 720, 'height': 760}`.
2. `tests/test_adversarial_m2.py::test_add_task_edge_cases` fails with `Failed: SECURITY VULNERABILITY DETECTED: Task description rendered raw HTML tags directly into innerHTML without sanitization! Found 1 injected DOM nodes.`

Invalidation condition: When the CSS rule is updated so `#view-mission-control` resolves to `display: none` when inactive, and `task.title` is properly escaped, both tests in `test_adversarial_m2.py` will pass (9 of 9 passed).
