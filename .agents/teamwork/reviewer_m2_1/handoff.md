# Review & Adversarial Challenge Report: Milestone 2 — Global Shell & Left Sidebar

**Reviewer**: `teamwork_preview_reviewer` (reviewer_m2_1)  
**Parent Orchestrator**: `orchestrator_1` (`20ee9337-54d2-4ed7-a02f-42aad4232d45`)  
**Target Code**: `c:\Users\andym\gschwelli-ai\ui\dashboard\index.html`  
**Worker Under Review**: `teamwork_preview_worker` (`worker_m2`)  
**Timestamp**: 2026-10-28T16:35:00Z  

---

## Review Summary

**Verdict**: **REQUEST_CHANGES**

The worker has done high-quality, comprehensive work implementing the design system tokens, 3-column cockpit grid, Top Navigation Bar, Left Sidebar, AppState reactive engine, and WebSocket/REST synchronization. In addition, all automated tests in `tests/test_api.py` (16 passed) and `tests/test_browser_dom.py` (12 passed) pass cleanly with zero console errors.

However, an **adversarial DOM layout stress-test** revealed a **Major CSS Defect**: `#view-mission-control` has `display: grid;` unconditionally applied via an ID selector. Because ID selectors override class rules (`.view-pane { display: none; }`), `#view-mission-control` is **never hidden** when switching to `Knowledge Studio`, `Vision SOM`, or `Focus Chat`. Instead, Mission Control and the newly selected tab render side-by-side simultaneously (each squeezed to 720px width), violating R3 and Acceptance Criteria ("Switching between Mission Control, Knowledge Studio, Vision SOM, and Focus Chat renders dedicated, interactive views for each tab").

A straightforward 2-line CSS adjustment completely fixes this issue and has already been verified in Playwright.

---

## Findings

### [Major] Finding 1: CSS Specificity Bug on `#view-mission-control` Prevents Hiding When Switching Views

- **What**: When the user switches to `Knowledge Studio`, `Vision SOM`, or `Focus Chat`, the `#view-mission-control` container remains visible instead of being hidden with `display: none`. As a result, `#workspace-container` renders both views simultaneously side-by-side, each occupying 50% screen width (720px out of 1440px).
- **Where**: `ui/dashboard/index.html`, lines 287–293:
  ```css
  /* Mission Control 3-Column Cockpit Grid */
  #view-mission-control {
    display: grid;
    grid-template-columns: var(--left-sidebar-width) 1fr var(--right-sidebar-width);
    width: 100%;
    height: 100%;
    overflow: hidden;
  }
  ```
- **Why**: `#view-mission-control` has CSS specificity `(1, 0, 0)`, which overrides the class selector `.view-pane { display: none; }` (specificity `0, 1, 0`). When `renderModeView()` removes `.active-view` from `#view-mission-control`, the element still resolves to `display: grid;`.
- **Proof of Failure (Playwright Evaluation)**:
  ```
  Switch to Knowledge Studio:
  MC computed display: grid, bounding rect: { width: 720, height: 760 }
  KS computed display: flex, bounding rect: { width: 720, height: 760 }
  ```
- **Suggested Fix**: Update lines 287–296 so that `display: grid;` is only active when `#view-mission-control` has the `.active-view` class:
  ```css
  /* Mission Control 3-Column Cockpit Grid */
  #view-mission-control {
    grid-template-columns: var(--left-sidebar-width) 1fr var(--right-sidebar-width);
    width: 100%;
    height: 100%;
    overflow: hidden;
  }
  #view-mission-control.active-view {
    display: grid;
  }
  ```
  *Verification of Fix*: Confirmed via Playwright that with this rule, `#view-mission-control` resolves to `display: none`, and `#view-knowledge-studio` takes full 1440px width.

---

### [Minor] Finding 2: Unbound Event Handlers for `#kb-folder-toggle` and `#btn-settings`

- **What**: The folder collapse chevron `#kb-folder-toggle` and the settings cog button `#btn-settings` have no click event listeners attached.
- **Where**: `ui/dashboard/index.html`, lines 1500 (`#btn-settings`) and 1565 (`#kb-folder-toggle`).
- **Why**: While visual structure matches the mockup, clicking `#kb-folder-toggle` does not collapse/expand the `📁 fabrication/` file list, and clicking `#btn-settings` does not trigger visual feedback or open a drawer/modal.
- **Suggested Fix**: Attach a simple toggle listener for `#kb-folder-toggle` (toggling `#kb-file-list` display) and a placeholder drawer/alert for `#btn-settings` to enhance tactile prototype responsiveness.

---

### [Minor] Finding 3: Telemetry VRAM Decimal Formatting in `syncBackendState()`

- **What**: In `syncBackendState()`, raw float values from `/api/state` (`data.system.ram_used_gb`) are interpolated directly without rounding.
- **Where**: `ui/dashboard/index.html`, line 2417:
  ```javascript
  telemEl.textContent = `Ollama 7B • 42 tok/s • ${data.system.ram_used_gb || 4.2}GB VRAM`;
  ```
- **Why**: If the system reports e.g. `4.2891345`, the telemetry badge displays `4.2891345GB VRAM`, causing badge text overflow.
- **Suggested Fix**: Use `Number(data.system.ram_used_gb || 4.2).toFixed(1)`.

---

## Verified Claims

| Claim from Worker | Verification Method | Status | Notes |
|-------------------|---------------------|--------|-------|
| `test_api.py` passes 16/16 tests | `uv run --with pytest pytest tests/test_api.py -v` | **PASS** | 16 passed, 33 deprecation warnings in 10.64s |
| `test_browser_dom.py` passes 12/12 tests | `uv run --with pytest,playwright pytest tests/test_browser_dom.py -v` | **PASS** | 12 passed in 14.13s |
| Zero console errors on load | Playwright listener on `console` and `pageerror` | **PASS** | 0 errors captured |
| Interactive task checkboxes | Playwright `t3` click test | **PASS** | Counter dynamically updates from `2 / 4` to `3 / 4` |
| Project selector switcher | Playwright `#workspace-dropdown` test | **PASS** | Updates `Active: Robotic Pick & Place` in card title |
| Wake-Word mic toggle | Playwright `#btn-wake-word` test | **PASS** | Switches label to `Wake-Word Muted` and calls `/api/voice` |
| Knowledge Base file selection | Playwright `.kb-file-item` click test | **PASS** | Updates selection styling and logs to REPL |
| WebSocket and REST sync | Inspected `syncBackendState` and `initWebSocket` | **PASS** | Valid reconnect logic and fallback |
| Tab switching visual isolation | Playwright computed style inspection | **FAIL** | `#view-mission-control` fails to hide; splits screen with other views (Finding 1) |

---

## Adversarial Challenge Report

### Challenge Summary
**Overall Risk Assessment**: **MEDIUM**

The prototype is robust against console crashes, missing assets, and offline backend scenarios. However, CSS cascade bugs bypassed the automated Playwright suite because the test only asserted `len(page._page_errors) == 0` without checking bounding boxes or `is_visible()` assertions for inactive views.

### Challenges

#### [High] Challenge 1: Inactive View Pane Visibility Leakage
- **Assumption Challenged**: Calling `classList.remove('active-view')` hides the container.
- **Attack Scenario**: User clicks `Knowledge Studio`, `Vision SOM`, or `Focus Chat`.
- **Actual Behavior**: `#view-mission-control` remains rendered at `display: grid; width: 720px;`, creating a broken side-by-side layout.
- **Blast Radius**: High — destroys visual fidelity of all 3 non-Mission-Control screens.
- **Mitigation**: Move `display: grid;` to `#view-mission-control.active-view`.

#### [Low] Challenge 2: Direct File Protocol Execution (`file:///`)
- **Assumption Challenged**: App is always served over HTTP from `server/api.py`.
- **Attack Scenario**: User double-clicks `ui/dashboard/index.html` directly from disk.
- **Actual Behavior**: `initWebSocket()` gracefully catches the `ws:///ws` URL syntax exception without crashing, and REST calls fail silently into mock fallback mode.
- **Result**: **PASS** (Gracefully handled).

---

## 5-Component Handoff Report

### 1. Observation
1. **Source Inspection**:
   - `ui/dashboard/index.html:287-293`:
     ```css
     #view-mission-control {
       display: grid;
       grid-template-columns: var(--left-sidebar-width) 1fr var(--right-sidebar-width);
       width: 100%;
       height: 100%;
       overflow: hidden;
     }
     ```
   - `ui/dashboard/index.html:276-284`:
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
     ```
2. **Tool Commands and Results**:
   - `uv run --with pytest pytest tests/test_api.py -v`:
     `16 passed, 33 warnings in 10.64s`
   - `uv run --with pytest,playwright pytest tests/test_browser_dom.py -v`:
     `12 passed, 2 warnings in 14.13s`
   - Playwright DOM interrogation:
     ```python
     page.locator("button[data-mode='knowledge_studio']").click()
     mc_display = page.eval_on_selector('#view-mission-control', 'el => getComputedStyle(el).display')
     ks_display = page.eval_on_selector('#view-knowledge-studio', 'el => getComputedStyle(el).display')
     mc_rect = page.eval_on_selector('#view-mission-control', 'el => el.getBoundingClientRect()')
     ks_rect = page.eval_on_selector('#view-knowledge-studio', 'el => el.getBoundingClientRect()')
     ```
     *Output*:
     ```
     MC computed display: grid
     KS computed display: flex
     MC rect: {'x': 0, 'y': 48, 'width': 720, 'height': 760}
     KS rect: {'x': 720, 'y': 48, 'width': 720, 'height': 760}
     ```

### 2. Logic Chain
1. CSS specificity dictates that `#view-mission-control` (specificity 1, 0, 0) takes precedence over `.view-pane` (specificity 0, 1, 0).
2. Consequently, `.view-pane { display: none; }` does NOT hide `#view-mission-control` when `.active-view` is removed.
3. When `Knowledge Studio` is selected, both `#view-mission-control` (`display: grid`) and `#view-knowledge-studio` (`display: flex`) are rendered simultaneously as flex items inside `#workspace-container`.
4. This results in both panes splitting the viewport width to 720px each, visibly corrupting the 3-column cockpit layout and the secondary view.
5. Updating the CSS rule to `#view-mission-control.active-view { display: grid; }` ensures that when `#view-mission-control` lacks `.active-view`, it falls back to `.view-pane { display: none; }`.

### 3. Caveats
- Backend endpoints for M3–M5 are not yet fully implemented, but this is expected per project roadmap.
- No other unexamined areas; all M2 deliverables have been independently tested.

### 4. Conclusion
The implementation of Milestone 2 is 95% complete and visually stunning, but cannot be approved until Finding 1 is corrected. The verdict is **REQUEST_CHANGES**. The worker needs to make the 2-line CSS adjustment in `ui/dashboard/index.html` to guarantee that inactive view panes are properly hidden.

### 5. Verification Method
1. In `ui/dashboard/index.html`, modify lines 287–296:
   ```css
   #view-mission-control {
     grid-template-columns: var(--left-sidebar-width) 1fr var(--right-sidebar-width);
     width: 100%;
     height: 100%;
     overflow: hidden;
   }
   #view-mission-control.active-view {
     display: grid;
   }
   ```
2. Verify with Playwright:
   ```powershell
   uv run --with playwright python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(headless=True); page = b.new_page(viewport={'width': 1440, 'height': 900}); page.goto('file:///c:/Users/andym/gschwelli-ai/ui/dashboard/index.html'); page.locator('button[data-mode=\'knowledge_studio\']').click(); assert page.eval_on_selector('#view-mission-control', 'el => getComputedStyle(el).display') == 'none'; assert page.eval_on_selector('#view-knowledge-studio', 'el => el.getBoundingClientRect().width') == 1440; b.close(); p.stop(); print('FIX VERIFIED!')"
   ```
3. Run test suites:
   ```powershell
   uv run --with pytest pytest tests/test_api.py -v
   uv run --with pytest,playwright pytest tests/test_browser_dom.py -v
   ```
   Both must pass with 0 failures and 0 console errors.
