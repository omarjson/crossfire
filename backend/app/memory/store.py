"""SQLite-backed session store — same interface as the Phase 1 in-memory
version, plus longitudinal progress stats across debates.

DB path: CROSSFIRE_DB_PATH env, default backend/data/crossfire.db.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Session:
    id: str
    motion: str
    persona: str
    difficulty: str
    lang: str = "en"
    rounds: list[dict[str, Any]] = field(default_factory=list)
    flips: list[dict[str, Any]] = field(default_factory=list)
    finished: bool = False


def _db_path() -> str:
    return os.environ.get(
        "CROSSFIRE_DB_PATH",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                     "data", "crossfire.db"),
    )


_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    motion TEXT NOT NULL,
    persona TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    finished INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS rounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    round_no INTEGER NOT NULL,
    payload TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS flips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    after_round INTEGER NOT NULL,
    payload TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rounds_session ON rounds(session_id);
CREATE INDEX IF NOT EXISTS idx_flips_session ON flips(session_id);
"""


class MemoryStore:
    """SQLite store. Single connection + lock; safe for the TestClient too."""

    def __init__(self, path: str | None = None) -> None:
        self._path = path or _db_path()
        if self._path != ":memory:":
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(_SCHEMA)
            # Migration: debate language for sessions created before i18n.
            cols = [r[1] for r in self._conn.execute(
                "PRAGMA table_info(sessions)").fetchall()]
            if "lang" not in cols:
                self._conn.execute(
                    "ALTER TABLE sessions ADD COLUMN lang TEXT NOT NULL DEFAULT 'en'")
            # WAL mode: readers don't block writers (concurrent API calls).
            self._conn.execute("PRAGMA journal_mode=WAL;")
            # Startup integrity check: fail fast on a corrupt database.
            row = self._conn.execute("PRAGMA integrity_check;").fetchone()
            if not row or row[0] != "ok":
                raise RuntimeError(
                    f"SQLite integrity check failed for {self._path}: "
                    f"{row[0] if row else 'no result'}")
            self._conn.commit()

    # ---- sessions ----

    def create(self, motion: str, persona: str, difficulty: str,
               lang: str = "en") -> Session:
        sid = uuid.uuid4().hex[:12]
        lang = lang if lang in ("en", "ar") else "en"
        with self._lock:
            self._conn.execute(
                "INSERT INTO sessions (id, motion, persona, difficulty, lang, finished, created_at)"
                " VALUES (?, ?, ?, ?, ?, 0, ?)",
                (sid, motion, persona, difficulty, lang, time.time()),
            )
            self._conn.commit()
        return Session(id=sid, motion=motion, persona=persona,
                       difficulty=difficulty, lang=lang)

    def get(self, session_id: str) -> Session | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
            if not row:
                return None
            rounds = [
                json.loads(r["payload"]) for r in self._conn.execute(
                    "SELECT payload FROM rounds WHERE session_id = ? ORDER BY round_no",
                    (session_id,))
            ]
            flips = [
                json.loads(r["payload"]) for r in self._conn.execute(
                    "SELECT payload FROM flips WHERE session_id = ? ORDER BY id",
                    (session_id,))
            ]
        return Session(id=row["id"], motion=row["motion"], persona=row["persona"],
                       difficulty=row["difficulty"], lang=row["lang"] or "en",
                       rounds=rounds, flips=flips,
                       finished=bool(row["finished"]))

    def append_round(self, session_id: str, round_data: dict[str, Any]) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO rounds (session_id, round_no, payload, created_at)"
                " VALUES (?, ?, ?, ?)",
                (session_id, round_data.get("round", 0),
                 json.dumps(round_data), time.time()),
            )
            self._conn.commit()

    def append_flip(self, session_id: str, flip_data: dict[str, Any]) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO flips (session_id, after_round, payload, created_at)"
                " VALUES (?, ?, ?, ?)",
                (session_id, flip_data.get("after_round", 0),
                 json.dumps(flip_data), time.time()),
            )
            self._conn.commit()

    def finish(self, session_id: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE sessions SET finished = 1 WHERE id = ?", (session_id,))
            self._conn.commit()

    # ---- longitudinal progress ----

    def progress(self) -> dict[str, Any]:
        """Cross-debate stats: fallacy profile, hygiene trend, debate count."""
        with self._lock:
            sessions = self._conn.execute(
                "SELECT id, finished, created_at FROM sessions ORDER BY created_at"
            ).fetchall()
            round_rows = self._conn.execute(
                "SELECT session_id, payload FROM rounds").fetchall()
            flip_count = self._conn.execute(
                "SELECT COUNT(*) AS n FROM flips").fetchone()["n"]

        fallacy_profile: dict[str, int] = {}
        total_rounds = 0
        hygiene_by_debate = []
        for s in sessions:
            payloads = [json.loads(r["payload"]) for r in round_rows
                        if r["session_id"] == s["id"]]
            if not payloads:
                continue
            total_rounds += len(payloads)
            for p in payloads:
                for f in p.get("user_fallacies", []):
                    t = f.get("type", "unknown")
                    fallacy_profile[t] = fallacy_profile.get(t, 0) + 1
            checked = sum(p.get("checks_total", 0) for p in payloads)
            verified = sum(p.get("checks_verified", 0) for p in payloads)
            hygiene_by_debate.append({
                "session_id": s["id"][:8],
                "rounds": len(payloads),
                "hygiene": round(verified / checked, 2) if checked else 1.0,
                "finished": bool(s["finished"]),
            })

        total_fallacies = sum(fallacy_profile.values())
        return {
            "debates": len(sessions),
            "finished_debates": sum(1 for s in sessions if s["finished"]),
            "total_rounds": total_rounds,
            "total_flips": flip_count,
            "fallacy_profile": dict(sorted(fallacy_profile.items(),
                                           key=lambda kv: -kv[1])),
            "fallacy_rate_per_round": round(total_fallacies / total_rounds, 2)
            if total_rounds else 0.0,
            "hygiene_by_debate": hygiene_by_debate,
        }
