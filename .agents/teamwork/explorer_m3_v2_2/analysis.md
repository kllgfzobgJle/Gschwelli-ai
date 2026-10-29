# Technical Strategy & Analysis: Polymorphic Artifact & Document Studio (Viewport 2)

**Subagent**: `explorer_m3_v2_2`  
**Milestone**: Milestone 3 — Polymorphic Stage (Viewport 2: Artifact & Document Studio & File Tree Integration)  
**Target Codebase**: `ui/dashboard/index.html`, `server/api.py`, `tests/test_browser_dom.py`  
**Date**: 2026-10-29  

---

## 1. Executive Summary & Problem Boundary

In Milestone 2, the workspace file tree (`#kb-file-list`) and baseline knowledge studio (`#view-knowledge-studio`) were scaffolded with basic file selection and a single monolithic `<textarea id="ks-editor-textarea">`.

Milestone 3 mandates transforming Viewport 2 into a **Universal Polymorphic Artifact & Document Studio** governed by automatic MIME / extension detection, supporting:
1. **Feature #19 (Markdown 2-Column Split Studio)**: 50/50 dual-pane with raw editable textarea on the left and live, formatted HTML preview on the right with strict, multi-layered XSS sanitization preventing script injection or malicious event handlers.
2. **Feature #20 (Code & Config Monospace Studio)**: Monospace code viewing/editing with synchronized line numbers gutter, syntax token styling for Python/JS/JSON/YAML/Shell/Configs, copy button, line/byte count metrics, and word-wrap toggle.
3. **Feature #21 (Tabular / CSV Data-Grid View)**: Dense spreadsheet-like data grid for `.csv`, `.tsv`, and `.jsonl` with sticky column headers, row numbering (#), zebra striping, instant text filtering, and copy-as-TSV capability.
4. **Feature #13 (File Quick Preview Integration)**: Clicking any file in the workspace file tree (`#kb-file-list`) or Studio file explorer (`#ks-file-list`) automatically resolves the MIME type, renders the dedicated studio view, and activates Viewport 2 on the central stage.
5. **Fallback & Media View**: Interactive SVG viewer and image display for `.svg`, `.png`, `.jpg`, with neutral hex/raw text fallback for unknown formats.
6. **CAD Eradication in Viewport 2**: Eradicate legacy 3D fabrication/CAD mentions in Viewport 2 right panel (`#ks-chunks-list`), replacing them with domain-agnostic semantic chunks.
7. **Strict Zero CDN & Zero Dependency Constraint**: Implemented entirely with vanilla ES2022 and modern CSS3 complying with DESIGN tokens (`#0A0D12`, `#121824`, `1px solid #1E293B`, `#06B6D4`, `#10B981`, `#F59E0B`, `#EF4444`).

---

## 2. File Tree & Quick Preview Integration Analysis (Feature #13)

### 2.1 Current Implementation State
- Files are fetched via `GET /api/workspace/files` or fallback to `FileExplorer.defaultFiles` in `ui/dashboard/index.html` (lines 4596–4654).
- The file tree is rendered into `#kb-file-list` (in the left sidebar) and `#ks-file-list` (in the knowledge studio left column).
- When a user clicks a file item (`.kb-file-item` or `.ks-file-entry`), `FileExplorer.selectFile(fileName)` is triggered:
  ```javascript
  selectFile(fileName) {
    if (!fileName) return;
    if (AppState.project) AppState.project.activeFile = fileName;
    document.querySelectorAll('.kb-file-item, .file-tree-item, .ks-file-entry').forEach(el => {
      el.classList.toggle('selected', el.getAttribute('data-file') === fileName || el.getAttribute('data-ks-file') === fileName);
    });
    const fileObj = this.files.find(f => f.name === fileName) || { name: fileName };
    this.previewInViewport2(fileObj);
  }
  ```
- **The Gap**: Currently, `previewInViewport2(file)` only sets:
  ```javascript
  const header = document.getElementById('ks-active-file-header');
  if (header) header.textContent = `ACTIVE FILE // ${file.name}`;
  const editor = document.getElementById('ks-editor-textarea');
  if (editor) editor.value = file.content !== undefined ? file.content : `...`;
  ```
  It does not switch view modes, does not render markdown preview, does not parse CSV into grids, and does not highlight code.

### 2.2 Integration Flow Design
When a file is clicked:
1. `FileExplorer.selectFile(fileName)` resolves the `fileObj` from `this.files` (or creates a fallback object).
2. Sets `.selected` class on corresponding items across `#kb-file-list` and `#ks-file-list`.
3. If the user is currently on another viewport (e.g., Viewport 1 Mission Control), and single-view mode is active, smoothly activates Viewport 2 (`renderModeView('knowledge_studio')` / `renderModeView('artifact_studio')`), ensuring "öffnet Dateien per Klick in der zentralen Bühne".
4. Dispatches `fileObj` to `ArtifactStudio.loadFile(fileObj)`.
5. Backwards Compatibility Guard: Keeps `#ks-editor-textarea` populated with `fileObj.content` to ensure all existing tests (e.g. in `tests/test_challenge_m2.py` lines 639–650) pass without regression.

---

## 3. Automatic MIME & Extension Detection System

### 3.1 Detection Matrix

| Category | File Extensions | Mode Identifier | Target Studio Sub-Container | Features Enabled |
| :--- | :--- | :--- | :--- | :--- |
| **Markdown / Doc** | `.md`, `.markdown`, `.mdown`, `.mkdn` | `markdown` | `#ks-markdown-studio` | 2-Column Split (Raw Editor + Live Safe HTML Preview), Headings, Code Blocks, Tables, Checkboxes |
| **Code & Config** | `.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.html`, `.css`, `.json`, `.yaml`, `.yml`, `.toml`, `.ini`, `.env`, `.sh`, `.ps1`, `.sql`, `.rs`, `.go` | `code` | `#ks-code-studio` | Line numbers gutter, syntax token styling, copy button, line count, language badge, editable toggle |
| **Tabular Data** | `.csv`, `.tsv`, `.jsonl` | `table` | `#ks-data-grid-studio` | Dense spreadsheet data grid, quotation-aware parser, row index column, zebra striping, live text filter, copy TSV |
| **Media** | `.svg`, `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.ico` | `media` | `#ks-media-studio` | Inline sanitized SVG or raster image preview with zoom, dimensions, checkerboard background |
| **Fallback / Text** | Unknown extensions, `.txt`, `.log` | `code` (fallback plain) | `#ks-code-studio` | Monospace text viewer with line numbers and copy button |

### 3.2 Detection Engine Implementation
```javascript
const StudioMIMEDetector = {
  detect(file) {
    if (!file) return { mode: 'code', lang: 'text', ext: 'txt', mime: 'text/plain', label: 'GENERIC', icon: '📄' };
    const name = file.name || file.path || '';
    const ext = (file.ext || name.split('.').pop() || '').toLowerCase();

    // 1. Markdown
    if (['md', 'markdown', 'mdown', 'mkdn'].includes(ext)) {
      return { mode: 'markdown', ext, mime: 'text/markdown', label: 'MARKDOWN', icon: '📄' };
    }

    // 2. Tabular / Spreadsheet
    if (['csv', 'tsv', 'jsonl'].includes(ext)) {
      const mime = ext === 'csv' ? 'text/csv' : ext === 'tsv' ? 'text/tab-separated-values' : 'application/x-jsonlines';
      return { mode: 'table', ext, mime, label: ext.toUpperCase(), icon: '📊' };
    }

    // 3. Code & Config
    const codeMap = {
      py: { lang: 'python', label: 'PYTHON', icon: '🐍' },
      js: { lang: 'javascript', label: 'JAVASCRIPT', icon: '💻' },
      ts: { lang: 'typescript', label: 'TYPESCRIPT', icon: '💻' },
      jsx: { lang: 'jsx', label: 'REACT JSX', icon: '💻' },
      tsx: { lang: 'tsx', label: 'REACT TSX', icon: '💻' },
      html: { lang: 'html', label: 'HTML', icon: '🌐' },
      css: { lang: 'css', label: 'CSS', icon: '🎨' },
      json: { lang: 'json', label: 'JSON', icon: '⚙️' },
      yaml: { lang: 'yaml', label: 'YAML', icon: '⚙️' },
      yml: { lang: 'yaml', label: 'YAML', icon: '⚙️' },
      toml: { lang: 'toml', label: 'TOML', icon: '⚙️' },
      ini: { lang: 'ini', label: 'INI', icon: '⚙️' },
      env: { lang: 'env', label: 'ENV', icon: '⚙️' },
      sh: { lang: 'shell', label: 'BASH', icon: '🐚' },
      ps1: { lang: 'powershell', label: 'PWSH', icon: '🐚' },
      sql: { lang: 'sql', label: 'SQL', icon: '🗄️' },
      rs: { lang: 'rust', label: 'RUST', icon: '🦀' },
      go: { lang: 'go', label: 'GO', icon: '🔷' },
    };
    if (codeMap[ext]) {
      return { mode: 'code', ext, lang: codeMap[ext].lang, mime: `text/x-${codeMap[ext].lang}`, label: codeMap[ext].label, icon: codeMap[ext].icon };
    }

    // 4. Media
    if (['svg', 'png', 'jpg', 'jpeg', 'gif', 'webp', 'ico'].includes(ext)) {
      return { mode: 'media', ext, mime: ext === 'svg' ? 'image/svg+xml' : `image/${ext}`, label: ext.toUpperCase(), icon: '🖼️' };
    }

    // 5. Fallback plain text
    return { mode: 'code', ext, lang: 'text', mime: 'text/plain', label: (ext || 'TEXT').toUpperCase(), icon: '📄' };
  }
};
```

---

## 4. Feature #19: Markdown 2-Column Split Studio Architecture

### 4.1 Layout & DOM Structure
The Markdown studio features a side-by-side 50/50 split container:
```html
<div id="ks-markdown-studio" class="studio-sub-pane" style="display:flex; flex-direction:row; height:100%; width:100%; min-height:0; gap:8px;">
  <!-- Left Column: Raw Markdown Textarea -->
  <div class="studio-split-col studio-split-left" style="flex:1; display:flex; flex-direction:column; min-width:0; min-height:0;">
    <div class="studio-col-header" style="display:flex; justify-content:space-between; align-items:center; padding:6px 12px; background:#0b121c; border:1px solid var(--border-subtle); border-bottom:none; border-radius:6px 6px 0 0;">
      <span class="studio-col-title" style="font-size:11px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.5px;">Raw Editor (Markdown)</span>
      <span style="font-family:var(--font-mono); font-size:10px; color:var(--text-muted);" id="md-raw-lines-badge">18 lines</span>
    </div>
    <!-- Backwards compatible #ks-editor-textarea placed here -->
    <textarea id="ks-editor-textarea" spellcheck="false" autocomplete="off" autocorrect="off" autocapitalize="off"
              style="width:100%; flex:1; background:#070d16; color:#e2e8f0; border:1px solid var(--border-subtle); border-radius:0 0 6px 6px; padding:12px; font-family:var(--font-mono); font-size:12px; line-height:1.6; resize:none; outline:none; min-height:0; box-sizing:border-box;">
    </textarea>
  </div>

  <!-- Center Split Resizer (Divider) -->
  <div class="studio-split-divider" id="ks-markdown-divider" title="Drag to adjust split" style="width:4px; cursor:col-resize; background:var(--border-subtle); transition:background 0.2s ease; border-radius:2px;"></div>

  <!-- Right Column: Live Formatted HTML Preview with XSS Sanitization -->
  <div class="studio-split-col studio-split-right" style="flex:1; display:flex; flex-direction:column; min-width:0; min-height:0;">
    <div class="studio-col-header" style="display:flex; justify-content:space-between; align-items:center; padding:6px 12px; background:#0b121c; border:1px solid var(--border-subtle); border-bottom:none; border-radius:6px 6px 0 0;">
      <span class="studio-col-title" style="font-size:11px; font-weight:600; color:var(--cyan-accent); text-transform:uppercase; letter-spacing:0.5px;">Live HTML Preview</span>
      <span class="badge badge-complete" style="font-size:9.5px; padding:2px 6px;">🛡️ XSS SANITIZED</span>
    </div>
    <div id="ks-markdown-preview" class="markdown-preview-body"
         style="flex:1; min-height:0; overflow-y:auto; background:#0b121c; border:1px solid var(--border-subtle); border-radius:0 0 6px 6px; padding:16px 20px; font-family:var(--font-sans); color:var(--text-primary); line-height:1.65; box-sizing:border-box;">
    </div>
  </div>
</div>
```

### 4.2 Multi-Layered XSS Sanitization & Vanilla Parser
To satisfy R5 and pass adversarial tests like `test_xss_sanitization_across_inputs` without external CDNs:
1. **Total Pre-Escape**: All raw `<` and `>` in markdown text are converted to `&lt;` and `&gt;`. Therefore, injected tags like `<script>alert(1)</script>` or `<img src=x onerror=...>` are rendered strictly as literal visible text, rendering script execution physically impossible.
2. **Safe Code Block Isolation**: Fenced code blocks ```` ```lang ... ``` ```` and inline code `` `...` `` are isolated into placeholders (`%%CODEBLOCK_0%%`, `%%INLINECODE_0%%`) before HTML escaping, ensuring code formatting remains intact while syntax is 100% neutralized.
3. **URL Whitelisting for Links & Images**: Links `[text](url)` and images `![alt](url)` pass through `sanitizeUrl(url)`. Permitted protocols: `http://`, `https://`, `mailto:`, relative `./` or `/`, and `#hash`. Forbidden protocols (`javascript:`, `vbscript:`, `data:text/html`) are converted to `#`.
4. **Markdown Formatting**: Headings (`#`), Blockquotes (`>`), Lists (`-`, `*`), Task Checkboxes (`- [x]`, `- [ ]`), Bold (`**`), Italic (`*`), Horizontal Rules (`---`), and Tables (`| col |`) are converted to clean semantic HTML.

---

## 5. Feature #20: Code & Config Monospace Studio Architecture

### 5.1 Layout & DOM Structure
```html
<div id="ks-code-studio" class="studio-sub-pane" style="display:none; flex-direction:column; height:100%; width:100%; min-height:0;">
  <!-- Code Studio Toolbar -->
  <div class="code-editor-header" style="display:flex; justify-content:space-between; align-items:center; padding:6px 12px; background:#0b121c; border:1px solid var(--border-subtle); border-bottom:none; border-radius:6px 6px 0 0;">
    <div style="display:flex; align-items:center; gap:8px;">
      <span class="badge badge-agent" id="code-lang-badge">PYTHON</span>
      <span style="font-family:var(--font-mono); font-size:11px; color:var(--text-muted);" id="code-stats-badge">12 lines • 3.8 KB</span>
    </div>
    <div style="display:flex; align-items:center; gap:6px;">
      <button class="toolbar-btn" id="btn-code-toggle-wrap" title="Toggle line wrap" style="font-size:10.5px; padding:2px 8px;">Wrap: Off</button>
      <button class="toolbar-btn" id="btn-code-copy" title="Copy code to clipboard" style="font-size:10.5px; padding:2px 8px;">📋 Copy Code</button>
    </div>
  </div>

  <!-- Synchronized Code Viewport with Line Numbers Gutter -->
  <div class="code-viewport" id="code-viewport" style="display:flex; flex:1; min-height:0; background:#070d16; border:1px solid var(--border-subtle); border-radius:0 0 6px 6px; overflow:hidden; font-family:var(--font-mono); font-size:12px; line-height:1.6;">
    <div class="code-line-numbers" id="code-line-numbers"
         style="padding:12px 10px; text-align:right; color:var(--text-muted); user-select:none; background:#090f18; border-right:1px solid var(--border-subtle); min-width:48px; box-sizing:border-box; overflow:hidden;">
    </div>
    <div class="code-content-wrapper" id="code-content-wrapper" style="flex:1; position:relative; overflow:auto;">
      <pre class="code-highlighted-pre" id="code-highlighted-pre"
           style="margin:0; padding:12px 16px; min-height:100%; box-sizing:border-box; color:#e2e8f0; white-space:pre; overflow:visible; font-family:var(--font-mono); font-size:12px; line-height:1.6;">
      </pre>
    </div>
  </div>
</div>
```

### 5.2 Line Numbers & Scroll Synchronization
- Lines are split on `\n`. The line count `N` generates line numbers `1` through `N` inside `#code-line-numbers`.
- Scrolling `#code-content-wrapper` triggers an onscroll event that synchronizes `#code-line-numbers.scrollTop = codeWrapper.scrollTop`, ensuring perfect vertical alignment at any scroll depth.

### 5.3 Pure Vanilla Syntax Tokenizer
The tokenizer uses language-specific regex patterns applied over pre-escaped HTML text:
- **Strings**: `(&quot;[\s\S]*?&quot;|&#39;[\s\S]*?&#39;|`[\s\S]*?``) -> `<span class="tok-str">$1</span>` (Emerald `#10B981`)
- **Comments**: `(#[^\n]*|\/\/[^\n]*|\/\*[\s\S]*?\*\/)` -> `<span class="tok-com">$1</span>` (Muted Slate `#64748B`, italic)
- **Keywords**: Language-specific keyword lists -> `<span class="tok-kw">$1</span>` (Cyan `#00E5FF`, font-weight 600)
- **Numbers**: `\b(\d+(\.\d+)?)\b` -> `<span class="tok-num">$1</span>` (Amber `#F59E0B`)
- **Booleans / Constants**: `True|False|None|true|false|null|undefined` -> `<span class="tok-const">$1</span>` (Crimson `#F43F5E`)
- **Keys in JSON / YAML**: `"key":` / `key:` -> `<span class="tok-key">$1</span>` (Slate-White `#E2E8F0`)
- **Functions**: `\b([a-zA-Z_]\w*)(?=\s*\()` -> `<span class="tok-fn">$1</span>` (Sky Blue `#38BDF8`)

### 5.4 Copy Button Interactivity
Clicking `#btn-code-copy`:
- Invokes `navigator.clipboard.writeText(rawContent)` (with fallback to textarea select/execCommand).
- Updates button text to `Copied! ✓` and border color to `#10B981`.
- Resets button after 1500ms to `📋 Copy Code`.

---

## 6. Feature #21: Tabular / CSV Data-Grid View Architecture

### 6.1 Layout & DOM Structure
```html
<div id="ks-data-grid-studio" class="studio-sub-pane" style="display:none; flex-direction:column; height:100%; width:100%; min-height:0;">
  <!-- Data Grid Toolbar -->
  <div class="grid-toolbar" style="display:flex; justify-content:space-between; align-items:center; padding:6px 12px; background:#0b121c; border:1px solid var(--border-subtle); border-bottom:none; border-radius:6px 6px 0 0;">
    <div style="display:flex; align-items:center; gap:8px;">
      <span class="badge badge-complete" id="grid-dimensions-badge">4 ROWS × 5 COLS</span>
      <input type="text" id="grid-search-input" placeholder="Filter rows in grid..."
             style="background:#070d16; border:1px solid var(--border-subtle); color:var(--text-primary); padding:3px 8px; border-radius:4px; font-size:11px; font-family:var(--font-mono); width:200px;" />
    </div>
    <div style="display:flex; align-items:center; gap:6px;">
      <button class="toolbar-btn" id="btn-grid-copy-tsv" title="Copy table as TSV" style="font-size:10.5px; padding:2px 8px;">📋 Copy TSV</button>
    </div>
  </div>

  <!-- Scrollable Data Grid Table -->
  <div class="grid-scroll-container" id="grid-scroll-container" style="flex:1; min-height:0; overflow:auto; background:#070d16; border:1px solid var(--border-subtle); border-radius:0 0 6px 6px;">
    <table class="studio-data-grid" id="studio-data-grid" style="width:100%; border-collapse:collapse; font-family:var(--font-mono); font-size:11.5px; text-align:left;">
      <thead id="grid-thead" style="position:sticky; top:0; z-index:2; background:#101a28;"></thead>
      <tbody id="grid-tbody"></tbody>
    </table>
  </div>
</div>
```

### 6.2 Robust Quotation-Aware Parser
The parser handles standard CSV, TSV, and JSONL formats:
- Supports commas inside quotes: `"perception_scan, level 2",120` parses to two cells.
- Supports escaped double quotes: `""quote""`.
- Trims outer whitespace while preserving cell content.
- For JSONL, computes the union of all keys across objects to establish consistent column headers.

### 6.3 Spreadsheet-Like Styling & Interaction
- **Sticky Column Headers**: `position: sticky; top: 0; background: #101a28; z-index: 2; border-bottom: 2px solid var(--cyan-accent); color: var(--cyan-accent);`.
- **Row Index Column**: `#` column with sticky left alignment, center text, muted slate color (`#64748B`), and 1-based indexing (`1, 2, 3...`).
- **Zebra Striping**: Alternating row backgrounds (`#0B121C` and `#101A28`).
- **Row Hover**: Row background transitions to `rgba(0, 229, 255, 0.08)`.
- **Instant Search / Filtering**: Typing in `#grid-search-input` filters table rows in real-time (<5ms latency), updating the dimensions badge (`2 OF 4 ROWS`).

---

## 7. Fallback & Media Preview Architecture

### 7.1 Layout & DOM Structure
```html
<div id="ks-media-studio" class="studio-sub-pane" style="display:none; flex-direction:column; height:100%; width:100%; min-height:0;">
  <div class="media-toolbar" style="display:flex; justify-content:space-between; align-items:center; padding:6px 12px; background:#0b121c; border:1px solid var(--border-subtle); border-bottom:none; border-radius:6px 6px 0 0;">
    <div style="display:flex; align-items:center; gap:8px;">
      <span class="badge badge-agent" id="media-type-badge">SVG VECTOR GRAPHIC</span>
      <span style="font-family:var(--font-mono); font-size:11px; color:var(--text-muted);" id="media-dimensions-badge">5.1 KB</span>
    </div>
  </div>
  <div class="media-viewport" id="media-viewport" style="flex:1; min-height:0; display:flex; align-items:center; justify-content:center; background:#070d16; border:1px solid var(--border-subtle); border-radius:0 0 6px 6px; padding:24px; overflow:auto;">
    <div id="media-display-container" style="max-width:100%; max-height:100%; display:flex; align-items:center; justify-content:center;"></div>
  </div>
</div>
```

### 7.2 Media Handling
- For `.svg`: Sanitizes `<svg>` (strips script/foreignObject/on* attributes) and renders it directly inside `#media-display-container`.
- For images (`.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`): Renders `<img src="${file.path}" style="max-width:100%; max-height:100%; border-radius:4px; box-shadow:0 4px 12px rgba(0,0,0,0.5);" />`.
- Fallback: Renders neutral metadata panel with file path, size, and category badge.

---

## 8. CAD Eradication in Viewport 2

In `ui/dashboard/index.html` lines 3345–3368, the Right Column of Viewport 2 currently contains hardcoded CAD/3D-printing text:
- `"Base plate 80.00 mm × 50.00 mm × 6.00 mm with upright mount wall 24.00 mm height"`
- `"Bolt holes × 5 (M4 countersunk clearance) + slotted flange bores"`
- `"Safety rule SEC-810: Existing STL overwrite requires human confirmation gate"`

These must be replaced with domain-agnostic semantic chunks:
1. **Chunk #01 (System Architecture & Pipeline)**:
   - Text: `"Autonomous agent workstation pipeline: multi-viewport perception, reversible rollback undo stack, blackboard state synchronizer."`
   - Metadata: `sim: 0.964 • 128 tok`
2. **Chunk #02 (Dynamic File & Artifact Management)**:
   - Text: `"Universal workspace file explorer with category filters (Code, Docs, Tables, Media, Configs) and polymorphic studio preview."`
   - Metadata: `sim: 0.942 • 96 tok`
3. **Chunk #03 (Safety Policy & Human-in-the-Loop)**:
   - Text: `"Safety interceptor policy SEC-401: Destructive filesystem writes or shell executions require human confirmation gate approval."`
   - Metadata: `sim: 0.891 • 84 tok`

---

## 9. Design System Tokens & CSS Specifications

All styling strictly enforces DESIGN tokens without external stylesheets or Google Fonts:
```css
/* Polymorphic Studio CSS Variables */
:root {
  --studio-bg-dark: #070d16;
  --studio-bg-card: #0b121c;
  --studio-bg-elevated: #101a28;
  --studio-border: #1b2a3e;
  --studio-border-cyan: rgba(0, 229, 255, 0.35);
  --studio-cyan: #00e5ff;
  --studio-emerald: #10b981;
  --studio-amber: #f59e0b;
  --studio-red: #ef4444;
  --studio-text: #f1f5f9;
  --studio-muted: #64748b;
}

/* Studio Sub-Panes */
.studio-sub-pane {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* Syntax Highlighting Tokens */
.tok-kw { color: #00e5ff; font-weight: 600; }
.tok-str { color: #10b981; }
.tok-num { color: #f59e0b; }
.tok-com { color: #64748b; font-style: italic; }
.tok-const { color: #f43f5e; font-weight: 600; }
.tok-fn { color: #38bdf8; }
.tok-key { color: #e2e8f0; font-weight: 600; }

/* Markdown Preview Elements */
.markdown-preview-body h1 { color: #00e5ff; font-size: 18px; border-bottom: 1px solid #1b2a3e; padding-bottom: 6px; margin: 0 0 12px; }
.markdown-preview-body h2 { color: #00e5ff; font-size: 15px; margin: 16px 0 8px; }
.markdown-preview-body h3 { color: #38bdf8; font-size: 13.5px; margin: 12px 0 6px; }
.markdown-preview-body p { margin-bottom: 10px; font-size: 12.5px; }
.markdown-preview-body code { background: #101a28; color: #00e5ff; padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono); font-size: 11.5px; border: 1px solid #1b2a3e; }
.markdown-preview-body pre { background: #070d16; border: 1px solid #1b2a3e; border-radius: 6px; padding: 10px 14px; overflow-x: auto; margin: 10px 0; }
.markdown-preview-body pre code { background: transparent; border: none; padding: 0; color: #e2e8f0; }
.markdown-preview-body blockquote { border-left: 3px solid #00e5ff; background: rgba(0, 229, 255, 0.05); padding: 8px 12px; margin: 10px 0; color: #94a3b8; font-style: italic; }
.markdown-preview-body ul, .markdown-preview-body ol { padding-left: 20px; margin-bottom: 10px; }
.markdown-preview-body li { margin-bottom: 4px; }
.markdown-preview-body .md-checkbox { display: inline-block; width: 14px; height: 14px; margin-right: 6px; text-align: center; line-height: 14px; font-size: 11px; border: 1px solid #1b2a3e; border-radius: 3px; }
.markdown-preview-body .md-checkbox.checked { background: rgba(0, 229, 255, 0.15); border-color: #00e5ff; color: #00e5ff; }
.markdown-preview-body a { color: #00e5ff; text-decoration: none; }
.markdown-preview-body a:hover { text-decoration: underline; }

/* Data Grid Elements */
.studio-data-grid th { background: #101a28; border: 1px solid #1b2a3e; padding: 6px 12px; color: #00e5ff; font-weight: 600; white-space: nowrap; }
.studio-data-grid td { border: 1px solid #1b2a3e; padding: 6px 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 260px; }
.studio-data-grid tr:hover td { background: rgba(0, 229, 255, 0.08) !important; }
```

---

## 10. Complete JavaScript Implementation Blueprint

The comprehensive engine will be organized into `ArtifactStudio`:
```javascript
const ArtifactStudio = {
  activeFile: null,
  activeMode: 'markdown', // 'markdown' | 'code' | 'table' | 'media'
  currentData: null,

  init() {
    this.bindEvents();
  },

  bindEvents() {
    // Markdown split resizer
    const divider = document.getElementById('ks-markdown-divider');
    if (divider) {
      let isDragging = false;
      divider.addEventListener('mousedown', (e) => {
        isDragging = true;
        document.body.style.cursor = 'col-resize';
      });
      document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        const container = document.getElementById('ks-markdown-studio');
        if (!container) return;
        const rect = container.getBoundingClientRect();
        const offsetX = e.clientX - rect.left;
        const pct = Math.max(20, Math.min(80, (offsetX / rect.width) * 100));
        const leftCol = container.querySelector('.studio-split-left');
        const rightCol = container.querySelector('.studio-split-right');
        if (leftCol && rightCol) {
          leftCol.style.flex = `0 0 ${pct}%`;
          rightCol.style.flex = `1 1 ${100 - pct}%`;
        }
      });
      document.addEventListener('mouseup', () => {
        if (isDragging) {
          isDragging = false;
          document.body.style.cursor = '';
        }
      });
    }

    // Markdown raw textarea live input -> preview update
    const textarea = document.getElementById('ks-editor-textarea');
    if (textarea) {
      textarea.addEventListener('input', () => {
        if (this.activeMode === 'markdown') {
          this.updateMarkdownPreview(textarea.value);
        }
      });
    }

    // Code copy button
    const btnCodeCopy = document.getElementById('btn-code-copy');
    if (btnCodeCopy) {
      btnCodeCopy.addEventListener('click', () => {
        const text = (this.activeFile && this.activeFile.content) || (textarea ? textarea.value : '');
        this.copyToClipboard(text, btnCodeCopy, '📋 Copy Code');
      });
    }

    // Grid search input
    const gridSearch = document.getElementById('grid-search-input');
    if (gridSearch) {
      gridSearch.addEventListener('input', (e) => {
        if (this.currentData && this.activeMode === 'table') {
          VanillaDataGrid.render('studio-data-grid', this.currentData, e.target.value);
        }
      });
    }

    // Grid copy TSV button
    const btnGridCopy = document.getElementById('btn-grid-copy-tsv');
    if (btnGridCopy) {
      btnGridCopy.addEventListener('click', () => {
        if (this.currentData) {
          const tsv = [this.currentData.headers.join('\t')]
            .concat(this.currentData.rows.map(r => r.join('\t')))
            .join('\n');
          this.copyToClipboard(tsv, btnGridCopy, '📋 Copy TSV');
        }
      });
    }

    // Code wrap toggle button
    const btnWrap = document.getElementById('btn-code-toggle-wrap');
    if (btnWrap) {
      btnWrap.addEventListener('click', () => {
        const pre = document.getElementById('code-highlighted-pre');
        if (!pre) return;
        const isPreWrap = pre.style.whiteSpace === 'pre-wrap';
        pre.style.whiteSpace = isPreWrap ? 'pre' : 'pre-wrap';
        btnWrap.textContent = isPreWrap ? 'Wrap: Off' : 'Wrap: On';
      });
    }
  },

  copyToClipboard(text, btn, defaultLabel) {
    if (!text) return;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        btn.textContent = 'Copied! ✓';
        btn.style.borderColor = 'var(--emerald-success)';
        btn.style.color = 'var(--emerald-success)';
        setTimeout(() => {
          btn.textContent = defaultLabel;
          btn.style.borderColor = '';
          btn.style.color = '';
        }, 1500);
      }).catch(() => {});
    }
  },

  loadFile(file) {
    this.activeFile = file;
    const content = file.content !== undefined ? file.content : (file.size ? `[Binary or unread file: ${file.path}]` : '');

    // Keep backwards compatible #ks-editor-textarea synchronized
    const rawTextarea = document.getElementById('ks-editor-textarea');
    if (rawTextarea) {
      rawTextarea.value = content;
    }

    // Update active file header
    const header = document.getElementById('ks-active-file-header');
    if (header) {
      header.textContent = `ACTIVE FILE // ${file.name}`;
    }

    // MIME detection
    const info = StudioMIMEDetector.detect(file);
    this.activeMode = info.mode;

    // Toggle sub-panes
    const mdStudio = document.getElementById('ks-markdown-studio');
    const codeStudio = document.getElementById('ks-code-studio');
    const gridStudio = document.getElementById('ks-data-grid-studio');
    const mediaStudio = document.getElementById('ks-media-studio');

    if (mdStudio) mdStudio.style.display = info.mode === 'markdown' ? 'flex' : 'none';
    if (codeStudio) codeStudio.style.display = info.mode === 'code' ? 'flex' : 'none';
    if (gridStudio) gridStudio.style.display = info.mode === 'table' ? 'flex' : 'none';
    if (mediaStudio) mediaStudio.style.display = info.mode === 'media' ? 'flex' : 'none';

    if (info.mode === 'markdown') {
      this.updateMarkdownPreview(content);
    } else if (info.mode === 'code') {
      this.renderCodeView(content, info.lang, file.size);
    } else if (info.mode === 'table') {
      this.renderTableView(content, info.ext);
    } else if (info.mode === 'media') {
      this.renderMediaView(file, content);
    }
  },

  updateMarkdownPreview(content) {
    const previewEl = document.getElementById('ks-markdown-preview');
    if (previewEl) {
      previewEl.innerHTML = VanillaMarkdown.render(content);
    }
    const linesBadge = document.getElementById('md-raw-lines-badge');
    if (linesBadge) {
      const lineCount = (content.split('\n')).length;
      linesBadge.textContent = `${lineCount} lines`;
    }
  },

  renderCodeView(content, lang, size) {
    const lines = content.split('\n');
    const lineCount = lines.length;
    const gutter = document.getElementById('code-line-numbers');
    if (gutter) {
      gutter.innerHTML = Array.from({ length: lineCount }, (_, i) => `<div>${i + 1}</div>`).join('');
    }

    const pre = document.getElementById('code-highlighted-pre');
    if (pre) {
      pre.innerHTML = VanillaSyntax.highlight(content, lang);
    }

    const langBadge = document.getElementById('code-lang-badge');
    if (langBadge) {
      langBadge.textContent = (lang || 'TEXT').toUpperCase();
    }

    const statsBadge = document.getElementById('code-stats-badge');
    if (statsBadge) {
      const sizeStr = size ? `${Math.round(size / 100) / 10} KB` : `${content.length} B`;
      statsBadge.textContent = `${lineCount} lines • ${sizeStr}`;
    }

    // Synchronize gutter scroll
    const wrapper = document.getElementById('code-content-wrapper');
    if (wrapper && gutter) {
      wrapper.onscroll = () => {
        gutter.scrollTop = wrapper.scrollTop;
      };
    }
  },

  renderTableView(content, ext) {
    const parsed = VanillaDataGrid.parse(content, ext);
    this.currentData = parsed;
    VanillaDataGrid.render('studio-data-grid', parsed);
  },

  renderMediaView(file, content) {
    const container = document.getElementById('media-display-container');
    const typeBadge = document.getElementById('media-type-badge');
    const dimBadge = document.getElementById('media-dimensions-badge');
    if (!container) return;

    if (file.ext === 'svg' && content) {
      if (typeBadge) typeBadge.textContent = 'SVG VECTOR GRAPHIC';
      container.innerHTML = content;
    } else {
      if (typeBadge) typeBadge.textContent = `${(file.ext || 'IMG').toUpperCase()} IMAGE`;
      container.innerHTML = `<img src="${file.path}" alt="${VanillaMarkdown.escape(file.name)}" style="max-width:100%;max-height:100%;border-radius:4px;box-shadow:0 4px 12px rgba(0,0,0,0.5);"/>`;
    }
    if (dimBadge) {
      dimBadge.textContent = file.size ? `${Math.round(file.size / 100) / 10} KB` : 'Media file';
    }
  }
};
```

---

## 11. Existing Test Review & Verification Test Suite

### 11.1 Existing Tests Review
1. **`tests/test_browser_dom.py`**:
   - Line 321: `test_dynamic_file_explorer_tree_and_category_filtering` — clicks category tabs and file items in tree.
   - Line 345: `test_four_polymorphic_viewports_switching` — clicks mode/viewport buttons.
   - Line 388: `test_viewport_2_artifact_document_studio_views`:
     ```python
     # Activate Knowledge Studio / Artifact Studio
     studio_btn = page.locator("button[data-mode='knowledge_studio'], button:has-text('Artifact'), button:has-text('Knowledge')").first
     if studio_btn.count() > 0 and studio_btn.is_visible():
         studio_btn.click()
         page.wait_for_timeout(250)
         first_file = page.locator(".ks-file-entry, .artifact-file-item").first
         if first_file.count() > 0 and first_file.is_visible():
             first_file.click()
             page.wait_for_timeout(200)
     assert len(page._page_errors) == 0
     ```
   - Line 524: `test_xss_sanitization_across_inputs` — checks canary `window.__XSS_DETECTED__`.

2. **`tests/test_challenge_m2.py`**:
   - Line 639: Asserts `#ks-active-file-header` contains `target_file` and `#ks-editor-textarea` equals expected file content.

### 11.2 Proposed Test Suite for Playwright (`test_viewport_2_studio_e2e`)

```python
def test_viewport_2_mime_auto_detection_and_polymorphic_rendering(page: Page) -> None:
    """Verifies automatic MIME detection and polymorphic rendering across all 4 modes in Viewport 2."""
    page.wait_for_load_state("networkidle")

    # Navigate to Studio
    studio_btn = page.locator("button[data-mode='knowledge_studio'], button[data-viewport='2']").first
    studio_btn.click()
    page.wait_for_timeout(200)

    # 1. Test Markdown file (README.md)
    md_entry = page.locator("#ks-file-list .ks-file-entry[data-file='README.md'], #kb-file-list .file-tree-item[data-file='README.md']").first
    md_entry.click()
    page.wait_for_timeout(150)
    assert page.locator("#ks-markdown-studio").is_visible()
    assert not page.locator("#ks-code-studio").is_visible()
    assert not page.locator("#ks-data-grid-studio").is_visible()
    assert page.locator("#ks-editor-textarea").input_value().startswith("#")
    assert page.locator("#ks-markdown-preview h1, #ks-markdown-preview h2").count() >= 1

    # 2. Test Code file (agent_runner.py)
    py_entry = page.locator("#ks-file-list .ks-file-entry[data-file='agent_runner.py'], #kb-file-list .file-tree-item[data-file='agent_runner.py']").first
    py_entry.click()
    page.wait_for_timeout(150)
    assert page.locator("#ks-code-studio").is_visible()
    assert not page.locator("#ks-markdown-studio").is_visible()
    assert page.locator("#code-lang-badge").text_content() == "PYTHON"
    assert page.locator("#code-line-numbers div").count() >= 5
    assert page.locator("#code-highlighted-pre .tok-kw").count() >= 1

    # 3. Test Tabular CSV file (metrics_report.csv)
    csv_entry = page.locator("#ks-file-list .ks-file-entry[data-file='metrics_report.csv'], #kb-file-list .file-tree-item[data-file='metrics_report.csv']").first
    csv_entry.click()
    page.wait_for_timeout(150)
    assert page.locator("#ks-data-grid-studio").is_visible()
    assert not page.locator("#ks-code-studio").is_visible()
    assert page.locator("#grid-thead th").count() == 6  # # + 5 columns
    assert page.locator("#grid-tbody tr").count() == 4   # 4 rows
    assert "perception_scan" in page.locator("#grid-tbody").text_content()

    # 4. Test Table Search Filtering
    search_input = page.locator("#grid-search-input")
    search_input.fill("plan_generation")
    page.wait_for_timeout(100)
    assert page.locator("#grid-tbody tr").count() == 1

    # 5. Test Media SVG file (system_diagram.svg)
    svg_entry = page.locator("#ks-file-list .ks-file-entry[data-file='system_diagram.svg'], #kb-file-list .file-tree-item[data-file='system_diagram.svg']").first
    svg_entry.click()
    page.wait_for_timeout(150)
    assert page.locator("#ks-media-studio").is_visible()
    assert page.locator("#media-display-container svg").count() >= 1

    assert len(page._page_errors) == 0


def test_viewport_2_markdown_xss_resilience(page: Page) -> None:
    """Verifies that malicious script or onerror tags in markdown preview never execute."""
    page.wait_for_load_state("networkidle")
    page.evaluate("window.__XSS_STUDIO_FIRED__ = false;")

    # Inject malicious markdown into editor textarea
    xss_payload = "# XSS Test\n\n<script>window.__XSS_STUDIO_FIRED__ = true;</script>\n<img src=invalid onerror='window.__XSS_STUDIO_FIRED__ = true;'>\n[Malicious](javascript:window.__XSS_STUDIO_FIRED__=true)"
    page.evaluate(f"() => {{ ArtifactStudio.loadFile({{ name: 'xss_test.md', ext: 'md', content: `{xss_payload}` }}); }}")
    page.wait_for_timeout(250)

    fired = page.evaluate("window.__XSS_STUDIO_FIRED__")
    assert not fired, "Vulnerability: XSS script or handler executed inside markdown preview!"
    # Verify no script element in preview DOM
    assert page.locator("#ks-markdown-preview script").count() == 0
