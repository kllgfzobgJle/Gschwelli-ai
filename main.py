#!/usr/bin/env python3
"""AETHER — Tiered Hybrid Automation Router Entrypoint for Windows 11."""

from __future__ import annotations

import argparse
import ctypes
import sys
import time
import webbrowser

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from core.router import AetherRouter, RouteResult


def set_dpi_awareness() -> None:
    """Set Windows Per-Monitor DPI Awareness (`shcore.SetProcessDpiAwareness(2)`)."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


_TIER_LABELS = {
    0: ("TIER 0 — Deterministic SQLite Cache", "bold cyan"),
    1: ("TIER 1 — Local Fast-Path (Ollama qwen2.5-coder:7b)", "bold green"),
    2: ("TIER 2 — Structural Windows UIA / Accessibility", "bold yellow"),
    3: ("TIER 3 — Selective Cloud Vision (Gemini 3.8 Flash)", "bold magenta"),
}


def render_result(console: Console, instruction: str, result: RouteResult) -> None:
    """Display active Tier, elapsed milliseconds, and execution logs using Rich."""
    tier_name, tier_style = _TIER_LABELS.get(result.active_tier, (f"TIER {result.active_tier}", "bold white"))
    status_str = "SUCCESS" if result.success else "FAILED"
    status_style = "bold green" if result.success else "bold red"

    header = Text()
    header.append("AETHER ", style="bold bright_white")
    header.append(f"[{status_str}] ", style=status_style)
    header.append(f"| {tier_name} ", style=tier_style)
    header.append(f"| {result.elapsed_ms:.1f} ms", style="bold bright_cyan")

    table = Table(show_header=True, header_style="bold dim", expand=True, box=None)
    table.add_column("Time (ms)", justify="right", style="cyan", width=10)
    table.add_column("Tier", justify="center", width=6)
    table.add_column("Level", justify="center", width=7)
    table.add_column("Execution Log", style="white")

    for entry in result.logs:
        lvl_style = "green" if entry.level == "INFO" else ("yellow" if entry.level == "WARN" else "red")
        table.add_row(
            f"{entry.timestamp_ms:7.1f}",
            f"T{entry.tier}",
            Text(entry.level, style=lvl_style),
            entry.message,
        )

    console.print(Panel(table, title=header, subtitle=f"Request: {instruction}", border_style="bright_blue"))


def main() -> int:
    set_dpi_awareness()
    console = Console()

    parser = argparse.ArgumentParser(
        prog="aether",
        description="AETHER — Lightweight 4-Tier Hybrid Windows 11 Desktop Automation Router",
    )
    parser.add_argument(
        "-r",
        "--request",
        type=str,
        help="Execute a single automation instruction directly and exit.",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch Mode A Floating Command Bar Overlay + System Tray + Background Dashboard Server.",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Launch Dual-Mode GUI and open the Full Web/Desktop Control Center Dashboard in browser.",
    )
    parser.add_argument(
        "--server",
        action="store_true",
        help="Run the FastAPI + WebSocket Control Center server and Global Hotkey Daemon.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port for the AETHER Control Center server (default: 8765).",
    )
    args = parser.parse_args()

    router = AetherRouter()

    if args.request:
        res = router.route(args.request)
        render_result(console, args.request, res)
        return 0 if res.success else 1

    if args.gui or args.dashboard:
        from ui.overlay import run_dual_mode_gui

        return run_dual_mode_gui(
            router=router,
            port=args.port,
            open_dashboard_on_start=bool(args.dashboard),
        )

    if args.server:
        from engines.voice_engine import VoiceDaemon
        from server.api import start_background_server

        vd = VoiceDaemon(router=router)
        vd.start()
        start_background_server(router=router, voice_daemon=vd, port=args.port, open_browser=False)
        console.print(
            Panel(
                f"[bold cyan]AETHER Server & Global Hotkey Daemon Active[/bold cyan]\n"
                f"Dashboard URL: [underline]http://127.0.0.1:{args.port}[/underline]\n"
                f"Push-to-Talk Hotkey: [bold]Ctrl+Space[/bold] ({vd.ptt.scope})\n"
                f"Press Ctrl+C to stop.",
                border_style="cyan",
            )
        )
        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            vd.stop()
            return 0

    console.print(
        Panel(
            "[bold cyan]AETHER[/bold cyan] Interactive Mode (4-Tier Waterfall Router)\n"
            "Type an instruction and press Enter, or use:\n"
            "  • [bold]dashboard[/bold] — start & open the Web Control Center (`http://127.0.0.1:8765`)\n"
            "  • [bold]undo[/bold]      — reverse the most recent reversible action\n"
            "  • [bold]exit[/bold]      — quit AETHER",
            border_style="cyan",
        )
    )
    server_started = False
    while True:
        try:
            user_input = console.input("[bold bright_cyan]AETHER > [/bold bright_cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Shutting down AETHER...[/dim]")
            break
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "q"}:
            break
        if user_input.lower() == "dashboard":
            if not server_started:
                from engines.voice_engine import VoiceDaemon
                from server.api import start_background_server

                vd = VoiceDaemon(router=router)
                vd.start()
                start_background_server(router=router, voice_daemon=vd, port=args.port, open_browser=True)
                server_started = True
            else:
                webbrowser.open(f"http://127.0.0.1:{args.port}")
            console.print(f"[green]Opened Control Center at http://127.0.0.1:{args.port}[/green]")
            continue

        res = router.route(user_input)
        render_result(console, user_input, res)

    return 0


if __name__ == "__main__":
    sys.exit(main())
