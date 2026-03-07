from __future__ import annotations

from channels.router import build_livekit_envelope


def normalize_livekit_text(*, participant_identity: str, room: str, text: str):
    return build_livekit_envelope(
        participant_identity=participant_identity,
        room=room,
        text=text,
    )
