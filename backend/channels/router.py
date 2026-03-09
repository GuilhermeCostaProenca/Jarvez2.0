from __future__ import annotations

from channels.types import ChannelIdentity, InboundEnvelope


def build_livekit_envelope(*, participant_identity: str, room: str, text: str) -> InboundEnvelope:
    return InboundEnvelope(
        identity=ChannelIdentity(
            channel="livekit",
            participant_identity=participant_identity,
            room=room,
        ),
        text=text,
    )
