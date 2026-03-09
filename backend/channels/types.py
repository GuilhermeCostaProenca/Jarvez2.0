from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ChannelIdentity:
    channel: str
    participant_identity: str
    room: str | None = None
    address: str | None = None


@dataclass(slots=True)
class InboundEnvelope:
    identity: ChannelIdentity
    text: str
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class OutboundEnvelope:
    identity: ChannelIdentity
    text: str
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ExecutionAuditRecord:
    channel: str
    participant_identity: str
    room: str | None
    action_name: str
    success: bool
    trace_id: str | None = None
