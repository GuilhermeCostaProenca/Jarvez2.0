from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import os
from typing import Any
from zoneinfo import ZoneInfo

from .rules import cooldown_remaining_seconds, normalize_cooldown_seconds, parse_iso, to_iso

JsonObject = dict[str, Any]


def _default_timezone_name() -> str:
    raw = os.getenv("JARVEZ_AUTOMATION_TIMEZONE", "UTC").strip()
    return raw or "UTC"


def _safe_timezone(name: str | None) -> ZoneInfo:
    try:
        return ZoneInfo((name or "").strip() or _default_timezone_name())
    except Exception:
        return ZoneInfo("UTC")


def _parse_time_of_day(value: Any) -> tuple[int, int] | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    parts = text.split(":")
    if len(parts) != 2:
        return None
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError:
        return None
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return None
    return hour, minute


def _schedule_due_at(now: datetime, *, hour: int, minute: int, tz: ZoneInfo) -> datetime:
    local_now = now.astimezone(tz)
    return local_now.replace(hour=hour, minute=minute, second=0, microsecond=0).astimezone(timezone.utc)


@dataclass(slots=True)
class SchedulerTickResult:
    due_runs: list[JsonObject]
    status_rows: list[JsonObject]
    next_due_at: str | None


def collect_daily_briefing_runs(
    *,
    schedules: Any,
    last_run_by_schedule: dict[str, Any] | None,
    now: datetime | None = None,
    default_cooldown_seconds: int = 3_600,
    default_timezone: str | None = None,
) -> SchedulerTickResult:
    utc_now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    rows = [row for row in schedules] if isinstance(schedules, list) else []
    last_runs = dict(last_run_by_schedule or {})
    due_runs: list[JsonObject] = []
    status_rows: list[JsonObject] = []
    next_due: datetime | None = None
    default_tz = default_timezone or _default_timezone_name()

    for row in rows:
        if not isinstance(row, dict):
            continue
        schedule_id = str(row.get("id") or "").strip()
        query = str(row.get("query") or "").strip()
        time_of_day = _parse_time_of_day(row.get("time_of_day"))
        enabled = bool(row.get("enabled", True))
        timezone_name = str(row.get("timezone") or default_tz).strip() or default_tz
        timezone_info = _safe_timezone(timezone_name)
        schedule_status: JsonObject = {
            "id": schedule_id or None,
            "automation_type": "daily_briefing",
            "query": query,
            "enabled": enabled,
            "timezone": timezone_name,
            "time_of_day": row.get("time_of_day"),
        }

        if not schedule_id:
            schedule_status["status"] = "skipped"
            schedule_status["reason"] = "missing_schedule_id"
            status_rows.append(schedule_status)
            continue
        if not query:
            schedule_status["status"] = "skipped"
            schedule_status["reason"] = "missing_query"
            status_rows.append(schedule_status)
            continue
        if not enabled:
            schedule_status["status"] = "disabled"
            schedule_status["reason"] = "schedule_disabled"
            status_rows.append(schedule_status)
            continue
        if time_of_day is None:
            schedule_status["status"] = "skipped"
            schedule_status["reason"] = "invalid_time_of_day"
            status_rows.append(schedule_status)
            continue

        hour, minute = time_of_day
        due_at = _schedule_due_at(utc_now, hour=hour, minute=minute, tz=timezone_info)
        local_now = utc_now.astimezone(timezone_info)
        last_run_at = parse_iso(last_runs.get(schedule_id))
        cooldown_seconds = normalize_cooldown_seconds(
            row.get("cooldown_seconds", int(row.get("cooldown_minutes", 0) or 0) * 60),
            default_seconds=default_cooldown_seconds,
        )
        cooldown_remaining = cooldown_remaining_seconds(
            last_run_at=last_run_at.isoformat() if last_run_at else None,
            now=utc_now,
            cooldown_seconds=cooldown_seconds,
        )

        already_ran_today = False
        if last_run_at is not None:
            last_local = last_run_at.astimezone(timezone_info)
            already_ran_today = (
                last_local.date() == local_now.date()
                and last_local.time() >= due_at.astimezone(timezone_info).time()
            )

        if due_at > utc_now:
            next_candidate = due_at
            schedule_status["status"] = "pending"
            schedule_status["reason"] = "not_due_yet"
        elif cooldown_remaining > 0:
            next_candidate = utc_now + timedelta(seconds=cooldown_remaining)
            schedule_status["status"] = "cooldown"
            schedule_status["reason"] = "cooldown_active"
            schedule_status["cooldown_remaining_seconds"] = cooldown_remaining
        elif already_ran_today:
            next_candidate = due_at + timedelta(days=1)
            schedule_status["status"] = "already_ran"
            schedule_status["reason"] = "already_executed_today"
        else:
            next_candidate = due_at + timedelta(days=1)
            dry_run = bool(row.get("dry_run", False))
            due_runs.append(
                {
                    "automation_type": "daily_briefing",
                    "source": "scheduler",
                    "schedule_id": schedule_id,
                    "query": query,
                    "dry_run": dry_run,
                    "time_of_day": f"{hour:02d}:{minute:02d}",
                    "timezone": timezone_name,
                    "cooldown_seconds": cooldown_seconds,
                    "due_at": to_iso(due_at),
                }
            )
            schedule_status["status"] = "due"
            schedule_status["reason"] = "due_now"

        if next_due is None or next_candidate < next_due:
            next_due = next_candidate
        schedule_status["next_due_at"] = to_iso(next_candidate)
        if last_run_at is not None:
            schedule_status["last_run_at"] = to_iso(last_run_at)
        status_rows.append(schedule_status)

    return SchedulerTickResult(
        due_runs=due_runs,
        status_rows=status_rows,
        next_due_at=to_iso(next_due) if next_due is not None else None,
    )


class AutomationScheduler:
    def __init__(self, *, interval_seconds: int = 30):
        self.interval_seconds = max(5, min(int(interval_seconds), 3_600))
        self.last_tick_at: str | None = None
        self.next_tick_at: str | None = None

    def record_tick(self, *, now: datetime | None = None) -> JsonObject:
        current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        self.last_tick_at = to_iso(current)
        self.next_tick_at = to_iso(current + timedelta(seconds=self.interval_seconds))
        return {
            "interval_seconds": self.interval_seconds,
            "last_tick_at": self.last_tick_at,
            "next_tick_at": self.next_tick_at,
        }
