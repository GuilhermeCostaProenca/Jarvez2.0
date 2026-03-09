from __future__ import annotations

from channels.types import ExecutionAuditRecord


def build_audit_record(
    *,
    channel: str,
    participant_identity: str,
    room: str | None,
    action_name: str,
    success: bool,
    trace_id: str | None = None,
) -> ExecutionAuditRecord:
    return ExecutionAuditRecord(
        channel=channel,
        participant_identity=participant_identity,
        room=room,
        action_name=action_name,
        success=success,
        trace_id=trace_id,
    )
