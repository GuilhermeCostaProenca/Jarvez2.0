from __future__ import annotations

from datetime import datetime, timezone
import os
from typing import Any

from .rules import cooldown_remaining_seconds, normalize_cooldown_seconds, parse_iso, to_iso

JsonObject = dict[str, Any]

HOME_STATES = {"home", "on", "present", "arriving"}


def _presence_entity_default() -> str | None:
    raw = os.getenv("JARVEZ_PRESENCE_ENTITY_ID", "").strip()
    return raw or None


def _normalize_state(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _extract_presence_event(params: JsonObject, *, default_entity_id: str | None) -> JsonObject | None:
    event = params.get("presence_event")
    if isinstance(event, dict):
        entity_id = str(event.get("entity_id") or default_entity_id or "").strip()
        if not entity_id:
            return None
        return {
            "entity_id": entity_id,
            "old_state": _normalize_state(event.get("old_state")),
            "new_state": _normalize_state(event.get("new_state")),
            "source": str(event.get("source") or "home_assistant_event"),
            "changed_at": event.get("changed_at"),
        }

    if "presence_state" not in params:
        return None
    entity_id = str(params.get("presence_entity_id") or default_entity_id or "").strip()
    if not entity_id:
        return None
    return {
        "entity_id": entity_id,
        "old_state": _normalize_state(params.get("presence_old_state")),
        "new_state": _normalize_state(params.get("presence_state")),
        "source": str(params.get("presence_source") or "presence_poll"),
        "changed_at": params.get("presence_changed_at"),
    }


def evaluate_arrival_presence_trigger(
    *,
    params: JsonObject,
    arrival_prefs: Any,
    arrival_state: JsonObject | None,
    now: datetime | None = None,
    default_cooldown_seconds: int = 2_700,
) -> tuple[JsonObject | None, JsonObject]:
    utc_now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    prefs = dict(arrival_prefs) if isinstance(arrival_prefs, dict) else {}
    state = dict(arrival_state) if isinstance(arrival_state, dict) else {}

    configured_entity_id = str(prefs.get("presence_entity_id") or _presence_entity_default() or "").strip()
    automation_enabled = bool(prefs.get("automation_enabled", bool(configured_entity_id)))
    status: JsonObject = {
        "automation_type": "arrival_prepare",
        "enabled": automation_enabled,
        "presence_entity_id": configured_entity_id or None,
    }
    if not automation_enabled:
        status["status"] = "disabled"
        status["reason"] = "presence_automation_disabled"
        return None, status
    if not configured_entity_id:
        status["status"] = "disabled"
        status["reason"] = "presence_entity_missing"
        return None, status

    event = _extract_presence_event(params, default_entity_id=configured_entity_id)
    if event is None:
        status["status"] = "idle"
        status["reason"] = "presence_event_missing"
        return None, status

    event_entity = str(event.get("entity_id") or "").strip()
    old_state = _normalize_state(event.get("old_state"))
    new_state = _normalize_state(event.get("new_state"))
    if event_entity.lower() != configured_entity_id.lower():
        status["status"] = "ignored"
        status["reason"] = "presence_entity_mismatch"
        status["event_entity_id"] = event_entity
        return None, status

    transitioned_home = new_state in HOME_STATES and old_state not in HOME_STATES
    status["old_state"] = old_state or None
    status["new_state"] = new_state or None
    status["event_source"] = event.get("source")
    if not transitioned_home:
        status["status"] = "idle"
        status["reason"] = "no_arrival_transition"
        return None, status

    cooldown_seconds = normalize_cooldown_seconds(
        prefs.get("cooldown_seconds", int(prefs.get("cooldown_minutes", 0) or 0) * 60),
        default_seconds=default_cooldown_seconds,
    )
    last_trigger_at = state.get("last_trigger_at")
    cooldown_remaining = cooldown_remaining_seconds(
        last_run_at=last_trigger_at,
        now=utc_now,
        cooldown_seconds=cooldown_seconds,
    )
    if cooldown_remaining > 0:
        status["status"] = "cooldown"
        status["reason"] = "arrival_trigger_cooldown"
        status["cooldown_remaining_seconds"] = cooldown_remaining
        status["last_trigger_at"] = last_trigger_at
        return None, status

    dry_run = bool(params.get("automation_dry_run", params.get("dry_run", True)))
    trigger: JsonObject = {
        "automation_type": "arrival_prepare",
        "source": "presence_trigger",
        "presence_entity_id": configured_entity_id,
        "presence_transition": {"from": old_state or None, "to": new_state or None},
        "triggered_at": to_iso(utc_now),
        "dry_run": dry_run,
        "cooldown_seconds": cooldown_seconds,
        "run_live_after_dry_run": bool(prefs.get("run_live_after_dry_run", True)),
    }
    status["status"] = "triggered"
    status["reason"] = "arrival_detected"
    status["triggered_at"] = trigger["triggered_at"]
    return trigger, status
