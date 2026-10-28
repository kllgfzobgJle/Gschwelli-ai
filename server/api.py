"""AETHER Unified FastAPI + WebSocket Server for Dual-Mode GUI (Overlay + Full Dashboard)."""

from __future__ import annotations

import asyncio
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional
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
    app = FastAPI(title="AETHER Control Center API", version="2.0.0")
    active_router = router or AetherRouter()
    ws_clients: List[WebSocket] = []
    loop_holder: Dict[str, Optional[asyncio.AbstractEventLoop]] = {"loop": None}

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

    @app.on_event("startup")
    async def _startup() -> None:
        loop_holder["loop"] = asyncio.get_running_loop()

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
            key="overwrite_stl",
            title="Overwrite toolhead_mount.stl",
            detail="backup saved • SEC-810",
            run=lambda: "Overwrote toolhead_mount.stl in C:\\Fabrication",
        )
        return JSONResponse(
            {
                "status": "scenario_reset",
                "project": "3D Fabrication & Automation",
                "mission": "M-024 / Export toolhead_mount.stl",
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
                        "name": "Menu Bar",
                        "type": "menu",
                        "rect": [10, 30, 220, 54],
                        "confidence": 0.991,
                        "selector": "OpenSCAD::MenuBar",
                        "uia_id": "MenuBar.Main",
                    },
                    {
                        "mark": 2,
                        "tag": "[02]",
                        "name": "Window Controls",
                        "type": "titlebar",
                        "rect": [1340, 6, 1432, 28],
                        "confidence": 0.995,
                        "selector": "OpenSCAD::WindowControls",
                        "uia_id": "TitleBar.Controls",
                    },
                    {
                        "mark": 3,
                        "tag": "[03]",
                        "name": "CSG Tree View",
                        "type": "treeview",
                        "rect": [14, 70, 260, 420],
                        "confidence": 0.988,
                        "selector": "OpenSCAD::CSGView",
                        "uia_id": "Tree.CSG",
                    },
                    {
                        "mark": 4,
                        "tag": "[04]",
                        "name": "Button 'Export'",
                        "type": "button",
                        "rect": [1280, 810, 1400, 846],
                        "confidence": 0.992,
                        "selector": "OpenSCAD::ButtonExport",
                        "uia_id": "Button.ExportSTL",
                    },
                    {
                        "mark": 5,
                        "tag": "[05]",
                        "name": "3D CAD Mesh Viewport",
                        "type": "viewport",
                        "rect": [270, 70, 1420, 780],
                        "confidence": 0.998,
                        "selector": "OpenSCAD::OpenGLViewport",
                        "uia_id": "Viewport.GLWidget",
                    },
                    {
                        "mark": 6,
                        "tag": "[06]",
                        "name": "Coordinate Axes Gizmo",
                        "type": "gizmo",
                        "rect": [285, 730, 345, 790],
                        "confidence": 0.989,
                        "selector": "OpenSCAD::AxesGizmo",
                        "uia_id": "Gizmo.XYZ",
                    },
                    {
                        "mark": 7,
                        "tag": "[07]",
                        "name": "Camera Orbit/Pan/Zoom",
                        "type": "toolbar",
                        "rect": [1390, 80, 1424, 210],
                        "confidence": 0.984,
                        "selector": "OpenSCAD::CameraTools",
                        "uia_id": "Toolbar.Camera",
                    },
                    {
                        "mark": 8,
                        "tag": "[08]",
                        "name": "Dimension X (80.00 mm)",
                        "type": "callout",
                        "rect": [640, 520, 760, 545],
                        "confidence": 0.987,
                        "selector": "OpenSCAD::DimensionDimX",
                        "uia_id": "Callout.DimX",
                    },
                    {
                        "mark": 9,
                        "tag": "[09]",
                        "name": "Dimension Z (24.00 mm)",
                        "type": "callout",
                        "rect": [880, 360, 990, 385],
                        "confidence": 0.986,
                        "selector": "OpenSCAD::DimensionDimZ",
                        "uia_id": "Callout.DimZ",
                    },
                    {
                        "mark": 10,
                        "tag": "[10]",
                        "name": "Console Log Drawer",
                        "type": "terminal",
                        "rect": [14, 780, 260, 870],
                        "confidence": 0.979,
                        "selector": "OpenSCAD::ConsoleOutput",
                        "uia_id": "Drawer.Console",
                    },
                    {
                        "mark": 11,
                        "tag": "[11]",
                        "name": "Mesh Quality Telemetry",
                        "type": "badge",
                        "rect": [290, 80, 480, 108],
                        "confidence": 0.994,
                        "selector": "OpenSCAD::ManifoldBadge",
                        "uia_id": "Badge.Telemetry",
                    },
                    {
                        "mark": 12,
                        "tag": "[12]",
                        "name": "Path Input",
                        "type": "textbox",
                        "rect": [180, 810, 1260, 846],
                        "confidence": 0.985,
                        "selector": "OpenSCAD::PathInput",
                        "uia_id": "TextBox.ExportPath",
                    },
                ],
            }
        )

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
