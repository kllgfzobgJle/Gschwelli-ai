"""Tier 0 Deterministic SQLite Exact + Parameterized Template Cache (<10 ms lookup)."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.schemas import AgentPlan

_QUOTED_SLOT_RE = re.compile(r"(['\"])([^'\"]+)\1")


def normalize_instruction_hash(instruction: str) -> str:
    """Compute a deterministic SHA-256 hash for an incoming user instruction."""
    normalized = " ".join((instruction or "").strip().split()).lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def extract_template_and_slots(instruction: str) -> Tuple[str, List[str]]:
    """
    Normalize quoted values in an instruction into positional placeholders `{slot_0}`, `{slot_1}`, ...
    Returns `(template_hash, extracted_slot_values)`.
    Example:
      "Starte Notepad und schreibe 'Hallo Welt' in ein neues Dokument"
      -> pattern "starte notepad und schreibe '{slot_0}' in ein neues dokument", slots=["Hallo Welt"]
    """
    slots: List[str] = []

    def _repl(match: re.Match[str]) -> str:
        idx = len(slots)
        slots.append(match.group(2))
        return f"'{{" + f"slot_{idx}" + f"}}'"

    templated = _QUOTED_SLOT_RE.sub(_repl, (instruction or "").strip())
    normalized_pattern = " ".join(templated.split()).lower()
    template_hash = hashlib.sha256(normalized_pattern.encode("utf-8")).hexdigest()
    return template_hash, slots


def _replace_value_with_placeholders(obj: Any, slots: List[str]) -> Any:
    """Replace literal slot values in a plan dictionary with `{slot_i}` placeholders."""
    if isinstance(obj, str):
        out = obj
        for idx, val in enumerate(slots):
            if val and val in out:
                out = out.replace(val, f"{{slot_{idx}}}")
        return out
    if isinstance(obj, dict):
        return {k: _replace_value_with_placeholders(v, slots) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_replace_value_with_placeholders(item, slots) for item in obj]
    return obj


def _substitute_placeholders(obj: Any, slots: List[str]) -> Any:
    """Substitute `{slot_i}` placeholders in a plan template with runtime slot values."""
    if isinstance(obj, str):
        out = obj
        for idx, val in enumerate(slots):
            placeholder = f"{{slot_{idx}}}"
            if placeholder in out:
                out = out.replace(placeholder, val)
        return out
    if isinstance(obj, dict):
        return {k: _substitute_placeholders(v, slots) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_substitute_placeholders(item, slots) for item in obj]
    return obj


class CacheStore:
    """SQLite-backed hash & parameterized template cache for verified AgentPlans (`cache/aether.db`)."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        base_dir = Path(__file__).resolve().parent.parent
        self.db_path = db_path or (base_dir / "cache" / "aether.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        with self._conn:
            self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.execute("PRAGMA synchronous=NORMAL;")
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS verified_plans (
                    task_hash TEXT PRIMARY KEY,
                    instruction TEXT NOT NULL,
                    plan_json TEXT NOT NULL,
                    origin_tier INTEGER NOT NULL,
                    created_at REAL NOT NULL,
                    hit_count INTEGER DEFAULT 0
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS plan_templates (
                    template_hash TEXT PRIMARY KEY,
                    pattern_example TEXT NOT NULL,
                    slot_count INTEGER NOT NULL,
                    template_plan_json TEXT NOT NULL,
                    origin_tier INTEGER NOT NULL,
                    created_at REAL NOT NULL,
                    hit_count INTEGER DEFAULT 0
                )
                """
            )

    def get(self, instruction: str) -> Optional[AgentPlan]:
        """
        Look up a verified plan in <10 ms:
          1. Check exact SHA-256 hash (`verified_plans`).
          2. Check parameterized slot template (`plan_templates`) when quoted arguments vary.
        """
        task_hash = normalize_instruction_hash(instruction)
        cur = self._conn.cursor()
        row = cur.execute(
            "SELECT plan_json FROM verified_plans WHERE task_hash = ?",
            (task_hash,),
        ).fetchone()
        if row:
            try:
                plan = AgentPlan.model_validate_json(row[0])
                plan.tier = 0
                with self._conn:
                    self._conn.execute(
                        "UPDATE verified_plans SET hit_count = hit_count + 1 WHERE task_hash = ?",
                        (task_hash,),
                    )
                return plan
            except Exception:
                pass

        # Fallback to parameterized template lookup (<2 ms)
        template_hash, slots = extract_template_and_slots(instruction)
        if slots:
            t_row = cur.execute(
                "SELECT template_plan_json, slot_count FROM plan_templates WHERE template_hash = ?",
                (template_hash,),
            ).fetchone()
            if t_row and int(t_row[1]) == len(slots):
                try:
                    raw_dict = json.loads(t_row[0])
                    hydrated_dict = _substitute_placeholders(raw_dict, slots)
                    plan = AgentPlan.model_validate(hydrated_dict)
                    plan.tier = 0
                    with self._conn:
                        self._conn.execute(
                            "UPDATE plan_templates SET hit_count = hit_count + 1 WHERE template_hash = ?",
                            (template_hash,),
                        )
                    return plan
                except Exception:
                    pass

        return None

    def put(self, instruction: str, plan: AgentPlan, origin_tier: int = 1) -> None:
        """Store both the exact plan and (if parameterized slots exist) a generalized template plan."""
        task_hash = normalize_instruction_hash(instruction)
        plan_json = plan.model_dump_json()
        now = time.time()
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO verified_plans (task_hash, instruction, plan_json, origin_tier, created_at, hit_count)
                VALUES (?, ?, ?, ?, ?, 0)
                ON CONFLICT(task_hash) DO UPDATE SET
                    plan_json = excluded.plan_json,
                    origin_tier = excluded.origin_tier,
                    created_at = excluded.created_at
                """,
                (task_hash, instruction.strip(), plan_json, origin_tier, now),
            )

            template_hash, slots = extract_template_and_slots(instruction)
            if slots:
                raw_dict = plan.model_dump()
                templated_dict = _replace_value_with_placeholders(raw_dict, slots)
                template_json = json.dumps(templated_dict, ensure_ascii=False)
                self._conn.execute(
                    """
                    INSERT INTO plan_templates (
                        template_hash, pattern_example, slot_count, template_plan_json, origin_tier, created_at, hit_count
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                    ON CONFLICT(template_hash) DO UPDATE SET
                        template_plan_json = excluded.template_plan_json,
                        origin_tier = excluded.origin_tier,
                        created_at = excluded.created_at
                    """,
                    (template_hash, instruction.strip(), len(slots), template_json, origin_tier, now),
                )

    def list_entries(self, limit: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """Return cached exact plans and templates for the Dashboard UI."""
        cur = self._conn.cursor()
        exact_rows = cur.execute(
            "SELECT task_hash, instruction, origin_tier, created_at, hit_count FROM verified_plans ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        tmpl_rows = cur.execute(
            "SELECT template_hash, pattern_example, slot_count, origin_tier, created_at, hit_count FROM plan_templates ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return {
            "exact": [
                {
                    "hash": r[0][:12],
                    "instruction": r[1],
                    "origin_tier": r[2],
                    "created_at": r[3],
                    "hits": r[4],
                }
                for r in exact_rows
            ],
            "templates": [
                {
                    "hash": r[0][:12],
                    "pattern_example": r[1],
                    "slots": r[2],
                    "origin_tier": r[3],
                    "created_at": r[4],
                    "hits": r[5],
                }
                for r in tmpl_rows
            ],
        }

    def clear(self) -> None:
        """Clear all cached plans and templates."""
        with self._conn:
            self._conn.execute("DELETE FROM verified_plans")
            self._conn.execute("DELETE FROM plan_templates")


cache_store = CacheStore()
