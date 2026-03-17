from __future__ import annotations

import json
from typing import Any

from channels.router import (
    build_livekit_inbound_envelope,
    build_livekit_outbound_envelope,
    DEFAULT_EVENTS_TOPIC,
)
from channels.types import InboundEnvelope, OutboundEnvelope


def normalize_livekit_text(*, participant_identity: str, room: str, text: str) -> InboundEnvelope:
    return build_livekit_inbound_envelope(
        participant_identity=participant_identity,
        room=room,
        text=text,
    )


def build_livekit_event_envelope(
    *,
    participant_identity: str,
    room: str,
    payload: dict[str, Any],
    topic: str = DEFAULT_EVENTS_TOPIC,
) -> OutboundEnvelope:
    return build_livekit_outbound_envelope(
        participant_identity=participant_identity,
        room=room,
        payload=payload,
        topic=topic,
    )


def normalize_livekit_data_packet(packet: Any, *, room: str) -> InboundEnvelope | None:
    sender = getattr(packet, "participant", None)
    participant_identity = str(getattr(sender, "identity", "") or "").strip()
    if not participant_identity:
        return None
    topic = str(getattr(packet, "topic", "") or "").strip() or None
    data = getattr(packet, "data", None)
    if not isinstance(data, (bytes, bytearray)):
        return None
    text = data.decode("utf-8", errors="replace")
    payload: Any = None
    try:
        payload = json.loads(text)
    except Exception:
        payload = None
    raw_payload: dict[str, Any] = {"packet_type": "livekit.data"}
    if isinstance(payload, dict):
        raw_payload["payload"] = payload
    return build_livekit_inbound_envelope(
        participant_identity=participant_identity,
        room=room,
        text=text,
        topic=topic,
        raw_payload=raw_payload,
    )
