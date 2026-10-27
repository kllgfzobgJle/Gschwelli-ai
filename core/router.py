"""AETHER 4-Tier Hybrid Automation Waterfall Router."""

from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Callable, List, Optional

from core.blackboard import LogEntry, blackboard
from core.schemas import Action, AgentPlan, VerificationCheck
from core.verifier import verify_plan
from engines.cache_store import cache_store
from engines.gemini_engine import gemini_engine
from engines.ollama_engine import ollama_engine
from executors.vision_som import capture_window_som_jpeg
from executors.win32_uia import get_active_target_hwnd, uia_executor
from memory.memory_manager import save_session_summary
from tools.registry import registry

_NON_CACHEABLE_TOOLS = {
    "undo_action",
    "confirm_pending",
    "remember_fact",
    "recall_memory",
    "forget_fact",
    "delete_to_trash",
}


@dataclass
class RouteResult:
    success: bool
    active_tier: int
    elapsed_ms: float
    instruction: str = ""
    plan: Optional[AgentPlan] = None
    outputs: List[str] = field(default_factory=list)
    verification_logs: List[str] = field(default_factory=list)
    logs: List[LogEntry] = field(default_factory=list)


class AetherRouter:
    """
    4-Tier Waterfall Router:
      Tier 0: Deterministic SQLite Cache & Parameterized Template Cache (<10 ms)
      Tier 1: Local Fast-Path Executor via Ollama qwen2.5-coder:7b (<1.5 s, NO screenshots)
      Tier 2: Structural Windows UIA / Accessibility (0.1s - 0.5s, no terminal OCR clicks)
      Tier 3: Selective Cloud Vision Fallback via Gemini 3.8 Flash SoM (3s - 8s)
    """

    def __init__(self) -> None:
        registry.discover()
        self._listeners: List[Callable[[RouteResult], None]] = []
        self._history: List[RouteResult] = []

    def add_listener(self, callback: Callable[[RouteResult], None]) -> None:
        """Register a listener notified after every completed route (used by GUI/WebSocket)."""
        self._listeners.append(callback)

    def get_history(self, limit: int = 30) -> List[RouteResult]:
        return list(reversed(self._history[-limit:]))

    def _should_cache(self, plan: AgentPlan) -> bool:
        for act in plan.actions:
            if act.tool in _NON_CACHEABLE_TOOLS:
                return False
        return True

    def _finalize(self, result: RouteResult) -> RouteResult:
        self._history.append(result)
        if len(self._history) > 100:
            self._history = self._history[-100:]
        try:
            summary_out = "; ".join(result.outputs)[:200] if result.outputs else "no output"
            save_session_summary(
                f"[T{result.active_tier} | {result.elapsed_ms:.1f}ms | {'OK' if result.success else 'FAIL'}] "
                f"{result.instruction} -> {summary_out}"
            )
        except Exception:
            pass
        for cb in list(self._listeners):
            try:
                cb(result)
            except Exception:
                pass
        return result

    def _execute_actions(self, plan: AgentPlan, tier: int) -> tuple[bool, List[str]]:
        outputs: List[str] = []
        if not plan.actions:
            return False, ["Plan contained no executable actions"]

        for act in plan.actions:
            tool_name = act.tool.strip()
            blackboard.log(tier, f"Executing {tool_name}({act.args})")
            try:
                out = registry.execute(tool_name, act.args)
                outputs.append(out)
                blackboard.log(tier, f"Result -> {out}")
                if out.startswith("status=failed"):
                    return False, outputs
            except Exception as exc:
                err_msg = f"Action '{tool_name}' raised exception: {exc}"
                outputs.append(err_msg)
                blackboard.log(tier, err_msg, "ERROR")
                return False, outputs

        return True, outputs

    def _ensure_default_verification(self, plan: AgentPlan) -> None:
        """Ensure Notepad / file actions always carry a deterministic verification check."""
        if plan.verification:
            return
        for act in plan.actions:
            if act.tool == "write_text_to_notepad":
                txt = str(act.args.get("text") or "")
                plan.verification = [
                    VerificationCheck(type="process_running", target="notepad.exe"),
                    VerificationCheck(type="file_exists", target="", expected=txt),
                ]
                return
            if act.tool == "open_or_focus_app":
                app = str(act.args.get("app_name") or "")
                if app:
                    plan.verification = [VerificationCheck(type="process_running", target=app)]
                    return
            if act.tool == "write_text":
                path = str(act.args.get("path") or "")
                txt = str(act.args.get("text") or "")
                plan.verification = [VerificationCheck(type="file_exists", target=path, expected=txt)]
                return

    def _try_tier2_uia(self, instruction: str, failed_plan: Optional[AgentPlan] = None) -> Optional[AgentPlan]:
        """Attempt Tier 2 structural Windows UIA execution on the active non-terminal window."""
        blackboard.log(2, "Inspecting active non-terminal GUI window via Windows UIA tree...")
        hwnd = get_active_target_hwnd(exclude_terminal=True)
        if not hwnd:
            blackboard.log(2, "No non-terminal GUI window found for Tier 2 UIA interaction.", "WARN")
            return None

        controls = uia_executor.inspect_window_controls(hwnd=hwnd, max_elements=30)
        blackboard.log(2, f"Found {len(controls)} interactive UIA controls on HWND {hwnd}")

        if failed_plan and failed_plan.actions:
            for act in failed_plan.actions:
                if act.tool in ("uia_click", "uia_type"):
                    return failed_plan

        low = instruction.lower()
        for ctrl in controls:
            cname = (ctrl.get("name") or "").strip()
            if cname and len(cname) >= 3 and cname.lower() in low and ("klick" in low or "click" in low):
                return AgentPlan(
                    thought=f"Tier 2 structural UIA match on control '{cname}'",
                    tier=2,
                    requires_vision=False,
                    actions=[Action(tool="uia_click", args={"control_name": cname})],
                    verification=[],
                )
        return None

    def route(self, instruction: str) -> RouteResult:
        """Process an incoming user instruction through the 4-Tier Waterfall."""
        blackboard.reset_turn()
        t_start = time.perf_counter()

        # ─────────────────────────────────────────────────────────────────────
        # TIER 0: Deterministic SQLite Hash + Parameterized Template Cache (<10 ms)
        # ─────────────────────────────────────────────────────────────────────
        t0_start = time.perf_counter()
        cached_plan = cache_store.get(instruction)
        t0_ms = (time.perf_counter() - t0_start) * 1000.0
        if cached_plan is not None:
            blackboard.log(0, f"Cache HIT in {t0_ms:.2f} ms — replaying verified plan without LLM")
            exec_ok, outputs = self._execute_actions(cached_plan, tier=0)
            ver_ok, ver_logs = verify_plan(cached_plan.verification)
            for vlog in ver_logs:
                blackboard.log(0, vlog)
            if exec_ok and ver_ok:
                total_ms = (time.perf_counter() - t_start) * 1000.0
                return self._finalize(
                    RouteResult(
                        success=True,
                        active_tier=0,
                        elapsed_ms=total_ms,
                        instruction=instruction,
                        plan=cached_plan,
                        outputs=outputs,
                        verification_logs=ver_logs,
                        logs=blackboard.get_logs(),
                    )
                )
            blackboard.log(0, "Cached plan replay verification failed; escalating to Tier 1", "WARN")
        else:
            blackboard.log(0, f"Cache MISS ({t0_ms:.2f} ms) -> Escalating to Tier 1 (Ollama Fast-Path)")

        # ─────────────────────────────────────────────────────────────────────
        # TIER 1: Local Fast-Path Executor (<1.5 s, Ollama qwen2.5-coder:7b)
        # ─────────────────────────────────────────────────────────────────────
        blackboard.log(1, "Querying local Ollama (qwen2.5-coder:7b) for fast-path JSON plan...")
        plan_t1 = ollama_engine.generate_plan(instruction)
        if plan_t1 is not None and not plan_t1.requires_vision and plan_t1.actions:
            self._ensure_default_verification(plan_t1)
            exec_ok, outputs = self._execute_actions(plan_t1, tier=1)
            ver_ok, ver_logs = verify_plan(plan_t1.verification)
            for vlog in ver_logs:
                blackboard.log(1, vlog)

            if exec_ok and ver_ok:
                if self._should_cache(plan_t1):
                    cache_store.put(instruction, plan_t1, origin_tier=1)
                    blackboard.log(1, "Tier 1 execution verified and stored in Tier 0 cache (`cache/aether.db`).")
                total_ms = (time.perf_counter() - t_start) * 1000.0
                return self._finalize(
                    RouteResult(
                        success=True,
                        active_tier=1,
                        elapsed_ms=total_ms,
                        instruction=instruction,
                        plan=plan_t1,
                        outputs=outputs,
                        verification_logs=ver_logs,
                        logs=blackboard.get_logs(),
                    )
                )
            blackboard.log(1, "Tier 1 verification did not pass; escalating to Tier 2 (Windows UIA)", "WARN")
        else:
            blackboard.log(1, "Tier 1 deferred to GUI/Vision tiers", "WARN")

        # ─────────────────────────────────────────────────────────────────────
        # TIER 2: Structural Windows UIA / Accessibility (0.1s - 0.5s)
        # ─────────────────────────────────────────────────────────────────────
        plan_t2 = self._try_tier2_uia(instruction, failed_plan=plan_t1)
        if plan_t2 is not None:
            exec_ok, outputs = self._execute_actions(plan_t2, tier=2)
            ver_ok, ver_logs = verify_plan(plan_t2.verification)
            for vlog in ver_logs:
                blackboard.log(2, vlog)
            if exec_ok and ver_ok:
                if self._should_cache(plan_t2):
                    cache_store.put(instruction, plan_t2, origin_tier=2)
                total_ms = (time.perf_counter() - t_start) * 1000.0
                return self._finalize(
                    RouteResult(
                        success=True,
                        active_tier=2,
                        elapsed_ms=total_ms,
                        instruction=instruction,
                        plan=plan_t2,
                        outputs=outputs,
                        verification_logs=ver_logs,
                        logs=blackboard.get_logs(),
                    )
                )

        # ─────────────────────────────────────────────────────────────────────
        # TIER 3: Selective Cloud Vision Fallback (3s - 8s, Gemini 3.8 Flash)
        # ─────────────────────────────────────────────────────────────────────
        blackboard.log(3, "Escalating to Tier 3 Selective Cloud Vision Fallback (Gemini 3.8 Flash + SoM)...")
        try:
            som_jpeg, som_elements, _ = capture_window_som_jpeg()
            plan_t3 = gemini_engine.generate_vision_plan(instruction, som_jpeg, som_elements)
            if plan_t3 is not None and plan_t3.actions:
                exec_ok, outputs = self._execute_actions(plan_t3, tier=3)
                ver_ok, ver_logs = verify_plan(plan_t3.verification)
                for vlog in ver_logs:
                    blackboard.log(3, vlog)
                if exec_ok and ver_ok:
                    if self._should_cache(plan_t3):
                        cache_store.put(instruction, plan_t3, origin_tier=3)
                    total_ms = (time.perf_counter() - t_start) * 1000.0
                    return self._finalize(
                        RouteResult(
                            success=True,
                            active_tier=3,
                            elapsed_ms=total_ms,
                            instruction=instruction,
                            plan=plan_t3,
                            outputs=outputs,
                            verification_logs=ver_logs,
                            logs=blackboard.get_logs(),
                        )
                    )
        except Exception as exc:
            blackboard.log(3, f"Tier 3 Vision fallback error: {exc}", "ERROR")

        total_ms = (time.perf_counter() - t_start) * 1000.0
        return self._finalize(
            RouteResult(
                success=False,
                active_tier=3,
                elapsed_ms=total_ms,
                instruction=instruction,
                plan=plan_t1,
                outputs=[],
                verification_logs=["All tiers exhausted without verified completion."],
                logs=blackboard.get_logs(),
            )
        )
