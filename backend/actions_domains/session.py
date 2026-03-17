from __future__ import annotations

import secrets
from collections.abc import Awaitable, Callable, Mapping, MutableMapping
from typing import Any

from actions_core import ActionContext, ActionResult

JsonObject = dict[str, Any]


async def confirm_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    peek_confirmation: Callable[[str], Any],
    pop_confirmation: Callable[[str], Any],
    extract_last_user_text: Callable[[Any | None], str],
    is_explicit_confirmation: Callable[[str], bool],
    remaining_seconds: Callable[[Any], int],
    dispatch_action: Callable[[str, JsonObject, ActionContext], Awaitable[ActionResult]],
) -> ActionResult:
    token = str(params.get("confirmation_token", "")).strip()
    if not token:
        return ActionResult(success=False, message="Token de confirmacao ausente.", error="missing token")

    pending = peek_confirmation(token)
    if pending is None:
        return ActionResult(success=False, message="Token de confirmacao invalido ou expirado.", error="invalid token")

    if pending.participant_identity != ctx.participant_identity:
        return ActionResult(success=False, message="Token pertence a outro participante.", error="identity mismatch")

    if pending.room != ctx.room:
        return ActionResult(success=False, message="Token pertence a outra sala.", error="room mismatch")

    last_user_text = extract_last_user_text(ctx.session)
    if not is_explicit_confirmation(last_user_text):
        return ActionResult(
            success=False,
            message="Preciso de confirmacao explicita. Diga claramente 'sim, confirmo' para executar.",
            data={
                "confirmation_required": True,
                "confirmation_token": pending.token,
                "expires_in": remaining_seconds(pending.expires_at),
                "action_name": pending.action_name,
                "params": pending.params,
            },
        )

    pop_confirmation(token)
    return await dispatch_action(pending.action_name, pending.params, ctx)


async def authenticate_identity(
    params: JsonObject,
    ctx: ActionContext,
    *,
    security_pin: Callable[[], str],
    security_passphrase: Callable[[], str],
    clear_authentication: Callable[[str], None],
    security_status_payload: Callable[[str, str], JsonObject],
    set_authenticated: Callable[[str, str, str], None],
    voice_step_up_pending: MutableMapping[str, float],
) -> ActionResult:
    pin = str(params.get("pin", "")).strip()
    passphrase = str(params.get("passphrase", "")).strip()
    if not passphrase:
        passphrase = str(params.get("security_phrase", "")).strip()

    expected_pin = security_pin()
    expected_passphrase = security_passphrase()
    if not expected_pin and not expected_passphrase:
        return ActionResult(
            success=False,
            message="Credenciais de seguranca nao configuradas no servidor.",
            error="missing JARVEZ_SECURITY_PIN and JARVEZ_SECURITY_PASSPHRASE",
        )

    pin_configured = bool(expected_pin)
    passphrase_configured = bool(expected_passphrase)
    pin_valid = pin_configured and bool(pin) and secrets.compare_digest(pin, expected_pin)
    normalized_passphrase = passphrase.casefold()
    normalized_expected_passphrase = expected_passphrase.casefold()
    passphrase_valid = passphrase_configured and bool(passphrase) and secrets.compare_digest(
        normalized_passphrase, normalized_expected_passphrase
    )
    authenticated = pin_valid or passphrase_valid

    if not authenticated:
        clear_authentication(ctx.participant_identity)
        return ActionResult(
            success=False,
            message="Falha na autenticacao. Informe PIN ou frase de seguranca validos.",
            data={"authentication_required": True, **security_status_payload(ctx.participant_identity, ctx.room)},
            error="invalid credentials",
        )

    step_up_pending = ctx.participant_identity in voice_step_up_pending
    auth_method = "pin" if pin_valid else "passphrase"
    if step_up_pending:
        auth_method = "voice+pin"
    elif pin_valid and passphrase_valid:
        auth_method = "voice+pin"

    set_authenticated(ctx.participant_identity, ctx.room, auth_method)
    return ActionResult(
        success=True,
        message="Sessao autenticada. Modo privado liberado.",
        data={"auth_method": auth_method, "private_access_granted": True, **security_status_payload(ctx.participant_identity, ctx.room)},
    )


async def lock_private_mode(
    params: JsonObject,
    ctx: ActionContext,
    *,
    clear_authentication: Callable[[str], None],
    security_status_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    _ = params
    clear_authentication(ctx.participant_identity)
    return ActionResult(
        success=True,
        message="Modo privado bloqueado.",
        data=security_status_payload(ctx.participant_identity, ctx.room),
    )


async def get_security_status(
    params: JsonObject,
    ctx: ActionContext,
    *,
    security_status_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    _ = params
    status = security_status_payload(ctx.participant_identity, ctx.room)
    if status["security_status"]["authenticated"]:
        message = "Sessao autenticada."
    else:
        message = "Sessao nao autenticada."
    return ActionResult(success=True, message=message, data=status)


async def list_persona_modes(
    params: JsonObject,
    ctx: ActionContext,
    *,
    get_persona_mode: Callable[[str, str], str],
    persona_modes: Mapping[str, JsonObject],
    persona_payload: Callable[[str], JsonObject],
) -> ActionResult:
    _ = params
    current_mode = get_persona_mode(ctx.participant_identity, ctx.room)
    return ActionResult(
        success=True,
        message="Modos de personalidade disponiveis listados.",
        data={
            "available_persona_modes": dict(persona_modes),
            "current_persona_mode": current_mode,
            **persona_payload(current_mode),
        },
    )


async def get_persona_mode_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    get_persona_mode: Callable[[str, str], str],
    persona_modes: Mapping[str, JsonObject],
    default_persona_mode: str,
    persona_payload: Callable[[str], JsonObject],
) -> ActionResult:
    _ = params
    current_mode = get_persona_mode(ctx.participant_identity, ctx.room)
    profile = persona_modes.get(current_mode, persona_modes[default_persona_mode])
    return ActionResult(
        success=True,
        message=f"Modo atual: {profile.get('label', current_mode)}.",
        data={"current_persona_mode": current_mode, **persona_payload(current_mode)},
    )


async def set_persona_mode_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    normalize_persona_mode: Callable[[str], str],
    persona_modes: Mapping[str, JsonObject],
    set_persona_mode: Callable[[str, str, str], str],
    persona_payload: Callable[[str], JsonObject],
    on_mode_applied: Callable[[str], None] | None = None,
) -> ActionResult:
    requested_mode = str(params.get("mode", "")).strip()
    normalized = normalize_persona_mode(requested_mode)
    if normalized not in persona_modes:
        available = ", ".join(sorted(persona_modes.keys()))
        return ActionResult(
            success=False,
            message=f"Modo '{requested_mode}' nao existe. Use um destes: {available}.",
            data={"available_modes": sorted(persona_modes.keys())},
            error="invalid persona mode",
        )

    applied = set_persona_mode(ctx.participant_identity, ctx.room, normalized)
    if on_mode_applied is not None:
        on_mode_applied(applied)
    profile = persona_modes.get(applied, {})
    return ActionResult(
        success=True,
        message=f"Modo de personalidade alterado para {profile.get('label', applied)}.",
        data={
            "applied_persona_mode": applied,
            "style_guidance": profile.get("style"),
            **persona_payload(applied),
        },
    )


async def set_memory_scope(
    params: JsonObject,
    ctx: ActionContext,
    *,
    set_memory_scope_override: Callable[[str, str, str], None],
) -> ActionResult:
    scope = str(params.get("scope", "")).strip().lower()
    if scope not in {"public", "private"}:
        return ActionResult(success=False, message="Escopo invalido. Use public ou private.", error="invalid scope")
    set_memory_scope_override(ctx.participant_identity, ctx.room, scope)
    return ActionResult(success=True, message=f"Ok, vou tratar o proximo contexto como {scope}.", data={"memory_scope": scope})


async def verify_voice_identity(
    params: JsonObject,
    ctx: ActionContext,
    *,
    voice_profile_store: Any | None,
    get_recent_voice_embedding: Callable[[str], Any | None],
    voice_threshold: Callable[[], float],
    voice_stepup_threshold: Callable[[], float],
    set_authenticated: Callable[[str, str, str], None],
    clear_authentication: Callable[[str], None],
    security_status_payload: Callable[[str, str], JsonObject],
    voice_step_up_pending: MutableMapping[str, float],
) -> ActionResult:
    _ = params
    if voice_profile_store is None:
        return ActionResult(success=False, message="Biometria de voz desativada.", error="voice biometrics disabled")

    embedding = get_recent_voice_embedding(ctx.participant_identity)
    if embedding is None:
        return ActionResult(
            success=False,
            message="Nao detectei audio suficiente para verificar sua voz. Fale por alguns segundos e repita.",
            error="insufficient voice sample",
            data={"step_up_required": True},
        )

    verify = voice_profile_store.verify_identity(participant_identity=ctx.participant_identity, embedding=embedding)
    threshold = voice_threshold()
    stepup_limit = max(threshold, voice_stepup_threshold())

    if verify.score >= stepup_limit:
        set_authenticated(ctx.participant_identity, ctx.room, "voice")
        return ActionResult(
            success=True,
            message="Identidade por voz validada com alta confianca.",
            data={
                "auth_method": "voice",
                "voice_score": verify.score,
                "private_access_granted": True,
                "step_up_required": False,
                "matched_profile": verify.profile_name,
                "voice_method": verify.method,
                "compared_profiles": verify.compared_profiles,
                **security_status_payload(ctx.participant_identity, ctx.room),
            },
        )

    if verify.score >= threshold:
        voice_step_up_pending[ctx.participant_identity] = verify.score
        clear_authentication(ctx.participant_identity)
        return ActionResult(
            success=False,
            message="Voz reconhecida com confianca media. Confirme com PIN/frase para liberar acesso privado.",
            data={
                "authentication_required": True,
                "step_up_required": True,
                "voice_score": verify.score,
                "matched_profile": verify.profile_name,
                "voice_method": verify.method,
                "compared_profiles": verify.compared_profiles,
                **security_status_payload(ctx.participant_identity, ctx.room),
            },
            error="voice_step_up_required",
        )

    clear_authentication(ctx.participant_identity)
    return ActionResult(
        success=False,
        message="Nao consegui validar sua identidade por voz.",
        data={
            "voice_score": verify.score,
            "step_up_required": True,
            "voice_method": verify.method,
            "compared_profiles": verify.compared_profiles,
        },
        error="voice_not_matched",
    )
