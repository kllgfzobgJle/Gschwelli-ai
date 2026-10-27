"""Tier 0 Deterministic SQLite Hash Cache (<10 ms lookup)."""

from __future__ import annotations

import hashlib
import sqlite3
import time
from pathlib import Path
from typing import Optional

from core.schemas import AgentPlan


def normalize_instruction_hash(instruction: str) -> str:
    """Compute a deterministic SHA-256 hash for an incoming user instruction."""
    normalized = " ".join((instruction or "").strip().split()).lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class CacheStore:
    """SQLite-backed hash cache for previously verified AgentPlans (`cache/aether.db`)."""

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

    def get(self, instruction: str) -> Optional[AgentPlan]:
        """Look up a verified plan in <10 ms by normalized instruction hash."""
        task_hash = normalize_instruction_hash(instruction)
        cur = self._conn.cursor()
        row = cur.execute(
            "SELECT plan_json FROM verified_plans WHERE task_hash = ?",
            (task_hash,),
        ).fetchone()
        if not row:
            return None

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
            return None

    def put(self, instruction: str, plan: AgentPlan, origin_tier: int = 1) -> None:
        """Store a verified execution plan in `cache/aether.db`."""
        task_hash = normalize_instruction_hash(instruction)
        plan_json = plan.model_dump_json()
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
                (task_hash, instruction.strip(), plan_json, origin_tier, time.time()),
            )


cache_store = CacheStore()
