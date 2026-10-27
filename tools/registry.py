"""Dynamic tool discovery and @action decorator registry (adapted from Mark-LVI action_loader.py)."""

from __future__ import annotations

import importlib.util
import inspect
import re
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,63}$")


@dataclass
class ToolRecord:
    name: str
    description: str
    handler: Callable[..., Any]
    parameters: Dict[str, Any] = field(default_factory=dict)
    module_file: str = ""


_REGISTERED_TOOLS: Dict[str, ToolRecord] = {}


def action(
    name: Optional[str] = None,
    description: str = "",
    parameters: Optional[Dict[str, Any]] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to register a function as a discoverable AETHER tool."""

    def _decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = (name or fn.__name__).strip()
        if not _NAME_RE.match(tool_name):
            raise ValueError(f"Invalid tool name: {tool_name!r}")
        tool_desc = (description or (fn.__doc__ or "")).strip()
        sig = inspect.signature(fn)
        inferred_params = parameters or {
            param_name: str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any"
            for param_name, param in sig.parameters.items()
        }
        rec = ToolRecord(
            name=tool_name,
            description=tool_desc,
            handler=fn,
            parameters=inferred_params,
            module_file=getattr(fn, "__module__", ""),
        )
        _REGISTERED_TOOLS[tool_name] = rec
        setattr(fn, "_aether_tool_record", rec)
        return fn

    return _decorator


class ToolRegistry:
    """Registry managing discovered `@action` tools in `tools/`."""

    def __init__(self) -> None:
        self._discovered = False

    def discover(self, tools_dir: Optional[Path] = None) -> None:
        if self._discovered and _REGISTERED_TOOLS:
            return
        target_dir = tools_dir or Path(__file__).resolve().parent
        for path in sorted(target_dir.glob("*.py"), key=lambda p: p.name):
            if path.name.startswith("_") or path.name == "registry.py":
                continue
            mod_name = f"tools.{path.stem}"
            if mod_name not in sys.modules:
                try:
                    spec = importlib.util.spec_from_file_location(mod_name, path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[mod_name] = module
                        spec.loader.exec_module(module)
                except Exception:
                    traceback.print_exc()
        # Also import memory_manager so @action memory tools are registered
        try:
            import memory.memory_manager  # noqa: F401
        except Exception:
            pass
        self._discovered = True

    def has(self, name: str) -> bool:
        self.discover()
        return name in _REGISTERED_TOOLS

    def names(self) -> List[str]:
        self.discover()
        return sorted(_REGISTERED_TOOLS.keys())

    def get_declarations(self) -> List[Dict[str, Any]]:
        self.discover()
        return [
            {
                "name": rec.name,
                "description": rec.description,
                "parameters": rec.parameters,
            }
            for rec in _REGISTERED_TOOLS.values()
        ]

    def list_tools(self) -> List[ToolRecord]:
        self.discover()
        return list(_REGISTERED_TOOLS.values())

    def execute(self, name: str, args: Optional[Dict[str, Any]] = None) -> str:
        self.discover()
        rec = _REGISTERED_TOOLS.get(name)
        if rec is None:
            raise KeyError(f"Tool '{name}' is not registered. Available: {self.names()}")

        kwargs = dict(args or {})
        sig = inspect.signature(rec.handler)
        has_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
        if not has_var_kw:
            # Map common parameter aliases gracefully
            param_names = list(sig.parameters.keys())
            filtered: Dict[str, Any] = {}
            for k, v in kwargs.items():
                if k in sig.parameters:
                    filtered[k] = v
                elif k in ("content", "value", "string", "message") and "text" in sig.parameters and "text" not in filtered:
                    filtered["text"] = v
                elif k in ("app", "application", "target", "program", "name") and "app_name" in sig.parameters and "app_name" not in filtered:
                    filtered["app_name"] = v
                elif k in ("file", "filepath", "filename", "target") and "path" in sig.parameters and "path" not in filtered:
                    filtered["path"] = v
                elif k in ("cmd", "script", "powershell") and "command" in sig.parameters and "command" not in filtered:
                    filtered["command"] = v
            # If a single positional parameter exists and only 1 arg was passed with a different key
            if not filtered and len(param_names) == 1 and len(kwargs) == 1:
                filtered[param_names[0]] = next(iter(kwargs.values()))
            kwargs = filtered

        result = rec.handler(**kwargs)
        return str(result) if result is not None else "status=done"


registry = ToolRegistry()
