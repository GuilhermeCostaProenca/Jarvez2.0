from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]

_ALLOWED_FIELDS = {
    "timestamp",
    "event_type",
    "participant_identity",
    "room",
    "method",
    "profile_name",
    "success",
    "confidence",
    "threshold_used",
    "margin_to_second",
    "failure_reason",
    "relock_reason",
    "auth_state_status",
    "source_action",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_telemetry_path() -> Path:
    raw = os.getenv("JARVEZ_BIOMETRIC_TELEMETRY_PATH", "data/identity/biometric_telemetry.jsonl").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _normalize_event(payload: JsonObject) -> JsonObject:
    event: JsonObject = {
        "timestamp": str(payload.get("timestamp") or _now_iso()),
        "event_type": str(payload.get("event_type") or "unknown").strip() or "unknown",
        "participant_identity": str(payload.get("participant_identity") or "").strip(),
        "room": str(payload.get("room") or "").strip(),
    }
    for key in _ALLOWED_FIELDS - {"timestamp", "event_type", "participant_identity", "room"}:
        value = payload.get(key)
        if value is None or value == "":
            continue
        if key == "success":
            event[key] = bool(value)
        elif key in {"confidence", "threshold_used", "margin_to_second"}:
            try:
                event[key] = max(0.0, min(float(value), 1.0))
            except (TypeError, ValueError):
                continue
        else:
            event[key] = str(value).strip()
    return event


class BiometricTelemetryStore:
    def __init__(self, file_path: Path | None = None) -> None:
        self.file_path = file_path or _default_telemetry_path()
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    @classmethod
    def from_env(cls) -> "BiometricTelemetryStore":
        return cls(file_path=_default_telemetry_path())

    def append_event(self, payload: JsonObject) -> JsonObject:
        normalized = _normalize_event(payload)
        with self._lock:
            with self.file_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(normalized, ensure_ascii=False) + "\n")
        return normalized

    def list_events(
        self,
        *,
        participant_identity: str | None = None,
        room: str | None = None,
        limit: int = 50,
        event_types: set[str] | None = None,
    ) -> list[JsonObject]:
        if not self.file_path.exists():
            return []
        try:
            rows = self.file_path.read_text(encoding="utf-8").splitlines()
        except Exception:
            return []
        events: list[JsonObject] = []
        for raw in rows:
            if not raw.strip():
                continue
            try:
                payload = json.loads(raw)
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            if participant_identity and str(payload.get("participant_identity") or "") != participant_identity:
                continue
            if room and str(payload.get("room") or "") != room:
                continue
            if event_types and str(payload.get("event_type") or "") not in event_types:
                continue
            events.append(payload)
        return list(reversed(events[-max(1, limit) :]))

    def recent_failure_reasons(
        self,
        *,
        participant_identity: str,
        room: str,
        limit: int = 5,
    ) -> list[JsonObject]:
        rows = self.list_events(
            participant_identity=participant_identity,
            room=room,
            limit=max(limit * 3, limit),
            event_types={"unlock_failure", "recovery_failure", "step_up_required", "relock"},
        )
        failures: list[JsonObject] = []
        for row in rows:
            reason = str(row.get("failure_reason") or row.get("relock_reason") or "").strip()
            if not reason:
                continue
            failures.append(
                {
                    "timestamp": row.get("timestamp"),
                    "method": row.get("method"),
                    "reason": reason,
                    "event_type": row.get("event_type"),
                }
            )
            if len(failures) >= limit:
                break
        return failures
