from __future__ import annotations

import logging
from typing import Any

from channels.audit import build_audit_record
from channels.livekit_adapter import build_livekit_event_envelope

logger = logging.getLogger(__name__)


async def publish_session_event(session: Any | None, payload: dict[str, object]) -> None:
    if session is None:
        return
    room_io = getattr(session, "room_io", None)
    room = getattr(room_io, "room", None)
    room_name = str(getattr(room, "name", "") or "").strip() or "room"
    participant = getattr(room, "local_participant", None)
    if participant is None:
        return
    participant_identity = str(getattr(participant, "identity", "") or "").strip() or "agent"
    envelope = build_livekit_event_envelope(
        participant_identity=participant_identity,
        room=room_name,
        payload=payload,
    )
    audit = build_audit_record(
        channel="livekit",
        participant_identity=participant_identity,
        room=room_name,
        action_name=None,
        success=True,
        direction="outbound",
        event_type=str(payload.get("type") or "") or None,
        metadata={"topic": envelope.topic},
    )
    try:
        await participant.publish_data(
            envelope.text,
            topic=envelope.topic or "lk.agent.events",
        )
    except Exception:
        audit.success = False
        audit.detail = "publish_data_failed"
        logger.warning(
            "failed to publish agent event channel=%s participant=%s room=%s event=%s",
            audit.channel,
            audit.participant_identity,
            audit.room,
            audit.event_type or "unknown",
            exc_info=True,
        )
