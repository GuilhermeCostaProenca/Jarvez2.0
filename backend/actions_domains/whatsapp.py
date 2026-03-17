from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from actions_core import ActionContext, ActionResult

JsonObject = dict[str, Any]


async def whatsapp_get_recent_messages(
    params: JsonObject,
    ctx: ActionContext,
    *,
    normalize_whatsapp_to: Callable[[str], str],
    whatsapp_read_inbox: Callable[[], list[JsonObject]],
) -> ActionResult:
    _ = ctx
    contact = normalize_whatsapp_to(str(params.get("contact", "")).strip()) if params.get("contact") else None
    limit = int(params.get("limit", 10))
    entries = whatsapp_read_inbox()
    if contact:
        entries = [item for item in entries if str(item.get("from", "")).strip() == contact]
    entries = sorted(entries, key=lambda item: str(item.get("timestamp", "")), reverse=True)
    sliced = entries[: max(1, min(limit, 50))]
    return ActionResult(
        success=True,
        message=f"{len(sliced)} mensagem(ns) recuperada(s) do WhatsApp.",
        data={"messages": sliced},
    )


async def whatsapp_send_text(
    params: JsonObject,
    ctx: ActionContext,
    *,
    normalize_whatsapp_to: Callable[[str], str],
    whatsapp_send_message: Callable[[JsonObject], ActionResult],
) -> ActionResult:
    _ = ctx
    to = str(params.get("to") or params.get("contact") or "").strip()
    to = normalize_whatsapp_to(to)
    text = str(params.get("text") or params.get("message") or "").strip()
    if not to or not text:
        return ActionResult(success=False, message="Parametros invalidos para WhatsApp.", error="missing to/text")
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    }
    result = whatsapp_send_message(payload)
    if result.success:
        result.message = f"Mensagem enviada para {to}."
    return result


async def whatsapp_send_audio_tts(
    params: JsonObject,
    ctx: ActionContext,
    *,
    normalize_whatsapp_to: Callable[[str], str],
    build_jarvez_tts_file: Callable[[str], Awaitable[tuple[Path | None, ActionResult | None]]],
    upload_whatsapp_media: Callable[[Path, str], tuple[str | None, ActionResult | None]],
    whatsapp_send_message: Callable[[JsonObject], ActionResult],
) -> ActionResult:
    _ = ctx
    to = str(params.get("to") or params.get("contact") or "").strip()
    to = normalize_whatsapp_to(to)
    text = str(params.get("text") or params.get("message") or "").strip()
    if not to or not text:
        return ActionResult(success=False, message="Parametros invalidos para audio WhatsApp.", error="missing to/text")

    audio_file, tts_error = await build_jarvez_tts_file(text)
    if tts_error is not None:
        return tts_error
    if audio_file is None:
        return ActionResult(success=False, message="Falha ao gerar audio do Jarvez.", error="tts generation failed")

    media_id, media_error = upload_whatsapp_media(audio_file, "audio/mpeg")
    try:
        audio_file.unlink(missing_ok=True)
    except Exception:
        pass

    if media_error is not None:
        return media_error
    if not media_id:
        return ActionResult(success=False, message="Nao consegui enviar audio ao WhatsApp.", error="missing media id")

    payload: JsonObject = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "audio",
        "audio": {"id": media_id},
    }
    result = whatsapp_send_message(payload)
    if result.success:
        result.message = f"Audio do Jarvez enviado para {to}."
        if result.data is None:
            result.data = {}
        result.data["media_id"] = media_id
    return result
