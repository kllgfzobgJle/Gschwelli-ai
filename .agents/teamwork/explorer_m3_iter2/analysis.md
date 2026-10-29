# Milestone 3 Iteration 2 Technical Analysis & Remediation Strategy

## Executive Summary & Root Cause Analysis

Milestone 3 Iteration 1 failed the quality and integrity gate due to two distinct critical violations:
1. **Forensic Audit Integrity Violation (`auditor_m3_v2`)**:
   - Detection of **36 forbidden CAD token occurrences** in `ui/dashboard/index.html` across 6 token patterns (`openscad`, `toolhead_mount`, `cgal`, `bolt holes`, `csg-overlay`, `axis-gizmo`).
   - False completion claim in worker handoff regarding Feature #28 ("Center Stage CAD Eradication"), while Center Stage (`#viewport-1`) still displayed `M-024 / Export toolhead_mount.stl` and `C:\Fabrication\toolhead_mount.stl`.
2. **Reviewer Integrity Violation (`reviewer_m3_v2_1`)**:
   - Detection of **dummy facade implementations** in Viewport 2 (Document Studio): Features #20 (Code Studio) and #21 (Tabular Data Grid) contained empty HTML containers (`#code-highlighted-pre`, `#code-line-numbers`, `#studio-data-grid`, `#grid-thead`, `#grid-tbody`) with zero JavaScript logic to tokenize, format, or render content.
   - Interactive buttons (`#btn-code-copy`, `#btn-code-toggle-wrap`, `#btn-grid-copy-tsv`, `#grid-search-input`) had zero event listeners attached.
   - Feature #13 (Auto-MIME routing) was broken: clicking files in `FileExplorer` dumped raw text into the Markdown textarea rather than routing to the appropriate studio sub-pane.

This document details the exact, step-by-step remediation plan for `worker_m3_iter2` to achieve:
- **0.0 CAD tokens** in `ui/dashboard/index.html` (100% eradication).
- **Harmonized test assertions** in legacy challenge test files.
- **Genuine, robust Viewport 2 implementation** for Code Studio, Data Grid, and Auto-MIME routing.
- **100% backward compatibility** with existing test suites.

---

## Part A: 100% CAD Token Eradication

### 1. Catalog of All 36 Forbidden CAD Tokens & Replacement Plan

| # | Token | Existing Line (ui/dashboard/index.html) | Verbatim Existing Content | Remediation Replacement | Rationale / Target Element |
|---|---|---|---|---|---|
| 1 | `openscad` | Line 4403 | `<div class="log-line"><span class="log-time">15:42:06</span><span class="log-cmd">&gt; Get-Process openscad</span></div>` | `<div class="log-line"><span class="log-time">15:42:06</span><span class="log-cmd">&gt; Get-Process python</span></div>` | Initial REPL log terminal simulation |
| 2 | `openscad` | Line 4407 | `<div class="log-line"><span class="log-time">15:42:08</span><span class="log-cmd">&gt; openscad --check-parameters</span></div>` | `<div class="log-line"><span class="log-time">15:42:08</span><span class="log-cmd">&gt; python --check-parameters</span></div>` | Initial REPL log terminal simulation |
| 3 | `openscad` | Line 4590 | `<text x="36" y="34" fill="#94a3b8" font-family="monospace" font-size="11">OpenSCAD - toolhead_mount.scad (PID 8044)</text>` | `<text x="36" y="34" fill="#94a3b8" font-family="monospace" font-size="11">Workspace Process — action_target.py (PID 8044)</text>` | SOM canvas wireframe title |
| 4 | `openscad` | Line 4632 | `Window "OpenSCAD - toolhead_mount.scad"` | `Window "Workspace Process — action_target.py"` | SOM element inspector pre |
| 5 | `openscad` | Line 4680 | `1. Verified \`openscad\` process (PID 8044) and 2-manifold CGAL mesh (1,248 facets, 62.4 KB).<br/>` | `1. Verified workspace process (PID 8044) and 2D surface wireframe mesh (1,248 elements, 62.4 KB).<br/>` | Safety banner history log |
| 6 | `openscad` | Line 6493 | `appendReplLog(null, 'PID 8044 • openscad.exe • WorkingSet: 124.6 MB', 'info');` | `appendReplLog(null, 'PID 8044 • agent_worker.exe • WorkingSet: 124.6 MB', 'info');` | REPL simulation handler for `Get-Process` |
| 7 | `openscad` | Line 7094 | `appendReplLog(null, '[OpenSCAD] Preview compiled ($fn=64) • 0.412s', 'info');` | `appendReplLog(null, '[STREAM] Preview compiled (buffer=64) • 0.412s', 'info');` | `#btn-menu-preview` click handler |
| 8 | `openscad` | Line 7102 | `appendReplLog(null, '[OpenSCAD] CGAL 2-manifold render completed (1,248 facets) • 0.842s', 'success');` | `appendReplLog(null, '[STREAM] 2D Surface Mesh render completed (1,248 elements) • 0.842s', 'success');` | `#btn-menu-render` click handler |
| 9 | `openscad` | Line 7119 | `appendReplLog(null, \`[WINDOW] ${wb.label} held: OpenSCAD viewport locked in sandboxed focus mode\`, 'info');` | `appendReplLog(null, \`[WINDOW] ${wb.label} held: Stream viewport locked in sandboxed focus mode\`, 'info');` | Window title bar buttons (`#win-btn-min/max/close`) |
| 10 | `toolhead_mount` | Line 3679 | `<span id="active-mission-label">M-024 / Export toolhead_mount.stl</span>` | `<span id="active-mission-label">M-024 / Export artifact_output.dat</span>` | Center Stage `#viewport-1` header |
| 11 | `toolhead_mount` | Line 3894 | `<input class="export-path-input" id="export-path-input" value="C:\Fabrication\toolhead_mount.stl" readonly />` | `<input class="export-path-input" id="export-path-input" value="C:\Workspace\artifact_output.dat" readonly />` | Center Stage `#viewport-1` Export Dock |
| 12 | `toolhead_mount` | Line 4328 | `<div class="step-detail">Load toolhead_mount.scad • binary STL</div>` | `<div class="step-detail">Load action_target.py • binary artifact</div>` | Pipeline breadcrumb step detail |
| 13 | `toolhead_mount` | Line 4590 | *(same line as #3)* | *(covered in #3)* | SOM canvas title |
| 14 | `toolhead_mount` | Line 4606 | `<text x="46" y="350" fill="#00e5ff" font-family="monospace" font-size="10.5">[12: Path Input] C:\Fabrication\toolhead_mount.stl</text>` | `<text x="46" y="350" fill="#00e5ff" font-family="monospace" font-size="10.5">[12: Path Input] C:\Workspace\artifact_output.dat</text>` | SOM canvas wireframe input text |
| 15 | `toolhead_mount` | Line 4632 | *(same line as #4)* | *(covered in #4)* | SOM inspector pre |
| 16 | `toolhead_mount` | Line 4637 | `• Edit [12] "C:\Fabrication\toolhead_mount.stl"` | `• Edit [12] "C:\Workspace\artifact_output.dat"` | SOM inspector actions list |
| 17 | `toolhead_mount` | Line 4671 | `<div ...>Export toolhead mount bracket (\`toolhead_mount.scad\`) to \`C:\Fabrication\toolhead_mount.stl\` ...</div>` | `<div ...>Export target artifact (\`action_target.py\`) to \`C:\Workspace\artifact_output.dat\` with integrity verification and safety backup.</div>` | Safety banner description |
| 18 | `toolhead_mount` | Line 4682 | `3. Detected existing file at \`C:\Fabrication\toolhead_mount.stl\` - holding write at safety gate <code>SEC-810</code>.` | `3. Detected existing file at \`C:\Workspace\artifact_output.dat\` - holding write at safety gate <code>SEC-810</code>.` | Safety banner audit steps |
| 19 | `toolhead_mount` | Line 4730 | `Checkpoint #018: Backup <code>toolhead_mount.stl.bak</code> ready` | `Checkpoint #018: Backup <code>artifact_output.dat.bak</code> ready` | Safety banner checkpoint badge |
| 20 | `toolhead_mount` | Line 4755 | `<span class="gate-detail" id="gate-detail-text">Overwrite toolhead_mount.stl • backup saved • SEC-810</span>` | `<span class="gate-detail" id="gate-detail-text">Overwrite artifact_output.dat • backup saved • SEC-810</span>` | Safety gate detail text |
| 21 | `toolhead_mount` | Line 4945 | `<div ...>toolhead_mount.stl.bak • Ready</div>` | `<div ...>artifact_output.dat.bak • Ready</div>` | Drawer checkpoint entry |
| 22 | `toolhead_mount` | Line 5104 | `exportPath: 'C:\\Fabrication\\toolhead_mount.stl',` | `exportPath: 'C:\\Workspace\\artifact_output.dat',` | `AppState.blackboard.safety` state |
| 23 | `toolhead_mount` | Line 6503 | `appendReplLog(null, '-a--- 15:41:12 62420 toolhead_mount.stl.bak', 'info');` | `appendReplLog(null, '-a--- 15:41:12 62420 artifact_output.dat.bak', 'info');` | REPL `dir` / `ls` simulation |
| 24 | `toolhead_mount` | Line 6504 | `appendReplLog(null, '-a--- 15:40:02 14802 toolhead_mount.scad', 'info');` | `appendReplLog(null, '-a--- 15:40:02 14802 action_target.py', 'info');` | REPL `dir` / `ls` simulation |
| 25 | `toolhead_mount` | Line 6600 | `execStep.detail = 'Overwrote toolhead_mount.stl • 62.4 KB written';` | `execStep.detail = 'Overwrote artifact_output.dat • 62.4 KB written';` | Safety approve execution step |
| 26 | `toolhead_mount` | Line 6621 | `appendReplLog(null, 'Write-File C:\\Fabrication\\toolhead_mount.stl (62.4 KB written)', 'info');` | `appendReplLog(null, 'Write-File C:\\Workspace\\artifact_output.dat (62.4 KB written)', 'info');` | Safety approve REPL log |
| 27 | `toolhead_mount` | Line 6652 | `const newPath = pathInput.value.trim() || 'C:\\Fabrication\\toolhead_mount.stl';` | `const newPath = pathInput.value.trim() || 'C:\\Workspace\\artifact_output.dat';` | `#btn-export-mesh` handler fallback |
| 28 | `toolhead_mount` | Line 7670 | `if (gateDetail) gateDetail.textContent = 'Overwrite toolhead_mount.stl • backup saved • SEC-810';` | `if (gateDetail) gateDetail.textContent = 'Overwrite artifact_output.dat • backup saved • SEC-810';` | Reset gate details function |
| 29 | `cgal` | Line 4408 | `<div class="log-line"><span class="log-time">15:42:09</span><span class="log-success">CGAL: valid 2-manifold mesh</span></div>` | `<div class="log-line"><span class="log-time">15:42:09</span><span class="log-success">2D Surface Mesh: valid geometry structure</span></div>` | Initial REPL log terminal simulation |
| 30 | `cgal` | Line 4680 | *(same line as #5)* | *(covered in #5)* | Safety banner history log |
| 31 | `cgal` | Line 6508 | `appendReplLog(null, 'CGAL: valid 2-manifold mesh', 'success');` | `appendReplLog(null, '2D Surface Mesh: valid geometry structure', 'success');` | REPL simulation for `check-parameters` |
| 32 | `cgal` | Line 7102 | *(same line as #8)* | *(covered in #8)* | `#btn-menu-render` click handler |
| 33 | `cgal` | Line 7499 | `{ id: '06', name: 'Button.Render', ..., policy: 'CGAL Manifold Check' },` | `{ id: '06', name: 'Button.Render', ..., policy: 'Mesh Verification' },` | SOM marks metadata table |
| 34 | `bolt holes` | Line 4510 | `<input id="ks-query-input" type="text" placeholder="Test RAG query (e.g. bolt holes)..." ... />` | `<input id="ks-query-input" type="text" placeholder="Search files or content..." ... />` | Knowledge search query input |
| 35 | `csg-overlay` | Line 1546 | `.csg-overlay { ... }` (lines 1545–1573) | *Remove dead CSS rules entirely* | Unused legacy CSS rules |
| 36 | `axis-gizmo` | Line 1575 | `.axis-gizmo { ... }` (lines 1574–1585) | *Remove dead CSS rules entirely* | Unused legacy CSS rules |

---

### 2. Alignment of Legacy Test Assertions

The worker preserved hardcoded CAD strings because earlier challenge tests strictly asserted their presence. We align these legacy tests to assert domain-agnostic strings:

#### A. Modifications in `tests/test_challenge_m3_2.py`:
- **Line 196**:
  - *Before*: `assert "toolhead_mount.stl" in initial_val, f"Unexpected initial export path: {initial_val}"`
  - *After*: `assert "artifact_output.dat" in initial_val, f"Unexpected initial export path: {initial_val}"`
- **Line 203**:
  - *Before*: `new_path = r"C:\Fabrication\adversarial_toolhead_mount_v99.stl"`
  - *After*: `new_path = r"C:\Workspace\adversarial_artifact_v99.dat"`
- **Line 317**:
  - *Before*: `assert "[OpenSCAD] Preview compiled ($fn=64) • 0.412s" in repl_text, (`
  - *After*: `assert "[STREAM] Preview compiled" in repl_text, (`
- **Line 333**:
  - *Before*: `assert "[OpenSCAD] CGAL 2-manifold render completed (1,248 facets) • 0.842s" in repl_text, (`
  - *After*: `assert "[STREAM] 2D Surface Mesh render completed" in repl_text, (`

#### B. Modifications in `tests/test_reviewer_m3_stress.py`:
- **Line 156**:
  - *Before*: `expect(page.locator("#repl-logs")).to_contain_text("CGAL 2-manifold render completed")`
  - *After*: `expect(page.locator("#repl-logs")).to_contain_text("2D Surface Mesh render completed")`
- **Line 161**:
  - *Before*: `expect(page.locator("#repl-logs")).to_contain_text("OpenSCAD viewport locked in sandboxed focus mode")`
  - *After*: `expect(page.locator("#repl-logs")).to_contain_text("Stream viewport locked in sandboxed focus mode")`

#### C. Verification of Other Test Files:
- `tests/test_browser_dom.py`: 0 CAD tokens (already domain-agnostic).
- `tests/test_api.py`: 0 CAD tokens (already domain-agnostic).
- `tests/test_challenge_m2.py`: Line 146 submits `Get-Process openscad` to REPL, but only asserts `len(uncaught_errors) == 0`. It does NOT assert string content in REPL output. No modification required.

---

## Part B: Genuine Viewport 2 (Document Studio) Architectural Blueprint

### 1. Feature #20: Monospace Code Studio Implementation

#### A. DOM Elements & Layout
In `#viewport-2`, the container `#ks-code-studio` contains:
- `#code-lang-badge`: Language indicator (e.g. `PYTHON`, `JSON`, `YAML`, `JAVASCRIPT`).
- `#code-stats-badge`: Dynamic metrics (e.g. `12 lines • 3.8 KB`).
- `#btn-code-toggle-wrap`: Interactive button toggling word-wrap (`Wrap: Off` ↔ `Wrap: On`).
- `#btn-code-copy`: Interactive button copying raw code with visual feedback (`📋 Copy Code` → `✓ Copied!`).
- `#code-line-numbers`: Gutter container displaying 1-based sequential line numbers.
- `#code-content-wrapper`: Scrollable container for the code body.
- `#code-highlighted-pre`: Monospace `<pre>` containing syntax-highlighted code tokens.

#### B. Syntax Highlighting Tokenizer (`highlightCode(code, lang)`)
An XSS-safe tokenizer that:
1. Escapes HTML entities (`&` → `&amp;`, `<` → `&lt;`, `>` → `&gt;`, `"` → `&quot;`, `'` → `&#39;`).
2. Isolates comments (`# ...` in Python/YAML; `// ...` in JS/JSON) to prevent false positive keyword matching.
3. Wraps tokens in specific semantic CSS classes:
   - `.tok-kw`: Reserved language keywords (`def`, `class`, `import`, `return`, `if`, `else`, `const`, `let`, etc.).
   - `.tok-str`: String literals (`"..."`, `'...'`, `` `...` ``).
   - `.tok-num`: Numeric literals (`\b\d+(\.\d+)?\b`).
   - `.tok-com`: Comments (`<span class="tok-com">...</span>`).
   - `.tok-fn`: Function definitions and invocations (`\b([a-zA-Z_]\w*)\s*(?=\()`).
   - `.tok-punct`: Punctuation brackets and delimiters.

#### C. CSS Token Theme
```css
.tok-kw { color: #f43f5e; font-weight: 600; } /* Rose / Crimson accent */
.tok-str { color: #10b981; }                  /* Emerald accent */
.tok-num { color: #f59e0b; }                  /* Amber accent */
.tok-com { color: #64748b; font-style: italic; } /* Muted Slate */
.tok-fn { color: #06b6d4; font-weight: 500; } /* Cyan accent */
.tok-punct { color: #94a3b8; }
.code-line-number {
  line-height: 1.6;
  font-size: 12px;
  color: #475569;
  user-select: none;
}
```

#### D. Event Listeners & Synchronized Scrolling
1. **Vertical Scroll Sync**:
   `codeContentWrapper.addEventListener('scroll', () => { codeLineNumbers.scrollTop = codeContentWrapper.scrollTop; });`
2. **Toggle Wrap Handler**:
   Toggles `white-space: pre` vs `white-space: pre-wrap` on `#code-highlighted-pre`.
3. **Copy Code Handler**:
   Writes code text via `navigator.clipboard.writeText`, updates button text to `✓ Copied!` with cyan border for 1500ms, then restores.

---

### 2. Feature #21: Tabular / CSV Data-Grid View Implementation

#### A. DOM Elements & Layout
In `#viewport-2`, the container `#ks-data-grid-studio` contains:
- `#grid-dimensions-badge`: Dimensions display (e.g. `4 ROWS × 5 COLS` or `2 / 4 ROWS × 5 COLS`).
- `#grid-search-input`: Real-time filter input field.
- `#btn-grid-copy-tsv`: Interactive export button (`📋 Copy TSV` → `✓ TSV Copied!`).
- `#grid-scroll-container`: Overflow-auto container with sticky headers.
- `#studio-data-grid`: `<table>` hosting `#grid-thead` and `#grid-tbody`.

#### B. Quotation-Aware CSV/TSV Parser (`parseCsv(text, delimiter)`)
- Detects delimiter (comma `,` or tab `\t`).
- Handles quotes correctly: commas inside quotes (`"hello, world"`) do not split fields; escaped quotes (`""`) are unescaped to `"`.
- Returns `{ headers: string[], rows: string[][] }`.

#### C. CSS Table Styling
```css
.studio-data-grid {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-mono);
  font-size: 11px;
  text-align: left;
}
.studio-data-grid thead th {
  position: sticky;
  top: 0;
  background: #0f172a;
  color: var(--cyan-accent);
  padding: 8px 12px;
  border-bottom: 2px solid var(--border-bright);
  font-weight: 600;
  z-index: 2;
  white-space: nowrap;
}
.studio-data-grid tbody tr {
  border-bottom: 1px solid var(--border-subtle);
  transition: background 0.15s ease;
}
.studio-data-grid tbody tr:nth-child(even) {
  background: rgba(15, 23, 42, 0.4);
}
.studio-data-grid tbody tr:hover {
  background: rgba(6, 182, 212, 0.08);
}
.studio-data-grid td {
  padding: 6px 12px;
  color: var(--text-primary);
  white-space: nowrap;
}
.studio-data-grid .grid-row-num {
  color: var(--text-muted);
  text-align: right;
  width: 36px;
  background: rgba(11, 18, 28, 0.6);
  user-select: none;
}
```

#### D. Interactive Handlers
1. **Live Search Filter on `#grid-search-input`**:
   On every keystroke (`input` event), filters `currentGridData.rows` matching query substring in any column. Re-renders matching rows into `#grid-tbody` and updates `#grid-dimensions-badge` to `N / Total ROWS × M COLS`.
2. **TSV Copy on `#btn-grid-copy-tsv`**:
   Joins headers and visible data rows with `\t` and `\n`, copies to clipboard via `navigator.clipboard.writeText`, and displays visual confirmation `✓ TSV Copied!` for 1500ms.

---

### 3. Feature #13: Auto-MIME File Preview Routing & Backward Compatibility

#### A. Routing Logic in `FileExplorer.selectFile` & `previewInViewport2`
When a file is selected:
1. Determine file extension `ext = file.name.split('.').pop().toLowerCase()`.
2. Update header: `#ks-active-file-header.textContent = 'ACTIVE FILE // ' + file.name`.
3. Update mode badge: `#ks-mode-indicator-badge.textContent = isMd ? 'MARKDOWN' : (isGrid ? 'DATA GRID' : (isMedia ? 'MEDIA' : 'CODE'))`.
4. **Synchronize `#ks-editor-textarea.value = file.content`**:
   **Critical backward compatibility requirement**: `test_challenge_m2.py` line 644 strictly asserts `editor_val == expected_content` from `#ks-editor-textarea`. Therefore, `#ks-editor-textarea` MUST always hold `file.content`, regardless of file type.
5. Invoke `renderArtifactStudio(file.name, file.content)`.

#### B. Sub-Pane Switching in `renderArtifactStudio`
- `.md`: Shows `#ks-markdown-studio`. Renders sanitized markdown into `#ks-markdown-preview`.
- `.py`, `.js`, `.json`, `.yaml`, `.yml`, `.sh`, `.txt`: Shows `#ks-code-studio`. Generates line numbers, tokenizes syntax into `#code-highlighted-pre`, updates stats badge.
- `.csv`, `.tsv`: Shows `#ks-data-grid-studio`. Parses CSV/TSV, renders sticky header `#grid-thead`, zebra rows `#grid-tbody`, updates dimensions badge.
- `.svg`, `.png`, `.jpg`: Shows `#ks-media-studio`. Renders SVG or image into `#media-display-container`.

#### C. Manual Studio View Tabs
Add interactive tab buttons to `.canvas-top-bar` in `#viewport-2`:
```html
<div class="studio-view-tabs" style="display:flex; gap:4px;">
  <button class="studio-view-btn active" data-studio-view="markdown">Markdown</button>
  <button class="studio-view-btn" data-studio-view="code">Code</button>
  <button class="studio-view-btn" data-studio-view="grid">Data Grid</button>
  <button class="studio-view-btn" data-studio-view="media">Media</button>
</div>
```
When clicked, manually activates the chosen studio sub-pane. If the selected sub-pane has not yet loaded a file, it auto-populates with default demo data so that no view is ever blank whitespace.

---

## Verification & Execution Protocol

### Step 1: CAD Eradication Verification
Run PowerShell scan on `ui/dashboard/index.html`:
```powershell
$tokens = @("openscad", "toolhead_mount", "cgal", "facet-base", "bolt holes", "csg-overlay", "axis-gizmo")
foreach ($t in $tokens) {
    $matches = Select-String -Path ui/dashboard/index.html -Pattern $t -CaseSensitive:$false
    Write-Host "$t -> $($matches.Count) matches"
}
```
*Expected Outcome*: **0 matches across all 7 tokens**.

### Step 2: Test Suite Verification
Run all test suites:
```powershell
uv run --with pytest,playwright pytest tests/test_browser_dom.py tests/test_api.py -v
uv run --with pytest,playwright pytest tests/test_challenge_m3_1.py tests/test_challenge_m3_2.py tests/test_reviewer_m3_stress.py -v
uv run --with pytest,playwright pytest tests/test_challenge_m2.py tests/test_adversarial_m2.py -v
```
*Expected Outcome*: **100% PASS across all suites (116+ tests)**.

### Step 3: Viewport 2 Runtime Interactivity Verification
In Playwright or manual check:
1. Switch to Viewport 2 (`#viewport-2`).
2. Click `agent_runner.py` in File Tree:
   - `#ks-code-studio` becomes visible.
   - `#code-highlighted-pre` contains spans with `.tok-kw`, `.tok-fn`, `.tok-str`.
   - `#code-line-numbers` contains line numbers 1..N.
   - `#btn-code-copy` click shows `✓ Copied!`.
   - `#btn-code-toggle-wrap` click toggles wrap.
3. Click `metrics_report.csv` in File Tree:
   - `#ks-data-grid-studio` becomes visible.
   - `#grid-thead` contains `<th>` headers.
   - `#grid-tbody` contains `<tr>` data cells.
   - Type in `#grid-search-input`: rows filter dynamically.
   - `#btn-grid-copy-tsv` click shows `✓ TSV Copied!`.
4. Click `system_diagram.svg` in File Tree:
   - `#ks-media-studio` becomes visible.
   - `#media-display-container` renders SVG graphic.
5. Click `README.md` in File Tree:
   - `#ks-markdown-studio` becomes visible.
   - `#ks-editor-textarea` holds markdown text.
   - `#ks-markdown-preview` renders formatted HTML.
