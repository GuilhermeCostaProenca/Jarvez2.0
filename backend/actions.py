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


ACTION_REGISTRY: dict[str, ActionSpec] = {}
PENDING_CONFIRMATIONS: dict[str, PendingConfirmation] = {}
PARTICIPANT_PENDING_TOKENS: dict[str, str] = {}
AUTHENTICATED_SESSIONS: dict[str, AuthenticatedSession] = {}


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


def _clear_authentication(identity: str) -> None:
    AUTHENTICATED_SESSIONS.pop(identity, None)


def _set_authenticated(identity: str, room: str) -> None:
    AUTHENTICATED_SESSIONS[identity] = AuthenticatedSession(
        participant_identity=identity,
        room=room,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=_security_ttl_seconds()),
    )


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
    return True


def _security_status_payload(identity: str, room: str) -> JsonObject:
    authenticated = _is_authenticated(identity, room)
    session = AUTHENTICATED_SESSIONS.get(identity)
    expires_in = _remaining_seconds(session.expires_at) if session else 0
    return {
        "security_status": {
            "authenticated": authenticated,
            "identity_bound": bool(identity),
            "expires_in": expires_in,
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

    expected_pin = _security_pin()
    expected_passphrase = _security_passphrase()
    if not expected_pin:
        return ActionResult(
            success=False,
            message="PIN de seguranca nao configurado no servidor.",
            error="missing JARVEZ_SECURITY_PIN",
        )

    pin_valid = secrets.compare_digest(pin, expected_pin)
    passphrase_required = bool(expected_passphrase)
    passphrase_valid = (not passphrase_required) or secrets.compare_digest(passphrase, expected_passphrase)

    if not pin_valid or not passphrase_valid:
        _clear_authentication(ctx.participant_identity)
        return ActionResult(
            success=False,
            message="Falha na autenticacao. Verifique PIN e frase de seguranca.",
            data={"authentication_required": True, **_security_status_payload(ctx.participant_identity, ctx.room)},
            error="invalid credentials",
        )

    _set_authenticated(ctx.participant_identity, ctx.room)
    return ActionResult(
        success=True,
        message="Sessao autenticada. Modo privado liberado.",
        data=_security_status_payload(ctx.participant_identity, ctx.room),
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
                },
                "required": ["pin"],
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
