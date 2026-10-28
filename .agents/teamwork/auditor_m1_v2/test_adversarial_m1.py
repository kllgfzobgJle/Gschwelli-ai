"""Independent Adversarial Stress & Integrity Probe for Milestone 1.

Written by Forensic Auditor (auditor_m1_v2).
Tests assumption boundaries, failure modes, security guards, concurrency, and persistence authenticity.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import threading

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from server.api import create_app, workspace_store, BASE_DIR, WORKSPACE_STORE_FILE


def test_adversarial_suite():
    print("=== STARTING ADVERSARIAL STRESS TEST SUITE ===")
    app = create_app()
    client = TestClient(app)

    # ---------------------------------------------------------
    # 1. Path Traversal & Security Sandbox in /api/workspace/files
    # ---------------------------------------------------------
    print("\n[Probe 1] Testing Path Traversal Protections...")
    traversal_payloads = [
        "../..",
        "../../Windows",
        "../server",
        "../../../../../../../../Windows/System32",
        "C:\\Windows",
        "/etc/passwd",
    ]
    for p in traversal_payloads:
        res = client.get(f"/api/workspace/files?path={p}")
        print(f"  Payload: {p} -> HTTP {res.status_code}")
        assert res.status_code in (403, 400), f"Expected 403 Forbidden for traversal {p}, got {res.status_code}"
        assert "prohibited" in res.json().get("error", "").lower() or res.status_code == 403

    # Non-existent safe path returns empty list []
    res = client.get("/api/workspace/files?path=workspace/nonexistent_folder_abc123")
    assert res.status_code == 200
    assert res.json() == [], f"Expected empty list for nonexistent dir, got {res.json()}"
    print("  Safe nonexistent path returned empty list [] correctly.")

    # ---------------------------------------------------------
    # 2. Workspace Validation & Malformed Inputs
    # ---------------------------------------------------------
    print("\n[Probe 2] Testing Workspace Validation & Edge Cases...")
    
    # Empty name
    res = client.post("/api/workspaces", json={"name": ""})
    assert res.status_code == 400, f"Expected 400 for empty name, got {res.status_code}"
    
    # Whitespace-only name
    res = client.post("/api/workspaces", json={"name": "   "})
    assert res.status_code == 400, f"Expected 400 for whitespace name, got {res.status_code}"

    # Activating nonexistent workspace
    res = client.post("/api/workspaces/activate", json={"id": "ws-ghost-99999"})
    assert res.status_code == 404, f"Expected 404 for ghost workspace, got {res.status_code}"

    # Deleting nonexistent workspace
    res = client.delete("/api/workspaces/ws-ghost-99999")
    assert res.status_code == 404, f"Expected 404 for ghost delete, got {res.status_code}"

    # ---------------------------------------------------------
    # 3. Task Validation & Malformed Inputs
    # ---------------------------------------------------------
    print("\n[Probe 3] Testing Task Validation & Edge Cases...")

    # Empty title
    res = client.post("/api/tasks", json={"title": ""})
    assert res.status_code == 400, f"Expected 400 for empty task title, got {res.status_code}"

    # Whitespace-only title
    res = client.post("/api/tasks", json={"title": "   "})
    assert res.status_code == 400, f"Expected 400 for whitespace task title, got {res.status_code}"

    # Updating with invalid status
    res = client.post("/api/tasks", json={"title": "Valid Temp Task"})
    assert res.status_code == 201
    tid = res.json()["task"]["id"]

    res = client.patch(f"/api/tasks/{tid}", json={"status": "invalid_status_xyz"})
    assert res.status_code == 400, f"Expected 400 for invalid status, got {res.status_code}"

    # Updating with invalid priority
    res = client.patch(f"/api/tasks/{tid}", json={"priority": "P99"})
    assert res.status_code == 400, f"Expected 400 for invalid priority, got {res.status_code}"

    # Updating with empty title
    res = client.patch(f"/api/tasks/{tid}", json={"title": "  "})
    assert res.status_code == 400, f"Expected 400 for empty title in patch, got {res.status_code}"

    # Updating nonexistent task
    res = client.patch("/api/tasks/task-ghost-99999", json={"title": "foo"})
    assert res.status_code == 404, f"Expected 404 for nonexistent task patch, got {res.status_code}"

    # Deleting nonexistent task
    res = client.delete("/api/tasks/task-ghost-99999")
    assert res.status_code == 404, f"Expected 404 for nonexistent task delete, got {res.status_code}"

    # Cleanup temp task
    client.delete(f"/api/tasks/{tid}")

    # ---------------------------------------------------------
    # 4. Multi-Threaded Concurrent Mutations (Thread Safety)
    # ---------------------------------------------------------
    print("\n[Probe 4] Testing Multi-Threaded Concurrency on WorkspaceStore...")
    errors = []

    def worker_thread(index: int):
        try:
            # Create a task
            t_res = client.post("/api/tasks", json={"title": f"Concurrent Task {index}", "priority": "P2"})
            if t_res.status_code != 201:
                errors.append(f"Thread {index} create failed: {t_res.status_code}")
                return
            t_id = t_res.json()["task"]["id"]

            # Update status
            p_res = client.patch(f"/api/tasks/{t_id}", json={"status": "in_progress"})
            if p_res.status_code != 200:
                errors.append(f"Thread {index} patch failed: {p_res.status_code}")
                return

            # Delete task
            d_res = client.delete(f"/api/tasks/{t_id}")
            if d_res.status_code != 200:
                errors.append(f"Thread {index} delete failed: {d_res.status_code}")
                return
        except Exception as e:
            errors.append(f"Thread {index} exception: {e}")

    threads = [threading.Thread(target=worker_thread, args=(i,)) for i in range(15)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Concurrency errors encountered: {errors}"
    print("  15 concurrent threads executed Task lifecycle cleanly without deadlock or race condition.")

    # ---------------------------------------------------------
    # 5. Dual-Tier Persistence Authenticity Check
    # ---------------------------------------------------------
    print("\n[Probe 5] Testing Persistence Authenticity on Disk...")
    # Create a unique canary workspace
    canary_name = "Canary Auditor Workspace"
    ws_res = client.post("/api/workspaces", json={"name": canary_name, "prompt": "Auditor Probe"})
    assert ws_res.status_code == 201
    canary_id = ws_res.json()["workspace"]["id"]

    # Verify directly from disk file
    assert WORKSPACE_STORE_FILE.exists(), f"Store file {WORKSPACE_STORE_FILE} does not exist!"
    disk_data = json.loads(WORKSPACE_STORE_FILE.read_text(encoding="utf-8"))
    disk_ws_ids = [w["id"] for w in disk_data.get("workspaces", [])]
    assert canary_id in disk_ws_ids, f"Canary workspace {canary_id} was NOT found in on-disk JSON file!"
    print(f"  Verified canary workspace {canary_id} written to disk file {WORKSPACE_STORE_FILE}.")

    # Delete canary workspace and verify disk again
    del_res = client.delete(f"/api/workspaces/{canary_id}")
    assert del_res.status_code == 200

    disk_data_after = json.loads(WORKSPACE_STORE_FILE.read_text(encoding="utf-8"))
    disk_ws_ids_after = [w["id"] for w in disk_data_after.get("workspaces", [])]
    assert canary_id not in disk_ws_ids_after, f"Canary workspace {canary_id} still exists in disk file after delete!"
    print("  Verified canary workspace removed from disk file after deletion.")

    # ---------------------------------------------------------
    # 6. SOM Mark Coordinates & Geometric Boundaries
    # ---------------------------------------------------------
    print("\n[Probe 6] Testing SOM Geometric Boundaries and Mark Integrity...")
    som_res = client.get("/api/som")
    assert som_res.status_code == 200
    som_data = som_res.json()
    marks = som_data.get("marks", [])
    assert len(marks) == 12

    for m in marks:
        rect = m.get("rect")
        assert isinstance(rect, list) and len(rect) == 4, f"Invalid rect: {rect}"
        x1, y1, x2, y2 = rect
        assert x1 < x2, f"Invalid rect width (x1 >= x2): {rect} in mark {m['tag']}"
        assert y1 < y2, f"Invalid rect height (y1 >= y2): {rect} in mark {m['tag']}"
        assert 0 <= x1 <= 1920 and 0 <= x2 <= 1920, f"X coords out of range: {rect}"
        assert 0 <= y1 <= 1080 and 0 <= y2 <= 1080, f"Y coords out of range: {rect}"
    print("  All 12 marks have valid non-inverted geometric rectangles within viewport bounds.")

    print("\n=== ALL ADVERSARIAL CHECKS PASSED ===")


if __name__ == "__main__":
    test_adversarial_suite()
