from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Awaitable, Callable

from policy.risk_engine import RiskTier
from providers.provider_router import TaskType


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _key(participant_identity: str, room: str) -> str:
    return f"{participant_identity}:{room}"


@dataclass(slots=True)
class SubagentState:
    subagent_id: str
    participant_identity: str
    room: str
    request: str
    task_type: TaskType
    risk: RiskTier
    status: str
    created_at: str
    updated_at: str
    result_summary: str | None = None
    route_provider: str | None = None
    error: str | None = None
    finished_at: str | None = None

    def to_payload(self) -> dict[str, object]:
        return {
            "subagent_id": self.subagent_id,
            "participant_identity": self.participant_identity,
            "room": self.room,
            "request": self.request,
            "task_type": self.task_type,
            "risk": self.risk,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "result_summary": self.result_summary,
            "route_provider": self.route_provider,
            "error": self.error,
            "finished_at": self.finished_at,
        }


_SUBAGENTS: dict[str, dict[str, SubagentState]] = {}
_SUBAGENT_TASKS: dict[str, asyncio.Task[None]] = {}


def _task_key(*, participant_identity: str, room: str, subagent_id: str) -> str:
    return f"{_key(participant_identity, room)}:{subagent_id}"


def spawn_subagent(
    *,
    participant_identity: str,
    room: str,
    request: str,
    task_type: TaskType,
    risk: RiskTier,
    route_provider: str,
    initial_summary: str | None = None,
) -> SubagentState:
    sid = f"subagent_{uuid.uuid4().hex[:10]}"
    state = SubagentState(
        subagent_id=sid,
        participant_identity=participant_identity,
        room=room,
        request=request,
        task_type=task_type,
        risk=risk,
        status="running",
        created_at=_now_iso(),
        updated_at=_now_iso(),
        result_summary=initial_summary,
        route_provider=route_provider,
    )
    bucket = _SUBAGENTS.setdefault(_key(participant_identity, room), {})
    bucket[sid] = state
    return state


def complete_subagent(
    *,
    participant_identity: str,
    room: str,
    subagent_id: str,
    summary: str,
) -> SubagentState | None:
    item = get_subagent(participant_identity=participant_identity, room=room, subagent_id=subagent_id)
    if item is None:
        return None
    item.status = "completed"
    item.result_summary = summary
    item.updated_at = _now_iso()
    item.finished_at = _now_iso()
    task_key = _task_key(participant_identity=participant_identity, room=room, subagent_id=subagent_id)
    _SUBAGENT_TASKS.pop(task_key, None)
    return item


def cancel_subagent(*, participant_identity: str, room: str, subagent_id: str) -> SubagentState | None:
    item = get_subagent(participant_identity=participant_identity, room=room, subagent_id=subagent_id)
    if item is None:
        return None
    item.status = "cancelled"
    item.updated_at = _now_iso()
    item.finished_at = _now_iso()
    task_key = _task_key(participant_identity=participant_identity, room=room, subagent_id=subagent_id)
    task = _SUBAGENT_TASKS.pop(task_key, None)
    if task is not None and not task.done():
        task.cancel()
    return item


def get_subagent(*, participant_identity: str, room: str, subagent_id: str) -> SubagentState | None:
    return _SUBAGENTS.get(_key(participant_identity, room), {}).get(subagent_id)


def list_subagents(*, participant_identity: str, room: str) -> list[SubagentState]:
    bucket = _SUBAGENTS.get(_key(participant_identity, room), {})
    items = list(bucket.values())
    items.sort(key=lambda item: item.updated_at, reverse=True)
    return items


async def run_subagent_background(
    *,
    participant_identity: str,
    room: str,
    state: SubagentState,
    runner: Callable[[], Awaitable[str]],
) -> None:
    task_key = _task_key(participant_identity=participant_identity, room=room, subagent_id=state.subagent_id)
    try:
        summary = await runner()
    except asyncio.CancelledError:
        state.status = "cancelled"
        state.updated_at = _now_iso()
        state.finished_at = _now_iso()
        _SUBAGENT_TASKS.pop(task_key, None)
        raise
    except Exception as error:  # noqa: BLE001
        state.status = "failed"
        state.error = str(error)
        state.updated_at = _now_iso()
        state.finished_at = _now_iso()
        _SUBAGENT_TASKS.pop(task_key, None)
        return

    state.status = "completed"
    state.result_summary = summary
    state.updated_at = _now_iso()
    state.finished_at = _now_iso()
    _SUBAGENT_TASKS.pop(task_key, None)


def start_subagent_task(
    *,
    participant_identity: str,
    room: str,
    state: SubagentState,
    runner: Callable[[], Awaitable[str]],
) -> None:
    task_key = _task_key(participant_identity=participant_identity, room=room, subagent_id=state.subagent_id)
    task = asyncio.create_task(
        run_subagent_background(
            participant_identity=participant_identity,
            room=room,
            state=state,
            runner=runner,
        )
    )
    _SUBAGENT_TASKS[task_key] = task
