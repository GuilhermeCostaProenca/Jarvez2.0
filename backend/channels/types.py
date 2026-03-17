from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class ChannelIdentity:
    channel: str
    participant_identity: str
    room: str | None = None
    address: str | None = None
    session_id: str | None = None


@dataclass(slots=True)
class InboundEnvelope:
    identity: ChannelIdentity
    text: str
    topic: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)
    received_at: str = field(default_factory=_now_iso)


@dataclass(slots=True)
class OutboundEnvelope:
    identity: ChannelIdentity
    text: str
    topic: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)
    sent_at: str = field(default_factory=_now_iso)


@dataclass(slots=True)
class ExecutionAuditRecord:
    channel: str
    participant_identity: str
    room: str | None
    success: bool
    action_name: str | None = None
    trace_id: str | None = None
    direction: str = "action"
    event_type: str | None = None
    detail: str | None = None
    recorded_at: str = field(default_factory=_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)
