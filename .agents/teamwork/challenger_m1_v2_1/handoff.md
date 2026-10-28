# Milestone 1 Empirical Challenge Report: Backend Endpoints & Persistence

**Agent**: `teamwork_challenger` (`challenger_m1_v2_1`)  
**Parent**: `sub_orch_m1_backend` (`db3d98a0-f6a4-45e7-9dea-32dceda77cf0`)  
**Verdict**: **APPROVE**  
**Date**: 2026-10-28T22:04:30Z  
**Target Code**: `server/api.py`, `workspace/workspaces_store.json`, `workspace/default/*`  
**Adversarial Test Suite**: `tests/test_adversarial_m1_endpoints.py` (83 tests)  

---

## 1. Observation

Direct empirical evidence was gathered by constructing and executing an adversarial test harness (`tests/test_adversarial_m1_endpoints.py`) containing 83 distinct stress tests across 7 attack classes via `uv run --with pytest pytest tests/test_adversarial_m1_endpoints.py -v`.

### 1.1 Path Traversal & Sandboxing (`/api/workspace/files`)
- **Relative Traversal Payloads Tested**:
  - `../`, `../../`, `../../../`, `../../../../Windows`, `../server`, `workspace/../../`, `workspace/default/../../..`, `..%2F..%2F`, `%2e%2e%2f%2e%2e%2f`, `..\\..\\`, `..\\..\\Windows\\System32`, `workspace\\..\\..\\`.
  - **Result**: 100% (12/12) returned `HTTP 403 Forbidden` with body `{"error": "Path traversal prohibited"}`.
- **Absolute Root & Drive Payloads Tested**:
  - `/`, `//`, `///`, `C:/`, `C:\`, `C:/Windows`, `C:\Windows\System32`, `\\localhost\c$`, `\\?\C:\Windows`.
  - **Result**: 100% (9/9) returned `HTTP 403 Forbidden` with body `{"error": "Path traversal prohibited"}`.
- **Boundary Directory Targets**:
  - `workspace/nonexistent_subfolder_adversarial_xyz`: returned `HTTP 200 []` without 500 error.
  - `server/api.py` (regular file instead of directory): returned `HTTP 200 []` without crashing.
  - Active workspace default: returned `HTTP 200` listing 5 categorized items (`mission.md` -> `doc`, `pipeline.py` -> `code`, `sample_data.csv` -> `data`, `agent_config.json` -> `config`, `architecture.svg` -> `media`).
- **Malicious Workspace working_dir Sandboxing**:
  - Created a workspace with `working_dir="../../"`. When activated, calling `GET /api/workspace/files` evaluated `target_path.relative_to(BASE_DIR)`, raised `ValueError`, and returned `HTTP 403 Forbidden` (`{"error": "Path traversal prohibited"}`).

### 1.2 Boundary & Malicious Inputs (`/api/workspaces` & `/api/tasks`)
- **Empty & Whitespace-only Names / Titles**:
  - `POST /api/workspaces` with `""`, `"   "`, `"\t\t"`, `"\n\r  \n"`, `"   \t   \n  "`, `" \u00A0 "`: all returned `HTTP 400` with `{"error": "Workspace name cannot be empty"}`.
  - `POST /api/tasks` with `""`, `"   "`, `"\t\n  \r"`, `" \u00A0 "`: all returned `HTTP 400` with `{"error": "Task title cannot be empty"}`.
  - `PATCH /api/tasks/{id}` with `""`, `"   "`, `"\t\n "`: all returned `HTTP 400` with `{"error": "Task title cannot be empty"}` and left original title untouched.
  - Missing required fields (`{}`): returned `HTTP 422 Unprocessable Entity` via Pydantic validation.
- **Extreme Length Inputs (10,000 characters)**:
  - `POST /api/workspaces` with 10,000-character name and 10,000-character prompt: returned `HTTP 201 Created` (`status=created`), persisted without corrupting disk store, and clean deletion succeeded.
  - `POST /api/tasks` with 10,000-character title and complex nested metadata (`{"nested": ..., "unicode": "こんにちは世界 👾", "injection": "'; DROP TABLE tasks; --"}`): returned `HTTP 201 Created`, stored verbatim, and accurately retrieved.
- **XSS & Path Injection in Workspace Creation**:
  - `POST /api/workspaces` with `name="<script>alert('xss')</script> /..\\..\\ 🔥🚀"`: sanitized directory slug to alphanumeric/underscore (`workspace/script_alert_xss_script`), returned `HTTP 201 Created`, and did not traverse disk paths.

### 1.3 Enum Enforcement & Fallbacks (Status & Priority)
- **POST Fallback**:
  - `POST /api/tasks` with `status="invalid_status_foo"` and `priority="P99"`: returned `HTTP 201 Created` with safe fallbacks applied (`status="backlog"`, `priority="P2"`).
- **PATCH Strict Rejection**:
  - `PATCH /api/tasks/{id}` with invalid statuses (`"foo_status"`, `"DONE"`, `"completed"`, `"pending"`, `"active"`, `""`, `"123"`, `"back_log"`): 100% (8/8) returned `HTTP 400` (`Invalid status '<val>'`).
  - `PATCH /api/tasks/{id}` with invalid priorities (`"P99"`, `"p1"`, `"P0"`, `"P4"`, `"HIGH"`, `"urgent"`, `""`, `"1"`): 100% (8/8) returned `HTTP 400` (`Invalid priority '<val>'`).
  - `PATCH /api/tasks/{id}` with all 5 valid statuses (`backlog`, `in_progress`, `agent_delegated`, `blocked`, `done`) and all 3 valid priorities (`P1`, `P2`, `P3`): 100% passed with `HTTP 200`.

### 1.4 Non-Existent Entities (404 Verification)
- `DELETE /api/workspaces/{id}` with non-existent IDs (`ws-00000000`, `ws-99999999`, `ws-null`, `undefined`, `../../etc/passwd`): returned `HTTP 404`.
- `POST /api/workspaces/activate` with non-existent IDs (`ws-00000000`, `ws-99999999`, `""`, `"   "`): returned `HTTP 404`.
- `DELETE /api/tasks/{id}` with non-existent IDs (`task-000000`, `task-999999`, `task-invalid`): returned `HTTP 404`.
- `PATCH /api/tasks/{id}` with non-existent IDs: returned `HTTP 404`.

### 1.5 Concurrency & Store Integrity
- **Concurrent Workspace Creation**:
  - 30 threads concurrently posted new workspaces via `ThreadPoolExecutor(max_workers=10)`. Zero errors, 30 HTTP 201 responses, and `workspace/workspaces_store.json` contained all 30 unique IDs without corruption.
  - Concurrently deleted all 30 test workspaces without deadlock or file lock contention.
- **Concurrent Task Creation & Status Churn**:
  - 30 threads concurrently created tasks, patched to `in_progress` / `P1`, and patched to `done` / `delegated=True`.
  - Zero race conditions, zero lost updates, 100% tasks on disk had `status="done"`, `priority="P1"`, `delegated=True`.
- **Active Workspace Deletion Fallback**:
  - Deleted the active workspace while selected. The store cleanly transitioned `active_workspace_id` to the first remaining workspace without throwing `KeyError` or leaving an orphaned pointer.
- **Complete Workspace Wipeout Auto-Healing**:
  - Deleted all workspaces in store. System automatically re-initialized `ws-default`, keeping `active_workspace_id="ws-default"` alive.
- **Corrupted Store Recovery**:
  - Wrote malformed non-JSON string (`"{ CORRUPTED_BAD_JSON !!!"`) directly to `workspace/workspaces_store.json`. Re-initializing safely fell back to default state and overwrote corrupted file with valid JSON.

### 1.6 Strict Zero-CAD Token Eradication
- Comprehensive regex scan using case-insensitive boundary search:
  `[\bopenscad\b, \bcad\b, \bstl\b, \bcsg\b, 3d fabrication, \btoolhead\b, overwrite_stl, \bmanifold\b, mesh viewport, 3d-print, 3d_print, \bextrusion\b, toolhead_mount]`.
- **`GET /api/som`**:
  - Scanned entire raw response text. Total matches: **0**.
  - Verified all 12 marks use standard `Window::*` selectors (`Window::MenuBar`, `Window::Controls`, `Window::FileTree`, `Window::ButtonExecute`, `Window::CanvasViewport`, `Window::StatusGizmo`, `Window::ViewTools`, `Window::Inspector`, `Window::TelemetryBadge`, `Window::TerminalDrawer`, `Window::IntegrityBadge`, `Window::CommandInput`).
  - Coordinates verified as valid non-negative integers.
- **`POST /api/scenario/reset`**:
  - Scanned reset response and seeded `pending_confirmation` in `GET /api/state`. Total matches: **0**.
  - Confirmation gate correctly set to `key="system_file_write"`, `title="Update workspace configuration"`, `detail="Modifying workspace environment • Risk: Moderate"`.
  - Approved via `POST /api/confirm`, resolving gate cleanly.
  - Executed 20 consecutive reset calls: 100% idempotent, zero token leakage.

### 1.7 Execution Logs
```
uv run --with pytest pytest tests/test_adversarial_m1_endpoints.py -v
======================== 83 passed, 1 warning in 4.69s ========================

uv run --with pytest pytest tests/test_api.py -v
======================= 22 passed, 1 warning in 13.72s ========================

uv run --with pytest pytest tests/test_m1_adversarial_stress.py -v
======================== 7 passed, 1 warning in 1.87s =========================

uv run --with pytest pytest .agents/teamwork/worker_m1_v2/test_m1_verification.py -v
======================== 6 passed, 1 warning in 1.21s =========================
```
Total verified tests across all suites: **118 passed, 0 failed**.

---

## 2. Logic Chain

1. **Path Traversal Defense**: `server/api.py:764-767` evaluates `target_path.relative_to(BASE_DIR)`. Any relative (`..`), encoded (`%2e%2e`), backslash (`\\`), or absolute path pointing outside `BASE_DIR` raises `ValueError` before any filesystem access occurs, guaranteeing HTTP 403. Even if a workspace is configured with a malicious `working_dir`, `list_workspace_files` catches it at request time.
2. **Boundary & Input Sanitization**: Both workspace name and task title are stripped (`(req.name or "").strip()`) and checked for emptiness before store mutation, rejecting blanks with HTTP 400. In addition, workspace slug generation (`server/api.py:197`) strips non-alphanumeric characters, preventing injection into folder names on disk.
3. **Enum Contract Compliance**: Status and priority values are strictly checked against whitelist sets. In POST, safe defaults (`backlog`, `P2`) ensure client convenience; in PATCH, invalid values trigger an immediate HTTP 400 rejection, preventing corrupted or unexpected states from persisting.
4. **Thread-Safe Atomic Persistence**: `WorkspaceStore` locks all mutations behind `threading.RLock()` and writes to disk via a temporary file with atomic replacement (`tmp.replace(self._path)`). Under 30-worker concurrent load across both workspaces and tasks, no file collisions, corrupted writes, or lost updates occurred.
5. **CAD Token Eradication**: Both `/api/som` and `/api/scenario/reset` were scanned against 13 forbidden CAD/fabrication tokens with zero matches found. Selectors and fixtures are completely domain-agnostic.

---

## 3. Caveats

1. Zero-width Unicode format characters (e.g. `\u200b` U+200B) are not stripped by standard Python `str.strip()` (which strips Unicode category `Zs`). If passed as workspace name, `WorkspaceStore` slug generation converts it to `workspace/workspace`. This does not compromise system integrity or crash the server.
2. No other caveats.

---

## 4. Conclusion

**Verdict**: **APPROVE**

Milestone 1 backend implementation in `server/api.py` demonstrates excellent robustness, strict sandbox boundary enforcement, thread-safe persistence, and 100% elimination of legacy CAD/OpenSCAD elements. All 83 adversarial tests pass cleanly.

---

## 5. Verification Method

To independently execute and verify the adversarial stress test suite:

```powershell
uv run --with pytest pytest tests/test_adversarial_m1_endpoints.py -v
```
*Expected Result*: 83 passed in ~4.5 seconds.

To run the complete suite of all M1 backend tests:
```powershell
uv run --with pytest pytest tests/test_adversarial_m1_endpoints.py tests/test_api.py tests/test_m1_adversarial_stress.py .agents/teamwork/worker_m1_v2/test_m1_verification.py -v
```
*Expected Result*: 118 passed in ~20 seconds.
