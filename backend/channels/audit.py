from __future__ import annotations
from typing import Any

from channels.types import ExecutionAuditRecord


def build_audit_record(
    *,
    channel: str,
    participant_identity: str,
    room: str | None,
    action_name: str | None,
    success: bool,
    trace_id: str | None = None,
    direction: str = "action",
    event_type: str | None = None,
    detail: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> ExecutionAuditRecord:
    return ExecutionAuditRecord(
        channel=channel,
        participant_identity=participant_identity,
        room=room,
        action_name=action_name,
        success=success,
        trace_id=trace_id,
        direction=direction,
        event_type=event_type,
        detail=detail,
        metadata=metadata or {},
    )
