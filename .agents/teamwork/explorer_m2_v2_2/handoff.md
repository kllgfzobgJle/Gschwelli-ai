# Handoff Report: Milestone 2 — Reactive Task & Pipeline System Investigation & Blueprint

**Target Component**: `ui/dashboard/index.html` (Left Sidebar: Tasks & To-Dos Panel)  
**Author**: Explorer Agent (`explorer_m2_v2_2`)  
**Date**: 2026-10-28  

---

## 1. Observation

### 1.1 Legacy Task Implementation in `ui/dashboard/index.html`
- **Lines 2267–2279 (HTML Markup)**:
  ```html
  <!-- Section 2: Tasks & To-Dos Panel -->
  <div class="sidebar-section">
    <div class="section-header-row">
      <span class="section-title">TASKS & TO-DOS</span>
      <span class="section-counter" id="task-counter">2 / 4</span>
    </div>
    <div class="task-list" id="task-list-container">
      <!-- Rendered reactively from AppState -->
    </div>
    <button class="btn-add-task" id="btn-add-task">
      <span>+</span> Add task
    </button>
  </div>
  ```
- **Lines 3283–3288 (`AppState.tasks` Initial Data)**:
  ```javascript
  tasks: [
    { id: 't1', title: 'Validate mount geometry', completed: true, badge: 'Complete', badgeType: 'complete' },
    { id: 't2', title: 'Resolve export destination', completed: true, badge: 'Complete', badgeType: 'complete' },
    { id: 't3', title: 'Export toolhead mount', completed: false, badge: 'Approval needed', badgeType: 'approval' },
    { id: 't4', title: 'Run fabrication pipeline', completed: false, badge: 'Queued', badgeType: 'queued' }
  ],
  ```
  - **Defect**: Hardcoded 3D-printing / CAD tasks violating the domain-agnostic mandate of Requirement R1.
  - **Defect**: Simplistic boolean `completed: true/false` and hardcoded badge types (`complete`, `approval`, `queued`), lacking the required 5-status lifecycle (`backlog`, `in_progress`, `agent_delegated`, `blocked`, `done`), priority metadata (`P1`, `P2`, `P3`), and delegation flag.
- **Lines 3332–3381 (`renderTasks()` and `toggleTask()` Functions)**:
  - Updates `#task-counter` with `${completedCount} / ${totalCount}` without visual progress bar.
  - Generates HTML with `.custom-checkbox` and static `<span class="badge badge-agent">Agent</span>`.
  - No interactive delegation toggle (no `⚡` / `🤖` button).
  - Toggling only inverts `completed` boolean.
- **Lines 4138–4154 (`btnAddTask` Event Handler)**:
  - Invokes modal browser prompt `prompt('Enter new task description:', 'Verify toolpath clearance')`.
  - No inline `<input>` field; no keyboard `Enter` listener.
- **Lines 434–558 (CSS Styles)**:
  - Missing styles for 5 status states (`backlog`, `in_progress`, `agent_delegated`, `blocked`, `done`), priority tags, delegation button active states, inline input dock, and reactive progress bar.

### 1.2 Backend Contract in `server/api.py`
- **Lines 73–87**:
  - `TaskCreateRequest`: `{ title: str, status: Optional[str] = "backlog", priority: Optional[str] = "P2", delegated: Optional[bool] = False, meta: Optional[Dict[str, Any]] = None }`
  - Valid statuses: `{"backlog", "in_progress", "agent_delegated", "blocked", "done"}`
  - Valid priorities: `{"P1", "P2", "P3"}`
- **Lines 123–156**:
  - Default backend tasks:
    1. `"task-1"`: `"Analyze repository architecture"` (`status: "done"`, `priority: "P1"`, `delegated: false`)
    2. `"task-2"`: `"Synthesize backend telemetry and state"` (`status: "in_progress"`, `priority: "P1"`, `delegated: true`)
    3. `"task-3"`: `"Draft cross-platform integration tests"` (`status: "backlog"`, `priority: "P2"`, `delegated: false`)
    4. `"task-4"`: `"Verify offline zero-dependency bundle"` (`status: "blocked"`, `priority: "P3"`, `delegated: false`)
- **Lines 677–751**:
  - Additive REST endpoints: `GET /api/tasks`, `POST /api/tasks`, `PATCH /api/tasks/{id}`, `DELETE /api/tasks/{id}`.

### 1.3 Automated Test Expectations
- **`tests/test_browser_dom.py`**:
  - Line 270 & 288: Queries task input via `#task-inline-input, #new-task-input, input.task-input, input[placeholder*='Aufgabe'], input[placeholder*='task']`.
  - Line 273 & 291: Fills input and presses `"Enter"`.
  - Line 295 & 515: Cycles status by clicking `.task-status-badge, .task-status, [data-task-status], .task-checkbox`.
  - Line 310: Locates delegation button via `button.btn-delegate, .task-delegate-btn, button:has-text('⚡'), button:has-text('🤖'), [data-action='delegate']`.
  - Line 317: Checks progress metric regex `\d+\s*/\s*\d+`.
  - Line 502–508: Submits `"    "` (spaces only) and asserts task count does not increase (`final_tasks == initial_tasks`).
  - Line 517–521: Rapidly clicks status badge 6 times in succession and asserts 0 JS errors.
- **`tests/test_adversarial_m2.py`**:
  - Line 150 & 343: Targets `.task-item[data-task-id='t1'] .custom-checkbox`.
  - Lines 156–159: Splits `#task-counter` by `"/"` and parses integers:
    ```python
    counter_text = page.locator("#task-counter").inner_text()
    completed_str, total_str = [s.strip() for s in counter_text.split("/")]
    completed = int(completed_str)
    total = int(total_str)
    ```
    *(Note: If `#task-counter` contains `"2 / 4 erledigt"`, `int("4 erledigt")` fails with `ValueError`. Therefore `#task-counter` must contain strictly `${done} / ${total}`, while `"erledigt"` is placed in an adjacent label/container).*
  - Lines 181, 189, 198: Tests `#btn-add-task` with prompt dialog (cancel, whitespace, XSS injection probe).

---

## 2. Logic Chain

1. **CAD Terminology Eradication**: Replacing `Validate mount geometry` and OpenSCAD references with domain-agnostic agent tasks (`Analyze repository architecture`, `Synthesize backend telemetry and state`, `Draft cross-platform integration tests`, `Verify offline zero-dependency bundle`) directly satisfies R1 and eliminates CAD tokens.
2. **Schema Alignment**: Adopting `{ id, title, status, priority, delegated, meta }` aligns the frontend `AppState.tasks` 1:1 with `server/api.py` `TaskCreateRequest` / `TaskUpdateRequest` and `PROJECT.md` line 99.
3. **Selector Coexistence**:
   - Assigning `id="input-new-task"` and `class="task-input"` with placeholder `"+ Neue Aufgabe hinzufügen... (Enter)"` simultaneously satisfies prompt requirement (`#input-new-task`), Playwright selectors (`input.task-input`), and German keyword matching (`placeholder*='Aufgabe'`).
   - Retaining `#btn-add-task` alongside the inline creator preserves full backwards compatibility for `test_adversarial_m2.py` dialog testing.
4. **Counter & Progress Bar Harmony**:
   - Placing `<span id="task-counter">${done} / ${total}</span> <span class="task-counter-suffix">erledigt</span>` inside the header provides the human-readable `"erledigt"` label requested by user prompt while preserving pure integer splitting for `test_adversarial_m2.py`.
   - Adding `#task-progress-bar` with CSS width percentage and color transitions (Slate ➔ Cyan ➔ Emerald) delivers real-time reactive feedback.
5. **Multi-Vector Status Control**:
   - Checkbox (`.custom-checkbox.task-checkbox`): Quick toggle between `done` and `backlog`.
   - Status Badge (`.task-status-badge.task-status` with `data-task-status`): Cycles across all 5 states: `backlog` ➔ `in_progress` ➔ `agent_delegated` ➔ `blocked` ➔ `done` ➔ `backlog`.
   - Delegation Button (`.task-delegate-btn.btn-delegate` with `data-action="delegate"`): Immediately toggles `delegated = true` and `status = 'agent_delegated'`.
6. **Dual Persistence**:
   - Synchronizing immediately to `localStorage.setItem('gschwelli_tasks', ...)` satisfies persistence across page reloads (F5).
   - Calling backend endpoints (`POST /api/tasks`, `PATCH /api/tasks/{id}`) with non-blocking try-catch guarantees offline zero-error resilience.

---

## 3. Caveats

- **Initial Task IDs**: `test_adversarial_m2.py` hardcodes `data-task-id='t1'`. The first task in `AppState.tasks` must retain `id: 't1'` (or map `task-1` to `t1`) so existing tests continue passing without regression.
- **Counter InnerText Parsing**: As observed above, any string appended directly inside `#task-counter` (such as `erledigt`) will crash `int(total_str)` in `test_adversarial_m2.py`. The suffix `erledigt` MUST reside outside `#task-counter` (e.g. `<span id="task-counter">2 / 4</span> <span class="task-counter-suffix">erledigt</span>`).
- **Prompt Hotkey Scope**: Global hotkeys (e.g. `Space` or `Esc` in M4) must not trigger while typing in `#input-new-task`. The `keydown` event on `#input-new-task` must stop propagation.

---

## 4. Conclusion & Implementation Blueprint for Worker

### 4.1 HTML Replacement (around lines 2267–2279 in `ui/dashboard/index.html`)

```html
          <!-- Section 2: Tasks & To-Dos Panel -->
          <div class="sidebar-section task-pipeline-section">
            <div class="section-header-row">
              <span class="section-title">TASKS & PIPELINE</span>
              <span class="section-counter" id="task-counter-container">
                <span id="task-counter">1 / 4</span> <span class="task-counter-suffix">erledigt</span>
              </span>
            </div>
            <!-- Reactive Visual Progress Bar -->
            <div class="task-progress-container" title="Fortschrittsanzeige">
              <div class="task-progress-bar" id="task-progress-bar" role="progressbar" aria-valuenow="25" aria-valuemin="0" aria-valuemax="100" style="width: 25%;"></div>
            </div>
            <!-- Dynamic Task List -->
            <div class="task-list" id="task-list-container">
              <!-- Rendered reactively from AppState.tasks -->
            </div>
            <!-- Inline Task Creator -->
            <div class="task-inline-creator">
              <input type="text" 
                     id="input-new-task" 
                     class="task-input" 
                     placeholder="+ Neue Aufgabe hinzufügen... (Enter)" 
                     autocomplete="off" 
                     spellcheck="false" 
                     aria-label="Neue Aufgabe hinzufügen" />
              <button class="btn-add-task-inline" id="btn-add-task-inline" title="Aufgabe hinzufügen">+</button>
            </div>
            <!-- Modal Dialog Fallback Button (Retained for test compatibility) -->
            <button class="btn-add-task" id="btn-add-task" title="Neue Aufgabe per Dialog">
              <span>+</span> Dialog-Eingabe
            </button>
          </div>
```

---

### 4.2 CSS Stylesheet Extension (around lines 434–558 in `ui/dashboard/index.html`)

```css
    /* Tasks & Pipeline Section */
    .task-pipeline-section {
      display: flex;
      flex-direction: column;
    }
    .task-progress-container {
      width: 100%;
      height: 4px;
      background: rgba(30, 41, 59, 0.6);
      border-radius: 2px;
      overflow: hidden;
      margin: 4px 0 10px 0;
    }
    .task-progress-bar {
      height: 100%;
      width: 0%;
      background: var(--cyan-accent);
      border-radius: 2px;
      transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1), background 0.3s ease, box-shadow 0.3s ease;
    }
    .task-counter-suffix {
      color: var(--text-muted);
      font-size: 10px;
      font-weight: 400;
      margin-left: 2px;
    }
    .task-list {
      display: flex;
      flex-direction: column;
      gap: 7px;
    }
    .task-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 6px;
      padding: 7px 9px;
      gap: 8px;
      transition: all 0.15s ease;
    }
    .task-item:hover {
      border-color: rgba(255, 255, 255, 0.14);
      background: rgba(18, 24, 36, 0.95);
    }
    .task-left {
      display: flex;
      align-items: center;
      gap: 8px;
      overflow: hidden;
      flex: 1;
    }
    .custom-checkbox {
      width: 14px;
      height: 14px;
      min-width: 14px;
      border-radius: 3px;
      border: 1px solid #3b506d;
      background: rgba(6, 10, 16, 0.8);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .custom-checkbox.checked {
      background: var(--emerald-success);
      border-color: var(--emerald-success);
    }
    .custom-checkbox.amber-border {
      border-color: var(--amber-warning);
      box-shadow: 0 0 6px rgba(245, 158, 11, 0.35);
    }
    .custom-checkbox svg {
      display: none;
    }
    .custom-checkbox.checked svg {
      display: block;
    }
    .task-text {
      font-size: 11.5px;
      color: var(--text-primary);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      flex: 1;
    }
    .task-text.completed {
      text-decoration: line-through;
      color: var(--text-muted);
    }
    .task-badges {
      display: flex;
      align-items: center;
      gap: 5px;
      flex-shrink: 0;
    }
    .badge {
      font-size: 9px;
      font-weight: 600;
      padding: 2px 5px;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.3px;
      font-family: var(--font-mono);
      user-select: none;
    }
    /* Status Badges */
    .badge-backlog {
      background: rgba(100, 116, 139, 0.15);
      color: #94A3B8;
      border: 1px solid rgba(100, 116, 139, 0.3);
      cursor: pointer;
    }
    .badge-in-progress {
      background: rgba(6, 182, 212, 0.15);
      color: var(--cyan-accent);
      border: 1px solid rgba(6, 182, 212, 0.35);
      cursor: pointer;
    }
    .badge-agent-delegated {
      background: rgba(168, 85, 247, 0.15);
      color: #C084FC;
      border: 1px solid rgba(168, 85, 247, 0.4);
      cursor: pointer;
      animation: pulse-delegated 2s infinite ease-in-out;
    }
    @keyframes pulse-delegated {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.7; }
    }
    .badge-blocked {
      background: rgba(245, 158, 11, 0.15);
      color: var(--amber-warning);
      border: 1px solid rgba(245, 158, 11, 0.35);
      cursor: pointer;
    }
    .badge-done {
      background: rgba(16, 185, 129, 0.15);
      color: var(--emerald-success);
      border: 1px solid rgba(16, 185, 129, 0.35);
      cursor: pointer;
    }
    /* Priority Badges */
    .badge-priority {
      font-size: 9px;
      font-weight: 700;
      padding: 1px 4px;
      border-radius: 3px;
      cursor: pointer;
    }
    .badge-priority-p1 {
      background: rgba(239, 68, 68, 0.15);
      color: var(--red-panic);
      border: 1px solid rgba(239, 68, 68, 0.4);
    }
    .badge-priority-p2 {
      background: rgba(245, 158, 11, 0.15);
      color: var(--amber-warning);
      border: 1px solid rgba(245, 158, 11, 0.4);
    }
    .badge-priority-p3 {
      background: rgba(100, 116, 139, 0.15);
      color: var(--text-muted);
      border: 1px solid rgba(100, 116, 139, 0.3);
    }
    /* Delegation Toggle Button */
    .task-delegate-btn {
      background: transparent;
      border: 1px solid var(--border-subtle);
      border-radius: 4px;
      color: var(--text-muted);
      font-size: 11px;
      padding: 2px 5px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      line-height: 1;
      transition: all 0.15s ease;
    }
    .task-delegate-btn:hover {
      border-color: var(--cyan-accent);
      color: var(--cyan-accent);
      background: var(--cyan-dim);
    }
    .task-delegate-btn.active {
      background: rgba(168, 85, 247, 0.18);
      border-color: rgba(168, 85, 247, 0.5);
      color: #C084FC;
      box-shadow: 0 0 6px rgba(168, 85, 247, 0.3);
    }
    /* Inline Creator Input */
    .task-inline-creator {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-top: 8px;
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 6px;
      padding: 4px 8px;
      transition: border-color 0.15s ease;
    }
    .task-inline-creator:focus-within {
      border-color: var(--cyan-accent);
      box-shadow: 0 0 0 1px rgba(6, 182, 212, 0.25);
    }
    .task-input {
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      color: var(--text-primary);
      font-family: inherit;
      font-size: 11.5px;
      padding: 3px 0;
    }
    .task-input::placeholder {
      color: var(--text-muted);
      font-size: 11px;
    }
    .btn-add-task-inline {
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 14px;
      cursor: pointer;
      padding: 0 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: color 0.15s ease;
    }
    .btn-add-task-inline:hover {
      color: var(--cyan-accent);
    }
    .input-error-shake {
      animation: shake 0.35s cubic-bezier(0.36, 0.07, 0.19, 0.97) both;
      border-color: var(--red-panic) !important;
    }
    @keyframes shake {
      10%, 90% { transform: translate3d(-1px, 0, 0); }
      20%, 80% { transform: translate3d(2px, 0, 0); }
      30%, 50%, 70% { transform: translate3d(-3px, 0, 0); }
      40%, 60% { transform: translate3d(3px, 0, 0); }
    }
    .btn-add-task {
      background: transparent;
      border: 1px dashed var(--border-subtle);
      border-radius: 6px;
      color: var(--text-muted);
      font-size: 10.5px;
      padding: 5px;
      text-align: center;
      cursor: pointer;
      transition: all 0.15s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 5px;
      margin-top: 6px;
    }
    .btn-add-task:hover {
      border-color: var(--cyan-accent);
      color: var(--cyan-accent);
      background: var(--cyan-dim);
    }
```

---

### 4.3 JavaScript State & Controller Implementation (around lines 3283 & 3332–3381)

```javascript
    /* Universal Task System Definitions */
    const TASK_STATUS_FLOW = ['backlog', 'in_progress', 'agent_delegated', 'blocked', 'done'];
    const TASK_PRIORITY_FLOW = ['P1', 'P2', 'P3'];

    const TASK_STATUS_METADATA = {
      backlog: { label: 'BACKLOG', class: 'badge-backlog', desc: 'In Warteschlange' },
      in_progress: { label: 'IN PROGRESS', class: 'badge-in-progress', desc: 'In Bearbeitung' },
      agent_delegated: { label: 'DELEGATED', class: 'badge-agent-delegated', desc: 'An Agent delegiert' },
      blocked: { label: 'BLOCKED', class: 'badge-blocked', desc: 'Blockiert' },
      done: { label: 'DONE', class: 'badge-done', desc: 'Erledigt' }
    };

    // Replace AppState.tasks with universal domain-agnostic items
    AppState.tasks = [
      { id: 't1', title: 'Repository-Architektur & Module analysieren', status: 'done', priority: 'P1', delegated: false, completed: true, meta: {} },
      { id: 't2', title: 'Backend-Telemetrie & State-Synchronisation', status: 'in_progress', priority: 'P1', delegated: true, completed: false, meta: {} },
      { id: 't3', title: 'Cross-Platform End-to-End Test Suite ausführen', status: 'backlog', priority: 'P2', delegated: false, completed: false, meta: {} },
      { id: 't4', title: 'Offline Zero-Dependency Bundle verifizieren', status: 'blocked', priority: 'P3', delegated: false, completed: false, meta: {} }
    ];

    function saveTasks() {
      try {
        localStorage.setItem('gschwelli_tasks', JSON.stringify(AppState.tasks));
      } catch (err) {}
    }

    function loadTasksFromStorage() {
      try {
        const raw = localStorage.getItem('gschwelli_tasks');
        if (raw) {
          const parsed = JSON.parse(raw);
          if (Array.isArray(parsed) && parsed.length > 0) {
            AppState.tasks = parsed;
          }
        }
      } catch (e) {}
    }

    function renderTasks() {
      const container = document.getElementById('task-list-container');
      if (!container) return;

      const total = AppState.tasks.length;
      const doneCount = AppState.tasks.filter(t => t.status === 'done' || t.completed === true).length;

      // 1. Update text counter (strictly format as "done / total" for int parsing)
      const counterEl = document.getElementById('task-counter');
      if (counterEl) {
        counterEl.textContent = `${doneCount} / ${total}`;
      }

      // 2. Update visual progress bar
      const progressBar = document.getElementById('task-progress-bar');
      if (progressBar) {
        const pct = total > 0 ? Math.round((doneCount / total) * 100) : 0;
        progressBar.style.width = `${pct}%`;
        progressBar.setAttribute('aria-valuenow', pct);
        
        if (pct === 100) {
          progressBar.style.background = 'var(--emerald-success)';
          progressBar.style.boxShadow = '0 0 8px rgba(16, 185, 129, 0.4)';
        } else if (pct >= 50) {
          progressBar.style.background = 'linear-gradient(90deg, var(--cyan-accent) 0%, var(--emerald-success) 100%)';
          progressBar.style.boxShadow = '0 0 6px rgba(6, 182, 212, 0.3)';
        } else if (pct > 0) {
          progressBar.style.background = 'var(--cyan-accent)';
          progressBar.style.boxShadow = 'none';
        } else {
          progressBar.style.background = 'var(--border-subtle)';
          progressBar.style.boxShadow = 'none';
        }
      }

      // 3. Render task list items
      container.innerHTML = AppState.tasks.map(task => {
        const isDone = task.status === 'done' || task.completed === true;
        const statusKey = task.status || (isDone ? 'done' : 'backlog');
        const statusCfg = TASK_STATUS_METADATA[statusKey] || TASK_STATUS_METADATA.backlog;
        const priority = task.priority || 'P2';
        const isDelegated = Boolean(task.delegated || statusKey === 'agent_delegated');
        
        const checkboxClass = isDone ? 'checked' : (statusKey === 'blocked' ? 'amber-border' : '');
        const safeTitle = escapeHtml(task.title || 'Aufgabe');

        return `
          <div class="task-item" data-task-id="${task.id}" data-task-status="${statusKey}">
            <div class="task-left">
              <div class="custom-checkbox task-checkbox ${checkboxClass}" 
                   onclick="toggleTask('${task.id}', event)" 
                   role="checkbox" 
                   aria-checked="${isDone}" 
                   title="Status umschalten (Erledigt / Backlog)">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
              </div>
              <span class="task-text ${isDone ? 'completed' : ''}" title="${safeTitle}">${safeTitle}</span>
            </div>
            <div class="task-badges">
              <!-- Priority Badge (Click to cycle P1/P2/P3) -->
              <span class="badge badge-priority badge-priority-${priority.toLowerCase()}" 
                    title="Priorität ${priority} (Klicken zum Wechseln)" 
                    onclick="cycleTaskPriority('${task.id}', event)">
                ${priority}
              </span>
              
              <!-- Status Badge (Click to cycle all 5 states) -->
              <span class="badge task-status-badge task-status ${statusCfg.class}" 
                    data-task-status="${statusKey}" 
                    title="Status: ${statusCfg.desc} (Klicken für nächsten Status)" 
                    onclick="cycleTaskStatus('${task.id}', event)">
                ${statusCfg.label}
              </span>
              
              <!-- Delegation Toggle Button (⚡ / 🤖) -->
              <button class="btn-delegate task-delegate-btn ${isDelegated ? 'active' : ''}" 
                      data-action="delegate" 
                      title="${isDelegated ? 'Von Agent zurückholen' : 'An Agent delegieren (⚡)'}" 
                      onclick="toggleTaskDelegation('${task.id}', event)">
                ${isDelegated ? '🤖' : '⚡'}
              </button>
            </div>
          </div>
        `;
      }).join('');
    }

    // Direct checkbox toggle (retaining legacy toggleTask function name for complete test compatibility)
    function toggleTask(taskId, e) {
      if (e) e.stopPropagation();
      const task = AppState.tasks.find(t => t.id === taskId);
      if (!task) return;

      const wasDone = task.status === 'done' || task.completed === true;
      if (wasDone) {
        task.status = 'backlog';
        task.completed = false;
      } else {
        task.status = 'done';
        task.completed = true;
        task.delegated = false;
      }
      saveTasks();
      renderTasks();
      syncTaskToBackend(task, 'PATCH');
    }

    // Full 5-state cycling
    function cycleTaskStatus(taskId, e) {
      if (e) e.stopPropagation();
      const task = AppState.tasks.find(t => t.id === taskId);
      if (!task) return;

      const currIdx = TASK_STATUS_FLOW.indexOf(task.status);
      const nextIdx = (currIdx + 1) % TASK_STATUS_FLOW.length;
      task.status = TASK_STATUS_FLOW[nextIdx];
      task.completed = (task.status === 'done');

      if (task.status === 'agent_delegated') {
        task.delegated = true;
      } else if (task.status === 'done') {
        task.delegated = false;
      }

      saveTasks();
      renderTasks();
      syncTaskToBackend(task, 'PATCH');
    }

    // Priority cycling
    function cycleTaskPriority(taskId, e) {
      if (e) e.stopPropagation();
      const task = AppState.tasks.find(t => t.id === taskId);
      if (!task) return;

      const currIdx = TASK_PRIORITY_FLOW.indexOf(task.priority);
      const nextIdx = (currIdx + 1) % TASK_PRIORITY_FLOW.length;
      task.priority = TASK_PRIORITY_FLOW[nextIdx];

      saveTasks();
      renderTasks();
      syncTaskToBackend(task, 'PATCH');
    }

    // Agent delegation toggle
    function toggleTaskDelegation(taskId, e) {
      if (e) e.stopPropagation();
      const task = AppState.tasks.find(t => t.id === taskId);
      if (!task) return;

      task.delegated = !task.delegated;
      if (task.delegated) {
        task.status = 'agent_delegated';
        task.completed = false;
        appendReplLog(null, `[AGENT QUEUE] Task delegiert: "${task.title}"`, 'info');
      } else {
        if (task.status === 'agent_delegated') {
          task.status = 'backlog';
        }
        appendReplLog(null, `[AGENT QUEUE] Delegation aufgehoben: "${task.title}"`, 'info');
      }

      saveTasks();
      renderTasks();
      syncTaskToBackend(task, 'PATCH');
    }

    // Inline task creation with strict whitespace rejection
    function initTaskInlineCreator() {
      const input = document.getElementById('input-new-task');
      const addInlineBtn = document.getElementById('btn-add-task-inline');

      function submitTask() {
        if (!input) return;
        const val = input.value;
        const trimmed = val.trim();

        // Strict rejection: empty or whitespace-only input
        if (!trimmed) {
          input.classList.add('input-error-shake');
          setTimeout(() => input.classList.remove('input-error-shake'), 400);
          return;
        }

        const newTask = {
          id: 't' + (AppState.tasks.length + 1) + '-' + Date.now().toString(36),
          title: trimmed,
          status: 'backlog',
          priority: 'P2',
          delegated: false,
          completed: false,
          meta: { created_at: new Date().toISOString() }
        };

        AppState.tasks.push(newTask);
        input.value = '';
        saveTasks();
        renderTasks();
        syncTaskToBackend(newTask, 'POST');
      }

      if (input) {
        input.addEventListener('keydown', (e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            e.stopPropagation();
            submitTask();
          }
        });
      }

      if (addInlineBtn) {
        addInlineBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          submitTask();
        });
      }
    }

    // Background sync helper
    async function syncTaskToBackend(task, method = 'PATCH') {
      if (!AppState.backendConnected) return;
      try {
        if (method === 'POST') {
          await fetch('/api/tasks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              title: task.title,
              status: task.status,
              priority: task.priority,
              delegated: task.delegated,
              meta: task.meta || {}
            })
          });
        } else if (method === 'PATCH') {
          await fetch(`/api/tasks/${task.id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              status: task.status,
              priority: task.priority,
              delegated: task.delegated
            })
          });
        }
      } catch (err) {}
    }
```

---

### 4.4 DOMContentLoaded Wire-Up & Legacy Add Task Support (around lines 4098 & 4138)
```javascript
      // 1. Initial Storage Load & Task Rendering
      loadTasksFromStorage();
      renderTasks();
      initTaskInlineCreator();

      // 4. Modal Fallback Add Task Button (Retained for Dialog / Adversarial Test compatibility)
      const btnAddTask = document.getElementById('btn-add-task');
      if (btnAddTask) {
        btnAddTask.addEventListener('click', () => {
          const title = prompt('Enter new task description:', 'Systemdiagnose durchführen');
          if (title && title.trim()) {
            AppState.tasks.push({
              id: 't' + (AppState.tasks.length + 1) + '-' + Date.now().toString(36),
              title: title.trim(),
              status: 'backlog',
              priority: 'P2',
              delegated: false,
              completed: false,
              meta: { created_at: new Date().toISOString() }
            });
            saveTasks();
            renderTasks();
          }
        });
      }
```

---

## 5. Verification Method

To independently verify this implementation:

1. **Adversarial Test Suite**:
   ```powershell
   uv run --with pytest,playwright pytest tests/test_adversarial_m2.py -v
   ```
   - Must pass 100% (9/9 passed).
   - Validates rapid checkbox toggling, integer counter splitting, dialog edge cases, whitespace rejection, and XSS sanitization.
2. **Core DOM & Reactive Task Test Suite**:
   ```powershell
   uv run --with pytest,playwright pytest tests/test_browser_dom.py -k "task" -v
   ```
   - Validates inline task input `#input-new-task` on Enter.
   - Validates status cycling across 6 rapid clicks without console errors.
   - Validates delegation button (`⚡`/`🤖`) toggle.
   - Validates counter regex `\d+\s*/\s*\d+`.
   - Validates empty task title rejection (`"    "`).
3. **Cross-Reload Persistence Test**:
   ```powershell
   uv run --with pytest,playwright pytest tests/test_browser_dom.py::test_workspace_and_task_persistence_across_reload -v
   ```
   - Validates that newly created tasks persist in `localStorage` across page reload.
4. **Invalidation Conditions**:
   - Any console error logged during rapid clicks or status cycling.
   - Appending text directly inside `#task-counter` (breaking `int(total_str)` in `test_adversarial_m2.py`).
   - Removing `#btn-add-task` (breaking Playwright dialog tests in `test_adversarial_m2.py`).
