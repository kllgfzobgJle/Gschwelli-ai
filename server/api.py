"""AETHER Unified FastAPI + WebSocket Server for Dual-Mode GUI (Overlay + Full Dashboard)."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import json
from pathlib import Path
import threading
import time
from typing import Any, Dict, List, Optional
from uuid import uuid4
import webbrowser

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
import psutil
from pydantic import BaseModel
import uvicorn

from core.confirm import get_pending, request_confirmation, resolve as resolve_confirm
from core.router import AetherRouter, RouteResult
from core.tts import tts_engine
from core.undo import can_undo, history as undo_history, undo_last
from engines.cache_store import cache_store
from executors.ps_repl import ps_repl
from memory.memory_manager import all_entries_for_ui, forget_fact, remember_fact
from tools.registry import registry

BASE_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_HTML_PATH = BASE_DIR / "ui" / "dashboard" / "index.html"
WORKSPACE_STORE_FILE = BASE_DIR / "workspace" / "workspaces_store.json"


class RouteRequest(BaseModel):
    instruction: str


class ToolExecRequest(BaseModel):
    tool: str
    args: Dict[str, Any] = {}


class MemoryEntryRequest(BaseModel):
    key: str
    value: str
    category: str = "notes"


class ConfirmResolveRequest(BaseModel):
    approve: bool = True


class VoiceToggleRequest(BaseModel):
    tts_enabled: Optional[bool] = None
    voice_capture_enabled: Optional[bool] = None


class REPLRequest(BaseModel):
    command: str = ""


class WorkspaceCreateRequest(BaseModel):
    name: str
    prompt: Optional[str] = "Universal Autonomous Agent Operating Canvas"
    working_dir: Optional[str] = None


class WorkspaceActivateRequest(BaseModel):
    id: str


class TaskCreateRequest(BaseModel):
    title: str
    status: Optional[str] = "backlog"
    priority: Optional[str] = "P2"
    delegated: Optional[bool] = False
    meta: Optional[Dict[str, Any]] = None


class TaskUpdateRequest(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    delegated: Optional[bool] = None
    meta: Optional[Dict[str, Any]] = None


class WorkspaceStore:
    """Thread-safe dual-persistence store for workspaces and reactive task pipelines."""

    def __init__(self, store_path: Path):
        self._path = store_path
        self._lock = threading.RLock()
        self._workspaces: List[Dict[str, Any]] = []
        self._active_workspace_id: str = "ws-default"
        self._tasks: List[Dict[str, Any]] = []
        self._init_store()

    def _init_store(self) -> None:
        with self._lock:
            if self._path.exists():
                try:
                    data = json.loads(self._path.read_text(encoding="utf-8"))
                    self._workspaces = data.get("workspaces", [])
                    self._active_workspace_id = data.get("active_workspace_id", "ws-default")
                    self._tasks = data.get("tasks", [])
                    if self._workspaces and self._tasks:
                        return
                except Exception:
                    pass

            self._workspaces = [
                {
                    "id": "ws-default",
                    "name": "General Workspace",
                    "prompt": "Universal Autonomous Agent Operating Canvas",
                    "working_dir": "workspace/default",
                    "is_active": True,
                }
            ]
            self._active_workspace_id = "ws-default"
            self._tasks = [
                {
                    "id": "task-1",
                    "title": "Analyze repository architecture",
                    "status": "done",
                    "priority": "P1",
                    "delegated": False,
                    "meta": {},
                },
                {
                    "id": "task-2",
                    "title": "Synthesize backend telemetry and state",
                    "status": "in_progress",
                    "priority": "P1",
                    "delegated": True,
                    "meta": {},
                },
                {
                    "id": "task-3",
                    "title": "Draft cross-platform integration tests",
                    "status": "backlog",
                    "priority": "P2",
                    "delegated": False,
                    "meta": {},
                },
                {
                    "id": "task-4",
                    "title": "Verify offline zero-dependency bundle",
                    "status": "blocked",
                    "priority": "P3",
                    "delegated": False,
                    "meta": {},
                },
            ]
            self._save()

    def _save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "active_workspace_id": self._active_workspace_id,
                "workspaces": self._workspaces,
                "tasks": self._tasks,
            }
            tmp = self._path.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(self._path)
        except Exception as exc:
            print(f"[WorkspaceStore] Failed to save store: {exc}")

    def get_workspaces(self) -> List[Dict[str, Any]]:
        with self._lock:
            result = []
            for ws in self._workspaces:
                item = dict(ws)
                item["is_active"] = (item.get("id") == self._active_workspace_id)
                result.append(item)
            return result

    def get_active_workspace_id(self) -> str:
        with self._lock:
            return self._active_workspace_id

    def get_active_working_dir(self) -> Path:
        with self._lock:
            for ws in self._workspaces:
                if ws.get("id") == self._active_workspace_id:
                    wdir = ws.get("working_dir", "workspace/default")
                    return BASE_DIR / wdir
            return BASE_DIR / "workspace" / "default"

    def create_workspace(self, name: str, prompt: str = "", working_dir: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            ws_id = f"ws-{uuid4().hex[:8]}"
            slug = "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_") or "workspace"
            final_dir = working_dir if working_dir else f"workspace/{slug}"
            new_ws = {
                "id": ws_id,
                "name": name,
                "prompt": prompt or "Universal Autonomous Agent Operating Canvas",
                "working_dir": final_dir,
                "is_active": False,
            }
            try:
                (BASE_DIR / final_dir).mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            self._workspaces.append(new_ws)
            self._save()
            return new_ws

    def activate_workspace(self, ws_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            target_ws = None
            for ws in self._workspaces:
                if ws.get("id") == ws_id:
                    target_ws = ws
                    break
            if not target_ws:
                return None
            self._active_workspace_id = ws_id
            for ws in self._workspaces:
                ws["is_active"] = (ws.get("id") == ws_id)
            self._save()
            return dict(target_ws)

    def delete_workspace(self, ws_id: str) -> bool:
        with self._lock:
            idx = -1
            for i, ws in enumerate(self._workspaces):
                if ws.get("id") == ws_id:
                    idx = i
                    break
            if idx == -1:
                return False
            del self._workspaces[idx]
            if self._active_workspace_id == ws_id:
                if self._workspaces:
                    self._active_workspace_id = self._workspaces[0]["id"]
                    self._workspaces[0]["is_active"] = True
                else:
                    self._init_store()
            self._save()
            return True

    def get_tasks(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [dict(t) for t in self._tasks]

    def create_task(
        self,
        title: str,
        status: str = "backlog",
        priority: str = "P2",
        delegated: bool = False,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            t_id = f"task-{uuid4().hex[:6]}"
            new_task = {
                "id": t_id,
                "title": title,
                "status": status,
                "priority": priority,
                "delegated": bool(delegated),
                "meta": meta or {},
            }
            self._tasks.append(new_task)
            self._save()
            return new_task

    def update_task(self, task_id: str, **updates: Any) -> Optional[Dict[str, Any]]:
        with self._lock:
            for task in self._tasks:
                if task.get("id") == task_id:
                    for k, v in updates.items():
                        if v is not None:
                            task[k] = v
                    self._save()
                    return dict(task)
            return None

    def delete_task(self, task_id: str) -> bool:
        with self._lock:
            idx = -1
            for i, task in enumerate(self._tasks):
                if task.get("id") == task_id:
                    idx = i
                    break
            if idx == -1:
                return False
            del self._tasks[idx]
            self._save()
            return True


workspace_store = WorkspaceStore(WORKSPACE_STORE_FILE)


def serialize_route_result(res: RouteResult) -> Dict[str, Any]:
    return {
        "success": res.success,
        "active_tier": res.active_tier,
        "elapsed_ms": round(res.elapsed_ms, 2),
        "instruction": res.instruction,
        "thought": res.plan.thought if res.plan else "",
        "actions": [a.model_dump() for a in res.plan.actions] if res.plan else [],
        "outputs": res.outputs,
        "verification_logs": res.verification_logs,
        "logs": [
            {
                "timestamp_ms": round(entry.timestamp_ms, 2),
                "tier": entry.tier,
                "level": entry.level,
                "message": entry.message,
            }
            for entry in res.logs
        ],
    }


def create_app(router: Optional[AetherRouter] = None, voice_daemon: Any = None) -> FastAPI:
    active_router = router or AetherRouter()
    ws_clients: List[WebSocket] = []
    loop_holder: Dict[str, Optional[asyncio.AbstractEventLoop]] = {"loop": None}

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        loop_holder["loop"] = asyncio.get_running_loop()
        yield

    app = FastAPI(title="AETHER Control Center API", version="2.0.0", lifespan=lifespan)

    async def _broadcast(payload: Dict[str, Any]) -> None:
        stale: List[WebSocket] = []
        for ws in list(ws_clients):
            try:
                await ws.send_json(payload)
            except Exception:
                stale.append(ws)
        for s in stale:
            if s in ws_clients:
                ws_clients.remove(s)

    def _on_route_finished(res: RouteResult) -> None:
        ev_loop = loop_holder.get("loop")
        if ev_loop and ev_loop.is_running():
            asyncio.run_coroutine_threadsafe(
                _broadcast({"type": "route_result", "data": serialize_route_result(res)}),
                ev_loop,
            )

    active_router.add_listener(_on_route_finished)

    @app.get("/", response_class=HTMLResponse)
    async def index() -> HTMLResponse:
        if DASHBOARD_HTML_PATH.is_file():
            return HTMLResponse(DASHBOARD_HTML_PATH.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>AETHER Dashboard HTML not found</h1>", status_code=404)

    @app.get("/api/state")
    async def get_state() -> JSONResponse:
        vm = psutil.virtual_memory()
        batt = psutil.sensors_battery()
        tools_list = registry.get_declarations()
        return JSONResponse(
            {
                "system": {
                    "cpu_percent": psutil.cpu_percent(interval=None),
                    "ram_percent": vm.percent,
                    "ram_used_gb": round(vm.used / (1024**3), 1),
                    "ram_total_gb": round(vm.total / (1024**3), 1),
                    "battery_percent": round(batt.percent) if batt else None,
                    "battery_plugged": bool(batt.power_plugged) if batt else None,
                },
                "workspaces": workspace_store.get_workspaces(),
                "active_workspace_id": workspace_store.get_active_workspace_id(),
                "tasks": workspace_store.get_tasks(),
                "tools": tools_list,
                "cache": cache_store.list_entries(limit=50),
                "memory": all_entries_for_ui(),
                "undo": {
                    "can_undo": can_undo(),
                    "history": undo_history(limit=15),
                },
                "pending_confirmation": get_pending(),
                "history": [serialize_route_result(r) for r in active_router.get_history(limit=25)],
                "voice": voice_daemon.status_dict()
                if voice_daemon
                else {
                    "state": "idle",
                    "hotkey": "Ctrl+Space",
                    "hotkey_scope": "global",
                    "tts_enabled": tts_engine.enabled,
                },
            }
        )

    @app.post("/api/route")
    async def route_instruction(req: RouteRequest) -> JSONResponse:
        instruction = (req.instruction or "").strip()
        if not instruction:
            return JSONResponse({"error": "Empty instruction"}, status_code=400)
        res = await asyncio.to_thread(active_router.route, instruction)
        return JSONResponse(serialize_route_result(res))

    @app.post("/api/tool")
    async def execute_tool_direct(req: ToolExecRequest) -> JSONResponse:
        out = await asyncio.to_thread(registry.execute, req.tool, req.args)
        return JSONResponse({"tool": req.tool, "output": out})

    @app.post("/api/undo")
    async def trigger_undo() -> JSONResponse:
        msg = await asyncio.to_thread(undo_last, 1)
        return JSONResponse({"result": msg, "can_undo": can_undo(), "history": undo_history(limit=15)})

    @app.post("/api/confirm")
    async def resolve_confirmation(req: ConfirmResolveRequest) -> JSONResponse:
        resolved = resolve_confirm(req.approve)
        return JSONResponse({"resolved": resolved, "approved": req.approve, "pending": get_pending()})

    @app.post("/api/memory")
    async def add_memory(req: MemoryEntryRequest) -> JSONResponse:
        out = remember_fact(req.key, req.value, req.category)
        return JSONResponse({"result": out, "memory": all_entries_for_ui()})

    @app.delete("/api/memory/{key}")
    async def delete_memory(key: str, category: str = "notes") -> JSONResponse:
        out = forget_fact(key, category)
        return JSONResponse({"result": out, "memory": all_entries_for_ui()})

    @app.delete("/api/cache")
    async def clear_cache_endpoint() -> JSONResponse:
        cache_store.clear()
        return JSONResponse({"cleared": True, "cache": cache_store.list_entries()})

    @app.post("/api/voice")
    async def update_voice_settings(req: VoiceToggleRequest) -> JSONResponse:
        if req.tts_enabled is not None:
            tts_engine.enabled = bool(req.tts_enabled)
        if voice_daemon and req.voice_capture_enabled is not None:
            voice_daemon.voice_capture_enabled = bool(req.voice_capture_enabled)
        return JSONResponse(
            voice_daemon.status_dict()
            if voice_daemon
            else {"tts_enabled": tts_engine.enabled}
        )

    @app.post("/api/scenario/reset")
    async def reset_scenario() -> JSONResponse:
        request_confirmation(
            key="system_file_write",
            title="Update workspace configuration",
            detail="Modifying workspace environment • Risk: Moderate",
            run=lambda: "Applied workspace configuration update",
        )
        return JSONResponse(
            {
                "status": "scenario_reset",
                "workspace": "default",
                "mission": "Universal Agent Task Execution",
            }
        )

    @app.post("/api/repl")
    async def execute_repl_command(req: REPLRequest) -> JSONResponse:
        cmd = (req.command or "").strip()
        if not cmd:
            return JSONResponse({"command": "", "output": "", "exit_code": 0})
        out = await asyncio.to_thread(ps_repl.run, cmd)
        exit_code = 1 if ("status=failed" in out or "[PS_ERROR]" in out) else 0
        return JSONResponse({"command": cmd, "output": out, "exit_code": exit_code})

    @app.get("/api/som")
    async def get_som_targets() -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "targets_mapped": 12,
                "fusion_confidence": 0.992,
                "resolution": "1440x900",
                "display": "DISPLAY 01",
                "fusion_engine": "UIA + VISION FUSION",
                "marks": [
                    {
                        "mark": 1,
                        "tag": "[01]",
                        "name": "Navigation Menu",
                        "type": "menu",
                        "rect": [10, 30, 220, 54],
                        "confidence": 0.991,
                        "selector": "Window::MenuBar",
                        "uia_id": "MenuBar.Main",
                    },
                    {
                        "mark": 2,
                        "tag": "[02]",
                        "name": "Window Controls",
                        "type": "titlebar",
                        "rect": [1340, 6, 1432, 28],
                        "confidence": 0.995,
                        "selector": "Window::Controls",
                        "uia_id": "TitleBar.Controls",
                    },
                    {
                        "mark": 3,
                        "tag": "[03]",
                        "name": "Workspace Explorer",
                        "type": "treeview",
                        "rect": [14, 70, 260, 420],
                        "confidence": 0.988,
                        "selector": "Window::FileTree",
                        "uia_id": "Tree.Workspace",
                    },
                    {
                        "mark": 4,
                        "tag": "[04]",
                        "name": "Action Button 'Execute'",
                        "type": "button",
                        "rect": [1280, 810, 1400, 846],
                        "confidence": 0.992,
                        "selector": "Window::ButtonExecute",
                        "uia_id": "Button.Execute",
                    },
                    {
                        "mark": 5,
                        "tag": "[05]",
                        "name": "Main Canvas Viewport",
                        "type": "viewport",
                        "rect": [270, 70, 1420, 780],
                        "confidence": 0.998,
                        "selector": "Window::CanvasViewport",
                        "uia_id": "Viewport.Main",
                    },
                    {
                        "mark": 6,
                        "tag": "[06]",
                        "name": "Canvas Status Gizmo",
                        "type": "gizmo",
                        "rect": [285, 730, 345, 790],
                        "confidence": 0.989,
                        "selector": "Window::StatusGizmo",
                        "uia_id": "Gizmo.Status",
                    },
                    {
                        "mark": 7,
                        "tag": "[07]",
                        "name": "Viewport Controls (Pan/Zoom)",
                        "type": "toolbar",
                        "rect": [1390, 80, 1424, 210],
                        "confidence": 0.984,
                        "selector": "Window::ViewTools",
                        "uia_id": "Toolbar.Controls",
                    },
                    {
                        "mark": 8,
                        "tag": "[08]",
                        "name": "Property Inspector",
                        "type": "panel",
                        "rect": [640, 520, 760, 545],
                        "confidence": 0.987,
                        "selector": "Window::Inspector",
                        "uia_id": "Panel.Inspector",
                    },
                    {
                        "mark": 9,
                        "tag": "[09]",
                        "name": "Live Telemetry",
                        "type": "badge",
                        "rect": [880, 360, 990, 385],
                        "confidence": 0.986,
                        "selector": "Window::TelemetryBadge",
                        "uia_id": "Badge.Telemetry",
                    },
                    {
                        "mark": 10,
                        "tag": "[10]",
                        "name": "Terminal Console",
                        "type": "terminal",
                        "rect": [14, 780, 260, 870],
                        "confidence": 0.979,
                        "selector": "Window::TerminalDrawer",
                        "uia_id": "Drawer.Terminal",
                    },
                    {
                        "mark": 11,
                        "tag": "[11]",
                        "name": "Integrity Badge",
                        "type": "badge",
                        "rect": [290, 80, 480, 108],
                        "confidence": 0.994,
                        "selector": "Window::IntegrityBadge",
                        "uia_id": "Badge.Integrity",
                    },
                    {
                        "mark": 12,
                        "tag": "[12]",
                        "name": "Command / Path Input",
                        "type": "textbox",
                        "rect": [180, 810, 1260, 846],
                        "confidence": 0.985,
                        "selector": "Window::CommandInput",
                        "uia_id": "TextBox.Command",
                    },
                ],
            }
        )

    # =========================================================================
    # Workspace Management Endpoints (Additive REST)
    # =========================================================================

    @app.get("/api/workspaces")
    async def list_workspaces() -> JSONResponse:
        return JSONResponse(
            {
                "workspaces": workspace_store.get_workspaces(),
                "active_workspace_id": workspace_store.get_active_workspace_id(),
            }
        )

    @app.post("/api/workspaces", status_code=201)
    async def create_workspace_endpoint(req: WorkspaceCreateRequest) -> JSONResponse:
        name = (req.name or "").strip()
        if not name:
            return JSONResponse({"error": "Workspace name cannot be empty"}, status_code=400)
        ws = workspace_store.create_workspace(
            name=name,
            prompt=(req.prompt or "").strip() or "Universal Autonomous Agent Operating Canvas",
            working_dir=(req.working_dir or "").strip() or None,
        )
        return JSONResponse(
            {
                "status": "created",
                "workspace": ws,
                "workspaces": workspace_store.get_workspaces(),
                "active_workspace_id": workspace_store.get_active_workspace_id(),
            },
            status_code=201,
        )

    @app.post("/api/workspaces/activate")
    async def activate_workspace_endpoint(req: WorkspaceActivateRequest) -> JSONResponse:
        ws_id = (req.id or "").strip()
        ws = workspace_store.activate_workspace(ws_id)
        if not ws:
            return JSONResponse({"error": f"Workspace '{ws_id}' not found"}, status_code=404)
        return JSONResponse(
            {
                "status": "activated",
                "active_workspace_id": ws_id,
                "workspace": ws,
                "workspaces": workspace_store.get_workspaces(),
            }
        )

    @app.delete("/api/workspaces/{id}")
    async def delete_workspace_endpoint(id: str) -> JSONResponse:
        deleted = workspace_store.delete_workspace(id)
        if not deleted:
            return JSONResponse({"error": f"Workspace '{id}' not found"}, status_code=404)
        return JSONResponse(
            {
                "status": "deleted",
                "id": id,
                "active_workspace_id": workspace_store.get_active_workspace_id(),
                "workspaces": workspace_store.get_workspaces(),
            }
        )

    # =========================================================================
    # Task Management Endpoints (Additive REST)
    # =========================================================================

    @app.get("/api/tasks")
    async def list_tasks() -> JSONResponse:
        return JSONResponse({"tasks": workspace_store.get_tasks()})

    @app.post("/api/tasks", status_code=201)
    async def create_task_endpoint(req: TaskCreateRequest) -> JSONResponse:
        title = (req.title or "").strip()
        if not title:
            return JSONResponse({"error": "Task title cannot be empty"}, status_code=400)
        valid_statuses = {"backlog", "in_progress", "agent_delegated", "blocked", "done"}
        status = req.status if req.status in valid_statuses else "backlog"
        valid_priorities = {"P1", "P2", "P3"}
        priority = req.priority if req.priority in valid_priorities else "P2"
        task = workspace_store.create_task(
            title=title,
            status=status,
            priority=priority,
            delegated=bool(req.delegated),
            meta=req.meta or {},
        )
        return JSONResponse(
            {
                "status": "created",
                "task": task,
                "tasks": workspace_store.get_tasks(),
            },
            status_code=201,
        )

    @app.patch("/api/tasks/{id}")
    async def update_task_endpoint(id: str, req: TaskUpdateRequest) -> JSONResponse:
        updates: Dict[str, Any] = {}
        if req.title is not None:
            title = req.title.strip()
            if not title:
                return JSONResponse({"error": "Task title cannot be empty"}, status_code=400)
            updates["title"] = title
        if req.status is not None:
            valid_statuses = {"backlog", "in_progress", "agent_delegated", "blocked", "done"}
            if req.status not in valid_statuses:
                return JSONResponse({"error": f"Invalid status '{req.status}'"}, status_code=400)
            updates["status"] = req.status
        if req.priority is not None:
            valid_priorities = {"P1", "P2", "P3"}
            if req.priority not in valid_priorities:
                return JSONResponse({"error": f"Invalid priority '{req.priority}'"}, status_code=400)
            updates["priority"] = req.priority
        if req.delegated is not None:
            updates["delegated"] = bool(req.delegated)
        if req.meta is not None:
            updates["meta"] = req.meta

        task = workspace_store.update_task(id, **updates)
        if not task:
            return JSONResponse({"error": f"Task '{id}' not found"}, status_code=404)
        return JSONResponse(
            {
                "status": "updated",
                "task": task,
                "tasks": workspace_store.get_tasks(),
            }
        )

    @app.delete("/api/tasks/{id}")
    async def delete_task_endpoint(id: str) -> JSONResponse:
        deleted = workspace_store.delete_task(id)
        if not deleted:
            return JSONResponse({"error": f"Task '{id}' not found"}, status_code=404)
        return JSONResponse(
            {
                "status": "deleted",
                "id": id,
                "tasks": workspace_store.get_tasks(),
            }
        )

    # =========================================================================
    # Workspace File Browser Endpoint
    # =========================================================================

    @app.get("/api/workspace/files")
    async def list_workspace_files(path: Optional[str] = None) -> JSONResponse:
        if path:
            target_path = (BASE_DIR / path).resolve()
        else:
            target_path = workspace_store.get_active_working_dir().resolve()

        try:
            target_path.relative_to(BASE_DIR)
        except ValueError:
            return JSONResponse({"error": "Path traversal prohibited"}, status_code=403)

        if not target_path.exists() or not target_path.is_dir():
            return JSONResponse([])

        files_list: List[Dict[str, Any]] = []
        category_map = {
            # code
            "py": "code", "js": "code", "ts": "code", "jsx": "code", "tsx": "code",
            "html": "code", "css": "code", "sh": "code", "ps1": "code", "bat": "code",
            "rs": "code", "go": "code", "c": "code", "cpp": "code", "h": "code", "java": "code",
            # doc
            "md": "doc", "txt": "doc", "rst": "doc", "pdf": "doc", "doc": "doc", "docx": "doc",
            "rtf": "doc", "log": "doc",
            # data
            "csv": "data", "tsv": "data", "jsonl": "data", "xml": "data", "parquet": "data",
            "db": "data", "sqlite": "data", "sql": "data",
            # media
            "png": "media", "jpg": "media", "jpeg": "media", "gif": "media", "svg": "media",
            "webp": "media", "mp3": "media", "mp4": "media", "wav": "media", "ico": "media",
            # config
            "yaml": "config", "yml": "config", "toml": "config", "ini": "config", "env": "config",
            "conf": "config", "lock": "config",
        }

        try:
            items = list(target_path.iterdir())
        except Exception:
            return JSONResponse([])

        for item in sorted(items, key=lambda p: (not p.is_dir(), p.name.lower())):
            if item.name.startswith(".") or item.name == "__pycache__":
                continue
            ext = item.suffix.lstrip(".").lower()
            if "config" in item.name.lower():
                category = "config"
            elif ext in category_map:
                category = category_map[ext]
            elif ext == "json":
                category = "config" if "config" in item.name.lower() else "data"
            elif item.is_dir():
                category = "doc"
            else:
                category = "doc"

            rel_path = item.relative_to(BASE_DIR).as_posix()
            files_list.append(
                {
                    "name": item.name,
                    "path": rel_path,
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else 0,
                    "ext": ext,
                    "category": category,
                }
            )

        return JSONResponse(files_list)

    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket) -> None:
        await ws.accept()
        ws_clients.append(ws)
        try:
            while True:
                _ = await ws.receive_text()
        except WebSocketDisconnect:
            if ws in ws_clients:
                ws_clients.remove(ws)
        except Exception:
            if ws in ws_clients:
                ws_clients.remove(ws)

    return app


def start_background_server(
    router: AetherRouter,
    voice_daemon: Any = None,
    host: str = "127.0.0.1",
    port: int = 8765,
    open_browser: bool = False,
) -> threading.Thread:
    """Launch the FastAPI + WebSocket Control Center server on a background daemon thread."""
    app = create_app(router=router, voice_daemon=voice_daemon)
    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, name="aether-api-server", daemon=True)
    thread.start()

    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(f"http://{host}:{port}")).start()

    return thread
