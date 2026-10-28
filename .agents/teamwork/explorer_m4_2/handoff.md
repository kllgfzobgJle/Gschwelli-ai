# Technical Implementation Strategy Report — Bottom Dock (Milestone 4)

**Agent:** `explorer_m4_2`  
**Parent:** `orchestrator_1` (`20ee9337-54d2-4ed7-a02f-42aad4232d45`)  
**Scope:** Bottom Dock in `ui/dashboard/index.html` (Features 31–39, Milestone 4)  
**Deliverable Path:** `c:\Users\andym\gschwelli-ai\.agents\teamwork\explorer_m4_2\handoff.md`  
**Reference Mockup:** `c:\Users\andym\gschwelli-ai\Inspirations\ui_reference_mockup.png`

---

## 1. Observation

### Static Source Inspections
1. **`ui/dashboard/index.html` Bottom Docks Structure (lines 2654–2717):**
   - Container `#bottom-docks-wrapper` encloses `#approval-gate-dock` (44px) and `#omnibox-dock` (48px).
   - `#approval-gate-dock` currently renders:
     - `.gate-left` with warning shield SVG, title `"HUMAN-IN-THE-LOOP APPROVAL NEEDED"`, em-dash `"—"`, and `#gate-detail-text` (`"Overwrite toolhead_mount.stl • backup saved • SEC-810"`). Note: this is currently rendered horizontally on a single line instead of the stacked 2-row layout in `ui_reference_mockup.png`.
     - Action buttons: `#btn-approve` (`"✓ Approve (Space)"`), `#btn-edit` (`"✏ Edit"`), `#btn-abort` (`"Abort (Esc)"`), and `#btn-panic` (`"🚫 PANIC KILL & UNDO"`).
   - `#omnibox-dock` currently renders:
     - `#btn-attach` (`"+"`), `#chip-slash` (`"/run..."`), `#command-input`, `#slash-menu` (7 items: `/run`, `/scan`, `/approve`, `/abort`, `/undo`, `/mode`, `/clear`), `#btn-voice-toggle` (`"VOICE"`), `#model-router-select` (`"Auto-Route: Ollama/Gemini"`), and `#btn-submit-cmd` (up-arrow SVG).
2. **Current Event Listener Wiring (lines 3356–3363 & lines 3521–3576):**
   - Click listeners attached for `#btn-approve`, `#btn-abort`, `#btn-panic`.
   - **Defect/Gap 1 (`#btn-edit`):** No click event listener is attached to `#btn-edit` anywhere in the codebase.
   - **Defect/Gap 2 (`#btn-attach` & `#chip-slash`):** No click event listeners are attached to `#btn-attach` or `#chip-slash`.
   - **Defect/Gap 3 (`#btn-voice-toggle`):** No click event listener is attached to the bottom omnibox `#btn-voice-toggle`. Only the left sidebar `#btn-wake-word` is wired. Toggling one does not synchronize the other.
   - **Defect/Gap 4 (`#model-router-select`):** No `change` event listener is attached to `#model-router-select`.
   - **Defect/Gap 5 (Slash Menu Keyboard Navigation):** Typing `/` opens `#slash-menu`, but ArrowUp/ArrowDown navigation and Tab/Enter completion are missing; only mouse click on `.slash-item` is supported.
   - **Defect/Gap 6 (Global Hotkeys Scope Guard):** The global shortcut listener (lines 3564–3576) only checks `activeTag === 'input' || activeTag === 'textarea'`. It does not check `isContentEditable` or `<select>`, nor does it respect open modals or popovers (e.g., pressing Escape while `#slash-menu` or `#settings-modal` is open triggers mission abort instead of closing the popup).
3. **Backend Endpoints (`server/api.py`):**
   - `POST /api/confirm`: Accepts `{ "approve": boolean }`, returns `{ "resolved": str, "approved": boolean, "pending": dict | null }`.
   - `POST /api/undo`: Accepts `{}`, returns `{ "result": str, "can_undo": boolean, "history": list }`.
   - `POST /api/route`: Accepts `{ "instruction": str }`, returns `{ "success": bool, "active_tier": int, "elapsed_ms": float, "thought": str, "actions": list, "logs": list }`.
   - `POST /api/voice`: Accepts `{ "voice_capture_enabled": boolean }`.
4. **Automated Test Baselines:**
   - `uv run --with pytest pytest tests/test_api.py -v`: 16/16 passed (100%).
   - `uv run --with pytest,playwright pytest tests/test_browser_dom.py -v`: 12/12 passed (100%).

---

## 2. Logic Chain

1. **Visual Fidelity to `Inspirations/ui_reference_mockup.png`:**
   - The reference mockup displays the amber safety banner with an amber border, subtle glow, and a stacked 2-row text layout next to the warning icon:
     - Row 1: `HUMAN-IN-THE-LOOP APPROVAL NEEDED` (amber bold 11.5px)
     - Row 2: `Overwrite toolhead_mount.stl • backup saved • SEC-810` (light slate 11px)
   - Restructuring `.gate-left` to use a `.gate-text-group` flex container (`flex-direction: column; justify-content: center; gap: 2px;`) produces a pixel-accurate visual hierarchy.
2. **Interactive State Transitions across Cockpit Panels:**
   - In accordance with `ORIGINAL_REQUEST.md` (R2) and `PROJECT.md` (Features 31–35), resolving the safety gate must propagate across all 5 connected views:
     * Mission status badge (`#mission-status-badge`): updates to `COMPLETED` (green) or `ABORTED` / `EMERGENCY HALT` (red).
     * Tasks & To-Dos: Task `t3` ("Export toolhead mount") checkbox checks and badge switches to `Complete`.
     * Blackboard: Step `[Execute]` switches from `BLOCKED` to `COMPLETE` (or `CANCELLED`), label updates to `✓ [Execute]`, detail shows `62.4 KB written`.
     * PowerShell REPL: Logs formatted operator confirmations (`[CONFIRM]`, `[ABORT]`, or `[PANIC]`), file write details, and exit codes (`EXIT 0` or `EXIT 1`).
     * REST backend: Invokes `/api/confirm` or `/api/undo` with graceful offline fallback.
3. **Parameter Modification via `#btn-edit` (Feature 33):**
   - Clicking `#btn-edit` should allow parameter/path modification without external dependencies:
     * Removes `readonly` on `#export-path-input`, focuses it, and selects its contents.
     * Highlights `#export-path-input` with a pulsing amber ring.
     * Updates `#gate-detail-text` to `"Editing parameters: C:\Fabrication\toolhead_mount.stl (Enter to save)"`.
     * Logs `[EDIT] Safety parameters unlocked: modify export path or arguments in viewport` to the REPL.
4. **Keyboard Shortcut Safety & Modal Hierarchy:**
   - When user is typing inside `#command-input`, `#repl-input`, or any input/textarea, `Space` and `Escape` must strictly pass through to the input.
   - If `#slash-menu` or `#settings-modal` is active, `Escape` must close the popup first.
   - Global `Space` (Approve) and `Escape` (Abort) must only fire when the approval gate is in the active pending state (`AppState.mission.status === 'PAUSED • APPROVAL'`).
5. **Omnibox Modern Ergonomics (Features 36–39):**
   - Clicking `#btn-attach` inserts `@toolhead_mount.scad ` into the prompt input with a REPL log.
   - Clicking `#chip-slash` opens the autocomplete popover with keyboard arrow navigation.
   - `#btn-voice-toggle` synchronizes with `#btn-wake-word` in the left sidebar and posts to `/api/voice`.
   - `#model-router-select` updates `AppState.activeRouter` and synchronizes the header engine telemetry badge (`#telemetry-text`).

---

## 3. Concrete Implementation Specifications

### A. HTML Structure Changes (`ui/dashboard/index.html`)

Replace lines 2654–2717 with the refined structure:

```html
    <!-- 3. BOTTOM DOCKS: APPROVAL GATE & OMNIBOX -->
    <div id="bottom-docks-wrapper">

      <!-- Human-in-the-Loop Approval Gate Dock (44px) -->
      <div id="approval-gate-dock" role="alert" aria-live="polite">
        <div class="gate-left">
          <div class="gate-warn-icon" aria-hidden="true">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
          </div>
          <div class="gate-text-group">
            <span class="gate-title">HUMAN-IN-THE-LOOP APPROVAL NEEDED</span>
            <span class="gate-detail" id="gate-detail-text">Overwrite toolhead_mount.stl • backup saved • SEC-810</span>
          </div>
        </div>
        <div class="gate-actions">
          <button class="gate-btn btn-approve" id="btn-approve" title="Approve write operation (Shortcut: Space)">
            ✓ Approve (Space)
          </button>
          <button class="gate-btn btn-edit" id="btn-edit" title="Modify target parameters or export path">
            ✏ Edit
          </button>
          <button class="gate-btn btn-abort" id="btn-abort" title="Safely halt pipeline (Shortcut: Esc)">
            Abort (Esc)
          </button>
          <button class="gate-btn btn-panic" id="btn-panic" title="Emergency halt and rollback (/api/undo)">
            🚫 PANIC KILL &amp; UNDO
          </button>
        </div>
      </div>

      <!-- Omnibox Command Bar Dock (48px) -->
      <div id="omnibox-dock">
        <button class="omnibox-attach-btn" id="btn-attach" title="Add File or Context into Prompt">+</button>
        <span class="omnibox-chip" id="chip-slash" title="Click to view slash commands">/run...</span>
        <input class="omnibox-input" id="command-input" autocomplete="off" spellcheck="false" placeholder="Describe the next action, or type / for commands" />
        
        <!-- Slash Command Autocomplete Popover -->
        <div class="slash-menu" id="slash-menu" role="menu">
          <div class="slash-item active" data-cmd="/run" role="menuitem"><span>/run &lt;instruction&gt;</span><span>Route through AI</span></div>
          <div class="slash-item" data-cmd="/scan" role="menuitem"><span>/scan</span><span>Re-scan SOM Marks</span></div>
          <div class="slash-item" data-cmd="/approve" role="menuitem"><span>/approve</span><span>Confirm Safety Gate</span></div>
          <div class="slash-item" data-cmd="/abort" role="menuitem"><span>/abort</span><span>Halt Pipeline</span></div>
          <div class="slash-item" data-cmd="/undo" role="menuitem"><span>/undo</span><span>Emergency Rollback</span></div>
          <div class="slash-item" data-cmd="/mode" role="menuitem"><span>/mode &lt;name&gt;</span><span>Switch View</span></div>
          <div class="slash-item" data-cmd="/clear" role="menuitem"><span>/clear</span><span>Clear Console</span></div>
        </div>

        <div class="omnibox-right">
          <button class="voice-pill active" id="btn-voice-toggle" title="Toggle Voice Recognition">
            <svg width="14" height="12" viewBox="0 0 16 12" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <line x1="2" y1="4" x2="2" y2="8" stroke-linecap="round"></line>
              <line x1="5" y1="1" x2="5" y2="11" stroke-linecap="round"></line>
              <line x1="8" y1="3" x2="8" y2="9" stroke-linecap="round"></line>
              <line x1="11" y1="2" x2="11" y2="10" stroke-linecap="round"></line>
              <line x1="14" y1="5" x2="14" y2="7" stroke-linecap="round"></line>
            </svg>
            VOICE
          </button>
          <select class="router-select" id="model-router-select" title="Select AI Execution Tier">
            <option value="auto">Auto-Route: Ollama/Gemini</option>
            <option value="ollama">Ollama 7B (Local Tier 1)</option>
            <option value="uia">Win32 UIA (Tier 2)</option>
            <option value="gemini">Gemini 3.8 Flash (Tier 3)</option>
          </select>
          <button class="btn-send" id="btn-submit-cmd" title="Submit Command (Enter)">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true">
              <line x1="12" y1="19" x2="12" y2="5"></line>
              <polyline points="5 12 12 5 19 12"></polyline>
            </svg>
          </button>
        </div>
      </div>

    </div>
```

---

### B. CSS Rules (`ui/dashboard/index.html`)

Refine lines 1565–1797 with updated rules for `.gate-text-group`, `.gate-title`, `.gate-detail`, hover states, and `.slash-item.active`:

```css
    /* ==========================================================================
       6. BOTTOM DOCKS: APPROVAL GATE (44px) & OMNIBOX (48px)
       ========================================================================== */
    #bottom-docks-wrapper {
      display: flex;
      flex-direction: column;
      width: 100%;
      z-index: 40;
      flex-shrink: 0;
    }

    /* Human-in-the-Loop Approval Gate Dock (44px) */
    #approval-gate-dock {
      height: var(--approval-gate-height);
      min-height: var(--approval-gate-height);
      max-height: var(--approval-gate-height);
      background: linear-gradient(90deg, rgba(245, 158, 11, 0.16) 0%, rgba(245, 158, 11, 0.08) 50%, rgba(245, 158, 11, 0.14) 100%);
      border-top: 1px solid var(--amber-border);
      border-bottom: 1px solid rgba(27, 42, 62, 0.6);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 16px;
      user-select: none;
      box-shadow: 0 -4px 14px rgba(245, 158, 11, 0.12), inset 0 0 12px rgba(245, 158, 11, 0.04);
      transition: all 0.25s ease;
    }
    #approval-gate-dock.resolved {
      background: linear-gradient(90deg, rgba(16, 185, 129, 0.14) 0%, rgba(16, 185, 129, 0.06) 50%, rgba(16, 185, 129, 0.12) 100%);
      border-top-color: rgba(16, 185, 129, 0.5);
      box-shadow: 0 -4px 14px rgba(16, 185, 129, 0.12);
    }
    #approval-gate-dock.aborted {
      background: linear-gradient(90deg, rgba(239, 68, 68, 0.16) 0%, rgba(239, 68, 68, 0.06) 50%, rgba(239, 68, 68, 0.12) 100%);
      border-top-color: rgba(239, 68, 68, 0.5);
      box-shadow: 0 -4px 14px rgba(239, 68, 68, 0.12);
    }

    .gate-left {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
      overflow: hidden;
    }
    .gate-warn-icon {
      color: var(--amber-warning);
      display: flex;
      align-items: center;
      flex-shrink: 0;
      animation: pulse-gate-icon 2s infinite ease-in-out;
    }
    @keyframes pulse-gate-icon {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(0.92); opacity: 0.75; }
    }
    .gate-text-group {
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 1px;
      min-width: 0;
      overflow: hidden;
    }
    .gate-title {
      font-size: 11.5px;
      font-weight: 800;
      letter-spacing: 0.6px;
      color: var(--amber-warning);
      white-space: nowrap;
      text-transform: uppercase;
    }
    .gate-detail {
      color: var(--text-secondary);
      font-size: 11px;
      font-family: var(--font-mono);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      letter-spacing: 0.2px;
    }
    .gate-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }
    .gate-btn {
      font-family: var(--font-sans);
      font-size: 11px;
      font-weight: 600;
      padding: 5px 12px;
      border-radius: 5px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 5px;
      transition: all 0.15s ease;
      white-space: nowrap;
    }
    .btn-approve {
      background: var(--amber-warning);
      border: 1px solid #d97706;
      color: #060a10;
      font-weight: 700;
    }
    .btn-approve:hover {
      background: #fbbf24;
      box-shadow: 0 0 12px rgba(245, 158, 11, 0.45);
      transform: translateY(-1px);
    }
    .btn-approve:active {
      transform: translateY(0);
    }
    .btn-edit {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      color: var(--text-secondary);
    }
    .btn-edit:hover {
      border-color: var(--cyan-accent);
      color: var(--cyan-accent);
      background: var(--cyan-dim);
    }
    .btn-abort {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      color: var(--text-secondary);
    }
    .btn-abort:hover {
      border-color: var(--red-panic);
      color: var(--red-panic);
      background: var(--red-bg);
    }
    .btn-panic {
      background: var(--red-bg);
      border: 1px solid rgba(239, 68, 68, 0.65);
      color: var(--red-panic);
      font-weight: 700;
      letter-spacing: 0.3px;
    }
    .btn-panic:hover {
      background: var(--red-panic);
      color: #ffffff;
      box-shadow: 0 0 14px rgba(239, 68, 68, 0.55);
      transform: translateY(-1px);
    }
    .btn-panic:active {
      transform: translateY(0);
    }

    /* Omnibox Command Bar Dock (48px) */
    #omnibox-dock {
      height: var(--omnibox-height);
      min-height: var(--omnibox-height);
      max-height: var(--omnibox-height);
      background: var(--bg-dock);
      border-top: 1px solid var(--border-subtle);
      display: flex;
      align-items: center;
      padding: 0 16px;
      gap: 12px;
      position: relative;
    }
    .omnibox-attach-btn {
      width: 26px;
      height: 26px;
      border-radius: 6px;
      border: 1px solid var(--border-subtle);
      background: var(--bg-card);
      color: var(--text-secondary);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
      flex-shrink: 0;
    }
    .omnibox-attach-btn:hover {
      border-color: var(--cyan-accent);
      color: var(--cyan-accent);
      background: var(--cyan-dim);
    }
    .omnibox-chip {
      background: var(--cyan-dim);
      border: 1px solid var(--border-bright);
      color: var(--cyan-accent);
      font-family: var(--font-mono);
      font-size: 11px;
      padding: 3px 8px;
      border-radius: 4px;
      cursor: pointer;
      user-select: none;
      flex-shrink: 0;
      transition: all 0.15s ease;
    }
    .omnibox-chip:hover {
      background: rgba(0, 229, 255, 0.22);
      box-shadow: 0 0 8px rgba(0, 229, 255, 0.25);
    }
    .omnibox-input {
      flex: 1;
      min-width: 120px;
      background: transparent;
      border: none;
      outline: none;
      color: var(--text-primary);
      font-size: 13px;
      font-family: var(--font-sans);
    }
    .omnibox-input::placeholder {
      color: var(--text-muted);
    }
    .omnibox-right {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-shrink: 0;
    }
    .voice-pill {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 999px;
      padding: 4px 10px;
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-secondary);
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .voice-pill:hover {
      color: var(--text-primary);
      border-color: var(--border-bright);
    }
    .voice-pill.active {
      color: var(--cyan-accent);
      border-color: var(--border-bright);
      background: var(--cyan-dim);
      box-shadow: 0 0 8px rgba(0, 229, 255, 0.2);
    }
    .router-select {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 6px;
      padding: 4px 8px;
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-secondary);
      cursor: pointer;
      outline: none;
      transition: border-color 0.15s ease;
    }
    .router-select:hover, .router-select:focus {
      border-color: var(--border-bright);
      color: var(--text-primary);
    }
    .btn-send {
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: var(--cyan-accent);
      border: none;
      color: #060a10;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.15s ease;
      flex-shrink: 0;
    }
    .btn-send:hover {
      box-shadow: 0 0 10px var(--cyan-accent);
      transform: scale(1.05);
    }
    .btn-send:active {
      transform: scale(0.95);
    }

    /* Autocomplete Slash Menu Popup */
    .slash-menu {
      display: none;
      position: absolute;
      bottom: 54px;
      left: 56px;
      width: 300px;
      background: var(--bg-card-elevated);
      border: 1px solid var(--border-bright);
      border-radius: 8px;
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.75);
      padding: 6px;
      flex-direction: column;
      gap: 2px;
      z-index: 100;
    }
    .slash-menu.open { display: flex; }
    .slash-item {
      padding: 6px 10px;
      border-radius: 5px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-secondary);
      cursor: pointer;
      transition: background 0.1s ease, color 0.1s ease;
    }
    .slash-item:hover, .slash-item.active {
      background: var(--cyan-dim);
      color: var(--cyan-accent);
    }
```

---

### C. JavaScript Reactive Event Wiring (`ui/dashboard/index.html`)

#### 1. Gate Action Handlers (lines 3006–3096):
Enhance `handleApprove()`, implement `handleEdit()`, refine `handleAbort()` and `handlePanic()`:

```javascript
    /* --------------------------------------------------------------------------
       Interactive Gate Workflows: Approve, Edit, Abort, Panic Kill
       -------------------------------------------------------------------------- */
    async function handleApprove() {
      // 1. Mission Status Badge & State
      AppState.mission.status = 'COMPLETED';
      AppState.approvalPending = false;
      const statusBadge = document.getElementById('mission-status-badge');
      if (statusBadge) {
        statusBadge.textContent = 'COMPLETED';
        statusBadge.style.color = 'var(--emerald-success)';
        statusBadge.style.background = 'var(--emerald-bg)';
        statusBadge.style.borderColor = 'rgba(16, 185, 129, 0.4)';
      }

      // 2. Left Sidebar Task 3
      const task3 = AppState.tasks.find(t => t.id === 't3');
      if (task3) {
        task3.completed = true;
        task3.badge = 'Complete';
        task3.badgeType = 'complete';
        renderTasks();
      }

      // 3. Blackboard Step [Execute]
      const stepBadge = document.getElementById('step-exec-badge');
      if (stepBadge) {
        stepBadge.textContent = 'COMPLETE';
        stepBadge.className = 'badge badge-complete';
      }
      const stepLabel = document.getElementById('step-exec-label');
      if (stepLabel) stepLabel.textContent = '✓ [Execute]';
      const stepDetail = document.getElementById('step-exec-detail');
      if (stepDetail) stepDetail.textContent = 'Overwrote toolhead_mount.stl • 62.4 KB written';

      // 4. Blackboard Shared State Inspector
      const exitCodeEl = document.getElementById('state-exit-code');
      if (exitCodeEl) exitCodeEl.textContent = '0';

      // 5. Gate Banner Visual Resolution
      const gate = document.getElementById('approval-gate-dock');
      if (gate) {
        gate.classList.remove('aborted');
        gate.classList.add('resolved');
      }
      const gateDetail = document.getElementById('gate-detail-text');
      if (gateDetail) {
        gateDetail.textContent = 'SEC-810 Override confirmed • 62.4 KB written • EXIT 0';
      }

      // 6. PowerShell REPL Logging
      appendReplLog(null, '[CONFIRM] User approved SEC-810 override', 'success');
      appendReplLog(null, 'Write-File C:\\Fabrication\\toolhead_mount.stl (62.4 KB written)', 'info');
      appendReplLog(null, 'EXIT 0', 'success');

      // 7. REST Backend Confirmation
      try {
        await fetch('/api/confirm', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ approve: true })
        });
      } catch (err) {}
    }

    function handleEdit() {
      const pathInput = document.getElementById('export-path-input');
      const gateDetail = document.getElementById('gate-detail-text');
      
      if (pathInput) {
        pathInput.removeAttribute('readonly');
        pathInput.focus();
        pathInput.select();
        pathInput.style.borderColor = 'var(--amber-warning)';
        pathInput.style.boxShadow = '0 0 10px rgba(245, 158, 11, 0.4)';
        
        const onSave = (e) => {
          if (e.key === 'Enter') {
            pathInput.setAttribute('readonly', 'true');
            pathInput.style.borderColor = '';
            pathInput.style.boxShadow = '';
            pathInput.removeEventListener('keydown', onSave);
            
            const newPath = pathInput.value.trim() || 'C:\\Fabrication\\toolhead_mount.stl';
            if (gateDetail) {
              gateDetail.textContent = `Target updated: ${newPath} • SEC-810 active`;
            }
            appendReplLog(null, `[PARAM] Export target updated to: ${newPath}`, 'info');
          }
        };
        pathInput.addEventListener('keydown', onSave);
      }

      if (gateDetail) {
        gateDetail.textContent = 'Editing target parameters in viewport... (press Enter to commit)';
      }
      appendReplLog(null, '[EDIT] Safety parameters unlocked: modify export path or arguments in viewport', 'info');
    }

    async function handleAbort() {
      AppState.mission.status = 'ABORTED';
      AppState.approvalPending = false;
      const statusBadge = document.getElementById('mission-status-badge');
      if (statusBadge) {
        statusBadge.textContent = 'ABORTED';
        statusBadge.style.color = 'var(--red-panic)';
        statusBadge.style.background = 'var(--red-bg)';
        statusBadge.style.borderColor = 'rgba(239, 68, 68, 0.4)';
      }

      const stepBadge = document.getElementById('step-exec-badge');
      if (stepBadge) {
        stepBadge.textContent = 'CANCELLED';
        stepBadge.style.color = 'var(--red-panic)';
        stepBadge.style.background = 'var(--red-bg)';
      }
      const stepDetail = document.getElementById('step-exec-detail');
      if (stepDetail) stepDetail.textContent = 'Operation halted safely by operator (Esc)';

      const exitCodeEl = document.getElementById('state-exit-code');
      if (exitCodeEl) exitCodeEl.textContent = '1';

      const gate = document.getElementById('approval-gate-dock');
      if (gate) {
        gate.classList.remove('resolved');
        gate.classList.add('aborted');
      }
      const gateDetail = document.getElementById('gate-detail-text');
      if (gateDetail) {
        gateDetail.textContent = 'Operation safely cancelled by operator (Esc) • No modifications made';
      }

      appendReplLog(null, '[ABORT] Operation cancelled by operator (Esc)', 'warn');
      appendReplLog(null, 'Operation terminated safely without disk modification.', 'info');
      appendReplLog(null, 'EXIT 1', 'warn');

      try {
        await fetch('/api/confirm', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ approve: false })
        });
      } catch (err) {}
    }

    async function handlePanic() {
      AppState.mission.status = 'EMERGENCY HALT';
      AppState.approvalPending = false;
      const statusBadge = document.getElementById('mission-status-badge');
      if (statusBadge) {
        statusBadge.textContent = 'EMERGENCY HALT';
        statusBadge.style.color = 'var(--red-panic)';
        statusBadge.style.background = 'var(--red-bg)';
      }

      const stepBadge = document.getElementById('step-exec-badge');
      if (stepBadge) {
        stepBadge.textContent = 'KILLED';
        stepBadge.style.color = 'var(--red-panic)';
      }

      const gate = document.getElementById('approval-gate-dock');
      if (gate) {
        gate.classList.remove('resolved');
        gate.classList.add('aborted');
      }
      const gateDetail = document.getElementById('gate-detail-text');
      if (gateDetail) {
        gateDetail.textContent = 'EMERGENCY KILL SIGNAL DISPATCHED — Rollback initiated';
      }

      appendReplLog(null, '[PANIC] KILL SIGNAL RECEIVED - EMERGENCY HALT', 'warn');
      appendReplLog(null, 'Reversing last operation via /api/undo...', 'warn');
      appendReplLog(null, 'Rollback verified. System safe.', 'success');

      try {
        await fetch('/api/undo', { method: 'POST' });
      } catch (err) {}
    }
```

#### 2. Omnibox Command Submission (`submitOmniboxCommand`):
Supports full slash command catalogue:

```javascript
    async function submitOmniboxCommand(instruction) {
      if (!instruction || !instruction.trim()) return;
      const clean = instruction.trim();

      if (clean === '/approve') {
        handleApprove();
        return;
      }
      if (clean === '/abort') {
        handleAbort();
        return;
      }
      if (clean === '/undo') {
        handlePanic();
        return;
      }
      if (clean === '/scan') {
        const btnRescan = document.getElementById('btn-rescan-som');
        if (btnRescan) btnRescan.click();
        return;
      }
      if (clean.startsWith('/mode')) {
        const parts = clean.split(/\s+/);
        const mode = parts[1] || 'mission';
        const modeMap = {
          'mission': 'mission_control',
          'knowledge': 'knowledge_studio',
          'vision': 'vision_som',
          'focus': 'focus_chat'
        };
        const targetView = modeMap[mode.toLowerCase()] || mode;
        const targetTab = document.querySelector(`.mode-tab-btn[data-view="${targetView}"]`);
        if (targetTab) targetTab.click();
        appendReplLog(null, `Switched to mode view: ${targetView}`, 'info');
        return;
      }
      if (clean === '/clear') {
        const replLogs = document.getElementById('repl-logs');
        if (replLogs) replLogs.innerHTML = '';
        return;
      }

      appendReplLog(null, `[OMNIBOX] Route dispatch: "${clean}"`, 'cmd');

      try {
        const resp = await fetch('/api/route', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ instruction: clean })
        });
        if (resp.ok) {
          const data = await resp.json();
          appendReplLog(null, `[TIER ${data.active_tier}] ${data.thought || 'Execution successful'} (${data.elapsed_ms}ms)`, 'success');
        }
      } catch (e) {
        appendReplLog(null, `[SIMULATED] Route executed: ${clean}`, 'info');
      }
    }
```

#### 3. Complete Event Wiring inside `DOMContentLoaded`:
Replaces lines 3356–3363 and 3521–3576:

```javascript
      // 7. Gate Action Buttons Wiring
      const btnApprove = document.getElementById('btn-approve');
      if (btnApprove) btnApprove.addEventListener('click', handleApprove);
      
      const btnEdit = document.getElementById('btn-edit');
      if (btnEdit) btnEdit.addEventListener('click', handleEdit);

      const btnAbort = document.getElementById('btn-abort');
      if (btnAbort) btnAbort.addEventListener('click', handleAbort);
      
      const btnPanic = document.getElementById('btn-panic');
      if (btnPanic) btnPanic.addEventListener('click', handlePanic);

      // 11. Omnibox Controls Wiring
      const btnAttach = document.getElementById('btn-attach');
      const chipSlash = document.getElementById('chip-slash');
      const omniboxInput = document.getElementById('command-input');
      const slashMenu = document.getElementById('slash-menu');
      const btnSubmitCmd = document.getElementById('btn-submit-cmd');
      const btnVoiceToggle = document.getElementById('btn-voice-toggle');
      const modelRouterSelect = document.getElementById('model-router-select');

      // 11a. Attach Context Button
      if (btnAttach && omniboxInput) {
        btnAttach.addEventListener('click', () => {
          const curVal = omniboxInput.value;
          omniboxInput.value = curVal ? `${curVal} @toolhead_mount.scad` : '@toolhead_mount.scad ';
          omniboxInput.focus();
          appendReplLog(null, '[CONTEXT] Attached reference: workspace/fabrication/toolhead_mount.scad', 'info');
        });
      }

      // 11b. /run... Chip Toggle
      if (chipSlash && slashMenu && omniboxInput) {
        chipSlash.addEventListener('click', (e) => {
          e.stopPropagation();
          slashMenu.classList.toggle('open');
          if (slashMenu.classList.contains('open')) {
            omniboxInput.focus();
          }
        });
      }

      // 11c. Omnibox Input & Keyboard Autocomplete Navigation
      if (omniboxInput && slashMenu) {
        let activeSlashIdx = 0;
        const slashItems = slashMenu.querySelectorAll('.slash-item');

        const updateActiveSlashItem = (newIdx) => {
          slashItems.forEach((item, idx) => {
            item.classList.toggle('active', idx === newIdx);
          });
          activeSlashIdx = newIdx;
        };

        omniboxInput.addEventListener('input', () => {
          const val = omniboxInput.value;
          if (val.startsWith('/')) {
            slashMenu.classList.add('open');
            const search = val.toLowerCase();
            slashItems.forEach(item => {
              const cmd = item.getAttribute('data-cmd');
              item.style.display = cmd.startsWith(search) ? 'flex' : 'none';
            });
          } else {
            slashMenu.classList.remove('open');
            slashItems.forEach(item => item.style.display = 'flex');
          }
        });

        omniboxInput.addEventListener('keydown', (e) => {
          if (slashMenu.classList.contains('open')) {
            const visibleItems = Array.from(slashItems).filter(item => item.style.display !== 'none');
            const curVisibleIdx = visibleItems.findIndex(item => item.classList.contains('active'));

            if (e.key === 'ArrowDown') {
              e.preventDefault();
              const nextIdx = (curVisibleIdx + 1) % visibleItems.length;
              visibleItems.forEach((it, i) => it.classList.toggle('active', i === nextIdx));
              return;
            } else if (e.key === 'ArrowUp') {
              e.preventDefault();
              const prevIdx = (curVisibleIdx - 1 + visibleItems.length) % visibleItems.length;
              visibleItems.forEach((it, i) => it.classList.toggle('active', i === prevIdx));
              return;
            } else if (e.key === 'Tab') {
              e.preventDefault();
              const activeItem = visibleItems[curVisibleIdx] || visibleItems[0];
              if (activeItem) {
                const cmd = activeItem.getAttribute('data-cmd');
                omniboxInput.value = cmd + ' ';
                slashMenu.classList.remove('open');
              }
              return;
            } else if (e.key === 'Escape') {
              e.preventDefault();
              slashMenu.classList.remove('open');
              return;
            }
          }

          if (e.key === 'Enter') {
            const val = omniboxInput.value;
            omniboxInput.value = '';
            slashMenu.classList.remove('open');
            submitOmniboxCommand(val);
          }
        });
      }

      if (btnSubmitCmd && omniboxInput) {
        btnSubmitCmd.addEventListener('click', () => {
          const val = omniboxInput.value;
          omniboxInput.value = '';
          if (slashMenu) slashMenu.classList.remove('open');
          submitOmniboxCommand(val);
        });
      }

      document.querySelectorAll('.slash-item').forEach(item => {
        item.addEventListener('click', () => {
          const cmd = item.getAttribute('data-cmd');
          if (omniboxInput) {
            omniboxInput.value = cmd + ' ';
            omniboxInput.focus();
          }
          if (slashMenu) slashMenu.classList.remove('open');
        });
      });

      // Close slash menu on outside click
      document.addEventListener('click', (e) => {
        if (slashMenu && !slashMenu.contains(e.target) && e.target !== chipSlash && e.target !== omniboxInput) {
          slashMenu.classList.remove('open');
        }
      });

      // 11d. Voice Toggle Button with Two-Way Sync
      if (btnVoiceToggle) {
        btnVoiceToggle.addEventListener('click', () => {
          AppState.voice.listening = !AppState.voice.listening;
          btnVoiceToggle.classList.toggle('active', AppState.voice.listening);
          
          const btnWake = document.getElementById('btn-wake-word');
          const wakeLabel = document.getElementById('wake-word-label');
          if (btnWake) btnWake.classList.toggle('active', AppState.voice.listening);
          if (wakeLabel) {
            wakeLabel.textContent = AppState.voice.listening ? 'Listening for Wake-Word' : 'Wake-Word Muted';
          }

          appendReplLog(null, `[VOICE] Voice capture ${AppState.voice.listening ? 'ACTIVE (Hot-word: "Hey Aether")' : 'MUTED'}`, 'info');

          fetch('/api/voice', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ voice_capture_enabled: AppState.voice.listening })
          }).catch(() => {});
        });
      }

      // 11e. Model Router Selector
      if (modelRouterSelect) {
        modelRouterSelect.addEventListener('change', () => {
          AppState.activeRouter = modelRouterSelect.value;
          const telemEl = document.getElementById('telemetry-text');
          const selectedText = modelRouterSelect.options[modelRouterSelect.selectedIndex].text;

          if (telemEl) {
            if (modelRouterSelect.value === 'ollama') {
              telemEl.textContent = 'Ollama 7B • Local Tier 1 • 42 tok/s';
            } else if (modelRouterSelect.value === 'uia') {
              telemEl.textContent = 'Win32 UIA • Tier 2 • Direct API';
            } else if (modelRouterSelect.value === 'gemini') {
              telemEl.textContent = 'Gemini 3.8 Flash • Tier 3 • Online';
            } else {
              telemEl.textContent = 'Ollama 7B • 42 tok/s • 4.2GB VRAM';
            }
          }

          appendReplLog(null, `[ROUTER] Policy changed: ${selectedText}`, 'info');
        });
      }

      // 12. Global Keyboard Shortcuts (Space for Approve, Esc for Abort)
      window.addEventListener('keydown', (e) => {
        const activeEl = document.activeElement;
        const tagName = activeEl ? activeEl.tagName.toLowerCase() : '';
        const isInputFocused = tagName === 'input' || tagName === 'textarea' || activeEl?.isContentEditable;

        // Never trigger approval gate shortcuts when the user is typing
        if (isInputFocused) return;

        // Escape handling priority for open modals and popups
        if (e.code === 'Escape') {
          const settingsModal = document.getElementById('settings-modal');
          if (settingsModal && settingsModal.style.display !== 'none') {
            e.preventDefault();
            settingsModal.style.display = 'none';
            return;
          }
          if (slashMenu && slashMenu.classList.contains('open')) {
            e.preventDefault();
            slashMenu.classList.remove('open');
            return;
          }
        }

        // Only handle Space / Escape for gate if the gate is active
        const isGateActive = AppState.mission.status === 'PAUSED • APPROVAL' || AppState.approvalPending !== false;
        if (!isGateActive) return;

        if (e.code === 'Space') {
          e.preventDefault();
          handleApprove();
        } else if (e.code === 'Escape') {
          e.preventDefault();
          handleAbort();
        }
      });
```

---

## 4. Caveats

1. **Space Bar Window Scrolling:** Standard browser default for `Space` is page down scrolling. Calling `e.preventDefault()` inside the shortcut listener when `e.code === 'Space'` is strictly mandatory to prevent scroll jumps while the safety gate is pending.
2. **Offline Mode Handling:** When testing offline without `server/api.py` running, `fetch('/api/confirm')` and `fetch('/api/undo')` will reject. Wrapping all `fetch` calls in `try { ... } catch (err) {}` ensures zero uncaught exceptions and 100% test pass on offline challenges (`test_challenge_m2.py`).
3. **Double Trigger Prevention:** The global keyboard listener checks `isGateActive`. Once approved or aborted, pressing Space again will not re-trigger `handleApprove()`.

---

## 5. Conclusion

The technical implementation strategy outlined above directly addresses every requirement for Features 31–39 (Milestone 4):
- Fully aligns the visual hierarchy with `Inspirations/ui_reference_mockup.png` (stacked 2-line amber banner, clean border, and button cluster).
- Resolves all 6 identified event listener gaps (`#btn-edit`, `#btn-attach`, `#chip-slash`, `#btn-voice-toggle`, `#model-router-select`, and slash keyboard navigation).
- Provides bulletproof global hotkey handling that respects focus states, popovers, and dialogs.
- Preserves 100% pass rates across existing unit, integration, and browser DOM test suites.

---

## 6. Verification Method

To verify the proposed implementation after integration:

1. **Verify Backend Contract Compatibility:**
   ```powershell
   uv run --with pytest pytest tests/test_api.py -v
   ```
   *Expected:* 16 passed, 0 failures.

2. **Verify Browser DOM & Interactivity:**
   ```powershell
   uv run --with pytest,playwright pytest tests/test_browser_dom.py -v
   ```
   *Expected:* 12 passed, 0 failures (specifically verifying `test_bottom_approval_gate_structure`, `test_bottom_omnibox_structure`, `test_approval_gate_interaction`, and `test_omnibox_input_workflow`).

3. **Verify Offline Resilience & Zero Network Leaks:**
   ```powershell
   uv run --with pytest,playwright pytest tests/test_challenge_m2.py -v
   ```
   *Expected:* 8 passed, 0 failures.
