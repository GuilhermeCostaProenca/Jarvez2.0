from __future__ import annotations

# Privacy: no raw frames or embeddings leave the device
# Only structured events (event_type, posture, timestamps) are persisted.

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Union

from .movement_detector import MovementEvent
from .presence_detector import PresenceResult

logger = logging.getLogger(__name__)

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS visual_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    posture TEXT,
    presence INTEGER,
    confidence REAL,
    hour_of_day INTEGER,
    day_of_week INTEGER,
    timestamp TEXT NOT NULL,
    metadata TEXT
)
"""

_INSERT_SQL = """
INSERT INTO visual_events
    (event_type, posture, presence, confidence, hour_of_day, day_of_week, timestamp, metadata)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""

_RECENT_EVENTS_SQL = """
SELECT id, event_type, posture, presence, confidence, hour_of_day, day_of_week, timestamp, metadata
FROM visual_events
WHERE timestamp >= ?
ORDER BY timestamp DESC
"""

_PATTERN_SQL = """
SELECT event_type, hour_of_day, COUNT(*) as cnt
FROM visual_events
GROUP BY event_type, hour_of_day
ORDER BY event_type, cnt DESC
"""


def _default_db_path() -> Path:
    raw = os.getenv("JARVEZ_DB_PATH", "data/jarvez.db").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class VisualRoutineStore:
    """
    CAM5 — Persists structured visual events in SQLite.
    Uses the same DB as memory_manager (JARVEZ_DB_PATH or backend/data/jarvez.db).
    No raw frames, images, or embeddings are stored.
    """

    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path or _default_db_path()
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(_CREATE_TABLE_SQL)
                conn.commit()
            finally:
                conn.close()

    def record_event(self, event: Union[MovementEvent, PresenceResult]) -> None:
        """
        Persist a MovementEvent or PresenceResult as a structured row.
        Privacy: only event metadata is stored — no frames or embeddings.
        """
        now_dt = datetime.now(timezone.utc)
        hour_of_day = now_dt.hour
        day_of_week = now_dt.weekday()

        if isinstance(event, MovementEvent):
            event_type = event.event_type
            posture = event.metadata.get("to_posture") or event.metadata.get("from_posture")
            presence = None
            confidence = event.confidence
            timestamp = event.timestamp
            metadata_str = json.dumps(event.metadata) if event.metadata else None
        elif isinstance(event, PresenceResult):
            event_type = "presence_detected" if event.has_presence else "presence_lost"
            posture = None
            presence = 1 if event.has_presence else 0
            confidence = event.confidence
            timestamp = event.timestamp
            metadata_str = json.dumps({"motion_area": event.motion_area})
        else:
            logger.warning("VisualRoutineStore.record_event: unknown event type %s", type(event))
            return

        try:
            with self._lock:
                conn = self._connect()
                try:
                    conn.execute(
                        _INSERT_SQL,
                        (
                            event_type,
                            posture,
                            presence,
                            confidence,
                            hour_of_day,
                            day_of_week,
                            timestamp,
                            metadata_str,
                        ),
                    )
                    conn.commit()
                finally:
                    conn.close()
        except Exception as exc:
            logger.error("VisualRoutineStore: failed to record event: %s", exc)

    def get_recent_events(self, hours: int = 24) -> list[dict[str, Any]]:
        """Return events from the last N hours."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        try:
            with self._lock:
                conn = self._connect()
                try:
                    rows = conn.execute(_RECENT_EVENTS_SQL, (cutoff,)).fetchall()
                finally:
                    conn.close()
            result = []
            for row in rows:
                meta = None
                if row["metadata"]:
                    try:
                        meta = json.loads(row["metadata"])
                    except Exception:
                        meta = row["metadata"]
                result.append(
                    {
                        "id": row["id"],
                        "event_type": row["event_type"],
                        "posture": row["posture"],
                        "presence": bool(row["presence"]) if row["presence"] is not None else None,
                        "confidence": row["confidence"],
                        "hour_of_day": row["hour_of_day"],
                        "day_of_week": row["day_of_week"],
                        "timestamp": row["timestamp"],
                        "metadata": meta,
                    }
                )
            return result
        except Exception as exc:
            logger.error("VisualRoutineStore: failed to get recent events: %s", exc)
            return []

    def get_routine_patterns(self) -> dict[str, Any]:
        """
        Return simple heuristics: most common hour for each event type.
        """
        try:
            with self._lock:
                conn = self._connect()
                try:
                    rows = conn.execute(_PATTERN_SQL).fetchall()
                finally:
                    conn.close()

            patterns: dict[str, dict[str, Any]] = {}
            for row in rows:
                etype = row["event_type"]
                if etype not in patterns:
                    patterns[etype] = {
                        "most_common_hour": row["hour_of_day"],
                        "count": row["cnt"],
                    }
            return patterns
        except Exception as exc:
            logger.error("VisualRoutineStore: failed to get routine patterns: %s", exc)
            return {}
