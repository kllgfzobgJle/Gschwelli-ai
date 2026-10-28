"""Adversarial stress test suite for Milestone 1 in server/api.py.

Empirical verification of:
1. State consistency: GET /api/state immediate reflection after workspace/task mutations.
2. Task status lifecycle: Cycling through all 5 statuses:
   backlog -> in_progress -> agent_delegated -> blocked -> done -> backlog.
3. Task delegation toggle: Toggling delegated: true and false.
4. File categorization: Accurate mapping of extensions
   (.py -> code, .md -> doc, .csv -> data, .svg -> media, .json -> config).
5. Persistence survival: State survival across simulated store and server reloads.
6. Concurrency stress: Concurrent task creation and status patching under threading pressure.
7. Adversarial edge cases: Validation rejection, path traversal guards, and special character safety.
"""

from __future__ import annotations

import concurrent.futures
import json
from pathlib import Path
import shutil
import sys
from typing import Any, Dict, List
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server.api import BASE_DIR, WorkspaceStore, create_app, workspace_store


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


# ============================================================================
# 1. State Consistency Tests
# ============================================================================

def test_state_consistency_workspace_and_tasks(client: TestClient) -> None:
    """Verify that creating workspaces and adding tasks immediately updates GET /api/state."""
    unique_tag = uuid4().hex[:6]
    ws_name = f"Stress Workspace {unique_tag}"
    ws_dir = f"workspace/stress_{unique_tag}"

    # 1. Create a new workspace
    create_res = client.post(
        "/api/workspaces",
        json={"name": ws_name, "prompt": "State Consistency Test", "working_dir": ws_dir},
    )
    assert create_res.status_code == 201, f"Failed to create workspace: {create_res.text}"
    ws_data = create_res.json()["workspace"]
    ws_id = ws_data["id"]

    try:
        # 2. Activate the workspace
        act_res = client.post("/api/workspaces/activate", json={"id": ws_id})
        assert act_res.status_code == 200

        # 3. Verify GET /api/state immediately reflects active workspace
        state_after_act = client.get("/api/state").json()
        assert state_after_act["active_workspace_id"] == ws_id, (
            f"State active_workspace_id ({state_after_act['active_workspace_id']}) != {ws_id}"
        )
        active_ws_list = [w for w in state_after_act["workspaces"] if w["is_active"]]
        assert len(active_ws_list) == 1, f"Expected exactly 1 active workspace, got {len(active_ws_list)}"
        assert active_ws_list[0]["id"] == ws_id

        # 4. Add tasks and verify immediate reflection in GET /api/state
        created_task_ids: List[str] = []
        for i in range(3):
            task_title = f"Consistency Task {unique_tag} #{i}"
            task_res = client.post(
                "/api/tasks",
                json={
                    "title": task_title,
                    "status": "backlog",
                    "priority": f"P{i+1}",
                    "delegated": (i % 2 == 1),
                },
            )
            assert task_res.status_code == 201
            t_id = task_res.json()["task"]["id"]
            created_task_ids.append(t_id)

            # Check GET /api/state immediately after EACH addition
            current_state = client.get("/api/state").json()
            state_task_ids = [t["id"] for t in current_state["tasks"]]
            assert t_id in state_task_ids, f"Task {t_id} not immediately reflected in GET /api/state"

        # 5. Verify task attributes in GET /api/state match created tasks
        final_state = client.get("/api/state").json()
        task_map = {t["id"]: t for t in final_state["tasks"]}
        for i, t_id in enumerate(created_task_ids):
            assert task_map[t_id]["priority"] == f"P{i+1}"
            assert task_map[t_id]["delegated"] == (i % 2 == 1)

        # 6. Delete tasks and verify immediate deletion in GET /api/state
        for t_id in created_task_ids:
            del_res = client.delete(f"/api/tasks/{t_id}")
            assert del_res.status_code == 200
            updated_state = client.get("/api/state").json()
            assert t_id not in [t["id"] for t in updated_state["tasks"]], (
                f"Deleted task {t_id} still present in GET /api/state"
            )

    finally:
        # Revert active workspace to default and cleanup test workspace
        client.post("/api/workspaces/activate", json={"id": "ws-default"})
        client.delete(f"/api/workspaces/{ws_id}")
        target_dir = BASE_DIR / ws_dir
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)


# ============================================================================
# 2. Task Status Lifecycle Tests (All 5 Statuses)
# ============================================================================

def test_task_status_lifecycle_all_five_states(client: TestClient) -> None:
    """Verify task cycles through: backlog -> in_progress -> agent_delegated -> blocked -> done -> backlog."""
    # 1. Create a task in initial backlog status
    create_res = client.post(
        "/api/tasks",
        json={"title": "Lifecycle Validation Probe", "status": "backlog", "priority": "P2"},
    )
    assert create_res.status_code == 201
    task = create_res.json()["task"]
    task_id = task["id"]
    assert task["status"] == "backlog"

    # Define full 5-state lifecycle cycle
    lifecycle_sequence = [
        "in_progress",
        "agent_delegated",
        "blocked",
        "done",
        "backlog",  # cycle complete
    ]

    try:
        for target_status in lifecycle_sequence:
            patch_res = client.patch(f"/api/tasks/{task_id}", json={"status": target_status})
            assert patch_res.status_code == 200, (
                f"Transition to {target_status} failed: {patch_res.text}"
            )
            patched_task = patch_res.json()["task"]
            assert patched_task["status"] == target_status

            # Verify GET /api/tasks
            tasks_list = client.get("/api/tasks").json()["tasks"]
            target_in_list = next((t for t in tasks_list if t["id"] == task_id), None)
            assert target_in_list is not None, f"Task {task_id} not found in /api/tasks"
            assert target_in_list["status"] == target_status

            # Verify GET /api/state
            state_tasks = client.get("/api/state").json()["tasks"]
            target_in_state = next((t for t in state_tasks if t["id"] == task_id), None)
            assert target_in_state is not None, f"Task {task_id} not found in /api/state"
            assert target_in_state["status"] == target_status

        # Adversarial check: Reject invalid status transitions with 400
        invalid_statuses = ["finished", "in-progress", "COMPLETE", "", "pending"]
        for bad_status in invalid_statuses:
            bad_res = client.patch(f"/api/tasks/{task_id}", json={"status": bad_status})
            assert bad_res.status_code == 400, (
                f"Expected 400 for invalid status '{bad_status}', got {bad_res.status_code}"
            )

        # Confirm status remained intact at "backlog" after rejected transitions
        state_tasks = client.get("/api/state").json()["tasks"]
        target_in_state = next((t for t in state_tasks if t["id"] == task_id), None)
        assert target_in_state["status"] == "backlog"

    finally:
        client.delete(f"/api/tasks/{task_id}")


# ============================================================================
# 3. Task Delegation Toggle Tests
# ============================================================================

def test_task_delegation_toggle(client: TestClient) -> None:
    """Verify toggling delegated: true and false across multiple transitions and combined patches."""
    create_res = client.post(
        "/api/tasks",
        json={"title": "Delegation Toggle Probe", "status": "backlog", "delegated": False},
    )
    assert create_res.status_code == 201
    task_id = create_res.json()["task"]["id"]

    try:
        # Toggle 1: False -> True
        p1 = client.patch(f"/api/tasks/{task_id}", json={"delegated": True})
        assert p1.status_code == 200
        assert p1.json()["task"]["delegated"] is True
        assert next(t for t in client.get("/api/tasks").json()["tasks"] if t["id"] == task_id)["delegated"] is True
        assert next(t for t in client.get("/api/state").json()["tasks"] if t["id"] == task_id)["delegated"] is True

        # Toggle 2: True -> False
        p2 = client.patch(f"/api/tasks/{task_id}", json={"delegated": False})
        assert p2.status_code == 200
        assert p2.json()["task"]["delegated"] is False
        assert next(t for t in client.get("/api/tasks").json()["tasks"] if t["id"] == task_id)["delegated"] is False
        assert next(t for t in client.get("/api/state").json()["tasks"] if t["id"] == task_id)["delegated"] is False

        # Toggle 3: Combined patch (delegated + status + priority + title)
        p3 = client.patch(
            f"/api/tasks/{task_id}",
            json={
                "delegated": True,
                "status": "agent_delegated",
                "priority": "P1",
                "title": "Delegation Toggle Probe - Delegated Active",
            },
        )
        assert p3.status_code == 200
        updated = p3.json()["task"]
        assert updated["delegated"] is True
        assert updated["status"] == "agent_delegated"
        assert updated["priority"] == "P1"
        assert updated["title"] == "Delegation Toggle Probe - Delegated Active"

        # Toggle 4: Return delegated to False while retaining P1
        p4 = client.patch(f"/api/tasks/{task_id}", json={"delegated": False})
        assert p4.status_code == 200
        updated4 = p4.json()["task"]
        assert updated4["delegated"] is False
        assert updated4["priority"] == "P1"

    finally:
        client.delete(f"/api/tasks/{task_id}")


# ============================================================================
# 4. File Categorization Tests
# ============================================================================

def test_file_categorization_extension_mapping(client: TestClient) -> None:
    """Verify that GET /api/workspace/files accurately maps extensions:
    .py -> code, .md -> doc, .csv -> data, .svg -> media, .json -> config.
    """
    # Part A: Verify workspace/default fixtures
    res = client.get("/api/workspace/files?path=workspace/default")
    assert res.status_code == 200
    files = res.json()
    assert isinstance(files, list)

    files_by_name = {f["name"]: f for f in files}

    # .py -> code
    assert "pipeline.py" in files_by_name
    assert files_by_name["pipeline.py"]["ext"] == "py"
    assert files_by_name["pipeline.py"]["category"] == "code"

    # .md -> doc
    assert "mission.md" in files_by_name
    assert files_by_name["mission.md"]["ext"] == "md"
    assert files_by_name["mission.md"]["category"] == "doc"

    # .csv -> data
    assert "sample_data.csv" in files_by_name
    assert files_by_name["sample_data.csv"]["ext"] == "csv"
    assert files_by_name["sample_data.csv"]["category"] == "data"

    # .svg -> media
    assert "architecture.svg" in files_by_name
    assert files_by_name["architecture.svg"]["ext"] == "svg"
    assert files_by_name["architecture.svg"]["category"] == "media"

    # .json -> config (agent_config.json)
    assert "agent_config.json" in files_by_name
    assert files_by_name["agent_config.json"]["ext"] == "json"
    assert files_by_name["agent_config.json"]["category"] == "config"

    # Part B: Synthetic extension matrix verification in a clean temporary directory
    matrix_dir = BASE_DIR / "workspace" / "matrix_test_env"
    matrix_dir.mkdir(parents=True, exist_ok=True)
    try:
        test_files = {
            "script.py": "print('hello')",
            "spec.md": "# Spec",
            "table.csv": "a,b\n1,2",
            "diagram.svg": "<svg></svg>",
            "app_config.json": '{"mode": "test"}',
        }
        for fname, content in test_files.items():
            (matrix_dir / fname).write_text(content, encoding="utf-8")

        res_matrix = client.get("/api/workspace/files?path=workspace/matrix_test_env")
        assert res_matrix.status_code == 200
        matrix_map = {f["name"]: f for f in res_matrix.json()}

        assert matrix_map["script.py"]["category"] == "code"
        assert matrix_map["spec.md"]["category"] == "doc"
        assert matrix_map["table.csv"]["category"] == "data"
        assert matrix_map["diagram.svg"]["category"] == "media"
        assert matrix_map["app_config.json"]["category"] == "config"

    finally:
        shutil.rmtree(matrix_dir, ignore_errors=True)


# ============================================================================
# 5. Persistence Survival Tests
# ============================================================================

def test_persistence_survival_on_simulated_reload(tmp_path: Path) -> None:
    """Verify state survival across simulated store restarts and re-initializations."""
    store_file = tmp_path / "test_store.json"

    # 1. Instantiate initial WorkspaceStore
    store1 = WorkspaceStore(store_file)
    init_workspaces = store1.get_workspaces()
    assert len(init_workspaces) >= 1

    # 2. Add custom workspace and tasks to store1
    new_ws = store1.create_workspace(
        name="Persistence Verification Sandbox",
        prompt="Autonomous Persistence Test Agent",
        working_dir="workspace/persist_test",
    )
    ws_id = new_ws["id"]
    store1.activate_workspace(ws_id)

    task_a = store1.create_task(
        title="Persisted Task A",
        status="agent_delegated",
        priority="P1",
        delegated=True,
        meta={"checkpoint": "alpha", "iter": 42},
    )
    task_b = store1.create_task(
        title="Persisted Task B",
        status="blocked",
        priority="P3",
        delegated=False,
        meta={"blocker": "waiting_on_review"},
    )

    # Verify store_file was written to disk
    assert store_file.exists()
    disk_data = json.loads(store_file.read_text(encoding="utf-8"))
    assert disk_data["active_workspace_id"] == ws_id
    assert len(disk_data["workspaces"]) >= 2
    assert any(t["id"] == task_a["id"] for t in disk_data["tasks"])

    # 3. Simulate process death & reload: Instantiate completely new store2 on same file
    store2 = WorkspaceStore(store_file)

    # 4. Verify all entities survived intact
    assert store2.get_active_workspace_id() == ws_id
    workspaces2 = store2.get_workspaces()
    survived_ws = next((w for w in workspaces2 if w["id"] == ws_id), None)
    assert survived_ws is not None
    assert survived_ws["name"] == "Persistence Verification Sandbox"
    assert survived_ws["is_active"] is True

    tasks2 = store2.get_tasks()
    survived_a = next((t for t in tasks2 if t["id"] == task_a["id"]), None)
    assert survived_a is not None
    assert survived_a["title"] == "Persisted Task A"
    assert survived_a["status"] == "agent_delegated"
    assert survived_a["priority"] == "P1"
    assert survived_a["delegated"] is True
    assert survived_a["meta"] == {"checkpoint": "alpha", "iter": 42}

    survived_b = next((t for t in tasks2 if t["id"] == task_b["id"]), None)
    assert survived_b is not None
    assert survived_b["status"] == "blocked"
    assert survived_b["meta"] == {"blocker": "waiting_on_review"}

    # 5. Adversarial: Corrupt file recovery
    corrupt_file = tmp_path / "corrupt_store.json"
    corrupt_file.write_text("{ THIS IS CORRUPT NOT VALID JSON }", encoding="utf-8")
    recovering_store = WorkspaceStore(corrupt_file)
    # Store must gracefully fall back to default fixtures without throwing unhandled exception
    assert recovering_store.get_active_workspace_id() == "ws-default"
    assert len(recovering_store.get_workspaces()) >= 1
    assert len(recovering_store.get_tasks()) >= 1


# ============================================================================
# 6. Concurrency Stress Tests
# ============================================================================

def test_adversarial_concurrency_stress(client: TestClient) -> None:
    """Stress test WorkspaceStore under concurrent task creation and patching pressure."""
    num_threads = 16
    created_task_ids: List[str] = []

    def _create_task(idx: int) -> Dict[str, Any]:
        res = client.post(
            "/api/tasks",
            json={
                "title": f"Concurrent Task Worker-{idx}",
                "status": "backlog",
                "priority": "P2",
                "delegated": False,
            },
        )
        assert res.status_code == 201
        return res.json()["task"]

    # Concurrently create tasks
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(_create_task, i) for i in range(num_threads)]
        for f in concurrent.futures.as_completed(futures):
            t = f.result()
            created_task_ids.append(t["id"])

    assert len(created_task_ids) == num_threads

    # Verify all tasks exist in state
    state_tasks = client.get("/api/state").json()["tasks"]
    state_ids = {t["id"] for t in state_tasks}
    for tid in created_task_ids:
        assert tid in state_ids, f"Concurrent task {tid} missing from state"

    # Concurrently patch tasks
    def _patch_task(tid: str) -> None:
        res = client.patch(
            f"/api/tasks/{tid}",
            json={"status": "in_progress", "delegated": True, "priority": "P1"},
        )
        assert res.status_code == 200

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        patch_futures = [executor.submit(_patch_task, tid) for tid in created_task_ids]
        for f in concurrent.futures.as_completed(patch_futures):
            f.result()

    # Verify patched values survived concurrently
    final_tasks = {t["id"]: t for t in client.get("/api/tasks").json()["tasks"]}
    for tid in created_task_ids:
        assert final_tasks[tid]["status"] == "in_progress"
        assert final_tasks[tid]["delegated"] is True
        assert final_tasks[tid]["priority"] == "P1"

    # Clean up all created tasks
    for tid in created_task_ids:
        client.delete(f"/api/tasks/{tid}")


# ============================================================================
# 7. Edge Cases and Security Mining
# ============================================================================

def test_adversarial_edge_cases_and_security(client: TestClient) -> None:
    """Stress test boundary validation, empty fields, 404s, and path traversal guards."""
    # 1. Empty workspace name rejected with 400
    res_empty_ws = client.post("/api/workspaces", json={"name": "   "})
    assert res_empty_ws.status_code == 400
    assert "empty" in res_empty_ws.json()["error"].lower()

    # 2. Empty task title rejected with 400
    res_empty_task = client.post("/api/tasks", json={"title": "   "})
    assert res_empty_task.status_code == 400
    assert "empty" in res_empty_task.json()["error"].lower()

    # 3. Patching task title to empty rejected with 400
    dummy = client.post("/api/tasks", json={"title": "Valid Initial Title"}).json()["task"]
    tid = dummy["id"]
    try:
        res_empty_patch = client.patch(f"/api/tasks/{tid}", json={"title": ""})
        assert res_empty_patch.status_code == 400

        # 4. Invalid priority rejected with 400
        res_bad_pri = client.patch(f"/api/tasks/{tid}", json={"priority": "P99"})
        assert res_bad_pri.status_code == 400

        # 5. Non-existent IDs return 404
        assert client.patch("/api/tasks/task-nonexistent-12345", json={"status": "done"}).status_code == 404
        assert client.delete("/api/tasks/task-nonexistent-12345").status_code == 404
        assert client.post("/api/workspaces/activate", json={"id": "ws-nonexistent-12345"}).status_code == 404
        assert client.delete("/api/workspaces/ws-nonexistent-12345").status_code == 404

        # 6. Path traversal guard returns 403
        traversal_res = client.get("/api/workspace/files?path=../../windows/system32")
        assert traversal_res.status_code == 403, (
            f"Expected 403 on traversal attempt, got {traversal_res.status_code}"
        )

        # 7. Unicode and special characters preserved faithfully
        special_title = "🤖 Task: <script>alert('xss')</script> & 'quotes' — [P1] ⚡"
        spec_res = client.patch(f"/api/tasks/{tid}", json={"title": special_title})
        assert spec_res.status_code == 200
        assert spec_res.json()["task"]["title"] == special_title

        state_check = next(t for t in client.get("/api/state").json()["tasks"] if t["id"] == tid)
        assert state_check["title"] == special_title

    finally:
        client.delete(f"/api/tasks/{tid}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
