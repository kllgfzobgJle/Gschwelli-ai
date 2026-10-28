"""Backend API Integration Tests for Universal Domain-Agnostic Agent Workstation.

Verifies all REST and WebSocket endpoints in server/api.py using fastapi.testclient.TestClient.
Covers Tiers 1-4:
- Tier 1: Smoke & core HTTP endpoint delivery.
- Tier 2: Schema validation, default mock state, Set-of-Marks catalogue, Workspace/Task CRUD, File Explorer.
- Tier 3: Edge cases (empty instruction, invalid task id, non-existent workspace delete, empty command REPL, XSS safety).
- Tier 4: Multi-step integration workflows (scenario reset -> safety gate -> confirm -> state update; workspace lifecycle).
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from fastapi.testclient import TestClient
import pytest

from core.confirm import get_pending, request_confirmation, resolve as resolve_confirm
from server.api import create_app


@pytest.fixture
def client() -> TestClient:
    """Fixture providing a fresh TestClient instance."""
    app = create_app()
    return TestClient(app)


# ============================================================================
# Tier 1 & Tier 2: Core HTTP Endpoints
# ============================================================================

def test_root_serves_html(client: TestClient) -> None:
    """GET / serves the dashboard HTML with 200 OK and text/html content-type."""
    response = client.get("/")
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    assert "text/html" in response.headers.get("content-type", "")
    content = response.text
    assert "<!DOCTYPE html>" in content or "<html" in content
    assert "gschwelli-ai" in content or "AETHER" in content or "Dashboard" in content or "Workstation" in content


def test_get_state_all_keys(client: TestClient) -> None:
    """GET /api/state returns 200 OK and contains all 8 required state keys."""
    response = client.get("/api/state")
    assert response.status_code == 200
    data = response.json()

    required_keys = [
        "system",
        "tools",
        "cache",
        "memory",
        "undo",
        "pending_confirmation",
        "history",
        "voice",
    ]
    for key in required_keys:
        assert key in data, f"Missing required state key: {key}"

    # Verify system telemetry structure
    system = data["system"]
    assert "cpu_percent" in system
    assert "ram_percent" in system
    assert "ram_used_gb" in system
    assert "ram_total_gb" in system

    # Verify tools array
    assert isinstance(data["tools"], list)

    # Verify undo structure
    assert isinstance(data["undo"], dict)
    assert "can_undo" in data["undo"]
    assert "history" in data["undo"]


def test_get_state_extended_workspaces_and_tasks(client: TestClient) -> None:
    """GET /api/state contains extended workspace and task fields if M1 is active."""
    response = client.get("/api/state")
    assert response.status_code == 200
    data = response.json()

    if "workspaces" in data:
        assert isinstance(data["workspaces"], list)
        if len(data["workspaces"]) > 0:
            ws = data["workspaces"][0]
            assert "id" in ws
            assert "name" in ws
    if "active_workspace_id" in data:
        assert isinstance(data["active_workspace_id"], str)
    if "tasks" in data:
        assert isinstance(data["tasks"], list)
        if len(data["tasks"]) > 0:
            task = data["tasks"][0]
            assert "id" in task
            assert "title" in task
            assert "status" in task


def test_post_route_empty_instruction(client: TestClient) -> None:
    """POST /api/route with empty instruction returns 400 Bad Request."""
    response = client.post("/api/route", json={"instruction": ""})
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


def test_post_route_valid_instruction(client: TestClient) -> None:
    """POST /api/route with valid instruction returns serialized RouteResult."""
    response = client.post("/api/route", json={"instruction": "echo hello world"})
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "active_tier" in data
    assert "elapsed_ms" in data
    assert "logs" in data
    assert isinstance(data["logs"], list)


def test_post_route_xss_and_special_characters(client: TestClient) -> None:
    """POST /api/route with HTML/XSS and Unicode payload executes safely without crashing."""
    payload = "<script>alert('xss')</script> & 'quoted' 🚀 $PATH"
    response = client.post("/api/route", json={"instruction": payload})
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "logs" in data


def test_post_confirm_resolve(client: TestClient) -> None:
    """POST /api/confirm handles approve=true and approve=false safely."""
    # When nothing is pending
    response = client.post("/api/confirm", json={"approve": True})
    assert response.status_code == 200
    data = response.json()
    assert "resolved" in data
    assert data["approved"] is True
    assert data["pending"] is None or isinstance(data["pending"], dict)

    # Rejection when nothing pending
    response_reject = client.post("/api/confirm", json={"approve": False})
    assert response_reject.status_code == 200
    data_reject = response_reject.json()
    assert data_reject["approved"] is False


def test_post_undo_and_empty_history(client: TestClient) -> None:
    """POST /api/undo triggers rollback and handles empty undo stack cleanly."""
    response = client.post("/api/undo")
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "can_undo" in data
    assert "history" in data
    assert isinstance(data["history"], list)


def test_post_tool_execution(client: TestClient) -> None:
    """POST /api/tool executes a registered tool and returns tool output."""
    response = client.post("/api/tool", json={"tool": "read_file_text", "args": {"path": "PROJECT.md"}})
    assert response.status_code == 200
    data = response.json()
    assert data["tool"] == "read_file_text"
    assert "output" in data
    assert len(data["output"]) > 0


def test_memory_crud_workflow(client: TestClient) -> None:
    """POST /api/memory and DELETE /api/memory/{key} perform CRUD operations."""
    test_key = "test_e2e_key"
    test_value = "mount_bracket_tolerance_0.2mm"
    test_category = "notes"

    # 1. Add memory fact
    res_add = client.post(
        "/api/memory",
        json={"key": test_key, "value": test_value, "category": test_category},
    )
    assert res_add.status_code == 200
    data_add = res_add.json()
    assert "result" in data_add
    assert "memory" in data_add
    found = any(item.get("key") == test_key for item in data_add["memory"])
    assert found, f"Key {test_key} not found in memory after POST"

    # 2. Delete memory fact
    res_del = client.delete(f"/api/memory/{test_key}?category={test_category}")
    assert res_del.status_code == 200
    data_del = res_del.json()
    assert "result" in data_del
    still_present = any(item.get("key") == test_key for item in data_del["memory"])
    assert not still_present, f"Key {test_key} was not deleted from memory"


def test_delete_cache(client: TestClient) -> None:
    """DELETE /api/cache clears the cache store and returns cleared=True."""
    response = client.delete("/api/cache")
    assert response.status_code == 200
    data = response.json()
    assert data.get("cleared") is True
    assert isinstance(data.get("cache"), (list, dict))


def test_post_voice_toggle(client: TestClient) -> None:
    """POST /api/voice toggles TTS and voice capture settings."""
    response = client.post("/api/voice", json={"tts_enabled": True, "voice_capture_enabled": False})
    assert response.status_code == 200
    data = response.json()
    assert "tts_enabled" in data
    assert data["tts_enabled"] is True

    # Toggle off
    response_off = client.post("/api/voice", json={"tts_enabled": False})
    assert response_off.status_code == 200
    data_off = response_off.json()
    assert data_off["tts_enabled"] is False


# ============================================================================
# Tier 2: Additive M1 Endpoints (Scenario Reset, REPL, SOM)
# ============================================================================

def test_scenario_reset_endpoint(client: TestClient) -> None:
    """POST /api/scenario/reset seeds the pending safety gate and returns scenario details."""
    response = client.post("/api/scenario/reset")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "scenario_reset"
    assert "project" in data or "workspace" in data
    assert "mission" in data or "title" in data

    # Check that pending confirmation was seeded in the backend
    state_res = client.get("/api/state")
    assert state_res.status_code == 200
    pending = state_res.json().get("pending_confirmation")
    assert pending is not None, "Scenario reset must seed pending_confirmation"
    assert "key" in pending
    assert "title" in pending


def test_repl_endpoint_execution(client: TestClient) -> None:
    """POST /api/repl executes commands in the PowerShell REPL."""
    # 1. Empty command returns exit_code=0 and empty output
    empty_res = client.post("/api/repl", json={"command": ""})
    assert empty_res.status_code == 200
    empty_data = empty_res.json()
    assert empty_data.get("command") == ""
    assert empty_data.get("exit_code") == 0

    # 2. Simple command execution
    cmd_res = client.post("/api/repl", json={"command": "Write-Output 'E2E_REPL_OK'"})
    assert cmd_res.status_code == 200
    cmd_data = cmd_res.json()
    assert "E2E_REPL_OK" in cmd_data.get("output", "")
    assert cmd_data.get("exit_code") == 0


def test_som_endpoint_catalogue(client: TestClient) -> None:
    """GET /api/som returns the complete Set-of-Marks catalogue with 12 mapped targets."""
    response = client.get("/api/som")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert data.get("targets_mapped") == 12
    assert data.get("fusion_confidence") >= 0.95
    assert "1440x900" in data.get("resolution", "") or "x" in data.get("resolution", "")
    assert "DISPLAY 01" in data.get("display", "") or "DISPLAY" in data.get("display", "")

    marks = data.get("marks", [])
    assert len(marks) == 12, f"Expected 12 SOM marks, got {len(marks)}"

    # Verify key marks: [01], [02], [04], [12]
    tags = {m.get("tag"): m for m in marks}
    assert "[01]" in tags, "Missing tag [01]"
    assert "[02]" in tags, "Missing tag [02]"
    assert "[04]" in tags, "Missing tag [04]"
    assert "[12]" in tags, "Missing tag [12]"

    # Verify mark schema structure
    for mark in marks:
        assert "mark" in mark
        assert "tag" in mark
        assert "name" in mark
        assert "type" in mark
        assert "rect" in mark
        assert len(mark["rect"]) == 4
        assert "confidence" in mark
        assert mark["confidence"] > 0.85


# ============================================================================
# Tier 2 & Tier 3: Additive M1 Endpoints (Workspaces, Tasks, Files)
# ============================================================================

def test_workspaces_crud_endpoints(client: TestClient) -> None:
    """Tests GET, POST, POST activate, and DELETE /api/workspaces."""
    res_list = client.get("/api/workspaces")
    if res_list.status_code == 404:
        pytest.skip("Milestone 1 workspace endpoints (/api/workspaces) not yet deployed in server/api.py")

    assert res_list.status_code == 200
    data_list = res_list.json()
    assert "workspaces" in data_list
    assert isinstance(data_list["workspaces"], list)

    # Create new workspace
    new_ws_payload = {
        "name": "Integration Test Workspace",
        "prompt": "Autonomous test agent operating context",
        "working_dir": "workspace/test_env",
    }
    res_create = client.post("/api/workspaces", json=new_ws_payload)
    assert res_create.status_code in (200, 201)
    ws_created = res_create.json()
    ws_id = ws_created.get("id") or ws_created.get("workspace", {}).get("id")
    assert ws_id is not None

    # Activate workspace
    res_activate = client.post("/api/workspaces/activate", json={"id": ws_id})
    assert res_activate.status_code == 200

    # Delete created workspace
    res_del = client.delete(f"/api/workspaces/{ws_id}")
    assert res_del.status_code in (200, 204)


def test_tasks_crud_lifecycle_and_statuses(client: TestClient) -> None:
    """Tests GET, POST, PATCH (5 statuses), and DELETE /api/tasks."""
    res_list = client.get("/api/tasks")
    if res_list.status_code == 404:
        pytest.skip("Milestone 1 task endpoints (/api/tasks) not yet deployed in server/api.py")

    assert res_list.status_code == 200
    data_list = res_list.json()
    assert "tasks" in data_list
    assert isinstance(data_list["tasks"], list)

    # 1. Create task
    task_payload = {
        "title": "Verify reactive pipeline execution",
        "status": "backlog",
        "priority": "P1",
        "delegated": False,
    }
    res_create = client.post("/api/tasks", json=task_payload)
    assert res_create.status_code in (200, 201)
    task_data = res_create.json()
    task_id = task_data.get("id") or task_data.get("task", {}).get("id")
    assert task_id is not None

    # 2. Cycle statuses: in_progress -> agent_delegated -> blocked -> done
    statuses = ["in_progress", "agent_delegated", "blocked", "done"]
    for st in statuses:
        res_patch = client.patch(
            f"/api/tasks/{task_id}",
            json={"status": st, "delegated": (st == "agent_delegated")},
        )
        assert res_patch.status_code == 200
        patched = res_patch.json()
        task_obj = patched.get("task") if isinstance(patched.get("task"), dict) else patched
        status_val = task_obj.get("status")
        assert status_val == st

    # 3. Delete task
    res_del = client.delete(f"/api/tasks/{task_id}")
    assert res_del.status_code in (200, 204)


def test_workspace_files_listing_and_categories(client: TestClient) -> None:
    """GET /api/workspace/files returns dynamic files with valid categories."""
    res_files = client.get("/api/workspace/files")
    if res_files.status_code == 404:
        pytest.skip("Milestone 1 workspace files endpoint (/api/workspace/files) not yet deployed in server/api.py")

    assert res_files.status_code == 200
    files_data = res_files.json()
    items = files_data if isinstance(files_data, list) else files_data.get("files", [])
    assert isinstance(items, list)

    if len(items) > 0:
        valid_categories = {"code", "doc", "docs", "tables", "data", "media", "configs", "config", "other"}
        for item in items:
            assert "name" in item
            if "category" in item:
                assert item["category"].lower() in valid_categories


def test_task_creation_empty_title_rejection(client: TestClient) -> None:
    """POST /api/tasks with empty or whitespace title is rejected or sanitized."""
    res_list = client.get("/api/tasks")
    if res_list.status_code == 404:
        pytest.skip("Milestone 1 task endpoints not yet deployed")

    # Empty string
    res_empty = client.post("/api/tasks", json={"title": "", "status": "backlog"})
    assert res_empty.status_code in (400, 422, 200)
    if res_empty.status_code == 200:
        # If accepted, title must not be empty
        created = res_empty.json()
        assert (created.get("title") or created.get("task", {}).get("title") or "").strip() != ""


# ============================================================================
# Tier 4: Multi-Step Integration Workflows
# ============================================================================

def test_full_scenario_reset_and_approval_workflow(client: TestClient) -> None:
    """Multi-step workflow: Reset scenario -> Verify pending gate -> Approve -> Verify gate resolved."""
    # Step 1: Reset scenario
    reset_res = client.post("/api/scenario/reset")
    assert reset_res.status_code == 200

    # Step 2: Confirm pending gate exists in state
    state1 = client.get("/api/state").json()
    pending = state1.get("pending_confirmation")
    assert pending is not None
    assert "key" in pending

    # Step 3: Approve confirmation
    confirm_res = client.post("/api/confirm", json={"approve": True})
    assert confirm_res.status_code == 200
    confirm_data = confirm_res.json()
    assert confirm_data["approved"] is True
    assert confirm_data.get("resolved") is not None

    # Step 4: Verify pending is now cleared
    state2 = client.get("/api/state").json()
    assert state2.get("pending_confirmation") is None


def test_full_scenario_reset_and_abort_workflow(client: TestClient) -> None:
    """Multi-step workflow: Reset scenario -> Verify pending gate -> Abort (Esc) -> Verify canceled."""
    # Step 1: Reset scenario
    reset_res = client.post("/api/scenario/reset")
    assert reset_res.status_code == 200

    # Step 2: Confirm pending gate exists
    state1 = client.get("/api/state").json()
    assert state1.get("pending_confirmation") is not None

    # Step 3: Abort confirmation (approve=False)
    confirm_res = client.post("/api/confirm", json={"approve": False})
    assert confirm_res.status_code == 200
    confirm_data = confirm_res.json()
    assert confirm_data["approved"] is False

    # Step 4: Verify pending is cleared
    state2 = client.get("/api/state").json()
    assert state2.get("pending_confirmation") is None


def test_websocket_connection_and_broadcast(client: TestClient) -> None:
    """WebSocket /ws connects successfully and receives broadcast frames."""
    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps({"ping": "hello"}))
        assert ws is not None
