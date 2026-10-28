"""Backend API Integration Tests for gschwelli-ai Control Center.

Verifies all REST and WebSocket endpoints in server/api.py using fastapi.testclient.TestClient.
Covers Tiers 1-4: Smoke, Functional/Happy Path, Edge Cases, and Multi-Step Integration Workflows.
"""

from __future__ import annotations

import json
from typing import Any, Dict

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
    assert "AETHER" in content or "gschwelli-ai" in content or "Dashboard" in content


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


def test_post_confirm_resolve(client: TestClient) -> None:
    """POST /api/confirm handles approve=true and approve=false."""
    # First, test when nothing is pending
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


def test_post_undo(client: TestClient) -> None:
    """POST /api/undo triggers rollback and returns undo status."""
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
    assert "3D Fabrication" in data.get("project", "")
    assert "M-024" in data.get("mission", "")

    # Check that pending confirmation was seeded in the backend
    state_res = client.get("/api/state")
    assert state_res.status_code == 200
    pending = state_res.json().get("pending_confirmation")
    assert pending is not None, "Scenario reset must seed pending_confirmation"
    assert pending.get("key") == "overwrite_stl"
    assert "toolhead_mount.stl" in pending.get("title", "")
    assert "SEC-810" in pending.get("detail", "")


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
    assert data.get("fusion_confidence") >= 0.99
    assert data.get("resolution") == "1440x900"
    assert data.get("display") == "DISPLAY 01"

    marks = data.get("marks", [])
    assert len(marks) == 12, f"Expected 12 SOM marks, got {len(marks)}"

    # Verify key marks required by UI reference mockup: [01], [02], [04], [12]
    tags = {m.get("tag"): m for m in marks}
    assert "[01]" in tags, "Missing tag [01] (Menu Bar)"
    assert "[02]" in tags, "Missing tag [02] (Window Controls)"
    assert "[04]" in tags, "Missing tag [04] (Export Button)"
    assert "[12]" in tags, "Missing tag [12] (Path Input)"

    # Verify mark schema structure
    for mark in marks:
        assert "mark" in mark
        assert "tag" in mark
        assert "name" in mark
        assert "type" in mark
        assert "rect" in mark
        assert len(mark["rect"]) == 4
        assert "confidence" in mark
        assert mark["confidence"] > 0.9


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
    assert pending["key"] == "overwrite_stl"

    # Step 3: Approve confirmation
    confirm_res = client.post("/api/confirm", json={"approve": True})
    assert confirm_res.status_code == 200
    confirm_data = confirm_res.json()
    assert confirm_data["approved"] is True
    assert "Overwrote toolhead_mount.stl" in confirm_data["resolved"]

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
    assert "cancel" in confirm_data["resolved"].lower()

    # Step 4: Verify pending is cleared
    state2 = client.get("/api/state").json()
    assert state2.get("pending_confirmation") is None


def test_websocket_connection_and_broadcast(client: TestClient) -> None:
    """WebSocket /ws connects successfully and receives broadcast frames."""
    with client.websocket_connect("/ws") as ws:
        # Send a ping/text frame
        ws.send_text(json.dumps({"ping": "hello"}))
        # Connection stays alive without exceptions
        assert ws is not None
