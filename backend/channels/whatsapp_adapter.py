from __future__ import annotations

from typing import Any

from channels.types import ChannelIdentity, InboundEnvelope


DEFAULT_WHATSAPP_ROOM = "whatsapp_legacy_v1"


def _extract_message_text(message: dict[str, Any]) -> str:
    text_obj = message.get("text")
    if isinstance(text_obj, dict):
        body = str(text_obj.get("body") or "").strip()
        if body:
            return body
    if isinstance(text_obj, str):
        body = text_obj.strip()
        if body:
            return body
    for key in ("body", "caption"):
        value = str(message.get(key) or "").strip()
        if value:
            return value
    interactive = message.get("interactive")
    if isinstance(interactive, dict):
        for nested_key in ("button_reply", "list_reply"):
            nested_value = interactive.get(nested_key)
            if isinstance(nested_value, dict):
                for text_key in ("title", "id", "description"):
                    text = str(nested_value.get(text_key) or "").strip()
                    if text:
                        return text
    return ""


def normalize_inbound_webhook_message(
    message: dict[str, Any],
    *,
    profile_name: str | None = None,
    default_room: str = DEFAULT_WHATSAPP_ROOM,
) -> InboundEnvelope:
    sender = str(message.get("from") or message.get("sender") or message.get("wa_id") or "").strip()
    text = _extract_message_text(message)
    room = str(message.get("source") or "").strip() or default_room
    identity = ChannelIdentity(
        channel="whatsapp",
        participant_identity=sender or "unknown",
        room=room,
        address=sender or None,
    )
    payload: dict[str, Any] = dict(message)
    resolved_profile_name = profile_name or str(message.get("profile_name") or "").strip()
    if resolved_profile_name:
        payload["profile_name"] = resolved_profile_name
    received_at = str(message.get("received_at") or "").strip()
    if received_at:
        return InboundEnvelope(
            identity=identity,
            text=text,
            raw_payload=payload,
            received_at=received_at,
        )
    return InboundEnvelope(identity=identity, text=text, raw_payload=payload)


def normalize_bridge_payload(
    payload: dict[str, Any],
    *,
    default_room: str = DEFAULT_WHATSAPP_ROOM,
) -> list[InboundEnvelope]:
    messages = payload.get("messages")
    if not isinstance(messages, list):
        return []
    normalized: list[InboundEnvelope] = []
    for item in messages:
        if not isinstance(item, dict):
            continue
        normalized.append(
            normalize_inbound_webhook_message(
                item,
                default_room=default_room,
            )
        )
    return normalized
