"""Adversarial Stress Test Suite for Milestone 1 Backend Endpoints.

Empirically challenges server/api.py against:
1. Malicious / illegal inputs:
   - Path traversal in /api/workspace/files (relative, absolute, backslash, invalid characters, non-directories).
   - Empty, whitespace-only, extremely long, and adversarial strings in /api/workspaces and /api/tasks.
   - Invalid task statuses and invalid priorities (POST fallback vs PATCH strict 400 rejection).
   - Deleting non-existent workspaces and tasks (strict 404).
   - Activating non-existent workspace IDs (strict 404).
2. Concurrency & Stress:
   - Concurrent workspace creation across threads.
   - Concurrent task creation and status churn across threads.
   - Active workspace deletion and automatic fallback under rapid churn.
   - Thread-safe atomic JSON persistence without corruption or data loss.
3. Strict CAD/OpenSCAD Token Eradication:
   - /api/som: complete scan of all marks, selectors, types, and tags against CAD tokens.
   - /api/scenario/reset: complete scan of reset payload, state pending confirmation, and approval workflow.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import re
from typing import Any, Dict, Generator, List

from fastapi.testclient import TestClient
import pytest

from core.confirm import resolve as resolve_confirm
from server.api import BASE_DIR, WORKSPACE_STORE_FILE, create_app, workspace_store


@pytest.fixture(autouse=True)
def preserve_workspace_store() -> Generator[None, None, None]:
    """Backup workspaces_store.json before test and restore it after."""
    original_content = None
    if WORKSPACE_STORE_FILE.exists():
        original_content = WORKSPACE_STORE_FILE.read_text(encoding="utf-8")

    yield

    if original_content is not None:
        WORKSPACE_STORE_FILE.write_text(original_content, encoding="utf-8")
    workspace_store._init_store()


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


# ============================================================================
# Group 1: Path Traversal & File Explorer Boundary Tests (/api/workspace/files)
# ============================================================================

class TestPathTraversalAndFileExplorer:
    """Adversarial testing of /api/workspace/files sandbox boundaries."""

    @pytest.mark.parametrize(
        "payload_path",
        [
            "../",
            "../../",
            "../../../",
            "../../../../Windows",
            "../server",
            "workspace/../../",
            "workspace/default/../../..",
            "..%2F..%2F",
            "%2e%2e%2f%2e%2e%2f",
            "..\\..\\",
            "..\\..\\Windows\\System32",
            "workspace\\..\\..\\",
        ],
    )
    def test_relative_path_traversal_blocked(self, client: TestClient, payload_path: str) -> None:
        """Any attempt to escape BASE_DIR via relative traversal must return 403 Forbidden."""
        res = client.get(f"/api/workspace/files?path={payload_path}")
        assert res.status_code == 403, (
            f"Expected 403 Forbidden for path traversal '{payload_path}', got {res.status_code}: {res.text}"
        )
        data = res.json()
        assert "error" in data
        assert "Path traversal prohibited" in data["error"]

    @pytest.mark.parametrize(
        "abs_path",
        [
            "/",
            "//",
            "///",
            "C:/",
            "C:\\",
            "C:/Windows",
            "C:\\Windows\\System32",
            "\\\\localhost\\c$",
            "\\\\?\\C:\\Windows",
        ],
    )
    def test_absolute_root_path_traversal_blocked(self, client: TestClient, abs_path: str) -> None:
        """Any attempt to inspect arbitrary absolute root/drive paths must return 403 Forbidden."""
        res = client.get(f"/api/workspace/files?path={abs_path}")
        assert res.status_code == 403, (
            f"Expected 403 Forbidden for absolute path '{abs_path}', got {res.status_code}: {res.text}"
        )
        data = res.json()
        assert "error" in data
        assert "Path traversal prohibited" in data["error"]

    def test_nonexistent_directory_returns_empty_list_safely(self, client: TestClient) -> None:
        """Non-existent subdirectories within BASE_DIR must return 200 [] without 500 error."""
        res = client.get("/api/workspace/files?path=workspace/nonexistent_subfolder_adversarial_xyz")
        assert res.status_code == 200
        assert res.json() == []

    def test_regular_file_target_returns_empty_list_safely(self, client: TestClient) -> None:
        """Targeting a regular file instead of a directory must return 200 [] without crash."""
        res = client.get("/api/workspace/files?path=server/api.py")
        assert res.status_code == 200
        assert res.json() == []

    def test_active_workspace_default_files_and_categories(self, client: TestClient) -> None:
        """Listing active workspace files without path parameter succeeds and categorizes correctly."""
        res = client.get("/api/workspace/files")
        assert res.status_code == 200
        files = res.json()
        assert isinstance(files, list)
        assert len(files) >= 4

        valid_categories = {"code", "doc", "data", "media", "config"}
        for f in files:
            assert "name" in f
            assert "path" in f
            assert "is_dir" in f
            assert "size" in f
            assert "ext" in f
            assert "category" in f
            assert f["category"] in valid_categories, f"Invalid category '{f['category']}' for file {f['name']}"

        # Verify default files are correctly categorized
        file_map = {f["name"]: f for f in files}
        if "mission.md" in file_map:
            assert file_map["mission.md"]["category"] == "doc"
        if "pipeline.py" in file_map:
            assert file_map["pipeline.py"]["category"] == "code"
        if "sample_data.csv" in file_map:
            assert file_map["sample_data.csv"]["category"] == "data"
        if "agent_config.json" in file_map:
            assert file_map["agent_config.json"]["category"] == "config"
        if "architecture.svg" in file_map:
            assert file_map["architecture.svg"]["category"] == "media"


# ============================================================================
# Group 2: Empty, Whitespace, Boundary & Long Inputs
# ============================================================================

class TestInputValidationAndBoundaries:
    """Stress tests on empty, whitespace, giant, and adversarial payloads."""

    @pytest.mark.parametrize(
        "bad_name",
        [
            "",
            "   ",
            "\t\t",
            "\n\r  \n",
            "   \t   \n  ",
            " \u00A0 ",  # Non-breaking space
        ],
    )
    def test_workspace_create_rejects_empty_and_whitespace_names(
        self, client: TestClient, bad_name: str
    ) -> None:
        """POST /api/workspaces must return 400 for empty or whitespace-only names."""
        res = client.post("/api/workspaces", json={"name": bad_name})
        assert res.status_code == 400, f"Expected 400 for bad name {repr(bad_name)}, got {res.status_code}"
        assert "Workspace name cannot be empty" in res.json().get("error", "")

    def test_workspace_create_missing_required_name(self, client: TestClient) -> None:
        """POST /api/workspaces without name field returns 422 Unprocessable Entity."""
        res = client.post("/api/workspaces", json={"prompt": "Some prompt"})
        assert res.status_code == 422

    def test_workspace_create_extreme_length_strings(self, client: TestClient) -> None:
        """POST /api/workspaces with 10,000-char name and prompt must not crash server."""
        giant_name = "W" * 10000
        giant_prompt = "P" * 10000
        res = client.post("/api/workspaces", json={"name": giant_name, "prompt": giant_prompt})
        assert res.status_code == 201
        data = res.json()
        assert data["status"] == "created"
        created_id = data["workspace"]["id"]
        assert data["workspace"]["name"] == giant_name

        # Verify retrieval
        list_res = client.get("/api/workspaces")
        assert list_res.status_code == 200
        ws_ids = [w["id"] for w in list_res.json()["workspaces"]]
        assert created_id in ws_ids

        # Clean up
        del_res = client.delete(f"/api/workspaces/{created_id}")
        assert del_res.status_code == 200

    def test_workspace_create_adversarial_special_characters(self, client: TestClient) -> None:
        """POST /api/workspaces with XSS, path chars, and Unicode emojis must be handled cleanly."""
        adversarial_name = "<script>alert('xss')</script> /..\\..\\ 🔥🚀"
        res = client.post("/api/workspaces", json={"name": adversarial_name})
        assert res.status_code == 201
        ws = res.json()["workspace"]
        assert ws["name"] == adversarial_name
        # Verify working_dir slug was safely sanitized to alphanumeric/underscore
        assert ".." not in ws["working_dir"]
        assert "<" not in ws["working_dir"]

        # Clean up
        client.delete(f"/api/workspaces/{ws['id']}")

    @pytest.mark.parametrize(
        "bad_title",
        [
            "",
            "   ",
            "\t\n  \r",
            " \u00A0 ",
        ],
    )
    def test_task_create_rejects_empty_and_whitespace_titles(
        self, client: TestClient, bad_title: str
    ) -> None:
        """POST /api/tasks must return 400 for empty or whitespace-only titles."""
        res = client.post("/api/tasks", json={"title": bad_title})
        assert res.status_code == 400, f"Expected 400 for bad title {repr(bad_title)}, got {res.status_code}"
        assert "Task title cannot be empty" in res.json().get("error", "")

    def test_task_create_missing_required_title(self, client: TestClient) -> None:
        """POST /api/tasks without title field returns 422 Unprocessable Entity."""
        res = client.post("/api/tasks", json={"status": "in_progress"})
        assert res.status_code == 422

    def test_task_create_extreme_length_and_adversarial_metadata(self, client: TestClient) -> None:
        """POST /api/tasks with 10,000-char title and deeply nested metadata persists cleanly."""
        giant_title = "T" * 10000
        complex_meta = {
            "nested": {"level1": {"level2": [1, 2, 3, "four"]}},
            "unicode": "こんにちは世界 👾 🤖 🛰️",
            "injection": "'; DROP TABLE tasks; --",
        }
        res = client.post("/api/tasks", json={"title": giant_title, "meta": complex_meta})
        assert res.status_code == 201
        task = res.json()["task"]
        t_id = task["id"]
        assert task["title"] == giant_title
        assert task["meta"]["injection"] == "'; DROP TABLE tasks; --"

        # Verify state persistence
        state_tasks = client.get("/api/tasks").json()["tasks"]
        matched = [t for t in state_tasks if t["id"] == t_id]
        assert len(matched) == 1
        assert matched[0]["title"] == giant_title

        # Clean up
        client.delete(f"/api/tasks/{t_id}")

    @pytest.mark.parametrize("bad_title", ["", "   ", "\t\n "])
    def test_task_patch_rejects_empty_whitespace_titles(self, client: TestClient, bad_title: str) -> None:
        """PATCH /api/tasks/{id} must reject empty or whitespace titles with 400."""
        # Create a valid task first
        init_res = client.post("/api/tasks", json={"title": "Valid Initial Task"})
        assert init_res.status_code == 201
        t_id = init_res.json()["task"]["id"]

        try:
            res = client.patch(f"/api/tasks/{t_id}", json={"title": bad_title})
            assert res.status_code == 400
            assert "Task title cannot be empty" in res.json().get("error", "")

            # Verify original title untouched
            tasks = client.get("/api/tasks").json()["tasks"]
            target = [t for t in tasks if t["id"] == t_id][0]
            assert target["title"] == "Valid Initial Task"
        finally:
            client.delete(f"/api/tasks/{t_id}")


# ============================================================================
# Group 3: Task Status and Priority Enum Enforcement
# ============================================================================

class TestTaskEnumsAndFallbacks:
    """Empirical verification of enum handling in POST and PATCH /api/tasks."""

    def test_task_create_invalid_status_and_priority_fallbacks(self, client: TestClient) -> None:
        """POST /api/tasks falls back gracefully to default 'backlog' and 'P2' when given invalid values."""
        res = client.post(
            "/api/tasks",
            json={
                "title": "Fallback Enum Task",
                "status": "invalid_status_foo",
                "priority": "P99",
            },
        )
        assert res.status_code == 201
        task = res.json()["task"]
        t_id = task["id"]
        try:
            assert task["status"] == "backlog", f"Expected fallback to 'backlog', got {task['status']}"
            assert task["priority"] == "P2", f"Expected fallback to 'P2', got {task['priority']}"
        finally:
            client.delete(f"/api/tasks/{t_id}")

    @pytest.mark.parametrize(
        "invalid_status",
        [
            "foo_status",
            "DONE",  # case-sensitive
            "completed",
            "pending",
            "active",
            "",
            "123",
            "back_log",
        ],
    )
    def test_task_patch_rejects_invalid_status_with_400(
        self, client: TestClient, invalid_status: str
    ) -> None:
        """PATCH /api/tasks/{id} must reject invalid status values with HTTP 400."""
        init = client.post("/api/tasks", json={"title": "Patch Status Guard Task", "status": "backlog"})
        t_id = init.json()["task"]["id"]
        try:
            res = client.patch(f"/api/tasks/{t_id}", json={"status": invalid_status})
            assert res.status_code == 400, f"Expected 400 for status '{invalid_status}', got {res.status_code}"
            assert f"Invalid status '{invalid_status}'" in res.json().get("error", "")

            # Confirm status unchanged
            current = [t for t in client.get("/api/tasks").json()["tasks"] if t["id"] == t_id][0]
            assert current["status"] == "backlog"
        finally:
            client.delete(f"/api/tasks/{t_id}")

    @pytest.mark.parametrize(
        "invalid_priority",
        [
            "P99",
            "p1",  # case-sensitive
            "P0",
            "P4",
            "HIGH",
            "urgent",
            "",
            "1",
        ],
    )
    def test_task_patch_rejects_invalid_priority_with_400(
        self, client: TestClient, invalid_priority: str
    ) -> None:
        """PATCH /api/tasks/{id} must reject invalid priority values with HTTP 400."""
        init = client.post("/api/tasks", json={"title": "Patch Priority Guard Task", "priority": "P2"})
        t_id = init.json()["task"]["id"]
        try:
            res = client.patch(f"/api/tasks/{t_id}", json={"priority": invalid_priority})
            assert res.status_code == 400, (
                f"Expected 400 for priority '{invalid_priority}', got {res.status_code}"
            )
            assert f"Invalid priority '{invalid_priority}'" in res.json().get("error", "")

            # Confirm priority unchanged
            current = [t for t in client.get("/api/tasks").json()["tasks"] if t["id"] == t_id][0]
            assert current["priority"] == "P2"
        finally:
            client.delete(f"/api/tasks/{t_id}")

    def test_task_patch_accepts_all_valid_enums(self, client: TestClient) -> None:
        """PATCH /api/tasks/{id} succeeds for all 5 valid statuses and all 3 valid priorities."""
        init = client.post("/api/tasks", json={"title": "All Enums Test"})
        t_id = init.json()["task"]["id"]
        valid_statuses = ["backlog", "in_progress", "agent_delegated", "blocked", "done"]
        valid_priorities = ["P1", "P2", "P3"]

        try:
            for s in valid_statuses:
                res = client.patch(f"/api/tasks/{t_id}", json={"status": s})
                assert res.status_code == 200
                assert res.json()["task"]["status"] == s

            for p in valid_priorities:
                res = client.patch(f"/api/tasks/{t_id}", json={"priority": p})
                assert res.status_code == 200
                assert res.json()["task"]["priority"] == p
        finally:
            client.delete(f"/api/tasks/{t_id}")


# ============================================================================
# Group 4: Non-Existent Entity Handling (404 Verification)
# ============================================================================

class TestNonExistentEntityRejection:
    """Verify strict 404 responses when operating on non-existent IDs."""

    @pytest.mark.parametrize(
        "missing_ws_id",
        [
            "nonexistent-ws-00000000",
            "ws-99999999",
            "ws-null",
            "undefined",
            "../../etc/passwd",
        ],
    )
    def test_delete_nonexistent_workspace_returns_404(
        self, client: TestClient, missing_ws_id: str
    ) -> None:
        """DELETE /api/workspaces/{id} returns 404 for non-existent workspace."""
        res = client.delete(f"/api/workspaces/{missing_ws_id}")
        assert res.status_code == 404
        data = res.json()
        assert "not found" in data.get("error", "").lower() or "not found" in data.get("detail", "").lower()

    @pytest.mark.parametrize(
        "missing_ws_id",
        [
            "nonexistent-ws-00000000",
            "ws-99999999",
            "",
            "   ",
        ],
    )
    def test_activate_nonexistent_workspace_returns_404(
        self, client: TestClient, missing_ws_id: str
    ) -> None:
        """POST /api/workspaces/activate returns 404 for non-existent workspace."""
        res = client.post("/api/workspaces/activate", json={"id": missing_ws_id})
        assert res.status_code == 404
        assert "not found" in res.json().get("error", "").lower()

    @pytest.mark.parametrize(
        "missing_task_id",
        [
            "nonexistent-task-000000",
            "task-999999",
            "task-invalid",
        ],
    )
    def test_delete_nonexistent_task_returns_404(
        self, client: TestClient, missing_task_id: str
    ) -> None:
        """DELETE /api/tasks/{id} returns 404 for non-existent task."""
        res = client.delete(f"/api/tasks/{missing_task_id}")
        assert res.status_code == 404
        assert f"Task '{missing_task_id}' not found" in res.json().get("error", "")

    @pytest.mark.parametrize(
        "missing_task_id",
        [
            "nonexistent-task-000000",
            "task-999999",
        ],
    )
    def test_patch_nonexistent_task_returns_404(
        self, client: TestClient, missing_task_id: str
    ) -> None:
        """PATCH /api/tasks/{id} returns 404 for non-existent task."""
        res = client.patch(f"/api/tasks/{missing_task_id}", json={"status": "done"})
        assert res.status_code == 404
        assert f"Task '{missing_task_id}' not found" in res.json().get("error", "")


# ============================================================================
# Group 5: High Concurrency & Stress Testing
# ============================================================================

class TestConcurrencyAndStoreIntegrity:
    """Empirical verification of thread-safety and race condition resilience."""

    def test_concurrent_workspace_creation(self, client: TestClient) -> None:
        """30 concurrent threads creating workspaces simultaneously must not corrupt store."""
        created_ids: List[str] = []
        errors: List[str] = []

        def worker(index: int) -> None:
            try:
                res = client.post(
                    "/api/workspaces",
                    json={
                        "name": f"Stress Workspace {index}",
                        "prompt": f"Autonomous Stress Execution Node {index}",
                    },
                )
                if res.status_code == 201:
                    created_ids.append(res.json()["workspace"]["id"])
                else:
                    errors.append(f"Worker {index} failed with {res.status_code}: {res.text}")
            except Exception as e:
                errors.append(f"Worker {index} threw exception: {e}")

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker, i) for i in range(30)]
            for f in as_completed(futures):
                f.result()

        assert not errors, f"Concurrency errors occurred: {errors}"
        assert len(created_ids) == 30

        # Verify disk persistence integrity
        assert WORKSPACE_STORE_FILE.exists()
        disk_data = json.loads(WORKSPACE_STORE_FILE.read_text(encoding="utf-8"))
        disk_ws_ids = {w["id"] for w in disk_data.get("workspaces", [])}
        for cid in created_ids:
            assert cid in disk_ws_ids, f"Created workspace {cid} missing from disk store!"

        # Concurrently delete all 30 workspaces
        def delete_worker(ws_id: str) -> None:
            client.delete(f"/api/workspaces/{ws_id}")

        with ThreadPoolExecutor(max_workers=10) as executor:
            list(executor.map(delete_worker, created_ids))

    def test_concurrent_task_creation_and_churn(self, client: TestClient) -> None:
        """30 concurrent threads creating and patching tasks simultaneously must be race-free."""
        created_task_ids: List[str] = []
        errors: List[str] = []

        def create_and_churn(index: int) -> None:
            try:
                # 1. Create task
                c_res = client.post(
                    "/api/tasks",
                    json={
                        "title": f"Concurrent Task {index}",
                        "status": "backlog",
                        "priority": "P2",
                    },
                )
                if c_res.status_code != 201:
                    errors.append(f"Create task {index} failed: {c_res.status_code}")
                    return
                t_id = c_res.json()["task"]["id"]
                created_task_ids.append(t_id)

                # 2. Patch to in_progress
                p1_res = client.patch(f"/api/tasks/{t_id}", json={"status": "in_progress", "priority": "P1"})
                if p1_res.status_code != 200:
                    errors.append(f"Patch task {t_id} to in_progress failed: {p1_res.status_code}")
                    return

                # 3. Patch to done
                p2_res = client.patch(f"/api/tasks/{t_id}", json={"status": "done", "delegated": True})
                if p2_res.status_code != 200:
                    errors.append(f"Patch task {t_id} to done failed: {p2_res.status_code}")
                    return
            except Exception as e:
                errors.append(f"Churn error on index {index}: {e}")

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_and_churn, i) for i in range(30)]
            for f in as_completed(futures):
                f.result()

        assert not errors, f"Task concurrency errors: {errors}"
        assert len(created_task_ids) == 30

        # Verify disk store integrity
        disk_data = json.loads(WORKSPACE_STORE_FILE.read_text(encoding="utf-8"))
        disk_task_map = {t["id"]: t for t in disk_data.get("tasks", [])}
        for tid in created_task_ids:
            assert tid in disk_task_map, f"Task {tid} missing from disk store!"
            assert disk_task_map[tid]["status"] == "done"
            assert disk_task_map[tid]["priority"] == "P1"
            assert disk_task_map[tid]["delegated"] is True

        # Clean up
        for tid in created_task_ids:
            client.delete(f"/api/tasks/{tid}")

    def test_active_workspace_deletion_fallback(self, client: TestClient) -> None:
        """Deleting the active workspace must automatically switch active_workspace_id without failure."""
        # Create ws-A and ws-B
        res_a = client.post("/api/workspaces", json={"name": "Workspace A"})
        id_a = res_a.json()["workspace"]["id"]
        res_b = client.post("/api/workspaces", json={"name": "Workspace B"})
        id_b = res_b.json()["workspace"]["id"]

        try:
            # Activate ws-A
            act_res = client.post("/api/workspaces/activate", json={"id": id_a})
            assert act_res.status_code == 200
            assert act_res.json()["active_workspace_id"] == id_a

            # Delete ws-A while it is active
            del_res = client.delete(f"/api/workspaces/{id_a}")
            assert del_res.status_code == 200
            del_data = del_res.json()
            new_active_id = del_data["active_workspace_id"]

            # Must NOT be deleted workspace id_a
            assert new_active_id != id_a
            # Must be one of the remaining workspaces
            remaining_ids = [w["id"] for w in del_data["workspaces"]]
            assert new_active_id in remaining_ids

            # Verify in GET /api/state
            state = client.get("/api/state").json()
            assert state["active_workspace_id"] == new_active_id
        finally:
            client.delete(f"/api/workspaces/{id_b}")


# ============================================================================
# Group 6: Strict CAD/OpenSCAD Token Eradication Verification
# ============================================================================

class TestZeroCadTokenEradication:
    """Empirical verification that all CAD/OpenSCAD fixtures are 100% eradicated."""

    CAD_FORBIDDEN_PATTERNS = [
        r"\bopenscad\b",
        r"\bcad\b",
        r"\bstl\b",
        r"\bcsg\b",
        r"3d fabrication",
        r"\btoolhead\b",
        r"overwrite_stl",
        r"\bmanifold\b",
        r"mesh viewport",
        r"3d-print",
        r"3d_print",
        r"\bextrusion\b",
        r"toolhead_mount",
    ]

    def test_som_endpoint_zero_cad_tokens(self, client: TestClient) -> None:
        """GET /api/som must contain zero CAD/OpenSCAD tokens across marks and metadata."""
        res = client.get("/api/som")
        assert res.status_code == 200
        raw_text = res.text.lower()

        # Scan for all forbidden patterns
        for pattern in self.CAD_FORBIDDEN_PATTERNS:
            matches = re.findall(pattern, raw_text, re.IGNORECASE)
            assert not matches, (
                f"Forbidden CAD pattern '{pattern}' found in /api/som response! Matches: {matches}"
            )

        data = res.json()
        assert data.get("status") == "ok"
        assert data.get("targets_mapped") == 12
        marks = data.get("marks", [])
        assert len(marks) == 12

        # Verify selectors use universal Window:: prefix
        for mark in marks:
            selector = mark.get("selector", "")
            assert selector.startswith("Window::"), (
                f"Mark {mark.get('tag')} has non-universal selector: {selector}"
            )
            # Verify coordinates are valid non-negative integers
            rect = mark.get("rect", [])
            assert len(rect) == 4
            assert all(isinstance(coord, int) and coord >= 0 for coord in rect)

    def test_scenario_reset_zero_cad_tokens(self, client: TestClient) -> None:
        """POST /api/scenario/reset must contain zero CAD tokens and seed generic confirmation."""
        res = client.post("/api/scenario/reset")
        assert res.status_code == 200
        reset_text = res.text.lower()

        for pattern in self.CAD_FORBIDDEN_PATTERNS:
            matches = re.findall(pattern, reset_text, re.IGNORECASE)
            assert not matches, (
                f"Forbidden CAD pattern '{pattern}' found in /api/scenario/reset response: {matches}"
            )

        data = res.json()
        assert data.get("status") == "scenario_reset"
        assert data.get("workspace") == "default"
        assert data.get("mission") == "Universal Agent Task Execution"

        # Check pending confirmation in state
        state_res = client.get("/api/state")
        assert state_res.status_code == 200
        pending = state_res.json().get("pending_confirmation")
        assert pending is not None

        pending_text = json.dumps(pending).lower()
        for pattern in self.CAD_FORBIDDEN_PATTERNS:
            matches = re.findall(pattern, pending_text, re.IGNORECASE)
            assert not matches, (
                f"Forbidden CAD pattern '{pattern}' found in pending_confirmation: {matches}"
            )

        assert pending.get("key") == "system_file_write"
        assert pending.get("title") == "Update workspace configuration"
        assert "Moderate" in pending.get("detail", "")

        # Clean up confirmation gate
        confirm_res = client.post("/api/confirm", json={"approve": True})
        assert confirm_res.status_code == 200
        assert "status=done" in confirm_res.json()["resolved"]

    def test_scenario_reset_idempotency_under_rapid_calls(self, client: TestClient) -> None:
        """Calling /api/scenario/reset 20 consecutive times seeds state consistently without leakage."""
        for _ in range(20):
            res = client.post("/api/scenario/reset")
            assert res.status_code == 200
            assert res.json()["mission"] == "Universal Agent Task Execution"

        # State has exactly one clean pending confirmation
        state = client.get("/api/state").json()
        pending = state.get("pending_confirmation")
        assert pending is not None
        assert pending["key"] == "system_file_write"

        # Approve and verify clear
        resolve_confirm(True)
        assert client.get("/api/state").json().get("pending_confirmation") is None


# ============================================================================
# Group 7: Extreme Edge Cases & Sandboxing Resilience
# ============================================================================

class TestExtremeEdgeCasesAndSandboxing:
    """Extreme resilience tests on storage recovery, sandboxing, and total wipeout."""

    def test_corrupted_store_file_auto_heals(self, client: TestClient) -> None:
        """Writing corrupted non-JSON to workspaces_store.json must not crash server and heals on init."""
        WORKSPACE_STORE_FILE.write_text("{ CORRUPTED_BAD_JSON !!!", encoding="utf-8")
        workspace_store._init_store()

        res = client.get("/api/workspaces")
        assert res.status_code == 200
        data = res.json()
        assert len(data["workspaces"]) >= 1
        assert data["active_workspace_id"] == "ws-default"

    def test_workspace_custom_working_dir_path_traversal_sandboxed(self, client: TestClient) -> None:
        """Even if a workspace specifies working_dir='../../', listing files still blocks with 403."""
        create_res = client.post(
            "/api/workspaces",
            json={
                "name": "Malicious Dir Workspace",
                "working_dir": "../../",
            },
        )
        assert create_res.status_code == 201
        ws_id = create_res.json()["workspace"]["id"]

        try:
            # Activate malicious workspace
            act_res = client.post("/api/workspaces/activate", json={"id": ws_id})
            assert act_res.status_code == 200

            # Query files without path parameter (uses active workspace's working_dir)
            files_res = client.get("/api/workspace/files")
            assert files_res.status_code == 403
            assert "Path traversal prohibited" in files_res.json().get("error", "")
        finally:
            client.delete(f"/api/workspaces/{ws_id}")

    def test_delete_all_workspaces_triggers_default_reinit(self, client: TestClient) -> None:
        """Deleting all workspaces in the system triggers auto-reinit to preserve active workspace."""
        current_ws = client.get("/api/workspaces").json()["workspaces"]
        for ws in current_ws:
            client.delete(f"/api/workspaces/{ws['id']}")

        # Verify system reinitialized ws-default
        final_ws = client.get("/api/workspaces").json()["workspaces"]
        assert len(final_ws) >= 1
        assert any(w["id"] == "ws-default" for w in final_ws)
        active_id = client.get("/api/workspaces").json()["active_workspace_id"]
        assert active_id == "ws-default"

