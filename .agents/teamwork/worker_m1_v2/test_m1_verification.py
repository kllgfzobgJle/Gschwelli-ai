import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
import pytest

from server.api import create_app, BASE_DIR, workspace_store


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_state_extended_keys(client: TestClient):
    """GET /api/state returns all 8 standard keys plus workspaces, active_workspace_id, tasks."""
    res = client.get("/api/state")
    assert res.status_code == 200
    data = res.json()
    
    # 8 standard keys
    required = ["system", "tools", "cache", "memory", "undo", "pending_confirmation", "history", "voice"]
    for k in required:
        assert k in data, f"Missing standard key: {k}"

    # New M1 keys
    assert "workspaces" in data, "Missing workspaces in state"
    assert "active_workspace_id" in data, "Missing active_workspace_id in state"
    assert "tasks" in data, "Missing tasks in state"
    assert isinstance(data["workspaces"], list)
    assert isinstance(data["tasks"], list)
    assert len(data["workspaces"]) >= 1
    assert data["active_workspace_id"] == "ws-default"


def test_som_universal_marks(client: TestClient):
    """GET /api/som returns 12 universal application marks with zero CAD references."""
    res = client.get("/api/som")
    assert res.status_code == 200
    data = res.json()
    assert data.get("status") == "ok"
    assert data.get("targets_mapped") == 12
    assert data.get("fusion_confidence") >= 0.99
    
    marks = data.get("marks", [])
    assert len(marks) == 12

    raw_json = json.dumps(data)
    for forbidden in ["OpenSCAD", "CSG", "Mesh Viewport", "Dimension", "Manifold", "toolhead"]:
        assert forbidden not in raw_json, f"Found forbidden CAD token: {forbidden}"

    tags = {m["tag"]: m for m in marks}
    for i in range(1, 13):
        tag_str = f"[{i:02d}]"
        assert tag_str in tags, f"Missing SOM tag: {tag_str}"

    assert tags["[01]"]["type"] == "menu"
    assert tags["[02]"]["type"] == "titlebar"
    assert tags["[03]"]["type"] == "treeview"
    assert tags["[04]"]["type"] == "button"
    assert tags["[05]"]["type"] == "viewport"
    assert tags["[06]"]["type"] == "gizmo"
    assert tags["[07]"]["type"] == "toolbar"
    assert tags["[08]"]["type"] == "panel"
    assert tags["[09]"]["type"] == "badge"
    assert tags["[10]"]["type"] == "terminal"
    assert tags["[11]"]["type"] == "badge"
    assert tags["[12]"]["type"] == "textbox"


def test_scenario_reset_generic(client: TestClient):
    """POST /api/scenario/reset seeds generic pending confirmation."""
    res = client.post("/api/scenario/reset")
    assert res.status_code == 200
    data = res.json()
    assert data.get("status") == "scenario_reset"
    assert data.get("workspace") == "default"
    assert data.get("mission") == "Universal Agent Task Execution"

    state = client.get("/api/state").json()
    pending = state.get("pending_confirmation")
    assert pending is not None
    assert pending.get("key") == "system_file_write"
    assert pending.get("title") == "Update workspace configuration"
    assert "Moderate" in pending.get("detail", "")

    # Clean up confirmation gate
    confirm_res = client.post("/api/confirm", json={"approve": True})
    assert confirm_res.status_code == 200


def test_workspace_crud_lifecycle(client: TestClient):
    """Test full Workspace CRUD: create, list, activate, delete."""
    # 1. List initial workspaces
    res = client.get("/api/workspaces")
    assert res.status_code == 200
    initial = res.json()
    assert "workspaces" in initial
    assert "active_workspace_id" in initial
    initial_count = len(initial["workspaces"])

    # 2. Create new workspace
    new_res = client.post(
        "/api/workspaces",
        json={
            "name": "Research Ops",
            "prompt": "Autonomous Literature & Data Analysis",
            "working_dir": "workspace/research",
        },
    )
    assert new_res.status_code == 201
    created_data = new_res.json()
    assert created_data["status"] == "created"
    ws = created_data["workspace"]
    assert ws["name"] == "Research Ops"
    assert ws["working_dir"] == "workspace/research"
    ws_id = ws["id"]

    # 3. Activate new workspace
    act_res = client.post("/api/workspaces/activate", json={"id": ws_id})
    assert act_res.status_code == 200
    act_data = act_res.json()
    assert act_data["status"] == "activated"
    assert act_data["active_workspace_id"] == ws_id

    # Verify active in state
    state = client.get("/api/state").json()
    assert state["active_workspace_id"] == ws_id

    # 4. Delete created workspace
    del_res = client.delete(f"/api/workspaces/{ws_id}")
    assert del_res.status_code == 200
    del_data = del_res.json()
    assert del_data["status"] == "deleted"
    assert del_data["id"] == ws_id


def test_task_crud_lifecycle(client: TestClient):
    """Test full Task CRUD: create, patch status/priority/delegation, delete."""
    # 1. Create task
    create_res = client.post(
        "/api/tasks",
        json={
            "title": "Verify SOM perception pipeline",
            "status": "backlog",
            "priority": "P1",
            "delegated": False,
        },
    )
    assert create_res.status_code == 201
    task = create_res.json()["task"]
    task_id = task["id"]
    assert task["title"] == "Verify SOM perception pipeline"
    assert task["status"] == "backlog"
    assert task["priority"] == "P1"
    assert task["delegated"] is False

    # 2. Patch status and delegation
    patch_res = client.patch(
        f"/api/tasks/{task_id}",
        json={
            "status": "agent_delegated",
            "delegated": True,
            "priority": "P1",
        },
    )
    assert patch_res.status_code == 200
    updated_task = patch_res.json()["task"]
    assert updated_task["status"] == "agent_delegated"
    assert updated_task["delegated"] is True

    # 3. Cycle to in_progress and then done
    patch2 = client.patch(f"/api/tasks/{task_id}", json={"status": "done"})
    assert patch2.status_code == 200
    assert patch2.json()["task"]["status"] == "done"

    # 4. Delete task
    del_res = client.delete(f"/api/tasks/{task_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"


def test_workspace_file_browser(client: TestClient):
    """GET /api/workspace/files lists categorized files for active workspace."""
    # Test listing workspace/default
    res = client.get("/api/workspace/files?path=workspace/default")
    assert res.status_code == 200
    files = res.json()
    assert isinstance(files, list)
    assert len(files) >= 4

    names = {f["name"]: f for f in files}
    assert "mission.md" in names
    assert names["mission.md"]["category"] == "doc"
    assert names["mission.md"]["ext"] == "md"

    assert "pipeline.py" in names
    assert names["pipeline.py"]["category"] == "code"
    assert names["pipeline.py"]["ext"] == "py"

    assert "sample_data.csv" in names
    assert names["sample_data.csv"]["category"] == "data"
    assert names["sample_data.csv"]["ext"] == "csv"

    assert "agent_config.json" in names
    assert names["agent_config.json"]["category"] == "config"
    assert names["agent_config.json"]["ext"] == "json"

    if "architecture.svg" in names:
        assert names["architecture.svg"]["category"] == "media"
        assert names["architecture.svg"]["ext"] == "svg"

    for f in files:
        assert "name" in f
        assert "path" in f
        assert "is_dir" in f
        assert "size" in f
        assert "ext" in f
        assert "category" in f
        assert f["category"] in {"code", "doc", "data", "media", "config"}
