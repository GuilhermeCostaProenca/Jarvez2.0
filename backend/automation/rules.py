from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import Any

JsonObject = dict[str, Any]

AUTOMATION_STATE_VERSION = "f2.3"

# Intermediate execution status constants
AUTOMATION_STATUS_IDLE = "idle"
AUTOMATION_STATUS_EXECUTING = "executing"
AUTOMATION_STATUS_DRY_RUN_COMPLETE = "dry_run_complete"
AUTOMATION_STATUS_EXECUTED = "executed"
AUTOMATION_STATUS_FAILED = "failed"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_iso(value: datetime | None = None) -> str:
    current = value or utc_now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc).isoformat()


def parse_iso(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = f"{raw[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def normalize_cooldown_seconds(
    value: Any,
    *,
    default_seconds: int,
    min_seconds: int = 30,
    max_seconds: int = 86_400,
) -> int:
    try:
        cooldown = int(value)
    except (TypeError, ValueError):
        cooldown = int(default_seconds)
    cooldown = max(min_seconds, cooldown)
    cooldown = min(max_seconds, cooldown)
    return cooldown


def cooldown_remaining_seconds(
    *,
    last_run_at: Any,
    now: datetime,
    cooldown_seconds: int,
) -> int:
    last = parse_iso(last_run_at)
    if last is None:
        return 0
    elapsed = (now.astimezone(timezone.utc) - last).total_seconds()
    remaining = int(cooldown_seconds - elapsed)
    return remaining if remaining > 0 else 0


def append_bounded(rows: list[JsonObject], entry: JsonObject, *, limit: int = 60) -> list[JsonObject]:
    next_rows = [entry, *rows]
    return next_rows[: max(1, min(limit, 300))]


def ensure_automation_state(raw_state: Any, *, now: datetime | None = None) -> JsonObject:
    current = now or utc_now()
    base: JsonObject
    if isinstance(raw_state, dict):
        base = dict(raw_state)
    else:
        base = {}

    if not isinstance(base.get("loop"), dict):
        legacy = dict(base) if base else None
        base = {"legacy_state": legacy} if legacy else {}
    loop = dict(base.get("loop", {}))
    daily = dict(loop.get("daily_briefing", {})) if isinstance(loop.get("daily_briefing"), dict) else {}
    arrival = dict(loop.get("arrival", {})) if isinstance(loop.get("arrival"), dict) else {}
    loop["daily_briefing"] = {
        "last_run_by_schedule": dict(daily.get("last_run_by_schedule", {}))
        if isinstance(daily.get("last_run_by_schedule"), dict)
        else {},
        "recent_status": list(daily.get("recent_status", [])) if isinstance(daily.get("recent_status"), list) else [],
    }
    loop["arrival"] = {
        "last_trigger_at": arrival.get("last_trigger_at"),
        "last_live_run_at": arrival.get("last_live_run_at"),
        "last_presence_state": arrival.get("last_presence_state"),
        "recent_status": list(arrival.get("recent_status", [])) if isinstance(arrival.get("recent_status"), list) else [],
    }
    loop["recent_runs"] = list(loop.get("recent_runs", [])) if isinstance(loop.get("recent_runs"), list) else []
    loop["recent_traces"] = list(loop.get("recent_traces", [])) if isinstance(loop.get("recent_traces"), list) else []
    base["loop"] = loop
    base["version"] = AUTOMATION_STATE_VERSION
    base["updated_at"] = to_iso(current)
    return base


def new_trace_id(prefix: str = "auto") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def build_trace_entry(
    *,
    trace_id: str,
    action_name: str,
    success: bool,
    message: str,
    risk: str | None = "R2",
    policy_decision: str | None = None,
    now: datetime | None = None,
    metadata: JsonObject | None = None,
) -> JsonObject:
    stamp = now or utc_now()
    payload: JsonObject = {
        "traceId": trace_id,
        "actionName": action_name,
        "timestamp": int(stamp.timestamp() * 1000),
        "risk": risk,
        "policyDecision": policy_decision,
        "provider": None,
        "fallbackUsed": False,
        "success": bool(success),
        "message": message,
    }
    if metadata:
        payload["metadata"] = metadata
    return payload


def build_evidence(
    *,
    automation_type: str,
    source: str,
    dry_run: bool,
    success: bool,
    detail: JsonObject | None = None,
    now: datetime | None = None,
) -> JsonObject:
    payload: JsonObject = {
        "kind": "automation_execution",
        "automation_type": automation_type,
        "source": source,
        "dry_run": dry_run,
        "success": success,
        "executed_at": to_iso(now),
    }
    if detail:
        payload["detail"] = detail
    return payload
