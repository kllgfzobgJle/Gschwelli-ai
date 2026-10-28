# Handoff Report: Frontend Workspace Manager & Persistence Architecture (Milestone 2)

## 1. Observation

Direct investigation of the codebase revealed the following exact locations, structures, and contracts:

### 1.1 Left Sidebar Static Project Selector (`ui/dashboard/index.html` lines 2239–2265)
The Left Sidebar currently features a static card and dropdown containing hardcoded 3D CAD fabrication strings:
```html
<!-- Section 1: Project / Local Workspace Card -->
<div class="sidebar-section">
  <div class="workspace-card" id="workspace-switcher-card">
    <span class="workspace-tag">PROJECT / LOCAL WORKSPACE</span>
    <div class="workspace-title-row">
      <span class="workspace-title" id="active-project-title">Active: 3D Fabrication & Automation</span>
      <span class="dropdown-chevron">▼</span>
    </div>
    <div class="workspace-meta-row">
      <span class="branch-icon">⎇</span>
      <span id="active-project-branch">main / 6 files indexed</span>
    </div>
    <!-- Interactive Project Switcher Dropdown -->
    <div class="workspace-dropdown-menu" id="workspace-dropdown">
      <div class="workspace-menu-item active" data-project="3D Fabrication & Automation">
        <span>3D Fabrication & Automation</span>
        <span style="color:var(--cyan-accent);">✓</span>
      </div>
      <div class="workspace-menu-item" data-project="Robotic Pick & Place">
        <span>Robotic Pick & Place</span>
      </div>
      <div class="workspace-menu-item" data-project="Drone Vision Inspection">
        <span>Drone Vision Inspection</span>
      </div>
    </div>
  </div>
</div>
```

### 1.2 Top Navigation Bar (`ui/dashboard/index.html` lines 2170–2226)
- The Top Navigation Bar contains:
  - Left: `.window-dots` and `.brand-cluster` (brand name `gschwelli-ai` and `#live-indicator`).
  - Center: `.mode-switcher` with 4 static mode buttons (`data-mode="mission_control"`, `knowledge_studio`, `vision_som`, `focus_chat`).
  - Right: `#telemetry-badge` and `#btn-settings`.
- **Finding**: There is currently no workspace indicator, quick workspace switcher, or `[+ Neuer Workspace]` button in the Top Navigation bar.

### 1.3 Static State Handling (`ui/dashboard/index.html` lines 3257–3317 & 4110–4136)
- In `AppState` (lines 3258–3267), the store only tracks:
  ```javascript
  project: {
    name: '3D Fabrication & Automation',
    branch: 'main',
    indexedFiles: 6,
    activeFile: 'toolhead_mount.scad',
    lastSync: '12s ago',
    totalChunks: 48
  }
  ```
  There is **no** `workspaces` array, no `activeWorkspaceId`, and no workspace CRUD or switching methods.
- In event listeners (lines 4110–4136):
  ```javascript
  const wsCard = document.getElementById('workspace-switcher-card');
  const wsDropdown = document.getElementById('workspace-dropdown');
  if (wsCard && wsDropdown) {
    wsCard.addEventListener('click', (e) => {
      e.stopPropagation();
      wsDropdown.classList.toggle('open');
    });
    document.querySelectorAll('.workspace-menu-item').forEach(item => {
      item.addEventListener('click', (e) => {
        e.stopPropagation();
        const proj = item.getAttribute('data-project');
        AppState.project.name = proj;
        document.getElementById('active-project-title').textContent = `Active: ${proj}`;
        document.querySelectorAll('.workspace-menu-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        wsDropdown.classList.remove('open');
      });
    });
    document.addEventListener('click', (e) => {
      if (wsDropdown.classList.contains('open') && !wsCard.contains(e.target)) {
        wsDropdown.classList.remove('open');
        e.stopPropagation();
        e.preventDefault(); // <-- BUG: interrupts global page clicks when closing dropdown
      }
    }, true);
  }
  ```
  Switching projects only mutates the text string `AppState.project.name`. It does not reload or filter tasks, does not update the file explorer, does not persist to `localStorage`, and does not communicate with the backend.

### 1.4 Backend Workspace Service (`server/api.py` lines 89–247 & 615–671)
The backend already provides a complete, tested REST API:
- `GET /api/workspaces` -> returns `{"workspaces": [...], "active_workspace_id": "ws-default"}`
- `POST /api/workspaces` -> creates workspace `{ id, name, prompt, working_dir, is_active }`
- `POST /api/workspaces/activate` -> activates workspace `{ id }`
- `DELETE /api/workspaces/{id}` -> deletes workspace
- `GET /api/workspace/files?path=...` -> returns files for active working directory
- `GET /api/state` -> returns `workspaces`, `active_workspace_id`, and `tasks`

### 1.5 Automated E2E Test Suite Expectations (`tests/test_browser_dom.py` lines 237–264)
The Playwright test `test_workspace_modal_crud_and_switching` searches for:
- Button: `#btn-new-workspace`, `button:has-text('Neuer Workspace')`, `button:has-text('New Workspace')`, `.btn-new-workspace`
- Selector Card: `#active-workspace-card`, `.project-card`, `#workspace-selector`, `#project-select-btn`
- Modal: `#workspace-modal`, `.workspace-modal`, `.modal-card:has-text('Workspace')`
- Inputs: `input[name='name']`, `#ws-name-input`, `input[placeholder*='Name']`
- Submit: `button:has-text('Erstellen')`, `button:has-text('Create')`, `button[type='submit']`

---

## 2. Logic Chain

From the observations above, the required frontend architecture is deduced through this step-by-step reasoning:

### Step 1: Left Sidebar & Top Bar UI Unification
- To fulfill requirement **R1** and pass E2E tests seamlessly, `#workspace-switcher-card` in the Left Sidebar should be given additional alias attributes (`id="workspace-switcher-card" class="workspace-card project-card" data-testid="active-workspace-card"`).
- Inside `#workspace-dropdown`, render workspaces dynamically from `AppState.workspaces` with a sticky divider and action button:
  `<button class="btn-dropdown-new-ws" id="btn-new-workspace-dropdown"><span style="color:var(--cyan-accent);">+</span> Neuer Workspace</button>`.
- In addition, place a prominent `[+ Neuer Workspace]` button (`#btn-new-workspace`) directly in the Left Sidebar header and/or Top Bar so that automated tests and users can trigger the modal in one click without first having to open the dropdown.
- Eliminate the buggy `e.preventDefault()` inside the document click listener (line 4133).

### Step 2: Modal Markup & Design System Conformance (DESIGN.md Tokens)
The modal must adhere strictly to the project design tokens:
- **Canvas / Void**: `#0A0D12` (used for input backgrounds and footer backdrop)
- **Cards / Panels**: `#121824` (modal card surface `background: #121824`)
- **Borders**: `1px solid #1E293B` (panel borders, inputs, separators)
- **Cyan Accent**: `#06B6D4` (focus outlines, submit button, active checkmarks, glow `0 0 16px rgba(6, 182, 212, 0.2)`)
- **Crimson Accent**: `#EF4444` (required field indicators and error text)
- **Backdrop**: `rgba(10, 13, 18, 0.82)` with `backdrop-filter: blur(5px)`

#### Recommended Modal Markup
```html
<!-- ====================================================================
     NEW WORKSPACE CREATION MODAL
     ==================================================================== -->
<div class="workspace-modal-backdrop" id="workspace-modal" style="display: none;">
  <div class="workspace-modal-card modal-card">
    <div class="workspace-modal-header">
      <div class="workspace-modal-title-group">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#06B6D4" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <line x1="12" y1="8" x2="12" y2="16"></line>
          <line x1="8" y1="12" x2="16" y2="12"></line>
        </svg>
        <span class="workspace-modal-title">Neuer Workspace / New Workspace</span>
      </div>
      <button class="workspace-modal-close-btn" id="btn-close-ws-modal" title="Schließen (Esc)">&times;</button>
    </div>
    <form id="form-new-workspace" class="workspace-modal-form" onsubmit="return false;">
      <div class="workspace-modal-body">
        <div class="ws-form-group">
          <label class="ws-form-label" for="ws-name-input">
            Workspace Name <span class="ws-required">*</span>
          </label>
          <input
            type="text"
            id="ws-name-input"
            name="name"
            class="ws-form-input"
            placeholder="z. B. Data Analysis & Processing"
            required
            autocomplete="off"
          />
          <span class="ws-form-hint">Eindeutiger Name des autonomen Arbeitsbereichs</span>
        </div>
        <div class="ws-form-group">
          <label class="ws-form-label" for="ws-prompt-input">
            System-Prompt / Mission des Agenten
          </label>
          <textarea
            id="ws-prompt-input"
            name="prompt"
            class="ws-form-textarea"
            rows="3"
            placeholder="z. B. Du bist ein autonomer Agent für Datenanalyse und API-Synthese..."
          ></textarea>
          <span class="ws-form-hint">Definiert Ziel, Rollenverhalten und Kontext des Agenten</span>
        </div>
        <div class="ws-form-group">
          <label class="ws-form-label" for="ws-dir-input">
            Lokales Arbeitsverzeichnis
          </label>
          <input
            type="text"
            id="ws-dir-input"
            name="working_dir"
            class="ws-form-input ws-dir-input"
            placeholder="workspace/data_analysis (optional)"
            autocomplete="off"
          />
          <span class="ws-form-hint">Relativer Pfad im Projekt (Standard: workspace/&lt;name&gt;)</span>
        </div>
        <div id="ws-modal-error" class="ws-modal-error" style="display: none;"></div>
      </div>
      <div class="workspace-modal-footer">
        <button type="button" class="btn-ws-secondary" id="btn-cancel-ws">Abbrechen</button>
        <button type="submit" class="btn-ws-primary" id="btn-create-ws">
          <span>+</span> Erstellen
        </button>
      </div>
    </form>
  </div>
</div>
```

#### Recommended CSS Styles
```css
/* ==========================================================================
   Workspace Modal & Dropdown Styles (DESIGN.md Tokens)
   ========================================================================== */
.workspace-modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(10, 13, 18, 0.82);
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
  z-index: 1100;
  display: flex;
  align-items: center;
  justify-content: center;
}

.workspace-modal-card {
  width: 480px;
  max-width: 92vw;
  background: #121824;
  border: 1px solid #1E293B;
  border-radius: 8px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.65), 0 0 16px rgba(6, 182, 212, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: wsModalIn 0.18s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes wsModalIn {
  from { opacity: 0; transform: scale(0.96) translateY(-8px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.workspace-modal-header {
  padding: 13px 18px;
  background: #0E1522;
  border-bottom: 1px solid #1E293B;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.workspace-modal-title-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.workspace-modal-title {
  font-size: 13px;
  font-weight: 600;
  color: #F1F5F9;
  letter-spacing: 0.3px;
}

.workspace-modal-close-btn {
  background: transparent;
  border: none;
  color: #64748B;
  font-size: 20px;
  cursor: pointer;
  line-height: 1;
  padding: 2px 6px;
  border-radius: 4px;
  transition: all 0.15s ease;
}

.workspace-modal-close-btn:hover {
  color: #F1F5F9;
  background: rgba(255, 255, 255, 0.08);
}

.workspace-modal-body {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.ws-form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.ws-form-label {
  font-size: 11.5px;
  font-weight: 600;
  color: #94A3B8;
  letter-spacing: 0.2px;
}

.ws-required {
  color: #EF4444;
}

.ws-form-input, .ws-form-textarea {
  background: #0A0D12;
  border: 1px solid #1E293B;
  border-radius: 5px;
  color: #F1F5F9;
  font-family: inherit;
  font-size: 12px;
  padding: 8px 10px;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.ws-form-input:focus, .ws-form-textarea:focus {
  border-color: #06B6D4;
  box-shadow: 0 0 0 2px rgba(6, 182, 212, 0.2);
}

.ws-form-textarea {
  resize: vertical;
  min-height: 64px;
  line-height: 1.4;
}

.ws-form-hint {
  font-size: 10.5px;
  color: #64748B;
}

.ws-modal-error {
  padding: 8px 12px;
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.35);
  border-radius: 4px;
  color: #EF4444;
  font-size: 11px;
}

.workspace-modal-footer {
  padding: 12px 18px;
  background: #0A0D12;
  border-top: 1px solid #1E293B;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

.btn-ws-secondary {
  background: transparent;
  border: 1px solid #1E293B;
  color: #94A3B8;
  padding: 6px 14px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-ws-secondary:hover {
  color: #F1F5F9;
  border-color: #334155;
  background: rgba(255, 255, 255, 0.04);
}

.btn-ws-primary {
  background: #06B6D4;
  border: 1px solid #06B6D4;
  color: #0A0D12;
  padding: 6px 18px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.15s ease;
}

.btn-ws-primary:hover {
  background: #0891B2;
  border-color: #0891B2;
  box-shadow: 0 0 12px rgba(6, 182, 212, 0.4);
}

/* Dropdown Neuer Workspace Button & Item Styling */
.workspace-dropdown-divider {
  height: 1px;
  background: #1E293B;
  margin: 4px 0;
}

.btn-dropdown-new-ws {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: transparent;
  border: none;
  color: #F1F5F9;
  font-size: 11.5px;
  font-weight: 600;
  cursor: pointer;
  text-align: left;
  transition: background 0.12s ease;
}

.btn-dropdown-new-ws:hover {
  background: rgba(6, 182, 212, 0.1);
  color: #06B6D4;
}

.ws-menu-item-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ws-menu-item-name {
  font-size: 11.5px;
  font-weight: 600;
  color: #F1F5F9;
}

.ws-menu-item-dir {
  font-size: 9.5px;
  font-family: var(--font-mono);
  color: #64748B;
}
```

### Step 3: `AppState` Workspace Data Model & Methods
Add full workspace management to `AppState`:
```javascript
const AppState = {
  // Existing fields ...
  activeTab: 'mission_control',
  
  // Workspace Manager state
  activeWorkspaceId: 'ws-default',
  workspaces: [
    {
      id: 'ws-default',
      name: 'General Workspace',
      prompt: 'Universal Autonomous Agent Operating Canvas',
      working_dir: 'workspace/default',
      is_active: true
    }
  ],

  // 1. Create Workspace
  createWorkspace(name, prompt = '', workingDir = '') {
    const cleanName = (name || '').trim();
    if (!cleanName) {
      throw new Error('Workspace name cannot be empty');
    }
    const wsId = 'ws-' + Date.now().toString(36) + Math.random().toString(36).substring(2, 6);
    const slug = cleanName.toLowerCase().replace(/[^a-z0-9_-]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '') || 'workspace';
    const finalDir = (workingDir || '').trim() || `workspace/${slug}`;
    const finalPrompt = (prompt || '').trim() || 'Universal Autonomous Agent Operating Canvas';

    const newWs = {
      id: wsId,
      name: cleanName,
      prompt: finalPrompt,
      working_dir: finalDir,
      is_active: false
    };

    this.workspaces.push(newWs);
    this.saveWorkspaces();
    this.switchWorkspace(wsId);

    // Asynchronous backend synchronization
    fetch('/api/workspaces', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: newWs.name,
        prompt: newWs.prompt,
        working_dir: newWs.working_dir
      })
    })
    .then(res => res.json())
    .then(data => {
      if (data && data.workspace && data.workspace.id) {
        // Update local object if backend assigned a specific id
        newWs.id = data.workspace.id;
        if (this.activeWorkspaceId === wsId) {
          this.activeWorkspaceId = data.workspace.id;
        }
        this.saveWorkspaces();
        renderWorkspaces();
      }
    })
    .catch(err => console.warn('[AppState] Backend offline, workspace stored in localStorage:', err));

    return newWs;
  },

  // 2. Switch Workspace (hot-switch without page reload)
  switchWorkspace(id) {
    const target = this.workspaces.find(w => w.id === id);
    if (!target) {
      console.warn(`[AppState] Workspace ${id} not found`);
      return false;
    }

    this.activeWorkspaceId = id;
    this.workspaces.forEach(w => {
      w.is_active = (w.id === id);
    });

    // Update active project metadata
    if (this.project) {
      this.project.name = target.name;
      this.project.working_dir = target.working_dir;
    }
    if (this.mission) {
      this.mission.name = target.name;
      this.mission.prompt = target.prompt;
    }

    // Persist active selection to localStorage
    try {
      localStorage.setItem('gschwelli_active_workspace', id);
    } catch (e) {}

    // Re-render UI components
    renderWorkspaces();
    renderTasks();
    refreshWorkspaceFiles(target.working_dir);

    // Notify backend
    fetch('/api/workspaces/activate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: id })
    }).catch(() => {});

    return true;
  },

  // 3. Load Workspaces (Dual-persistence hydration)
  async loadWorkspaces() {
    // Phase A: Instant synchronous load from localStorage
    try {
      const cached = localStorage.getItem('gschwelli_workspaces');
      const activeId = localStorage.getItem('gschwelli_active_workspace');
      if (cached) {
        const parsed = JSON.parse(cached);
        if (Array.isArray(parsed) && parsed.length > 0) {
          this.workspaces = parsed;
          this.activeWorkspaceId = activeId || parsed[0].id;
        }
      }
    } catch (e) {
      console.warn('[AppState] Failed to parse cached workspaces:', e);
    }

    renderWorkspaces();

    // Phase B: Asynchronous hydration from backend /api/workspaces
    try {
      const resp = await fetch('/api/workspaces');
      if (resp.ok) {
        const data = await resp.json();
        if (data.workspaces && data.workspaces.length > 0) {
          this.workspaces = data.workspaces;
          if (data.active_workspace_id) {
            this.activeWorkspaceId = data.active_workspace_id;
          }
          this.saveWorkspaces();
          renderWorkspaces();
        }
      }
    } catch (e) {
      console.info('[AppState] Working in offline/cached mode for workspaces');
    }
  },

  // 4. Save Workspaces
  saveWorkspaces() {
    try {
      localStorage.setItem('gschwelli_workspaces', JSON.stringify(this.workspaces));
      localStorage.setItem('gschwelli_active_workspace', this.activeWorkspaceId);
    } catch (e) {
      console.warn('[AppState] Failed to save workspaces to localStorage:', e);
    }
  }
};
```

### Step 4: Reactive DOM Propagation on Workspace Switch
When `switchWorkspace(id)` is executed, the following updates occur without a page reload:
1. **Dropdown & Card**:
   - `#active-project-title` is updated with `Active: ${ws.name}`.
   - `#active-project-branch` is updated with `${ws.working_dir}`.
   - `#workspace-dropdown` regenerates items, setting the active checkmark on the selected workspace.
2. **Tasks & To-Dos**:
   - `renderTasks()` re-executes, re-calculating the `#task-counter` and rebuilding the task list.
3. **Knowledge Base / File Tree**:
   - Folder label in `#kb-folder-toggle` updates to `📁 ${ws.working_dir || ws.name}/`.
   - `refreshWorkspaceFiles(workingDir)` queries `/api/workspace/files?path=${encodeURIComponent(workingDir)}` and populates the file list dynamically, completely removing CAD files (`toolhead_mount.scad`).
4. **Mission & System Prompt**:
   - `AppState.mission.prompt = ws.prompt` propagates to Omnibar placeholder and stage inspectors.

---

## 3. Caveats

1. **Reactive Tasks Delegation**: The detailed internal state transitions of the 5-status task lifecycle (`backlog`, `in_progress`, `agent_delegated`, `blocked`, `done`), fast inline creation on `Enter`, and delegation toggle (⚡/🤖) are explored concurrently by peer agent `explorer_m2_v2_2`. The workspace switcher integrates directly with `renderTasks()`.
2. **Offline Fallback**: In purely offline headless environments where `/api/workspaces` is not yet running, `localStorage` provides 100% functionality with graceful try/catch blocks and seed defaults, preventing any console errors.
3. **Keyboard Scope Guard**: The modal inputs must stop keydown event propagation for `Space` and `Esc` when typing, so they do not inadvertently trigger Safety Interceptor actions (`Approve` or `Abort`).

---

## 4. Conclusion

The recommended architecture solves all requirements of Milestone 2 regarding the Workspace Manager:
1. **Eradicates all CAD leftovers** from the Left Sidebar workspace card and dropdown.
2. **Implements the `[+ Neuer Workspace]` modal** with precise DESIGN.md tokens (`#0A0D12`, `#121824`, `1px solid #1E293B`, `#06B6D4`), validation, auto-slugging, and accessible triggers (`#btn-new-workspace` in Left Sidebar and inside dropdown).
3. **Embeds complete CRUD and switching methods in `AppState`** (`createWorkspace`, `switchWorkspace`, `loadWorkspaces`, `saveWorkspaces`).
4. **Guarantees dual persistence** with immediate `localStorage` caching and asynchronous `/api/workspaces` sync.
5. **Enables seamless hot-switching without page reload**, updating task metrics, file explorer, and agent context dynamically.

---

## 5. Verification Method

To independently verify the implementation once applied by the Worker:

### Automated Test Command
Run the headless Playwright browser test suite:
```powershell
uv run --with pytest,playwright pytest tests/test_browser_dom.py -k "workspace" -v
```
Full suite verification:
```powershell
uv run --with pytest,playwright pytest tests/test_browser_dom.py tests/test_api.py -v
```

### Manual / Browser Verification Checklist
1. Open `http://127.0.0.1:8765` in a browser.
2. Click `[+ Neuer Workspace]` button or open `#workspace-switcher-card` and click `+ Neuer Workspace`.
3. Verify the modal opens centered with dark backdrop blur (`rgba(10, 13, 18, 0.82)`) and card background (`#121824`).
4. Fill Name: `Data Pipeline Pro`, Prompt: `Analyze JSON records`, Directory: `workspace/data_pipe`.
5. Click `[+ Erstellen]`:
   - Modal closes.
   - Left Sidebar updates to `Active: Data Pipeline Pro` with `workspace/data_pipe`.
   - Dropdown displays `Data Pipeline Pro` with cyan checkmark `✓`.
   - File tree header updates to `📁 workspace/data_pipe/`.
6. Press `F5` (browser reload):
   - Workspace selection `Data Pipeline Pro` persists and restores automatically from `localStorage`.
7. Zero console errors throughout the entire flow.
