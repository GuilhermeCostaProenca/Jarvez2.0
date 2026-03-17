from __future__ import annotations

import json
from typing import Any

from channels.types import ChannelIdentity, InboundEnvelope, OutboundEnvelope


LIVEKIT_CHANNEL = "livekit"
DEFAULT_EVENTS_TOPIC = "lk.agent.events"


def build_livekit_identity(*, participant_identity: str, room: str) -> ChannelIdentity:
    return ChannelIdentity(
        channel=LIVEKIT_CHANNEL,
        participant_identity=participant_identity,
        room=room,
    )


def build_livekit_envelope(*, participant_identity: str, room: str, text: str) -> InboundEnvelope:
    return build_livekit_inbound_envelope(
        participant_identity=participant_identity,
        room=room,
        text=text,
    )


def build_livekit_inbound_envelope(
    *,
    participant_identity: str,
    room: str,
    text: str,
    topic: str | None = None,
    raw_payload: dict[str, Any] | None = None,
) -> InboundEnvelope:
    return InboundEnvelope(
        identity=build_livekit_identity(participant_identity=participant_identity, room=room),
        text=text,
        topic=topic,
        raw_payload=raw_payload or {},
    )


def build_livekit_outbound_envelope(
    *,
    participant_identity: str,
    room: str,
    payload: dict[str, Any],
    topic: str = DEFAULT_EVENTS_TOPIC,
) -> OutboundEnvelope:
    return OutboundEnvelope(
        identity=build_livekit_identity(participant_identity=participant_identity, room=room),
        text=json.dumps(payload, ensure_ascii=False),
        topic=topic,
        raw_payload={"topic": topic, "payload": payload},
    )
