# Empirical Challenge Handoff Report — Milestone 2

**Agent**: teamwork_preview_challenger (challenger_m2_2)  
**Parent**: orchestrator_1 (20ee9337-54d2-4ed7-a02f-42aad4232d45)  
**Target**: `ui/dashboard/index.html` (Milestone 2: Global Shell, Design System & Left Sidebar)  
**Empirical Verdict**: **CHALLENGE_REJECT**

---

## 1. Observation

### Observation 1: Tab Switching Display Leak (CSS Specificity Bug)
- **File & Lines**: `ui/dashboard/index.html` lines 277-284, 288-294, 2200-2207.
- **Rule in CSS**:
  ```css
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
- **Observed Behavior**:
  When switching to Knowledge Studio (`data-mode="knowledge_studio"`), Vision SOM, or Focus Chat, `renderModeView()` removes `.active-view` from `.view-pane`. However, `#view-mission-control` uses an ID selector `(1, 0, 0)`, which takes precedence over `.view-pane` `(0, 1, 0)`.
- **Verbatim Test Failure** from `pytest tests/test_challenge_m2.py::test_tab_switching_css_specificity_display_leak`:
  ```
  AssertionError: CSS SPECIFICITY BUG DETECTED: Inactive #view-mission-control has display: 'grid' instead of 'none'!
  ID selector #view-mission-control { display: grid } overrides .view-pane { display: none }.
  Knowledge Studio was pushed to x=720.
  assert 'grid' == 'none'
  ```
- **Visual Impact**: Mission Control is never hidden when switching tabs. It remains rendered at `x: 0, width: 720`, pushing Knowledge Studio off-screen to `x: 720`.

---

### Observation 2: XSS / HTML Injection in Task List
- **File & Lines**: `ui/dashboard/index.html` lines 2169, 2489-2504.
- **Code**:
  ```javascript
  container.innerHTML = AppState.tasks.map(task => {
    ...
    <span class="task-text ${task.completed ? 'completed' : ''}">${task.title}</span>
    ...
  }).join('');
  ```
- **Observed Behavior**: User input entered into `prompt('Enter new task description:', ...)` is pushed directly into `AppState.tasks` and concatenated into `container.innerHTML` without HTML entity escaping.
- **Verbatim Error** from `pytest tests/test_adversarial_m2.py::test_add_task_edge_cases`:
  ```
  Failed: SECURITY VULNERABILITY DETECTED: Task description rendered raw HTML tags directly into innerHTML without sanitization! Found 1 injected DOM nodes.
  ```

---

### Observation 3: Sub-Component Vertical Overflow at 1024x768
- **File & Lines**: `ui/dashboard/index.html` lines 960-989 (`.canvas-action-toolbar`), lines 186-220 (`.mode-switcher`).
- **Observed Bounding Box Metrics** at 1024x768 viewport:
  - `.canvas-action-toolbar`: container `height: 38px`, container bottom: `648px`.
  - Button `#btn-rescan-som`: lacks `white-space: nowrap;` and flex-shrink protection. When compressed into the 394px center column, the label wraps to 2 lines ("Re-scan\nSOM"), expanding button height to `49px`, button top: `605px`, button bottom: `654px`.
  - Result: Button vertically overflows the toolbar by 6 pixels (`btn1.bottom (654) > tb.bottom (648)`).
  - `#top-nav .mode-switcher`: Mode switcher pill buttons wrap, expanding `.mode-switcher` height to `52px`, which exceeds `--top-nav-height: 48px` by 4 pixels.
  - `#approval-gate-dock`: `.gate-left` wraps to 2 lines (`height: 33.6px`), and clearance between `.gate-left` and `.gate-actions` drops to `0px`.

---

### Observation 4: Zero-Dependency Verification
- **Tool Command**: `pytest tests/test_challenge_m2.py::test_zero_external_network_requests` & `test_zero_external_links_in_html_source`.
- **Result**: PASSED.
  - Zero external HTTP/WebSocket network calls initiated during page load or runtime.
  - Zero external `<link rel="stylesheet">`, `<script src="...">`, `@import url(...)`, or remote `@font-face` rules.
  - Fonts strictly rely on system font fallbacks (`Inter`, `Segoe UI`, `JetBrains Mono`, `Cascadia Code`).
  - Icons are 100% inline SVG.

---

### Observation 5: WebSocket Resilience & Offline AppState Fallback
- **Tool Command**: `pytest tests/test_challenge_m2.py::test_offline_page_load_and_mock_fallback`.
- **Result**: PASSED.
  - Under complete offline simulation (aborted `/api/*` and `/ws` connections), page loads with 0 uncaught JavaScript errors.
  - `AppState` cleanly retains default mock fixtures (`project: '3D Fabrication & Automation'`, `mission: 'PAUSED • APPROVAL'`, 4 tasks, blackboard pipeline).
  - Offline user interactions (`Approve`, `Abort`, `Panic Kill`, REPL commands, task checkbox toggling, tab navigation) update the DOM and AppState immediately without crashing.

---

## 2. Logic Chain

1. **Step 1 (Zero-Dependency & Offline Verification)**:
   Observations 4 and 5 confirm that `ui/dashboard/index.html` fulfills the zero-external-dependency requirement and implements robust offline/mock fallback for `AppState` without throwing uncaught exceptions.

2. **Step 2 (Tab Switching Broken by Specificity Bug)**:
   Observation 1 demonstrates that switching tabs does not hide `#view-mission-control`. Because `#view-mission-control` is defined with an ID selector having `display: grid;`, it overrides `.view-pane { display: none; }` (class selector). Therefore, when a user switches to Knowledge Studio, Vision SOM, or Focus Chat, Mission Control remains displayed at `x=0..720`, pushing the active tab off-screen (`x=720`). This violates Requirement R3 ("All four top-level navigation tabs must be fully functional, rich interactive views sharing global state").

3. **Step 3 (Security Vulnerability in Task Addition)**:
   Observation 2 demonstrates that task creation accepts raw HTML strings and injects them unescaped into `container.innerHTML`, creating an XSS injection vulnerability.

4. **Step 4 (Responsiveness Constraints at 1024x768)**:
   Observation 3 shows that while the SPA shell does not cause horizontal page scrolling at 1024x768, sub-components experience vertical overflow and tight clipping due to lack of `white-space: nowrap;` on `.toolbar-btn` and `.mode-tab-btn`.

5. **Step 5 (Synthesis to Verdict)**:
   Because the tab switching mechanism is fundamentally compromised by the CSS specificity bug and task addition has an unsanitized injection vulnerability, Milestone 2 cannot be accepted as complete without fixing these regressions. Therefore, the empirical verdict is **CHALLENGE_REJECT**.

---

## 3. Caveats

- **No Caveats**. All failure modes were reproduced empirically using automated headless Chromium browser test suites (`tests/test_challenge_m2.py` and `tests/test_adversarial_m2.py`).
- Fix proposals are provided below to guide immediate resolution by the implementation worker.

---

## 4. Conclusion & Required Mitigations

**Verdict**: **CHALLENGE_REJECT**

### Required Fixes for Milestone 2 Acceptance:

1. **Fix CSS Specificity Bug for View Switching**:
   In `ui/dashboard/index.html`:
   Change:
   ```css
   #view-mission-control {
     display: grid;
     grid-template-columns: var(--left-sidebar-width) 1fr var(--right-sidebar-width);
     width: 100%;
     height: 100%;
     overflow: hidden;
   }
   ```
   To:
   ```css
   #view-mission-control.active-view {
     display: grid;
   }
   ```
   Ensure `.view-pane` default `display: none;` is respected whenever `.active-view` is absent.

2. **Sanitize Task Titles to Prevent XSS**:
   In `ui/dashboard/index.html`, add an entity escaping helper:
   ```javascript
   function escapeHtml(str) {
     return String(str).replace(/[&<>"']/g, m => ({
       '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
     }[m]));
   }
   ```
   And use `${escapeHtml(task.title)}` inside `renderTasks()`.

3. **Harden 1024x768 Sub-Component Layout**:
   - Add `white-space: nowrap;` and `flex-shrink: 0;` to `.toolbar-btn` and `.mode-tab-btn`.
   - Add defensive text truncation (`text-overflow: ellipsis; overflow: hidden; white-space: nowrap;`) to `.gate-detail`.

4. **Defensive WebSocket Property Access**:
   - Change `msg.data.instruction` to `msg.data?.instruction` on line 2439.

---

## 5. Verification Method

To independently reproduce and verify this challenge verdict:

```powershell
# 1. Run the empirical challenge suite
uv run --with pytest,playwright pytest tests/test_challenge_m2.py -v

# 2. Run the adversarial stress suite
uv run --with pytest,playwright pytest tests/test_adversarial_m2.py -v
```

Expected output prior to fix:
- `test_tab_switching_css_specificity_display_leak`: FAILED (`AssertionError: display: 'grid' != 'none'`)
- `test_add_task_edge_cases`: FAILED (`SECURITY VULNERABILITY DETECTED`)

After the worker applies the mitigations above, both tests will pass cleanly (`100% pass`).
