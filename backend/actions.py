from __future__ import annotations

import json
import logging
import os
import re
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable

import requests
from voice_biometrics import VoiceProfileStore

logger = logging.getLogger(__name__)

JsonObject = dict[str, Any]
ActionHandler = Callable[[JsonObject, "ActionContext"], Awaitable["ActionResult"]]

SENSITIVE_KEYS = {
    "token",
    "secret",
    "password",
    "authorization",
    "api_key",
    "apikey",
    "key",
}
DEFAULT_ALLOWED_SERVICES = {"light.turn_on", "light.turn_off"}

EXPLICIT_CONFIRMATION_RE = re.compile(
    r"\b(sim|confirmo|pode executar|execute|pode fazer|faca|fa\u00e7a|autorizo|pode)\b",
    re.IGNORECASE,
)
AMBIGUOUS_CONFIRMATION_RE = re.compile(
    r"\b(talvez|acho que sim|nao sei|n\u00e3o sei|depois|quem sabe|mais ou menos)\b",
    re.IGNORECASE,
)


@dataclass(slots=True)
class ActionResult:
    success: bool
    message: str
    data: JsonObject | None = None
    error: str | None = None

    def to_json(self) -> str:
        payload: JsonObject = {
            "success": self.success,
            "message": self.message,
        }
        if self.data is not None:
            payload["data"] = self.data
        if self.error is not None:
            payload["error"] = self.error
        return json.dumps(payload, ensure_ascii=False)


@dataclass(slots=True)
class ActionContext:
    job_id: str
    room: str
    participant_identity: str
    session: Any | None = None
    memory_client: Any | None = None
    user_id: str | None = None


@dataclass(slots=True)
class ActionSpec:
    name: str
    description: str
    params_schema: JsonObject
    requires_confirmation: bool
    handler: ActionHandler
    expose_to_model: bool = True
    requires_auth: bool = False


@dataclass(slots=True)
class PendingConfirmation:
    token: str
    action_name: str
    params: JsonObject
    participant_identity: str
    room: str
    expires_at: datetime


@dataclass(slots=True)
class AuthenticatedSession:
    participant_identity: str
    room: str
    expires_at: datetime
    auth_method: str
    last_activity_at: datetime


ACTION_REGISTRY: dict[str, ActionSpec] = {}
PENDING_CONFIRMATIONS: dict[str, PendingConfirmation] = {}
PARTICIPANT_PENDING_TOKENS: dict[str, str] = {}
AUTHENTICATED_SESSIONS: dict[str, AuthenticatedSession] = {}
VOICE_STEP_UP_PENDING: dict[str, float] = {}
VOICE_PROFILE_STORE = VoiceProfileStore.from_env()
MEMORY_SCOPE_OVERRIDES: dict[str, str] = {}


def register_action(spec: ActionSpec) -> None:
    if spec.name in ACTION_REGISTRY:
        raise ValueError(f"duplicate action name: {spec.name}")
    ACTION_REGISTRY[spec.name] = spec


def get_action(name: str) -> ActionSpec | None:
    return ACTION_REGISTRY.get(name)


def get_exposed_actions() -> list[ActionSpec]:
    return [spec for spec in ACTION_REGISTRY.values() if spec.expose_to_model]


def is_authenticated_session(participant_identity: str, room: str) -> bool:
    return _is_authenticated(participant_identity, room)


def _memory_override_key(participant_identity: str, room: str) -> str:
    return f"{participant_identity}:{room}"


def set_memory_scope_override(participant_identity: str, room: str, scope: str) -> None:
    MEMORY_SCOPE_OVERRIDES[_memory_override_key(participant_identity, room)] = scope


def get_memory_scope_override(participant_identity: str, room: str) -> str | None:
    return MEMORY_SCOPE_OVERRIDES.get(_memory_override_key(participant_identity, room))


def action_spec_to_raw_schema(spec: ActionSpec) -> JsonObject:
    return {
        "name": spec.name,
        "description": spec.description,
        "parameters": spec.params_schema,
    }


def _value_matches_type(value: Any, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    return False


def _validate_against_property(name: str, value: Any, prop_schema: JsonObject) -> str | None:
    expected_type = prop_schema.get("type")
    if expected_type and not _value_matches_type(value, expected_type):
        return f"'{name}' must be of type {expected_type}"

    if isinstance(value, str):
        pattern = prop_schema.get("pattern")
        if pattern and not re.fullmatch(pattern, value):
            return f"'{name}' does not match required format"
        min_length = prop_schema.get("minLength")
        max_length = prop_schema.get("maxLength")
        if min_length is not None and len(value) < min_length:
            return f"'{name}' length must be >= {min_length}"
        if max_length is not None and len(value) > max_length:
            return f"'{name}' length must be <= {max_length}"

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = prop_schema.get("minimum")
        maximum = prop_schema.get("maximum")
        if minimum is not None and value < minimum:
            return f"'{name}' must be >= {minimum}"
        if maximum is not None and value > maximum:
            return f"'{name}' must be <= {maximum}"

    enum_values = prop_schema.get("enum")
    if enum_values is not None and value not in enum_values:
        return f"'{name}' must be one of {enum_values}"

    return None


def validate_params(params: JsonObject, schema: JsonObject) -> tuple[bool, str | None]:
    if not isinstance(params, dict):
        return False, "params must be an object"

    if schema.get("type") != "object":
        return False, "schema must declare type 'object'"

    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        return False, "schema properties must be an object"

    required = schema.get("required", [])
    for required_key in required:
        if required_key not in params:
            return False, f"missing required parameter '{required_key}'"

    allow_additional = bool(schema.get("additionalProperties", False))

    for key, value in params.items():
        prop_schema = properties.get(key)
        if prop_schema is None:
            if not allow_additional:
                return False, f"unexpected parameter '{key}'"
            continue

        if not isinstance(prop_schema, dict):
            return False, f"schema for '{key}' must be an object"

        validation_error = _validate_against_property(key, value, prop_schema)
        if validation_error:
            return False, validation_error

    return True, None


def _redact(value: Any, key: str | None = None) -> Any:
    if key and key.lower() in SENSITIVE_KEYS:
        return "[REDACTED]"

    if isinstance(value, dict):
        return {k: _redact(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(v) for v in value]
    return value


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _confirmation_ttl_seconds() -> int:
    raw = os.getenv("ACTION_CONFIRMATION_TTL_SECONDS", "60").strip()
    if not raw:
        return 60
    try:
        return max(10, int(raw))
    except ValueError:
        return 60


def _security_ttl_seconds() -> int:
    raw = os.getenv("JARVEZ_SECURE_SESSION_TTL_SECONDS", "600").strip()
    if not raw:
        return 600
    try:
        return max(60, int(raw))
    except ValueError:
        return 600


def _security_pin() -> str:
    return os.getenv("JARVEZ_SECURITY_PIN", "").strip()


def _security_passphrase() -> str:
    return os.getenv("JARVEZ_SECURITY_PASSPHRASE", "").strip()


def _secure_idle_lock_seconds() -> int:
    raw = os.getenv("JARVEZ_SECURE_IDLE_LOCK_SECONDS", "300").strip()
    if not raw:
        return 300
    try:
        return max(60, int(raw))
    except ValueError:
        return 300


def _voice_threshold() -> float:
    raw = os.getenv("JARVEZ_VOICE_MATCH_THRESHOLD", "0.78").strip()
    try:
        return max(0.0, min(1.0, float(raw)))
    except ValueError:
        return 0.78


def _voice_stepup_threshold() -> float:
    raw = os.getenv("JARVEZ_VOICE_REQUIRE_STEPUP_BELOW", "0.85").strip()
    try:
        return max(0.0, min(1.0, float(raw)))
    except ValueError:
        return 0.85


def _clear_authentication(identity: str) -> None:
    AUTHENTICATED_SESSIONS.pop(identity, None)
    VOICE_STEP_UP_PENDING.pop(identity, None)


def _set_authenticated(identity: str, room: str, auth_method: str) -> None:
    now = datetime.now(timezone.utc)
    AUTHENTICATED_SESSIONS[identity] = AuthenticatedSession(
        participant_identity=identity,
        room=room,
        expires_at=now + timedelta(seconds=_security_ttl_seconds()),
        auth_method=auth_method,
        last_activity_at=now,
    )
    VOICE_STEP_UP_PENDING.pop(identity, None)


def _touch_authenticated(identity: str) -> None:
    session = AUTHENTICATED_SESSIONS.get(identity)
    if session is None:
        return
    session.last_activity_at = datetime.now(timezone.utc)


def _is_authenticated(identity: str, room: str) -> bool:
    session = AUTHENTICATED_SESSIONS.get(identity)
    if session is None:
        return False
    if session.room != room:
        _clear_authentication(identity)
        return False
    if session.expires_at <= datetime.now(timezone.utc):
        _clear_authentication(identity)
        return False
    idle_limit = timedelta(seconds=_secure_idle_lock_seconds())
    if datetime.now(timezone.utc) - session.last_activity_at > idle_limit:
        _clear_authentication(identity)
        return False
    return True


def _security_status_payload(identity: str, room: str) -> JsonObject:
    authenticated = _is_authenticated(identity, room)
    session = AUTHENTICATED_SESSIONS.get(identity)
    expires_in = _remaining_seconds(session.expires_at) if session else 0
    auth_method = session.auth_method if session else None
    step_up_required = identity in VOICE_STEP_UP_PENDING
    return {
        "security_status": {
            "authenticated": authenticated,
            "identity_bound": bool(identity),
            "expires_in": expires_in,
            "auth_method": auth_method,
            "step_up_required": step_up_required,
        }
    }


def _cleanup_expired_confirmations() -> None:
    now = datetime.now(timezone.utc)
    expired_tokens = [token for token, pending in PENDING_CONFIRMATIONS.items() if pending.expires_at <= now]
    for token in expired_tokens:
        pending = PENDING_CONFIRMATIONS.pop(token, None)
        if pending:
            PARTICIPANT_PENDING_TOKENS.pop(pending.participant_identity, None)


def _remaining_seconds(expires_at: datetime) -> int:
    now = datetime.now(timezone.utc)
    return max(0, int((expires_at - now).total_seconds()))


def _store_confirmation(action_name: str, params: JsonObject, ctx: ActionContext) -> PendingConfirmation:
    _cleanup_expired_confirmations()

    previous_token = PARTICIPANT_PENDING_TOKENS.get(ctx.participant_identity)
    if previous_token:
        PENDING_CONFIRMATIONS.pop(previous_token, None)

    token = secrets.token_urlsafe(18)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=_confirmation_ttl_seconds())
    pending = PendingConfirmation(
        token=token,
        action_name=action_name,
        params=params,
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        expires_at=expires_at,
    )
    PENDING_CONFIRMATIONS[token] = pending
    PARTICIPANT_PENDING_TOKENS[ctx.participant_identity] = token
    return pending


def _pop_confirmation(token: str) -> PendingConfirmation | None:
    pending = PENDING_CONFIRMATIONS.pop(token, None)
    if pending:
        PARTICIPANT_PENDING_TOKENS.pop(pending.participant_identity, None)
    return pending


def _peek_confirmation(token: str) -> PendingConfirmation | None:
    _cleanup_expired_confirmations()
    return PENDING_CONFIRMATIONS.get(token)


def _extract_last_user_text(session: Any | None) -> str:
    if session is None:
        return ""

    history = getattr(session, "history", None)
    items = getattr(history, "items", None)
    if not isinstance(items, list):
        return ""

    for item in reversed(items):
        role = getattr(item, "role", None)
        if role != "user":
            continue

        content = getattr(item, "content", None)
        if isinstance(content, list):
            return " ".join(part for part in content if isinstance(part, str)).strip()
        if isinstance(content, str):
            return content.strip()

    return ""


def _is_explicit_confirmation(text: str) -> bool:
    if not text:
        return False
    if AMBIGUOUS_CONFIRMATION_RE.search(text):
        return False
    return EXPLICIT_CONFIRMATION_RE.search(text) is not None


def _get_allowed_services() -> set[str]:
    raw_value = os.getenv("HOME_ASSISTANT_ALLOWED_SERVICES", "").strip()
    if not raw_value:
        return DEFAULT_ALLOWED_SERVICES.copy()

    parsed = {item.strip().lower() for item in raw_value.split(",") if item.strip()}
    return parsed or DEFAULT_ALLOWED_SERVICES.copy()


def _service_key(domain: str, service: str) -> str:
    return f"{domain.strip().lower()}.{service.strip().lower()}"


def _is_allowed_service(domain: str, service: str) -> bool:
    return _service_key(domain, service) in _get_allowed_services()


def _build_ha_url(base_url: str, domain: str, service: str) -> str:
    return f"{base_url.rstrip('/')}/api/services/{domain}/{service}"


def _parse_retry_count() -> int:
    raw = os.getenv("HOME_ASSISTANT_RETRY_COUNT", "2").strip()
    if not raw:
        return 2
    try:
        return max(0, int(raw))
    except ValueError:
        return 2


def _parse_timeout() -> float:
    raw = os.getenv("HOME_ASSISTANT_TIMEOUT_SECONDS", "5").strip()
    if not raw:
        return 5.0
    try:
        return max(1.0, float(raw))
    except ValueError:
        return 5.0


def _call_home_assistant(
    *,
    domain: str,
    service: str,
    service_data: JsonObject,
) -> ActionResult:
    base_url = os.getenv("HOME_ASSISTANT_URL", "").strip()
    token = os.getenv("HOME_ASSISTANT_TOKEN", "").strip()
    if not base_url or not token:
        return ActionResult(
            success=False,
            message="Home Assistant nao configurado.",
            error="missing HOME_ASSISTANT_URL or HOME_ASSISTANT_TOKEN",
        )

    timeout = _parse_timeout()
    retries = _parse_retry_count()
    endpoint = _build_ha_url(base_url, domain, service)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    for attempt in range(retries + 1):
        try:
            response = requests.post(endpoint, headers=headers, json=service_data, timeout=timeout)
            if 200 <= response.status_code < 300:
                payload: Any
                try:
                    payload = response.json()
                except ValueError:
                    payload = {"raw": response.text}
                return ActionResult(
                    success=True,
                    message=f"Servico executado: {domain}.{service}.",
                    data={"service_response": payload},
                )

            if response.status_code >= 500 and attempt < retries:
                time.sleep(min(0.2 * (2**attempt), 1.5))
                continue

            return ActionResult(
                success=False,
                message=f"Falha ao chamar Home Assistant ({response.status_code}).",
                error=response.text[:500],
            )
        except requests.RequestException as error:
            if attempt < retries:
                time.sleep(min(0.2 * (2**attempt), 1.5))
                continue
            return ActionResult(
                success=False,
                message="Erro de comunicacao com Home Assistant.",
                error=str(error),
            )

    return ActionResult(success=False, message="Erro desconhecido ao chamar Home Assistant.", error="unexpected")


def _policy_gate(name: str, params: JsonObject) -> ActionResult | None:
    if name == "call_service":
        domain = params.get("domain")
        service = params.get("service")
        if not isinstance(domain, str) or not isinstance(service, str):
            return ActionResult(
                success=False,
                message="Parametros invalidos para call_service.",
                error="domain and service must be strings",
            )
        if not _is_allowed_service(domain, service):
            return ActionResult(
                success=False,
                message=f"Servico nao permitido: {domain}.{service}.",
                error="service not in allowlist",
            )
    return None


async def dispatch_action(
    name: str,
    params: JsonObject,
    ctx: ActionContext,
    *,
    skip_confirmation: bool = False,
) -> ActionResult:
    started_at = time.perf_counter()
    started_at_iso = _now_iso()
    spec = get_action(name)

    if spec is None:
        result = ActionResult(success=False, message="Action not allowed", error=f"unknown action '{name}'")
        _log_action_result(ctx=ctx, action_name=name, params=params, started_at=started_at_iso, elapsed_ms=0, result=result)
        return result

    valid, validation_error = validate_params(params, spec.params_schema)
    if not valid:
        result = ActionResult(success=False, message="Invalid parameters", error=validation_error)
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        _log_action_result(
            ctx=ctx,
            action_name=name,
            params=params,
            started_at=started_at_iso,
            elapsed_ms=elapsed_ms,
            result=result,
        )
        return result

    gate_result = _policy_gate(name, params)
    if gate_result is not None:
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        _log_action_result(
            ctx=ctx,
            action_name=name,
            params=params,
            started_at=started_at_iso,
            elapsed_ms=elapsed_ms,
            result=gate_result,
        )
        return gate_result

    if spec.requires_auth and not _is_authenticated(ctx.participant_identity, ctx.room):
        result = ActionResult(
            success=False,
            message="Sessao privada bloqueada. Confirme sua identidade com PIN para continuar.",
            data={
                "authentication_required": True,
                "step_up_required": ctx.participant_identity in VOICE_STEP_UP_PENDING,
                **_security_status_payload(ctx.participant_identity, ctx.room),
            },
            error="not authenticated",
        )
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        _log_action_result(
            ctx=ctx,
            action_name=name,
            params=params,
            started_at=started_at_iso,
            elapsed_ms=elapsed_ms,
            result=result,
        )
        return result

    if spec.requires_auth:
        _touch_authenticated(ctx.participant_identity)

    if spec.requires_confirmation and not skip_confirmation and name != "confirm_action":
        pending = _store_confirmation(name, params, ctx)
        result = ActionResult(
            success=False,
            message=f"Confirma executar {name} com os parametros informados?",
            data={
                "confirmation_required": True,
                "confirmation_token": pending.token,
                "expires_in": _remaining_seconds(pending.expires_at),
                "action_name": pending.action_name,
                "params": pending.params,
            },
        )
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        _log_action_result(
            ctx=ctx,
            action_name=name,
            params=params,
            started_at=started_at_iso,
            elapsed_ms=elapsed_ms,
            result=result,
        )
        return result

    try:
        result = await spec.handler(params, ctx)
    except Exception as error:  # noqa: BLE001
        logger.exception("action dispatch failed", extra={"action": name})
        result = ActionResult(success=False, message="Action execution failed", error=str(error))

    elapsed_ms = int((time.perf_counter() - started_at) * 1000)
    _log_action_result(
        ctx=ctx,
        action_name=name,
        params=params,
        started_at=started_at_iso,
        elapsed_ms=elapsed_ms,
        result=result,
    )
    return result


def _log_action_result(
    *,
    ctx: ActionContext,
    action_name: str,
    params: JsonObject,
    started_at: str,
    elapsed_ms: int,
    result: ActionResult,
) -> None:
    payload = {
        "job_id": ctx.job_id,
        "room": ctx.room,
        "participant_identity": ctx.participant_identity,
        "action_name": action_name,
        "params": _redact(params),
        "started_at": started_at,
        "duration_ms": elapsed_ms,
        "success": result.success,
        "error": result.error,
    }
    logger.info("tool_call %s", json.dumps(payload, ensure_ascii=False))


async def _turn_light_on(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    entity_id = str(params["entity_id"])
    return await _call_service(
        {
            "domain": "light",
            "service": "turn_on",
            "service_data": {"entity_id": entity_id},
        },
        ctx,
    )


async def _turn_light_off(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    entity_id = str(params["entity_id"])
    return await _call_service(
        {
            "domain": "light",
            "service": "turn_off",
            "service_data": {"entity_id": entity_id},
        },
        ctx,
    )


async def _set_light_brightness(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    entity_id = str(params["entity_id"])
    brightness = int(params["brightness"])
    return await _call_service(
        {
            "domain": "light",
            "service": "turn_on",
            "service_data": {"entity_id": entity_id, "brightness": brightness},
        },
        ctx,
    )


async def _call_service(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    domain = str(params["domain"]).strip().lower()
    service = str(params["service"]).strip().lower()
    service_data = params.get("service_data")

    if not isinstance(service_data, dict):
        return ActionResult(success=False, message="service_data invalido.", error="service_data must be object")

    if not _is_allowed_service(domain, service):
        return ActionResult(
            success=False,
            message=f"Servico nao permitido: {domain}.{service}.",
            error="service not in allowlist",
        )

    return _call_home_assistant(domain=domain, service=service, service_data=service_data)


async def _confirm_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    token = str(params.get("confirmation_token", "")).strip()
    if not token:
        return ActionResult(success=False, message="Token de confirmacao ausente.", error="missing token")

    pending = _peek_confirmation(token)
    if pending is None:
        return ActionResult(success=False, message="Token de confirmacao invalido ou expirado.", error="invalid token")

    if pending.participant_identity != ctx.participant_identity:
        return ActionResult(success=False, message="Token pertence a outro participante.", error="identity mismatch")

    if pending.room != ctx.room:
        return ActionResult(success=False, message="Token pertence a outra sala.", error="room mismatch")

    last_user_text = _extract_last_user_text(ctx.session)
    if not _is_explicit_confirmation(last_user_text):
        return ActionResult(
            success=False,
            message="Preciso de confirmacao explicita. Diga claramente 'sim, confirmo' para executar.",
            data={
                "confirmation_required": True,
                "confirmation_token": pending.token,
                "expires_in": _remaining_seconds(pending.expires_at),
                "action_name": pending.action_name,
                "params": pending.params,
            },
        )

    _pop_confirmation(token)
    return await dispatch_action(pending.action_name, pending.params, ctx, skip_confirmation=True)


async def _authenticate_identity(params: JsonObject, ctx: ActionContext) -> ActionResult:
    pin = str(params.get("pin", "")).strip()
    passphrase = str(params.get("passphrase", "")).strip()
    if not passphrase:
        passphrase = str(params.get("security_phrase", "")).strip()

    expected_pin = _security_pin()
    expected_passphrase = _security_passphrase()
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
        _clear_authentication(ctx.participant_identity)
        return ActionResult(
            success=False,
            message="Falha na autenticacao. Informe PIN ou frase de seguranca validos.",
            data={"authentication_required": True, **_security_status_payload(ctx.participant_identity, ctx.room)},
            error="invalid credentials",
        )

    step_up_pending = ctx.participant_identity in VOICE_STEP_UP_PENDING
    auth_method = "pin" if pin_valid else "passphrase"
    if step_up_pending:
        auth_method = "voice+pin"
    elif pin_valid and passphrase_valid:
        auth_method = "voice+pin"

    _set_authenticated(ctx.participant_identity, ctx.room, auth_method=auth_method)
    return ActionResult(
        success=True,
        message="Sessao autenticada. Modo privado liberado.",
        data={"auth_method": auth_method, "private_access_granted": True, **_security_status_payload(ctx.participant_identity, ctx.room)},
    )


async def _lock_private_mode(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    _clear_authentication(ctx.participant_identity)
    return ActionResult(
        success=True,
        message="Modo privado bloqueado.",
        data=_security_status_payload(ctx.participant_identity, ctx.room),
    )


async def _get_security_status(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    status = _security_status_payload(ctx.participant_identity, ctx.room)
    if status["security_status"]["authenticated"]:
        message = "Sessao autenticada."
    else:
        message = "Sessao nao autenticada."
    return ActionResult(success=True, message=message, data=status)


async def _set_memory_scope(params: JsonObject, ctx: ActionContext) -> ActionResult:
    scope = str(params.get("scope", "")).strip().lower()
    if scope not in {"public", "private"}:
        return ActionResult(success=False, message="Escopo invalido. Use public ou private.", error="invalid scope")
    set_memory_scope_override(ctx.participant_identity, ctx.room, scope)
    return ActionResult(success=True, message=f"Ok, vou tratar o proximo contexto como {scope}.", data={"memory_scope": scope})


async def _forget_memory(params: JsonObject, ctx: ActionContext) -> ActionResult:
    if ctx.memory_client is None or not ctx.user_id:
        return ActionResult(success=False, message="Memoria indisponivel nesta sessao.", error="memory client not available")

    query = str(params.get("query", "")).strip()
    scope = str(params.get("scope", "all")).strip().lower()
    limit = int(params.get("limit", 3))
    if not query:
        return ActionResult(success=False, message="Informe o que devo esquecer.", error="missing query")

    allowed_scopes = ["public", "private"] if scope == "all" else [scope]
    if scope not in {"all", "public", "private"}:
        return ActionResult(success=False, message="Escopo invalido para esquecimento.", error="invalid scope")

    if "private" in allowed_scopes and not _is_authenticated(ctx.participant_identity, ctx.room):
        return ActionResult(
            success=False,
            message="Para esquecer memoria privada, autentique a sessao primeiro.",
            data={"authentication_required": True, **_security_status_payload(ctx.participant_identity, ctx.room)},
            error="not authenticated",
        )

    deleted: list[JsonObject] = []
    for target_scope in allowed_scopes:
        scoped_user_id = f"{ctx.user_id}::{target_scope}"
        results = await ctx.memory_client.search(query, filters={"user_id": scoped_user_id})
        candidates = results.get("results") if isinstance(results, dict) else results
        if not isinstance(candidates, list):
            continue
        for item in candidates[: max(1, limit)]:
            if not isinstance(item, dict):
                continue
            memory_id = item.get("id")
            if not memory_id:
                continue
            await ctx.memory_client.delete(memory_id)
            deleted.append(
                {
                    "id": memory_id,
                    "scope": target_scope,
                    "memory": str(item.get("memory", ""))[:120],
                }
            )

    if not deleted:
        return ActionResult(success=False, message="Nao encontrei memoria correspondente para esquecer.", error="not found")

    return ActionResult(
        success=True,
        message=f"Esqueci {len(deleted)} memoria(s) correspondente(s).",
        data={"deleted_count": len(deleted), "deleted": deleted},
    )


async def _enroll_voice_profile(params: JsonObject, ctx: ActionContext) -> ActionResult:
    if VOICE_PROFILE_STORE is None:
        return ActionResult(success=False, message="Biometria de voz desativada.", error="voice biometrics disabled")

    name = str(params.get("name", "")).strip()
    if not name:
        return ActionResult(success=False, message="Informe um nome para o perfil de voz.", error="missing name")

    VOICE_PROFILE_STORE.enroll_profile(name=name, participant_identity=ctx.participant_identity)
    return ActionResult(success=True, message=f"Perfil de voz '{name}' salvo com sucesso.")


async def _list_voice_profiles(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    if VOICE_PROFILE_STORE is None:
        return ActionResult(success=False, message="Biometria de voz desativada.", error="voice biometrics disabled")
    profiles = VOICE_PROFILE_STORE.list_profiles()
    return ActionResult(success=True, message=f"{len(profiles)} perfil(is) de voz encontrado(s).", data={"profiles": profiles})


async def _delete_voice_profile(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    if VOICE_PROFILE_STORE is None:
        return ActionResult(success=False, message="Biometria de voz desativada.", error="voice biometrics disabled")

    name = str(params.get("name", "")).strip()
    if not name:
        return ActionResult(success=False, message="Informe o nome do perfil a remover.", error="missing name")
    deleted = VOICE_PROFILE_STORE.delete_profile(name=name)
    if not deleted:
        return ActionResult(success=False, message="Perfil de voz nao encontrado.", error="not found")
    return ActionResult(success=True, message=f"Perfil de voz '{name}' removido.")


async def _verify_voice_identity(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    if VOICE_PROFILE_STORE is None:
        return ActionResult(success=False, message="Biometria de voz desativada.", error="voice biometrics disabled")

    verify = VOICE_PROFILE_STORE.verify_identity(participant_identity=ctx.participant_identity)
    threshold = _voice_threshold()
    stepup_limit = max(threshold, _voice_stepup_threshold())

    if verify.score >= stepup_limit:
        _set_authenticated(ctx.participant_identity, ctx.room, auth_method="voice")
        return ActionResult(
            success=True,
            message="Identidade por voz validada com alta confianca.",
            data={
                "auth_method": "voice",
                "voice_score": verify.score,
                "private_access_granted": True,
                "step_up_required": False,
                "matched_profile": verify.profile_name,
                **_security_status_payload(ctx.participant_identity, ctx.room),
            },
        )

    if verify.score >= threshold:
        VOICE_STEP_UP_PENDING[ctx.participant_identity] = verify.score
        _clear_authentication(ctx.participant_identity)
        return ActionResult(
            success=False,
            message="Voz reconhecida com confianca media. Confirme com PIN/frase para liberar acesso privado.",
            data={
                "authentication_required": True,
                "step_up_required": True,
                "voice_score": verify.score,
                "matched_profile": verify.profile_name,
                **_security_status_payload(ctx.participant_identity, ctx.room),
            },
            error="voice_step_up_required",
        )

    _clear_authentication(ctx.participant_identity)
    return ActionResult(
        success=False,
        message="Nao consegui validar sua identidade por voz.",
        data={"voice_score": verify.score, "step_up_required": True},
        error="voice_not_matched",
    )


def register_default_actions() -> None:
    if ACTION_REGISTRY:
        return

    register_action(
        ActionSpec(
            name="get_security_status",
            description="Retorna o estado de autenticacao da sessao atual.",
            params_schema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_get_security_status,
        )
    )

    register_action(
        ActionSpec(
            name="authenticate_identity",
            description=(
                "Autentica o usuario atual usando PIN e, opcionalmente, frase de seguranca para liberar modo privado."
            ),
            params_schema={
                "type": "object",
                "properties": {
                    "pin": {"type": "string", "minLength": 4, "maxLength": 32},
                    "passphrase": {"type": "string", "minLength": 1, "maxLength": 128},
                    "security_phrase": {"type": "string", "minLength": 1, "maxLength": 128},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_authenticate_identity,
        )
    )

    register_action(
        ActionSpec(
            name="lock_private_mode",
            description="Bloqueia a sessao privada atual e remove autenticacao ativa.",
            params_schema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_lock_private_mode,
        )
    )

    register_action(
        ActionSpec(
            name="set_memory_scope",
            description="Define preferencia de memoria para o contexto atual: public ou private.",
            params_schema={
                "type": "object",
                "properties": {
                    "scope": {"type": "string", "enum": ["public", "private"]},
                },
                "required": ["scope"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_set_memory_scope,
        )
    )

    register_action(
        ActionSpec(
            name="forget_memory",
            description="Esquece memorias salvas que combinem com a consulta informada.",
            params_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "minLength": 2, "maxLength": 256},
                    "scope": {"type": "string", "enum": ["all", "public", "private"]},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 10},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_forget_memory,
        )
    )

    register_action(
        ActionSpec(
            name="enroll_voice_profile",
            description="Cadastra o perfil de voz local para a identidade atual.",
            params_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "minLength": 2, "maxLength": 64},
                },
                "required": ["name"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_enroll_voice_profile,
        )
    )

    register_action(
        ActionSpec(
            name="verify_voice_identity",
            description="Verifica identidade de voz e aplica step-up com PIN se necessario.",
            params_schema={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_verify_voice_identity,
        )
    )

    register_action(
        ActionSpec(
            name="list_voice_profiles",
            description="Lista perfis de voz cadastrados localmente.",
            params_schema={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_list_voice_profiles,
        )
    )

    register_action(
        ActionSpec(
            name="delete_voice_profile",
            description="Remove um perfil de voz cadastrado pelo nome.",
            params_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "minLength": 2, "maxLength": 64},
                },
                "required": ["name"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_delete_voice_profile,
        )
    )

    register_action(
        ActionSpec(
            name="turn_light_on",
            description="Liga uma luz do Home Assistant pelo entity_id informado.",
            params_schema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+$",
                    }
                },
                "required": ["entity_id"],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_turn_light_on,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="turn_light_off",
            description="Desliga uma luz do Home Assistant pelo entity_id informado.",
            params_schema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+$",
                    }
                },
                "required": ["entity_id"],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_turn_light_off,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="set_light_brightness",
            description="Define o brilho da luz (0-255) para o entity_id informado.",
            params_schema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+$",
                    },
                    "brightness": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 255,
                    },
                },
                "required": ["entity_id", "brightness"],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_set_light_brightness,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="call_service",
            description="Executa um servico permitido no Home Assistant.",
            params_schema={
                "type": "object",
                "properties": {
                    "domain": {"type": "string", "pattern": r"^[a-z_]+$"},
                    "service": {"type": "string", "pattern": r"^[a-z_]+$"},
                    "service_data": {"type": "object"},
                },
                "required": ["domain", "service", "service_data"],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_call_service,
            expose_to_model=False,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="confirm_action",
            description="Confirma e executa uma acao pendente usando confirmation_token.",
            params_schema={
                "type": "object",
                "properties": {
                    "confirmation_token": {"type": "string", "minLength": 8},
                },
                "required": ["confirmation_token"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_confirm_action,
            requires_auth=True,
        )
    )


register_default_actions()
