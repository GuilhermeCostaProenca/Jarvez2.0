from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _default_db_path() -> Path:
    raw = os.getenv("JARVEZ_STATE_DB_PATH", "data/jarvez_state.db").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_payload(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return {str(key): _to_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_payload(item) for item in value]
    if isinstance(value, tuple):
        return [_to_payload(item) for item in value]
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            return str(value)
    return value


class JarvezStateStore:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or _default_db_path()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 30000")
        try:
            conn.execute("PRAGMA journal_mode = WAL")
        except sqlite3.OperationalError:
            pass
        return conn

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_state (
                    participant_identity TEXT NOT NULL,
                    room TEXT NOT NULL,
                    namespace TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (participant_identity, room, namespace)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS event_state (
                    participant_identity TEXT NOT NULL,
                    room TEXT NOT NULL,
                    namespace TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (participant_identity, room, namespace)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pending_confirmations (
                    token TEXT PRIMARY KEY,
                    participant_identity TEXT NOT NULL,
                    room TEXT NOT NULL,
                    action_name TEXT NOT NULL,
                    params_json TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS authenticated_sessions (
                    participant_identity TEXT NOT NULL,
                    room TEXT NOT NULL,
                    auth_method TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    last_activity_at TEXT NOT NULL,
                    PRIMARY KEY (participant_identity, room)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS channel_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    participant_identity TEXT NOT NULL,
                    room TEXT,
                    address TEXT,
                    text TEXT,
                    payload_json TEXT NOT NULL,
                    external_message_id TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(channel, direction, external_message_id)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_channel_messages_lookup
                ON channel_messages(channel, direction, created_at DESC)
                """
            )

    def upsert_session_state(
        self,
        *,
        participant_identity: str,
        room: str,
        namespace: str,
        payload: Any,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO session_state (participant_identity, room, namespace, payload_json, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(participant_identity, room, namespace)
                DO UPDATE SET payload_json=excluded.payload_json, updated_at=excluded.updated_at
                """,
                (
                    participant_identity,
                    room,
                    namespace,
                    json.dumps(_to_payload(payload), ensure_ascii=False),
                    _now_iso(),
                ),
            )

    def get_session_state(self, *, participant_identity: str, room: str, namespace: str) -> Any | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT payload_json
                FROM session_state
                WHERE participant_identity = ? AND room = ? AND namespace = ?
                """,
                (participant_identity, room, namespace),
            ).fetchone()
        if row is None:
            return None
        try:
            return json.loads(str(row["payload_json"]))
        except Exception:
            return None

    def list_session_state(self, *, participant_identity: str, room: str) -> dict[str, Any]:
        rows: dict[str, Any] = {}
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT namespace, payload_json
                FROM session_state
                WHERE participant_identity = ? AND room = ?
                """,
                (participant_identity, room),
            )
            for row in cursor.fetchall():
                try:
                    rows[str(row["namespace"])] = json.loads(str(row["payload_json"]))
                except Exception:
                    continue
        return rows

    def upsert_event_state(
        self,
        *,
        participant_identity: str,
        room: str,
        namespace: str,
        payload: Any,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO event_state (participant_identity, room, namespace, payload_json, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(participant_identity, room, namespace)
                DO UPDATE SET payload_json=excluded.payload_json, updated_at=excluded.updated_at
                """,
                (
                    participant_identity,
                    room,
                    namespace,
                    json.dumps(_to_payload(payload), ensure_ascii=False),
                    _now_iso(),
                ),
            )

    def get_event_state(self, *, participant_identity: str, room: str, namespace: str) -> Any | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT payload_json
                FROM event_state
                WHERE participant_identity = ? AND room = ? AND namespace = ?
                """,
                (participant_identity, room, namespace),
            ).fetchone()
        if row is None:
            return None
        try:
            return json.loads(str(row["payload_json"]))
        except Exception:
            return None

    def list_event_state(self, *, participant_identity: str, room: str) -> dict[str, Any]:
        rows: dict[str, Any] = {}
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT namespace, payload_json
                FROM event_state
                WHERE participant_identity = ? AND room = ?
                """,
                (participant_identity, room),
            )
            for row in cursor.fetchall():
                try:
                    rows[str(row["namespace"])] = json.loads(str(row["payload_json"]))
                except Exception:
                    continue
        return rows

    def save_pending_confirmation(
        self,
        *,
        token: str,
        participant_identity: str,
        room: str,
        action_name: str,
        params: dict[str, Any],
        expires_at: Any,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO pending_confirmations (token, participant_identity, room, action_name, params_json, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(token)
                DO UPDATE SET
                    participant_identity=excluded.participant_identity,
                    room=excluded.room,
                    action_name=excluded.action_name,
                    params_json=excluded.params_json,
                    expires_at=excluded.expires_at
                """,
                (
                    token,
                    participant_identity,
                    room,
                    action_name,
                    json.dumps(_to_payload(params), ensure_ascii=False),
                    expires_at.isoformat() if hasattr(expires_at, "isoformat") else str(expires_at),
                ),
            )

    def delete_pending_confirmation(self, token: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM pending_confirmations WHERE token = ?", (token,))

    def get_pending_confirmation(self, token: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT token, participant_identity, room, action_name, params_json, expires_at
                FROM pending_confirmations
                WHERE token = ?
                """,
                (token,),
            ).fetchone()
        if row is None:
            return None
        try:
            params = json.loads(str(row["params_json"]))
        except Exception:
            params = {}
        return {
            "token": str(row["token"]),
            "participant_identity": str(row["participant_identity"]),
            "room": str(row["room"]),
            "action_name": str(row["action_name"]),
            "params": params if isinstance(params, dict) else {},
            "expires_at": str(row["expires_at"]),
        }

    def find_pending_confirmation_token(self, participant_identity: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT token
                FROM pending_confirmations
                WHERE participant_identity = ?
                ORDER BY expires_at DESC
                LIMIT 1
                """,
                (participant_identity,),
            ).fetchone()
        if row is None:
            return None
        return str(row["token"])

    def save_authenticated_session(
        self,
        *,
        participant_identity: str,
        room: str,
        auth_method: str,
        expires_at: Any,
        last_activity_at: Any,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO authenticated_sessions (participant_identity, room, auth_method, expires_at, last_activity_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(participant_identity, room)
                DO UPDATE SET
                    auth_method=excluded.auth_method,
                    expires_at=excluded.expires_at,
                    last_activity_at=excluded.last_activity_at
                """,
                (
                    participant_identity,
                    room,
                    auth_method,
                    expires_at.isoformat() if hasattr(expires_at, "isoformat") else str(expires_at),
                    last_activity_at.isoformat() if hasattr(last_activity_at, "isoformat") else str(last_activity_at),
                ),
            )

    def delete_authenticated_session(self, *, participant_identity: str, room: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM authenticated_sessions WHERE participant_identity = ? AND room = ?",
                (participant_identity, room),
            )

    def get_authenticated_session(self, *, participant_identity: str, room: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT participant_identity, room, auth_method, expires_at, last_activity_at
                FROM authenticated_sessions
                WHERE participant_identity = ? AND room = ?
                """,
                (participant_identity, room),
            ).fetchone()
        if row is None:
            return None
        return {
            "participant_identity": str(row["participant_identity"]),
            "room": str(row["room"]),
            "auth_method": str(row["auth_method"]),
            "expires_at": str(row["expires_at"]),
            "last_activity_at": str(row["last_activity_at"]),
        }

    def append_channel_message(
        self,
        *,
        channel: str,
        direction: str,
        participant_identity: str,
        room: str | None,
        address: str | None,
        text: str | None,
        payload: Any,
        external_message_id: str | None = None,
        created_at: str | None = None,
    ) -> bool:
        normalized_external_id = (
            str(external_message_id or "").strip() if external_message_id is not None else None
        )
        if normalized_external_id == "":
            normalized_external_id = None
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO channel_messages (
                        channel,
                        direction,
                        participant_identity,
                        room,
                        address,
                        text,
                        payload_json,
                        external_message_id,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(channel, direction, external_message_id)
                    DO NOTHING
                    """,
                    (
                        channel,
                        direction,
                        participant_identity,
                        room,
                        address,
                        text,
                        json.dumps(_to_payload(payload), ensure_ascii=False),
                        normalized_external_id,
                        created_at or _now_iso(),
                    ),
                )
                return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False

    def list_channel_messages(
        self,
        *,
        channel: str,
        limit: int = 50,
        direction: str | None = None,
        participant_identity: str | None = None,
        address: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses = ["channel = ?"]
        args: list[Any] = [channel]
        if direction:
            clauses.append("direction = ?")
            args.append(direction)
        if participant_identity:
            clauses.append("participant_identity = ?")
            args.append(participant_identity)
        if address:
            clauses.append("address = ?")
            args.append(address)
        safe_limit = max(1, min(int(limit), 500))
        where = " AND ".join(clauses)
        rows: list[dict[str, Any]] = []
        with self._connect() as conn:
            cursor = conn.execute(
                f"""
                SELECT
                    id,
                    channel,
                    direction,
                    participant_identity,
                    room,
                    address,
                    text,
                    payload_json,
                    external_message_id,
                    created_at
                FROM channel_messages
                WHERE {where}
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                [*args, safe_limit],
            )
            for row in cursor.fetchall():
                try:
                    payload = json.loads(str(row["payload_json"]))
                except Exception:
                    payload = None
                rows.append(
                    {
                        "id": int(row["id"]),
                        "channel": str(row["channel"]),
                        "direction": str(row["direction"]),
                        "participant_identity": str(row["participant_identity"]),
                        "room": str(row["room"]) if row["room"] is not None else None,
                        "address": str(row["address"]) if row["address"] is not None else None,
                        "text": str(row["text"]) if row["text"] is not None else None,
                        "payload": payload if isinstance(payload, dict) else payload,
                        "external_message_id": str(row["external_message_id"])
                        if row["external_message_id"] is not None
                        else None,
                        "created_at": str(row["created_at"]),
                    }
                )
        return rows

    def count_channel_messages(self, *, channel: str, direction: str | None = None) -> int:
        clauses = ["channel = ?"]
        args: list[Any] = [channel]
        if direction:
            clauses.append("direction = ?")
            args.append(direction)
        where = " AND ".join(clauses)
        with self._connect() as conn:
            row = conn.execute(
                f"""
                SELECT COUNT(1) AS total
                FROM channel_messages
                WHERE {where}
                """,
                args,
            ).fetchone()
        if row is None:
            return 0
        try:
            return int(row["total"])
        except Exception:
            return 0

    def latest_channel_message(self, *, channel: str, direction: str | None = None) -> dict[str, Any] | None:
        rows = self.list_channel_messages(channel=channel, limit=1, direction=direction)
        if not rows:
            return None
        return rows[0]

    def clear_all(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM session_state")
            conn.execute("DELETE FROM event_state")
            conn.execute("DELETE FROM pending_confirmations")
            conn.execute("DELETE FROM authenticated_sessions")
            conn.execute("DELETE FROM channel_messages")


_STATE_STORE: JarvezStateStore | None = None


def get_state_store() -> JarvezStateStore:
    global _STATE_STORE
    if _STATE_STORE is None:
        _STATE_STORE = JarvezStateStore()
    return _STATE_STORE
