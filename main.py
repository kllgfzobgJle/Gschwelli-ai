#!/usr/bin/env python3
"""AETHER — Tiered Hybrid Automation Router Entrypoint for Windows 11."""

from __future__ import annotations

import argparse
import ctypes
import sys

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
    args = parser.parse_args()

    router = AetherRouter()

    if args.request:
        res = router.route(args.request)
        render_result(console, args.request, res)
        return 0 if res.success else 1

    console.print(
        Panel(
            "[bold cyan]AETHER[/bold cyan] Interactive Mode (4-Tier Waterfall Router)\n"
            "Type an instruction and press Enter, or [bold]exit[/bold] / [bold]quit[/bold] to leave.",
            border_style="cyan",
        )
    )
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
        res = router.route(user_input)
        render_result(console, user_input, res)

    return 0


if __name__ == "__main__":
    sys.exit(main())
