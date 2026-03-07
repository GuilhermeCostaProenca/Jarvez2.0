from __future__ import annotations

from typing import Any

from channels.types import ChannelIdentity, InboundEnvelope


def normalize_inbound_webhook_message(message: dict[str, Any], *, profile_name: str | None = None) -> InboundEnvelope:
    sender = str(message.get("from") or "").strip()
    text_obj = message.get("text")
    text = ""
    if isinstance(text_obj, dict):
        text = str(text_obj.get("body") or "").strip()
    identity = ChannelIdentity(
        channel="whatsapp",
        participant_identity=sender or "unknown",
        address=sender or None,
    )
    payload: dict[str, Any] = dict(message)
    if profile_name:
        payload["profile_name"] = profile_name
    return InboundEnvelope(identity=identity, text=text, raw_payload=payload)
