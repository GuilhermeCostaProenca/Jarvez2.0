from __future__ import annotations

import json
import logging
import math
import os
import random
import re
import secrets
import subprocess
import tempfile
import time
import html
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable
from urllib.parse import quote, urlencode

import requests
from voice_biometrics import VoiceProfileStore, get_recent_voice_embedding
from rpg_knowledge import RPGKnowledgeIndex

try:
    from pypdf import PdfReader, PdfWriter
except Exception:  # pragma: no cover - optional dependency at runtime
    PdfReader = None
    PdfWriter = None

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
except Exception:  # pragma: no cover - optional dependency at runtime
    colors = None
    A4 = None
    ParagraphStyle = None
    getSampleStyleSheet = None
    mm = None
    Paragraph = None
    SimpleDocTemplate = None
    Spacer = None
    Table = None
    TableStyle = None

try:
    import edge_tts
except Exception:  # pragma: no cover - optional dependency at runtime
    edge_tts = None

logger = logging.getLogger(__name__)
logging.getLogger("pypdf").setLevel(logging.ERROR)

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

THREAT_SOLO_COMBAT_TABLE: dict[str, JsonObject] = {
    "1/4": {"attack_value": 6, "average_damage": 8, "defense": 11, "strong_save": 3, "medium_save": 0, "weak_save": -2, "hit_points": 7, "standard_effect_dc": 12},
    "1/3": {"attack_value": 6, "average_damage": 9, "defense": 12, "strong_save": 4, "medium_save": 1, "weak_save": -1, "hit_points": 10, "standard_effect_dc": 12},
    "1/2": {"attack_value": 7, "average_damage": 10, "defense": 14, "strong_save": 6, "medium_save": 3, "weak_save": -1, "hit_points": 15, "standard_effect_dc": 13},
    "1": {"attack_value": 9, "average_damage": 15, "defense": 16, "strong_save": 11, "medium_save": 5, "weak_save": 0, "hit_points": 35, "standard_effect_dc": 14},
    "2": {"attack_value": 12, "average_damage": 18, "defense": 19, "strong_save": 13, "medium_save": 7, "weak_save": 2, "hit_points": 70, "standard_effect_dc": 16},
    "3": {"attack_value": 14, "average_damage": 21, "defense": 21, "strong_save": 15, "medium_save": 9, "weak_save": 3, "hit_points": 105, "standard_effect_dc": 17},
    "4": {"attack_value": 16, "average_damage": 24, "defense": 23, "strong_save": 16, "medium_save": 10, "weak_save": 4, "hit_points": 140, "standard_effect_dc": 18},
    "5": {"attack_value": 17, "average_damage": 40, "defense": 24, "strong_save": 17, "medium_save": 11, "weak_save": 5, "hit_points": 200, "standard_effect_dc": 20},
    "6": {"attack_value": 20, "average_damage": 56, "defense": 27, "strong_save": 18, "medium_save": 12, "weak_save": 6, "hit_points": 240, "standard_effect_dc": 22},
    "7": {"attack_value": 24, "average_damage": 62, "defense": 31, "strong_save": 20, "medium_save": 14, "weak_save": 7, "hit_points": 280, "standard_effect_dc": 24},
    "8": {"attack_value": 26, "average_damage": 68, "defense": 33, "strong_save": 21, "medium_save": 15, "weak_save": 8, "hit_points": 320, "standard_effect_dc": 26},
    "9": {"attack_value": 27, "average_damage": 74, "defense": 34, "strong_save": 21, "medium_save": 15, "weak_save": 9, "hit_points": 360, "standard_effect_dc": 28},
    "10": {"attack_value": 29, "average_damage": 80, "defense": 36, "strong_save": 22, "medium_save": 16, "weak_save": 10, "hit_points": 400, "standard_effect_dc": 30},
    "11": {"attack_value": 34, "average_damage": 130, "defense": 41, "strong_save": 24, "medium_save": 18, "weak_save": 11, "hit_points": 550, "standard_effect_dc": 31},
    "12": {"attack_value": 36, "average_damage": 144, "defense": 43, "strong_save": 26, "medium_save": 20, "weak_save": 12, "hit_points": 600, "standard_effect_dc": 33},
    "13": {"attack_value": 37, "average_damage": 158, "defense": 44, "strong_save": 26, "medium_save": 20, "weak_save": 13, "hit_points": 650, "standard_effect_dc": 35},
    "14": {"attack_value": 39, "average_damage": 172, "defense": 46, "strong_save": 28, "medium_save": 22, "weak_save": 14, "hit_points": 700, "standard_effect_dc": 38},
    "15": {"attack_value": 43, "average_damage": 186, "defense": 50, "strong_save": 28, "medium_save": 22, "weak_save": 15, "hit_points": 750, "standard_effect_dc": 40},
    "16": {"attack_value": 46, "average_damage": 200, "defense": 53, "strong_save": 30, "medium_save": 24, "weak_save": 16, "hit_points": 800, "standard_effect_dc": 42},
    "17": {"attack_value": 48, "average_damage": 214, "defense": 55, "strong_save": 31, "medium_save": 25, "weak_save": 17, "hit_points": 850, "standard_effect_dc": 44},
    "18": {"attack_value": 50, "average_damage": 228, "defense": 57, "strong_save": 33, "medium_save": 27, "weak_save": 18, "hit_points": 900, "standard_effect_dc": 46},
    "19": {"attack_value": 52, "average_damage": 242, "defense": 59, "strong_save": 34, "medium_save": 28, "weak_save": 19, "hit_points": 950, "standard_effect_dc": 48},
    "20": {"attack_value": 54, "average_damage": 256, "defense": 61, "strong_save": 36, "medium_save": 30, "weak_save": 20, "hit_points": 1000, "standard_effect_dc": 50},
    "S": {"attack_value": 56, "average_damage": 280, "defense": 64, "strong_save": 38, "medium_save": 32, "weak_save": 22, "hit_points": 1200, "standard_effect_dc": 52},
    "S+": {"attack_value": 58, "average_damage": 300, "defense": 66, "strong_save": 40, "medium_save": 34, "weak_save": 24, "hit_points": 1400, "standard_effect_dc": 54},
}


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


@dataclass(slots=True)
class RPGSessionRecordingState:
    participant_identity: str
    room: str
    title: str
    world: str
    started_at: datetime
    start_history_index: int
    active: bool
    output_file: str | None = None


@dataclass(slots=True)
class ActiveCharacterMode:
    name: str
    source: str
    summary: str
    activated_at: str
    page_id: str | None = None
    page_title: str | None = None
    section_name: str | None = None
    one_note_url: str | None = None
    visual_reference_url: str | None = None
    pinterest_pin_url: str | None = None
    visual_description: str | None = None
    profile: JsonObject | None = None
    prompt_hint: str | None = None
    sheet_json_path: str | None = None
    sheet_markdown_path: str | None = None
    sheet_pdf_path: str | None = None


ACTION_REGISTRY: dict[str, ActionSpec] = {}
PENDING_CONFIRMATIONS: dict[str, PendingConfirmation] = {}
PARTICIPANT_PENDING_TOKENS: dict[str, str] = {}
AUTHENTICATED_SESSIONS: dict[str, AuthenticatedSession] = {}
VOICE_STEP_UP_PENDING: dict[str, float] = {}
VOICE_PROFILE_STORE = VoiceProfileStore.from_env()
MEMORY_SCOPE_OVERRIDES: dict[str, str] = {}
PERSONA_MODE_BY_PARTICIPANT: dict[str, str] = {}
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"
SPOTIFY_ACCOUNTS_URL = "https://accounts.spotify.com/api/token"
ONENOTE_GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
ONENOTE_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
ONENOTE_AUTHORIZE_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
DEFAULT_SPOTIFY_SCOPES = (
    "user-read-playback-state "
    "user-modify-playback-state "
    "user-read-currently-playing "
    "playlist-modify-private "
    "playlist-modify-public "
    "user-top-read"
)
DEFAULT_ONENOTE_SCOPES = "offline_access User.Read Notes.ReadWrite"
SPOTIFY_FALLBACK_TRACKS = [
    "spotify:track:7CyPwkp0oE8Ro9Dd5CUDjW",
    "spotify:track:21nV7Brjy93nQPM98QwIfr",
    "spotify:track:0k4d5YPDr1r7FX77VdqWez",
    "spotify:track:3Vi5XqYrmQgOYBajMWSvCi",
    "spotify:track:6iBMj762l27f5fH6E1PUHE",
    "spotify:track:2takcwOaAZWiXQijPHIx7B",
    "spotify:track:2Fxmhks0bxGSBdJ92vM42m",
    "spotify:track:0VjIjW4GlUZAMYd2vXMi3b",
]
SPOTIFY_TOKEN_CACHE: JsonObject = {}
ONENOTE_TOKEN_CACHE: JsonObject = {}
WHATSAPP_GRAPH_BASE = "https://graph.facebook.com"
DEFAULT_PERSONA_MODE = "default"
PERSONA_MODE_ALIASES = {
    "default": "default",
    "normal": "default",
    "padrao": "default",
    "padrão": "default",
    "jarvez": "default",
    "hetero_top": "faria_lima",
    "heterotop": "faria_lima",
    "faria_lima": "faria_lima",
    "faria lima": "faria_lima",
    "mona": "mona",
    "gay": "mona",
    "rpg": "rpg",
    "roleplay": "rpg",
}
PERSONA_MODES: dict[str, JsonObject] = {
    "default": {
        "label": "Jarvez Classico",
        "style": "tom confiante, tecnico e objetivo",
        "color_hex": "#1DA3B9",
        "voice_hint": "neutro confiante",
    },
    "faria_lima": {
        "label": "Hetero Top Faria Lima",
        "style": "tom de executivo paulistano, energia alta, linguagem de negocios e networking",
        "color_hex": "#A0A0A0",
        "voice_hint": "grave e direto",
    },
    "mona": {
        "label": "Mona",
        "style": "tom divertido, afetuoso, colorido e expressivo, mantendo respeito e sem ofensas",
        "color_hex": "#FF4DA6",
        "voice_hint": "brilhante e expressivo",
    },
    "rpg": {
        "label": "RPG",
        "style": "tom de mestre de jogo, narrativo, imersivo e criativo; pode interpretar personagens quando pedido",
        "color_hex": "#7A3EEA",
        "voice_hint": "narrativo dramático",
    },
}
RPG_KNOWLEDGE_INDEX: RPGKnowledgeIndex | None = None
RPG_ACTIVE_RECORDINGS: dict[str, RPGSessionRecordingState] = {}
RPG_LAST_SESSION_FILES: dict[str, str] = {}
ACTIVE_CHARACTER_BY_PARTICIPANT: dict[str, ActiveCharacterMode] = {}


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


def _persona_key(participant_identity: str, room: str) -> str:
    return f"{participant_identity}:{room}"


def _normalize_persona_mode(value: str) -> str:
    raw = value.strip().lower().replace("-", "_")
    return PERSONA_MODE_ALIASES.get(raw, raw)


def get_persona_mode(participant_identity: str, room: str) -> str:
    key = _persona_key(participant_identity, room)
    mode = PERSONA_MODE_BY_PARTICIPANT.get(key, DEFAULT_PERSONA_MODE)
    if mode not in PERSONA_MODES:
        return DEFAULT_PERSONA_MODE
    return mode


def set_persona_mode(participant_identity: str, room: str, mode: str) -> str:
    normalized = _normalize_persona_mode(mode)
    if normalized not in PERSONA_MODES:
        return DEFAULT_PERSONA_MODE
    PERSONA_MODE_BY_PARTICIPANT[_persona_key(participant_identity, room)] = normalized
    return normalized


def _persona_payload(mode: str) -> JsonObject:
    resolved_mode = mode if mode in PERSONA_MODES else DEFAULT_PERSONA_MODE
    profile = PERSONA_MODES.get(resolved_mode, PERSONA_MODES[DEFAULT_PERSONA_MODE])
    return {
        "persona_mode": resolved_mode,
        "persona_profile": profile,
    }


def _character_key(participant_identity: str, room: str) -> str:
    return f"{participant_identity}:{room}"


def get_active_character(participant_identity: str, room: str) -> ActiveCharacterMode | None:
    return ACTIVE_CHARACTER_BY_PARTICIPANT.get(_character_key(participant_identity, room))


def set_active_character(participant_identity: str, room: str, character: ActiveCharacterMode) -> None:
    ACTIVE_CHARACTER_BY_PARTICIPANT[_character_key(participant_identity, room)] = character


def clear_active_character(participant_identity: str, room: str) -> None:
    ACTIVE_CHARACTER_BY_PARTICIPANT.pop(_character_key(participant_identity, room), None)


def _active_character_payload(participant_identity: str, room: str) -> JsonObject:
    active = get_active_character(participant_identity, room)
    if active is None:
        return {
            "active_character": None,
            "active_character_name": None,
        }
    return {
        "active_character": {
            "name": active.name,
            "source": active.source,
            "summary": active.summary,
            "activated_at": active.activated_at,
            "page_id": active.page_id,
            "page_title": active.page_title,
            "section_name": active.section_name,
            "one_note_url": active.one_note_url,
            "visual_reference_url": active.visual_reference_url,
            "pinterest_pin_url": active.pinterest_pin_url,
            "visual_description": active.visual_description,
            "profile": active.profile,
            "prompt_hint": active.prompt_hint,
            "sheet_json_path": active.sheet_json_path,
            "sheet_markdown_path": active.sheet_markdown_path,
            "sheet_pdf_path": active.sheet_pdf_path,
        },
        "active_character_name": active.name,
    }


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
    persona = _persona_payload(get_persona_mode(identity, room))
    return {
        "security_status": {
            "authenticated": authenticated,
            "identity_bound": bool(identity),
            "expires_in": expires_in,
            "auth_method": auth_method,
            "step_up_required": step_up_required,
        },
        **persona,
        **_active_character_payload(identity, room),
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


def _spotify_tokens_path() -> Path:
    raw = os.getenv("SPOTIFY_TOKENS_PATH", "data/spotify_tokens.json").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _onenote_tokens_path() -> Path:
    raw = os.getenv("ONENOTE_TOKENS_PATH", "data/onenote_tokens.json").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _onenote_client_id() -> str:
    return os.getenv("ONENOTE_CLIENT_ID", "").strip()


def _onenote_client_secret() -> str:
    return os.getenv("ONENOTE_CLIENT_SECRET", "").strip()


def _onenote_redirect_uri() -> str:
    return os.getenv("ONENOTE_REDIRECT_URI", "").strip()


def _read_onenote_tokens_file() -> JsonObject:
    path = _onenote_tokens_path()
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass
    return {}


def _write_onenote_tokens_file(payload: JsonObject) -> None:
    path = _onenote_tokens_path()
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _onenote_initialize_cache() -> None:
    if ONENOTE_TOKEN_CACHE:
        return
    file_tokens = _read_onenote_tokens_file()
    ONENOTE_TOKEN_CACHE.update(file_tokens)

    env_access_token = os.getenv("ONENOTE_ACCESS_TOKEN", "").strip()
    env_refresh_token = os.getenv("ONENOTE_REFRESH_TOKEN", "").strip()
    env_expires_at = os.getenv("ONENOTE_ACCESS_TOKEN_EXPIRES_AT", "").strip()
    if env_access_token:
        ONENOTE_TOKEN_CACHE["access_token"] = env_access_token
    if env_refresh_token:
        ONENOTE_TOKEN_CACHE["refresh_token"] = env_refresh_token
    if env_expires_at:
        ONENOTE_TOKEN_CACHE["expires_at"] = env_expires_at


def _onenote_auth_url() -> str:
    query = urlencode(
        {
            "client_id": _onenote_client_id(),
            "response_type": "code",
            "redirect_uri": _onenote_redirect_uri() or f"{_spotify_frontend_base_url()}/api/onenote/callback",
            "response_mode": "query",
            "scope": os.getenv("ONENOTE_SCOPES", DEFAULT_ONENOTE_SCOPES),
        }
    )
    return f"{ONENOTE_AUTHORIZE_URL}?{query}"


def _onenote_save_tokens(access_token: str, refresh_token: str | None, expires_in_seconds: int | None) -> None:
    expires_at_iso = None
    if expires_in_seconds is not None:
        expires_at_iso = (datetime.now(timezone.utc) + timedelta(seconds=max(30, int(expires_in_seconds)))).isoformat()

    if access_token:
        ONENOTE_TOKEN_CACHE["access_token"] = access_token
    if refresh_token:
        ONENOTE_TOKEN_CACHE["refresh_token"] = refresh_token
    if expires_at_iso:
        ONENOTE_TOKEN_CACHE["expires_at"] = expires_at_iso
    ONENOTE_TOKEN_CACHE["updated_at"] = _now_iso()

    to_store = {
        "access_token": ONENOTE_TOKEN_CACHE.get("access_token", ""),
        "refresh_token": ONENOTE_TOKEN_CACHE.get("refresh_token", ""),
        "expires_at": ONENOTE_TOKEN_CACHE.get("expires_at", ""),
        "updated_at": ONENOTE_TOKEN_CACHE.get("updated_at", _now_iso()),
    }
    _write_onenote_tokens_file(to_store)


def _onenote_token_expiring() -> bool:
    raw_expires_at = str(ONENOTE_TOKEN_CACHE.get("expires_at", "")).strip()
    if not raw_expires_at:
        return False
    try:
        expires_at = datetime.fromisoformat(raw_expires_at)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at <= datetime.now(timezone.utc) + timedelta(seconds=30)
    except Exception:
        return False


def _onenote_refresh_access_token() -> ActionResult | None:
    client_id = _onenote_client_id()
    client_secret = _onenote_client_secret()
    refresh_token = str(ONENOTE_TOKEN_CACHE.get("refresh_token", "")).strip()
    if not client_id or not client_secret or not refresh_token:
        return ActionResult(
            success=False,
            message="OneNote nao autenticado. Abra /api/onenote/login para conectar.",
            data={"authorization_url": f"{_spotify_frontend_base_url()}/api/onenote/login"},
            error="onenote_auth_required",
        )

    try:
        response = requests.post(
            ONENOTE_TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "scope": os.getenv("ONENOTE_SCOPES", DEFAULT_ONENOTE_SCOPES),
            },
            timeout=8,
        )
    except requests.RequestException as error:
        return ActionResult(success=False, message="Erro ao renovar token do OneNote.", error=str(error))

    if response.status_code != 200:
        return ActionResult(
            success=False,
            message="Falha ao renovar token do OneNote.",
            error=response.text[:300],
            data={"authorization_url": f"{_spotify_frontend_base_url()}/api/onenote/login"},
        )

    payload = response.json() if response.content else {}
    access_token = str(payload.get("access_token", "")).strip()
    new_refresh_token = str(payload.get("refresh_token", "")).strip() or refresh_token
    expires_in = payload.get("expires_in")
    if not access_token:
        return ActionResult(success=False, message="Resposta invalida ao renovar token OneNote.", error="missing access token")

    _onenote_save_tokens(access_token, new_refresh_token, int(expires_in) if isinstance(expires_in, int) else 3600)
    return None


def _onenote_get_access_token() -> tuple[str | None, ActionResult | None]:
    _onenote_initialize_cache()
    access_token = str(ONENOTE_TOKEN_CACHE.get("access_token", "")).strip()
    if access_token and not _onenote_token_expiring():
        return access_token, None

    refresh_result = _onenote_refresh_access_token()
    if refresh_result is not None:
        if access_token:
            return access_token, None
        return None, refresh_result

    fresh_access_token = str(ONENOTE_TOKEN_CACHE.get("access_token", "")).strip()
    if not fresh_access_token:
        return None, ActionResult(
            success=False,
            message="OneNote nao autenticado. Abra /api/onenote/login para conectar.",
            data={"authorization_url": f"{_spotify_frontend_base_url()}/api/onenote/login"},
            error="onenote_auth_required",
        )
    return fresh_access_token, None


def _onenote_api_request(
    method: str,
    endpoint: str,
    *,
    params: JsonObject | None = None,
    body: JsonObject | list[Any] | None = None,
    raw_body: str | None = None,
    extra_headers: JsonObject | None = None,
    retry_on_401: bool = True,
) -> tuple[JsonObject | list[Any] | str | None, ActionResult | None]:
    token, token_error = _onenote_get_access_token()
    if token_error is not None:
        return None, token_error

    url = f"{ONENOTE_GRAPH_BASE_URL}/{endpoint.lstrip('/')}"
    headers = {"Authorization": f"Bearer {token}"}
    if extra_headers:
        for key, value in extra_headers.items():
            headers[str(key)] = str(value)
    if body is not None and "Content-Type" not in headers:
        headers["Content-Type"] = "application/json"

    request_kwargs: dict[str, Any] = {"params": params, "headers": headers, "timeout": 12}
    if raw_body is not None:
        request_kwargs["data"] = raw_body
    elif body is not None:
        request_kwargs["json"] = body

    try:
        response = requests.request(method, url, **request_kwargs)
    except requests.RequestException as error:
        return None, ActionResult(success=False, message="Erro de comunicacao com OneNote.", error=str(error))

    if response.status_code == 401 and retry_on_401:
        refresh_result = _onenote_refresh_access_token()
        if refresh_result is not None:
            return None, refresh_result
        return _onenote_api_request(
            method,
            endpoint,
            params=params,
            body=body,
            raw_body=raw_body,
            extra_headers=extra_headers,
            retry_on_401=False,
        )

    if not (200 <= response.status_code < 300):
        return None, ActionResult(
            success=False,
            message=f"OneNote retornou erro ({response.status_code}).",
            error=response.text[:400],
        )

    content_type = response.headers.get("Content-Type", "")
    if "application/json" in content_type:
        try:
            payload = response.json()
            if isinstance(payload, (dict, list)):
                return payload, None
            return {}, None
        except ValueError:
            return {}, None
    if response.content:
        return response.text, None
    return {}, None


def _strip_html_for_preview(text: str, max_len: int = 800) -> str:
    no_tags = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"\s+", " ", no_tags).strip()
    return clean[:max_len]


def _quote_path_segment(value: str) -> str:
    return quote(value.strip(), safe="")


def _summarize_character_text(text: str, max_len: int = 700) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= max_len:
        return clean
    return clean[:max_len].rstrip() + "..."


def _extract_section_html(html_content: str, heading: str) -> str:
    pattern = re.compile(
        rf"<h2[^>]*>\s*{re.escape(heading)}\s*</h2>(.*?)(?=<h2[^>]*>|</body>|</html>)",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(html_content)
    if not match:
        return ""
    return match.group(1)


def _clean_section_text(html_fragment: str, max_len: int = 700) -> str:
    clean = _strip_html_for_preview(html_fragment, max_len=max_len * 2)
    return _summarize_character_text(clean, max_len=max_len)


def _extract_onenote_character_profile(html_content: str) -> JsonObject:
    section_map = {
        "summary": "Resumo",
        "sheet_base": "Ficha Base",
        "voice_style": "Voz e Maneirismos",
        "visual": "Visual",
        "objectives": "Objetivos",
        "relations": "Relacoes",
        "secrets": "Segredos",
        "knowledge_limits": "Limites de Conhecimento",
        "session_evolution": "Evolucao em Sessao",
    }
    profile: JsonObject = {}
    for key, heading in section_map.items():
        fragment = _extract_section_html(html_content, heading)
        if not fragment:
            continue
        text = _clean_section_text(fragment)
        if text:
            profile[key] = text

    visual_block = str(profile.get("visual", ""))
    if visual_block:
        ref_match = re.search(r"referencia_visual_url:\s*(https?://\S+)", visual_block, flags=re.IGNORECASE)
        pin_match = re.search(r"pinterest_pin_url:\s*(https?://\S+)", visual_block, flags=re.IGNORECASE)
        desc_match = re.search(r"descricao_visual:\s*(.+)$", visual_block, flags=re.IGNORECASE)
        if ref_match:
            profile["visual_reference_url"] = ref_match.group(1).strip()
        if pin_match:
            profile["pinterest_pin_url"] = pin_match.group(1).strip()
        if desc_match:
            profile["visual_description"] = _summarize_character_text(desc_match.group(1).strip(), max_len=400)

    return profile


def _build_character_prompt_hint(name: str, summary: str, profile: JsonObject | None) -> str:
    parts = [f"Interprete {name} de forma persistente e coerente."]
    if summary:
        parts.append(f"Base do personagem: {summary}")
    if isinstance(profile, dict):
        voice_style = str(profile.get("voice_style", "")).strip()
        objectives = str(profile.get("objectives", "")).strip()
        relations = str(profile.get("relations", "")).strip()
        secrets = str(profile.get("secrets", "")).strip()
        knowledge_limits = str(profile.get("knowledge_limits", "")).strip()
        visual_description = str(profile.get("visual_description", "")).strip()
        if voice_style:
            parts.append(f"Voz e maneirismos: {voice_style}")
        if objectives:
            parts.append(f"Objetivos atuais: {objectives}")
        if relations:
            parts.append(f"Relacoes importantes: {relations}")
        if secrets:
            parts.append(f"Segredos que o personagem protege: {secrets}")
        if knowledge_limits:
            parts.append(f"Limites de conhecimento e revelacao: {knowledge_limits}")
        if visual_description:
            parts.append(f"Referencia visual: {visual_description}")
    parts.append("Nao contradiga os traços acima. Se faltar contexto, improvise sem quebrar a coerencia.")
    return " ".join(part for part in parts if part).strip()


def _find_onenote_character_page(name: str, section_name: str | None = None) -> JsonObject | None:
    sections_payload, sections_error = _onenote_api_request("GET", "me/onenote/sections", params={"$top": 100})
    if sections_error is not None:
        return None
    sections = sections_payload.get("value", []) if isinstance(sections_payload, dict) else []
    if not isinstance(sections, list):
        sections = []

    normalized_name = name.casefold().strip()
    normalized_section = section_name.casefold().strip() if section_name else ""

    candidates: list[JsonObject] = []
    for section in sections[:60]:
        if not isinstance(section, dict):
            continue
        current_section_id = str(section.get("id", "")).strip()
        current_section_name = str(section.get("displayName", "")).strip()
        if normalized_section and normalized_section not in current_section_name.casefold():
            continue
        if not current_section_id:
            continue

        encoded_section_id = _quote_path_segment(current_section_id)
        pages_payload, pages_error = _onenote_api_request(
            "GET",
            f"me/onenote/sections/{encoded_section_id}/pages",
            params={"$top": 100},
        )
        if pages_error is not None:
            continue
        pages = pages_payload.get("value", []) if isinstance(pages_payload, dict) else []
        if not isinstance(pages, list):
            continue
        for page in pages:
            if not isinstance(page, dict):
                continue
            title = str(page.get("title", "")).strip()
            title_folded = title.casefold()
            if normalized_name == title_folded:
                return {
                    "page": page,
                    "section_name": current_section_name,
                }
            if normalized_name in title_folded:
                candidates.append(
                    {
                        "page": page,
                        "section_name": current_section_name,
                    }
                )

    return candidates[0] if candidates else None


def _onenote_rpg_character_section_name() -> str:
    return os.getenv("ONENOTE_RPG_CHARACTER_SECTION_NAME", "").strip()


def _resolve_onenote_character_section(preferred_section_name: str | None = None) -> tuple[JsonObject | None, ActionResult | None]:
    sections_payload, sections_error = _onenote_api_request("GET", "me/onenote/sections", params={"$top": 100})
    if sections_error is not None:
        return None, sections_error

    sections = sections_payload.get("value", []) if isinstance(sections_payload, dict) else []
    if not isinstance(sections, list) or not sections:
        return None, ActionResult(
            success=False,
            message="Nao encontrei secoes no OneNote para salvar o personagem.",
            error="section not found",
        )

    requested_names = [
        preferred_section_name or "",
        _onenote_rpg_character_section_name(),
        "personagens",
        "personagens rpg",
        "npcs",
        "npc",
        "rpg",
    ]
    normalized_candidates = [item.casefold().strip() for item in requested_names if item and item.strip()]

    for requested in normalized_candidates:
        for section in sections:
            if not isinstance(section, dict):
                continue
            section_name = str(section.get("displayName", "")).strip()
            if requested in section_name.casefold():
                return section, None

    for section in sections:
        if isinstance(section, dict):
            return section, None

    return None, ActionResult(
        success=False,
        message="Nao encontrei uma secao valida no OneNote para o personagem.",
        error="section not found",
    )


def _build_onenote_character_template(
    *,
    title: str,
    summary: str,
    source: str,
    section_name: str | None,
    visual_reference_url: str | None,
    pinterest_pin_url: str | None,
    visual_description: str | None,
) -> str:
    safe_title = html.escape(title)
    safe_summary = html.escape(summary or "Resumo inicial pendente.")
    safe_source = html.escape(source or "manual")
    safe_section = html.escape(section_name or "Nao definida")
    safe_visual_reference = html.escape(visual_reference_url or "")
    safe_pinterest_pin = html.escape(pinterest_pin_url or "")
    safe_visual_description = html.escape(visual_description or "Sem descricao visual inicial.")
    activated_at = html.escape(datetime.now().strftime("%d/%m/%Y %H:%M"))

    visual_reference_html = (
        f"<p><strong>referencia_visual_url:</strong> <a href=\"{safe_visual_reference}\">{safe_visual_reference}</a></p>"
        if safe_visual_reference
        else "<p><strong>referencia_visual_url:</strong> </p>"
    )
    pinterest_html = (
        f"<p><strong>pinterest_pin_url:</strong> <a href=\"{safe_pinterest_pin}\">{safe_pinterest_pin}</a></p>"
        if safe_pinterest_pin
        else "<p><strong>pinterest_pin_url:</strong> </p>"
    )

    return (
        "<!DOCTYPE html><html><head><title>"
        f"{safe_title}"
        "</title><meta name=\"created\" content=\""
        f"{activated_at}"
        "\" /></head><body>"
        f"<h1>{safe_title}</h1>"
        "<h2>Identidade</h2>"
        f"<p><strong>Origem do contexto:</strong> {safe_source}</p>"
        f"<p><strong>Secao de referencia:</strong> {safe_section}</p>"
        f"<p><strong>Ativado em:</strong> {activated_at}</p>"
        "<h2>Resumo</h2>"
        f"<p>{safe_summary}</p>"
        "<h2>Ficha Base</h2>"
        "<p>Classe:</p><p>Raca:</p><p>Nivel:</p><p>Atributos:</p><p>Defesa:</p><p>PV/PM:</p>"
        "<h2>Voz e Maneirismos</h2>"
        "<p>Tom de voz:</p><p>Maneirismos:</p><p>Palavras recorrentes:</p>"
        "<h2>Visual</h2>"
        f"{visual_reference_html}"
        f"{pinterest_html}"
        f"<p><strong>descricao_visual:</strong> {safe_visual_description}</p>"
        "<h2>Objetivos</h2><p></p>"
        "<h2>Relacoes</h2><p></p>"
        "<h2>Segredos</h2><p></p>"
        "<h2>Limites de Conhecimento</h2><p>O que este personagem sabe, suspeita e nunca revelaria.</p>"
        "<h2>Evolucao em Sessao</h2><p>Pagina criada automaticamente pelo Jarvez para uso em interpretacao.</p>"
        "</body></html>"
    )


def _ensure_onenote_character_page(
    *,
    title: str,
    summary: str,
    source: str,
    preferred_section_name: str | None,
    visual_reference_url: str | None,
    pinterest_pin_url: str | None,
    visual_description: str | None,
) -> tuple[JsonObject | None, ActionResult | None]:
    existing = _find_onenote_character_page(title, preferred_section_name)
    if existing and isinstance(existing, dict):
        page = existing.get("page")
        if isinstance(page, dict):
            links = page.get("links", {})
            one_note_url = ""
            if isinstance(links, dict):
                one_note = links.get("oneNoteClientUrl")
                if isinstance(one_note, dict):
                    one_note_url = str(one_note.get("href", "")).strip()
            return {
                "page_id": str(page.get("id", "")).strip(),
                "title": str(page.get("title", "")).strip() or title,
                "section_name": str(existing.get("section_name", "")).strip() or preferred_section_name,
                "one_note_url": one_note_url or str(page.get("contentUrl", "")).strip(),
                "created": False,
            }, None

    section, section_error = _resolve_onenote_character_section(preferred_section_name)
    if section_error is not None:
        return None, section_error
    if not isinstance(section, dict):
        return None, ActionResult(success=False, message="Secao OneNote invalida.", error="section not found")

    section_id = str(section.get("id", "")).strip()
    section_name = str(section.get("displayName", "")).strip() or preferred_section_name
    if not section_id:
        return None, ActionResult(success=False, message="Secao OneNote sem id valido.", error="section not found")

    encoded_section_id = _quote_path_segment(section_id)
    html_doc = _build_onenote_character_template(
        title=title,
        summary=summary,
        source=source,
        section_name=section_name,
        visual_reference_url=visual_reference_url,
        pinterest_pin_url=pinterest_pin_url,
        visual_description=visual_description,
    )
    payload, error = _onenote_api_request(
        "POST",
        f"me/onenote/sections/{encoded_section_id}/pages",
        raw_body=html_doc,
        extra_headers={"Content-Type": "text/html"},
    )
    if error is not None:
        return None, error

    page_id = str(payload.get("id", "")).strip() if isinstance(payload, dict) else ""
    links = payload.get("links", {}) if isinstance(payload, dict) else {}
    one_note_url = ""
    if isinstance(links, dict):
        one_note = links.get("oneNoteClientUrl")
        if isinstance(one_note, dict):
            one_note_url = str(one_note.get("href", "")).strip()

    return {
        "page_id": page_id,
        "title": title,
        "section_name": section_name,
        "one_note_url": one_note_url,
        "created": True,
    }, None


def _spotify_client_id() -> str:
    return os.getenv("SPOTIFY_CLIENT_ID", "").strip()


def _spotify_client_secret() -> str:
    return os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()


def _spotify_redirect_uri() -> str:
    return os.getenv("SPOTIFY_REDIRECT_URI", "").strip()


def _spotify_frontend_base_url() -> str:
    return os.getenv("JARVEZ_FRONTEND_URL", "http://127.0.0.1:3001").strip()


def _read_spotify_tokens_file() -> JsonObject:
    path = _spotify_tokens_path()
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass
    return {}


def _write_spotify_tokens_file(payload: JsonObject) -> None:
    path = _spotify_tokens_path()
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _spotify_initialize_cache() -> None:
    if SPOTIFY_TOKEN_CACHE:
        return
    file_tokens = _read_spotify_tokens_file()
    SPOTIFY_TOKEN_CACHE.update(file_tokens)

    env_access_token = os.getenv("SPOTIFY_ACCESS_TOKEN", "").strip()
    env_refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN", "").strip()
    env_expires_at = os.getenv("SPOTIFY_ACCESS_TOKEN_EXPIRES_AT", "").strip()
    if env_access_token:
        SPOTIFY_TOKEN_CACHE["access_token"] = env_access_token
    if env_refresh_token:
        SPOTIFY_TOKEN_CACHE["refresh_token"] = env_refresh_token
    if env_expires_at:
        SPOTIFY_TOKEN_CACHE["expires_at"] = env_expires_at


def _spotify_auth_url() -> str:
    query = urlencode(
        {
            "client_id": _spotify_client_id(),
            "response_type": "code",
            "redirect_uri": _spotify_redirect_uri() or f"{_spotify_frontend_base_url()}/api/spotify/callback",
            "scope": os.getenv("SPOTIFY_SCOPES", DEFAULT_SPOTIFY_SCOPES),
            "show_dialog": "true",
        }
    )
    return f"https://accounts.spotify.com/authorize?{query}"


def _spotify_save_tokens(access_token: str, refresh_token: str | None, expires_in_seconds: int | None) -> None:
    expires_at_iso = None
    if expires_in_seconds is not None:
        expires_at_iso = (datetime.now(timezone.utc) + timedelta(seconds=max(30, int(expires_in_seconds)))).isoformat()

    if access_token:
        SPOTIFY_TOKEN_CACHE["access_token"] = access_token
    if refresh_token:
        SPOTIFY_TOKEN_CACHE["refresh_token"] = refresh_token
    if expires_at_iso:
        SPOTIFY_TOKEN_CACHE["expires_at"] = expires_at_iso
    SPOTIFY_TOKEN_CACHE["updated_at"] = _now_iso()

    to_store = {
        "access_token": SPOTIFY_TOKEN_CACHE.get("access_token", ""),
        "refresh_token": SPOTIFY_TOKEN_CACHE.get("refresh_token", ""),
        "expires_at": SPOTIFY_TOKEN_CACHE.get("expires_at", ""),
        "updated_at": SPOTIFY_TOKEN_CACHE.get("updated_at", _now_iso()),
    }
    _write_spotify_tokens_file(to_store)


def _spotify_token_expiring() -> bool:
    raw_expires_at = str(SPOTIFY_TOKEN_CACHE.get("expires_at", "")).strip()
    if not raw_expires_at:
        return False
    try:
        expires_at = datetime.fromisoformat(raw_expires_at)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at <= datetime.now(timezone.utc) + timedelta(seconds=30)
    except Exception:
        return False


def _spotify_refresh_access_token() -> ActionResult | None:
    client_id = _spotify_client_id()
    client_secret = _spotify_client_secret()
    refresh_token = str(SPOTIFY_TOKEN_CACHE.get("refresh_token", "")).strip()
    if not client_id or not client_secret or not refresh_token:
        return ActionResult(
            success=False,
            message="Spotify nao autenticado. Abra /api/spotify/login para conectar.",
            data={"authorization_url": f"{_spotify_frontend_base_url()}/api/spotify/login"},
            error="spotify_auth_required",
        )

    try:
        response = requests.post(
            SPOTIFY_ACCOUNTS_URL,
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
            auth=(client_id, client_secret),
            timeout=8,
        )
    except requests.RequestException as error:
        return ActionResult(success=False, message="Erro ao renovar token do Spotify.", error=str(error))

    if response.status_code != 200:
        return ActionResult(
            success=False,
            message="Falha ao renovar token do Spotify.",
            error=response.text[:300],
            data={"authorization_url": f"{_spotify_frontend_base_url()}/api/spotify/login"},
        )

    payload = response.json() if response.content else {}
    access_token = str(payload.get("access_token", "")).strip()
    new_refresh_token = str(payload.get("refresh_token", "")).strip() or refresh_token
    expires_in = payload.get("expires_in")
    if not access_token:
        return ActionResult(success=False, message="Resposta invalida ao renovar token Spotify.", error="missing access token")

    _spotify_save_tokens(access_token, new_refresh_token, int(expires_in) if isinstance(expires_in, int) else 3600)
    return None


def _spotify_get_access_token() -> tuple[str | None, ActionResult | None]:
    _spotify_initialize_cache()
    access_token = str(SPOTIFY_TOKEN_CACHE.get("access_token", "")).strip()
    if access_token and not _spotify_token_expiring():
        return access_token, None

    refresh_result = _spotify_refresh_access_token()
    if refresh_result is not None:
        # Use non-expiring env access token as fallback.
        if access_token:
            return access_token, None
        return None, refresh_result

    fresh_access_token = str(SPOTIFY_TOKEN_CACHE.get("access_token", "")).strip()
    if not fresh_access_token:
        return None, ActionResult(
            success=False,
            message="Spotify nao autenticado. Abra /api/spotify/login para conectar.",
            data={"authorization_url": f"{_spotify_frontend_base_url()}/api/spotify/login"},
            error="spotify_auth_required",
        )
    return fresh_access_token, None


def _spotify_api_request(
    method: str,
    endpoint: str,
    *,
    params: JsonObject | None = None,
    body: JsonObject | None = None,
    retry_on_401: bool = True,
) -> tuple[JsonObject | list[Any] | None, ActionResult | None]:
    token, token_error = _spotify_get_access_token()
    if token_error is not None:
        return None, token_error

    url = f"{SPOTIFY_API_BASE_URL}/{endpoint.lstrip('/')}"
    headers = {"Authorization": f"Bearer {token}"}
    if body is not None:
        headers["Content-Type"] = "application/json"

    try:
        response = requests.request(method, url, params=params, json=body, headers=headers, timeout=8)
    except requests.RequestException as error:
        return None, ActionResult(success=False, message="Erro de comunicacao com Spotify.", error=str(error))

    if response.status_code == 401 and retry_on_401:
        refresh_result = _spotify_refresh_access_token()
        if refresh_result is not None:
            return None, refresh_result
        return _spotify_api_request(method, endpoint, params=params, body=body, retry_on_401=False)

    if not (200 <= response.status_code < 300):
        return None, ActionResult(
            success=False,
            message=f"Spotify retornou erro ({response.status_code}).",
            error=response.text[:300],
        )

    if not response.content:
        return {}, None
    try:
        payload = response.json()
        if isinstance(payload, (dict, list)):
            return payload, None
        return {}, None
    except ValueError:
        return {}, None


def _spotify_find_device(device_name: str | None = None, device_id: str | None = None) -> tuple[JsonObject | None, ActionResult | None]:
    payload, error = _spotify_api_request("GET", "me/player/devices")
    if error is not None:
        return None, error
    devices = payload.get("devices", []) if isinstance(payload, dict) else []
    if not isinstance(devices, list):
        devices = []

    if device_id:
        for device in devices:
            if isinstance(device, dict) and str(device.get("id", "")).strip() == device_id:
                return device, None
        return None, ActionResult(success=False, message="Device Spotify nao encontrado pelo id informado.", error="device not found")

    if device_name:
        normalized = device_name.casefold().strip()
        exact = [
            d for d in devices if isinstance(d, dict) and str(d.get("name", "")).casefold().strip() == normalized
        ]
        if exact:
            return exact[0], None
        partial = [
            d for d in devices if isinstance(d, dict) and normalized in str(d.get("name", "")).casefold().strip()
        ]
        if partial:
            return partial[0], None
        available = [str(d.get("name", "")) for d in devices if isinstance(d, dict)]
        return None, ActionResult(
            success=False,
            message=f"Nao encontrei o speaker '{device_name}' no Spotify Connect.",
            data={"available_devices": available},
            error="device not found",
        )

    active = [d for d in devices if isinstance(d, dict) and bool(d.get("is_active"))]
    if active:
        return active[0], None

    return None, ActionResult(
        success=False,
        message="Nenhum device ativo do Spotify encontrado.",
        data={"available_devices": [str(d.get("name", "")) for d in devices if isinstance(d, dict)]},
        error="no active device",
    )


def _spotify_pick_surprise_tracks(top_tracks_payload: JsonObject | None) -> list[str]:
    uris: list[str] = []
    if isinstance(top_tracks_payload, dict):
        items = top_tracks_payload.get("items", [])
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    uri = str(item.get("uri", "")).strip()
                    if uri.startswith("spotify:track:"):
                        uris.append(uri)
    if len(uris) < 5:
        uris.extend(SPOTIFY_FALLBACK_TRACKS)
    uris = list(dict.fromkeys(uris))
    if not uris:
        return SPOTIFY_FALLBACK_TRACKS[:5]
    random.shuffle(uris)
    return uris[: min(20, len(uris))]


def _whatsapp_graph_version() -> str:
    return os.getenv("WHATSAPP_GRAPH_VERSION", "v22.0").strip() or "v22.0"


def _whatsapp_access_token() -> str:
    return os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()


def _whatsapp_phone_number_id() -> str:
    return os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()


def _whatsapp_default_country_code() -> str:
    return os.getenv("WHATSAPP_DEFAULT_COUNTRY_CODE", "55").strip() or "55"


def _whatsapp_inbox_path() -> Path:
    raw = os.getenv("WHATSAPP_INBOX_PATH", "data/whatsapp_inbox.json").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _rpg_db_path() -> Path:
    raw = os.getenv("RPG_KNOWLEDGE_DB_PATH", "data/rpg_knowledge.db").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _rpg_notes_dir() -> Path:
    raw = os.getenv("RPG_NOTES_DIR", "data/rpg_notes").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def _rpg_sources() -> list[Path]:
    raw = os.getenv("RPG_SOURCE_PATHS", "").strip()
    if not raw:
        return []
    return [Path(item.strip()) for item in raw.split(";") if item.strip()]


def _rpg_session_logs_dir() -> Path:
    raw = os.getenv("RPG_SESSION_LOGS_DIR", "data/rpg_sessions").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def _rpg_characters_dir() -> Path:
    raw = os.getenv("RPG_CHARACTERS_DIR", "data/rpg_characters").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def _rpg_character_pdfs_dir() -> Path:
    raw = os.getenv("RPG_CHARACTER_PDFS_DIR", "output/pdf/rpg-characters").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent.parent / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def _rpg_threats_dir() -> Path:
    raw = os.getenv("RPG_THREATS_DIR", "data/rpg_threats").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def _rpg_threat_pdfs_dir() -> Path:
    raw = os.getenv("RPG_THREAT_PDFS_DIR", "output/pdf/rpg-threats").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent.parent / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def _character_sheet_json_path(world: str, name: str) -> Path:
    return _rpg_characters_dir() / _safe_file_part(world) / f"{_safe_file_part(name)}.json"


def _load_existing_character_sheet(world: str, name: str) -> JsonObject | None:
    path = _character_sheet_json_path(world, name)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _find_existing_character_sheet_by_name(name: str) -> tuple[JsonObject | None, Path | None]:
    safe_name = f"{_safe_file_part(name)}.json"
    base_dir = _rpg_characters_dir()
    for path in base_dir.rglob(safe_name):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            return data, path
    return None, None


def _tormenta20_pdf_template_path() -> Path:
    raw = os.getenv(
        "RPG_CHARACTER_PDF_TEMPLATE_PATH",
        "backend/assets/pdf_templates/tormenta20_sheet_template.pdf",
    ).strip()
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent.parent / path
    return path


def _rpg_pdf_export_enabled() -> bool:
    raw = os.getenv("RPG_CHARACTER_PDF_TEMPLATE_PATH", "").strip().casefold()
    return raw not in {"disabled", "off", "false", "0"}


def _node_binary() -> str:
    return os.getenv("NODE_BIN", "node").strip() or "node"


def _t20_sheet_bridge_path() -> Path:
    return Path(__file__).resolve().parent / "tools" / "t20_sheet_bridge.cjs"


def _run_t20_sheet_builder(payload: JsonObject) -> tuple[JsonObject | None, str | None]:
    bridge_path = _t20_sheet_bridge_path()
    if not bridge_path.exists():
        return None, "bridge script not found"

    try:
        completed = subprocess.run(
            [_node_binary(), str(bridge_path)],
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            cwd=str(Path(__file__).resolve().parent.parent),
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return None, str(error)

    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    if completed.returncode != 0:
        return None, stderr or stdout or f"node exited with code {completed.returncode}"
    if not stdout:
        return None, "empty bridge response"
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError as error:
        return None, f"invalid bridge json: {error}"
    if not isinstance(parsed, dict):
        return None, "bridge response must be an object"
    if not parsed.get("success"):
        return None, str(parsed.get("error", "unknown bridge error"))
    data = parsed.get("data")
    if not isinstance(data, dict):
        return None, "bridge response missing data"
    return data, None


def _humanize_identifier(value: str) -> str:
    compact = str(value or "").strip()
    if not compact:
        return ""
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", compact.replace("_", " ").replace("-", " "))
    return " ".join(part.capitalize() for part in spaced.split())


def _sheet_modifier(sheet: JsonObject, logical_name: str) -> int:
    modifiers = sheet.get("modifiers")
    if isinstance(modifiers, dict):
        raw_value = modifiers.get(logical_name)
        if isinstance(raw_value, (int, float)):
            return int(raw_value)

    aliases = {
        "forca": ("forca", "strength"),
        "destreza": ("destreza", "dexterity"),
        "constituicao": ("constituicao", "constitution"),
        "inteligencia": ("inteligencia", "intelligence"),
        "sabedoria": ("sabedoria", "wisdom"),
        "carisma": ("carisma", "charisma"),
    }
    attributes = sheet.get("attributes")
    if isinstance(attributes, dict):
        for alias in aliases.get(logical_name, (logical_name,)):
            raw_value = attributes.get(alias)
            if isinstance(raw_value, (int, float)):
                return int(raw_value)
            if isinstance(raw_value, dict):
                nested = raw_value.get("value")
                if isinstance(nested, (int, float)):
                    return int(nested)
    return 0


def _string_list(items: Any, *, limit: int = 12) -> list[str]:
    if not isinstance(items, list):
        return []
    values: list[str] = []
    for item in items[:limit]:
        if isinstance(item, str):
            text = item.strip()
        elif isinstance(item, dict):
            nested_attack = item.get("attack")
            if isinstance(nested_attack, dict):
                text = str(nested_attack.get("name") or "").strip()
            else:
                text = str(item.get("name") or item.get("title") or item.get("description") or "").strip()
        else:
            text = str(item).strip()
        if text:
            values.append(text)
    return values


def _serialized_sheet(sheet: JsonObject) -> JsonObject:
    serialized = sheet.get("serialized_character")
    if not isinstance(serialized, dict):
        return {}
    nested = serialized.get("sheet")
    return nested if isinstance(nested, dict) else {}


def _json_list(values: Any) -> list[Any]:
    return values if isinstance(values, list) else []


def _extract_equipment_lines(serialized_sheet: JsonObject) -> list[str]:
    lines: list[str] = []
    equipment_groups = serialized_sheet.get("equipments")
    if isinstance(equipment_groups, dict):
        for _, items in equipment_groups.items():
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name") or item.get("nome") or "").strip()
                spaces = item.get("spaces")
                if name:
                    suffix = f" ({spaces} espacos)" if isinstance(spaces, (int, float)) and spaces else ""
                    lines.append(f"{name}{suffix}")
    if lines:
        return lines

    initial = serialized_sheet.get("initialEquipment")
    if isinstance(initial, dict):
        for key in ("simpleWeapon", "martialWeapon", "armor", "shield"):
            item = initial.get(key)
            if isinstance(item, dict):
                name = str(item.get("name") or "").strip()
                if name:
                    lines.append(name)
    return lines


def _extract_power_lines(serialized_sheet: JsonObject) -> list[str]:
    power_lists = [
        serialized_sheet.get("generalPowers"),
        serialized_sheet.get("rolePowers"),
        serialized_sheet.get("originPowers"),
        serialized_sheet.get("grantedPowers"),
    ]
    lines: list[str] = []
    seen: set[str] = set()
    for items in power_lists:
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            text = str(item.get("description") or item.get("text") or "").strip()
            if not name:
                continue
            key = name.casefold()
            if key in seen:
                continue
            seen.add(key)
            lines.append(f"- {name}: {text}".strip().rstrip(":"))
    return lines


def _extract_spell_lines(serialized_sheet: JsonObject) -> list[str]:
    spells = serialized_sheet.get("spells")
    if not isinstance(spells, list):
        return []
    lines: list[str] = []
    for item in spells:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("nome") or "").strip()
        if name:
            lines.append(name)
    return lines


def _extract_proficiencies(serialized_sheet: JsonObject) -> list[str]:
    proficiencies = serialized_sheet.get("proficiencies")
    if isinstance(proficiencies, list):
        return [str(item).strip() for item in proficiencies if str(item).strip()]
    return []


def _skill_display_name(key: str) -> str:
    names = {
        "acrobatics": "Acrobacia",
        "acting": "Atuacao",
        "aim": "Pontaria",
        "animalHandling": "Adestramento",
        "animalRide": "Cavalgar",
        "athletics": "Atletismo",
        "cheat": "Enganacao",
        "craft": "Oficio",
        "cure": "Cura",
        "diplomacy": "Diplomacia",
        "fight": "Luta",
        "fortitude": "Fortitude",
        "gambling": "Jogatina",
        "initiative": "Iniciativa",
        "intimidation": "Intimidacao",
        "intuition": "Intuicao",
        "investigation": "Investigacao",
        "knowledge": "Conhecimento",
        "mysticism": "Misticismo",
        "nobility": "Nobreza",
        "perception": "Percepcao",
        "piloting": "Pilotagem",
        "reflexes": "Reflexos",
        "religion": "Religiao",
        "stealth": "Furtividade",
        "survival": "Sobrevivencia",
        "thievery": "Ladinagem",
        "war": "Guerra",
        "will": "Vontade",
    }
    return names.get(key, _humanize_identifier(key))


def _skill_dropdown_value(attribute_name: str) -> str:
    mapping = {
        "forca": "modFor",
        "strength": "modFor",
        "destreza": "modDes",
        "dexterity": "modDes",
        "constituicao": "modCon",
        "constitution": "modCon",
        "inteligencia": "modInt",
        "intelligence": "modInt",
        "sabedoria": "modSab",
        "wisdom": "modSab",
        "carisma": "modCar",
        "charisma": "modCar",
    }
    return mapping.get(str(attribute_name or "").strip(), "modDes")


def _build_skill_row_fields(sheet: JsonObject) -> JsonObject:
    serialized_sheet = _serialized_sheet(sheet)
    if not isinstance(serialized_sheet, dict):
        return {}
    serialized_skills = serialized_sheet.get("skills")
    if not isinstance(serialized_skills, dict):
        return {}
    skills = serialized_skills.get("skills")
    if not isinstance(skills, dict):
        return {}

    rows: list[dict[str, Any]] = []
    craft_rows: list[dict[str, Any]] = []
    for key, data in skills.items():
        if not isinstance(data, dict):
            continue
        row = {
            "label": _skill_display_name(str(key)),
            "attribute": str(data.get("attribute") or data.get("defaultAttribute") or ""),
            "training": int(data.get("trainingPoints", 0) or 0),
            "others": int(((data.get("fixedModifiers") or {}).get("total", 0) if isinstance(data.get("fixedModifiers"), dict) else 0) or 0),
            "total": int(data.get("total", 0) or 0),
            "is_trained": bool(data.get("isTrained")),
        }
        if str(key) == "craft":
            craft_rows.append(row)
        else:
            rows.append(row)

    rows.sort(key=lambda item: str(item["label"]).casefold())
    craft_rows.sort(key=lambda item: str(item["label"]).casefold())
    rows.extend(craft_rows[:1])
    if len(craft_rows) <= 1:
        rows.append(
            {
                "label": "Oficio",
                "attribute": "intelligence",
                "training": 0,
                "others": 0,
                "total": 0,
                "is_trained": False,
            }
        )
    rows = rows[:30]

    fields: JsonObject = {}
    for index, row in enumerate(rows):
        number = index + 1
        fields[f"total{number}"] = str(row["total"])
        fields[f"treino{index}"] = str(row["training"])
        fields[f"outros{number}"] = str(row["others"])
        fields[f"modSelect{index}"] = _skill_dropdown_value(str(row["attribute"]))
        if row["is_trained"]:
            fields[f"treinado{number}"] = "/sim"

    oficio_names = [row["label"] for row in rows if str(row["label"]).startswith("Oficio")]
    if oficio_names:
        fields["Texto8"] = oficio_names[0].replace("Oficio", "").strip(" ()") or ""
    if len(oficio_names) > 1:
        fields["Texto9"] = oficio_names[1].replace("Oficio", "").strip(" ()") or ""
    return fields


def _attack_fields(sheet: JsonObject) -> JsonObject:
    attacks = sheet.get("attacks")
    if not isinstance(attacks, list):
        return {}

    fields: JsonObject = {}
    for index, item in enumerate(attacks[:5], start=1):
        if not isinstance(item, dict):
            continue
        attack = item.get("attack")
        if not isinstance(attack, dict):
            continue

        name = _humanize_identifier(str(attack.get("name", "")).strip())
        damage = attack.get("damage")
        critical = attack.get("critical")
        modifiers = item.get("modifiers")

        total_attack_bonus = int(item.get("testSkillAttributeModifier", 0) or 0)
        total_damage_bonus = 0

        if isinstance(modifiers, dict):
            test_mods = modifiers.get("test")
            if isinstance(test_mods, dict):
                fixed = test_mods.get("fixed")
                if isinstance(fixed, dict) and isinstance(fixed.get("total"), (int, float)):
                    total_attack_bonus += int(fixed["total"])
            damage_mods = modifiers.get("damage")
            if isinstance(damage_mods, dict):
                fixed = damage_mods.get("fixed")
                if isinstance(fixed, dict) and isinstance(fixed.get("total"), (int, float)):
                    total_damage_bonus += int(fixed["total"])

        damage_text = ""
        if isinstance(damage, dict):
            quantity = int(damage.get("diceQuantity", 0) or 0)
            sides = int(damage.get("diceSides", 0) or 0)
            if quantity > 0 and sides > 0:
                damage_text = f"{quantity}d{sides}"
                if total_damage_bonus:
                    damage_text += f"{total_damage_bonus:+d}"

        crit_text = ""
        if isinstance(critical, dict):
            threat = critical.get("threat")
            multiplier = critical.get("multiplier")
            if isinstance(threat, (int, float)) and isinstance(multiplier, (int, float)):
                crit_text = f"{int(threat)}/x{int(multiplier)}"

        fields[f"ataque{index}"] = name
        fields[f"tAtak{index}"] = f"{total_attack_bonus:+d}"
        fields[f"dano{index}"] = damage_text
        fields[f"critico{index}"] = crit_text
        fields[f"tipo{index}"] = "Corpo a corpo"
        fields[f"alcance{index}"] = "-"
    return fields


def _build_tormenta20_pdf_fields(sheet: JsonObject) -> JsonObject:
    level = int(sheet.get("level", 1) or 1)
    derived = sheet.get("derived") if isinstance(sheet.get("derived"), dict) else {}
    serialized_sheet = _serialized_sheet(sheet)
    trained = _string_list(sheet.get("trained_skills"), limit=12)
    if not trained:
        trained = _string_list(sheet.get("recommended_skills"), limit=12)
    top_skills = _string_list(sheet.get("top_skills"), limit=8)
    build_steps = _string_list(sheet.get("build_steps"), limit=10)
    powers = _extract_power_lines(serialized_sheet)
    spells = _extract_spell_lines(serialized_sheet)
    proficiencies = _extract_proficiencies(serialized_sheet)
    equipment_lines = _extract_equipment_lines(serialized_sheet)

    devotion = serialized_sheet.get("devotion")
    deity_name = ""
    if isinstance(devotion, dict):
        deity = devotion.get("deity")
        if isinstance(deity, dict):
            deity_name = str(deity.get("name") or "").strip()
        else:
            deity_name = str(devotion.get("name") or "").strip()

    displacement = serialized_sheet.get("displacement")
    if not isinstance(displacement, (int, float)):
        displacement = sheet.get("displacement", 9)

    money_value = serialized_sheet.get("money")
    if not isinstance(money_value, (int, float)):
        money_value = sheet.get("current_cargo", 0)

    max_cargo = sheet.get("max_cargo")
    if not isinstance(max_cargo, (int, float)):
        strength_mod = max(0, _sheet_modifier(sheet, "forca"))
        max_cargo = 10 + strength_mod * 5
    carry_capacity = sheet.get("carry_capacity")
    if not isinstance(carry_capacity, (int, float)):
        carry_capacity = int(max_cargo) * 2

    powers_lines = []
    concept = str(sheet.get("concept", "")).strip()
    world = str(sheet.get("world", "")).strip()
    if concept:
        powers_lines.append(f"Conceito: {concept}")
    if trained:
        powers_lines.append("Pericias: " + ", ".join(trained))
    if build_steps:
        powers_lines.append("Build: " + " | ".join(build_steps))
    if powers:
        powers_lines.extend(powers[:18])

    spell_lines = []
    if spells:
        spell_lines.append("Magias: " + ", ".join(spells[:24]))
    elif top_skills:
        spell_lines.append("Top skills: " + ", ".join(top_skills))
    if world:
        spell_lines.append(f"Mundo: {world}")

    feature_lines = []
    if concept:
        feature_lines.append(f"Conceito: {concept}")
    if trained:
        feature_lines.append("Treinadas: " + ", ".join(trained[:6]))
    if proficiencies:
        feature_lines.append("Proficiencias: " + ", ".join(proficiencies[:8]))

    item_lines = []
    if equipment_lines:
        item_lines.extend(equipment_lines[:24])
    else:
        attack_names = _string_list(sheet.get("attacks"), limit=5)
        if attack_names:
            item_lines.extend(attack_names)
        elif trained:
            item_lines.extend(trained[:5])

    fields: JsonObject = {
        "Nome": str(sheet.get("name", "")).strip(),
        "Raca": str(sheet.get("race", "")).strip(),
        "Origem": str(sheet.get("origin", "")).strip(),
        "Classe": f"{str(sheet.get('class_name', '')).strip()} {level}".strip(),
        "nivel": str(level),
        "Divindade": deity_name,
        "modFor": str(_sheet_modifier(sheet, "forca")),
        "modDes": str(_sheet_modifier(sheet, "destreza")),
        "modCon": str(_sheet_modifier(sheet, "constituicao")),
        "modInt": str(_sheet_modifier(sheet, "inteligencia")),
        "modSab": str(_sheet_modifier(sheet, "sabedoria")),
        "modCar": str(_sheet_modifier(sheet, "carisma")),
        "modDef": "modDes",
        "vidaMax": str(derived.get("pv", "")),
        "vidaAtual": str(derived.get("pv", "")),
        "manaMax": str(derived.get("pm", "")),
        "manaAtual": str(derived.get("pm", "")),
        "Texto13": str(derived.get("defense", "")),
        "deslocamento": str(displacement),
        "metadeDoNivel": str(max(0, level // 2)),
        "caracteristicas": "\n".join(feature_lines)[:1800],
        "Historico": "\n".join(powers_lines)[:7000],
        "Atualização": "\n".join(spell_lines)[:3000],
        "item1": "\n".join(item_lines)[:1000],
        "item2": "\n".join(item_lines[24:] or build_steps)[:1000],
        "cargaAtual": str(int(money_value)),
        "cargaMaxima": str(int(max_cargo)),
        "levantar": str(int(carry_capacity)),
        "TO": str(int(money_value)),
    }
    fields.update(_attack_fields(sheet))
    fields.update(_build_skill_row_fields(sheet))
    return {key: value for key, value in fields.items() if str(value).strip()}


def _export_tormenta20_sheet_pdf(sheet: JsonObject, output_path: Path) -> tuple[bool, str | None]:
    if PdfReader is None or PdfWriter is None:
        return False, "pypdf unavailable"

    template_path = _tormenta20_pdf_template_path()
    if not template_path.exists():
        return False, f"template not found: {template_path}"

    try:
        reader = PdfReader(str(template_path))
        writer = PdfWriter()
        writer.append(reader)
        if hasattr(writer, "set_need_appearances_writer"):
            writer.set_need_appearances_writer()
        field_values = _build_tormenta20_pdf_fields(sheet)
        for page in writer.pages:
            writer.update_page_form_field_values(page, field_values, auto_regenerate=False)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as file_handle:
            writer.write(file_handle)
    except Exception as error:
        return False, str(error)
    return True, None


def _parse_threat_nd_value(raw_value: str) -> tuple[str, float]:
    value = str(raw_value or "").strip().upper()
    mapping = {
        "1/4": 0.25,
        "1/3": 0.33,
        "1/2": 0.5,
        "S": 20.0,
        "S+": 21.0,
    }
    if value in mapping:
        return value, mapping[value]
    if re.fullmatch(r"\d{1,2}", value):
        numeric = float(int(value))
        if 1 <= numeric <= 20:
            return str(int(numeric)), numeric
    raise ValueError("challenge_level must be 1/4, 1/3, 1/2, 1..20, S or S+")


def _threat_challenge_tier(nd_value: float) -> str:
    if nd_value <= 4:
        return "Iniciante"
    if nd_value <= 10:
        return "Veterano"
    if nd_value <= 16:
        return "Campeao"
    if nd_value <= 20:
        return "Lenda"
    return "L+"


def _calculate_threat_combat_stats(role: str, challenge_level: str, has_mana_points: bool) -> JsonObject:
    normalized_challenge, nd_value = _parse_threat_nd_value(challenge_level)
    base = dict(THREAT_SOLO_COMBAT_TABLE[normalized_challenge])
    role_key = str(role or "Solo").strip().casefold()
    role_tuning = {
        "solo": {"attack": 0, "damage": 1.0, "defense": 0, "hp": 1.0, "dc": 0},
        "especial": {"attack": -2, "damage": 0.9, "defense": -1, "hp": 0.8, "dc": 1},
        "lacaio": {"attack": -4, "damage": 0.6, "defense": -2, "hp": 0.35, "dc": -2},
    }.get(role_key, {"attack": 0, "damage": 1.0, "defense": 0, "hp": 1.0, "dc": 0})

    combat_stats = {
        "attack_value": max(1, base["attack_value"] + int(role_tuning["attack"])),
        "average_damage": max(1, int(round(base["average_damage"] * float(role_tuning["damage"])))),
        "defense": max(10, base["defense"] + int(role_tuning["defense"])),
        "strong_save": base["strong_save"],
        "medium_save": base["medium_save"],
        "weak_save": base["weak_save"],
        "hit_points": max(1, int(round(base["hit_points"] * float(role_tuning["hp"])))),
        "standard_effect_dc": max(10, base["standard_effect_dc"] + int(role_tuning["dc"])),
    }
    if has_mana_points:
        combat_stats["mana_points"] = max(1, int(math.ceil(nd_value * 3)))
    return combat_stats


def _default_threat_attributes(role: str) -> JsonObject:
    role_key = str(role or "Solo").strip().casefold()
    profiles: dict[str, JsonObject] = {
        "solo": {"forca": 5, "destreza": 2, "constituicao": 5, "inteligencia": 1, "sabedoria": 2, "carisma": 1},
        "especial": {"forca": 2, "destreza": 3, "constituicao": 3, "inteligencia": 4, "sabedoria": 2, "carisma": 2},
        "lacaio": {"forca": 1, "destreza": 2, "constituicao": 1, "inteligencia": 0, "sabedoria": 0, "carisma": 0},
    }
    return dict(profiles.get(role_key, profiles["solo"]))


def _default_threat_resistance_assignments(role: str) -> JsonObject:
    role_key = str(role or "Solo").strip().casefold()
    profiles: dict[str, JsonObject] = {
        "solo": {"Fortitude": "strong", "Reflexos": "medium", "Vontade": "medium"},
        "especial": {"Fortitude": "medium", "Reflexos": "medium", "Vontade": "strong"},
        "lacaio": {"Fortitude": "medium", "Reflexos": "weak", "Vontade": "weak"},
    }
    return dict(profiles.get(role_key, profiles["solo"]))


def _recommended_threat_ability_count(challenge_level: str, role: str) -> JsonObject:
    _, nd_value = _parse_threat_nd_value(challenge_level)
    role_key = str(role or "Solo").strip().casefold()
    if nd_value <= 4:
        base = {"min": 1, "max": 2}
    elif nd_value <= 10:
        base = {"min": 2, "max": 4}
    elif nd_value <= 16:
        base = {"min": 4, "max": 6}
    elif nd_value <= 20:
        base = {"min": 5, "max": 8}
    else:
        base = {"min": 6, "max": 10}
    if role_key == "lacaio":
        base["max"] = max(base["min"], base["max"] - 2)
    elif role_key == "especial":
        base["max"] += 1
    return base


def _build_threat_qualities(role: str, challenge_level: str, combat_stats: JsonObject) -> list[str]:
    recommendations = _recommended_threat_ability_count(challenge_level, role)
    _, nd_value = _parse_threat_nd_value(challenge_level)
    role_key = str(role or "Solo").strip().casefold()
    qualities = [
        f"Recomenda-se entre {recommendations['min']} e {recommendations['max']} habilidades para este papel.",
        f"CD padrao sugerida: {combat_stats.get('standard_effect_dc')}.",
    ]
    if role_key == "solo":
        qualities.append("Considere ao menos 1 reacao e 1 efeito de area para sustentar o combate solo.")
    if role_key == "especial":
        qualities.append("Priorize efeitos de controle, mobilidade ou ruptura de acao para marcar a identidade especial.")
    if role_key == "lacaio":
        qualities.append("Mantenha ataques simples e dano comprimido; o perigo do lacaio vem do numero, nao da complexidade.")
    if nd_value >= 15:
        qualities.append("Para ND alto, inclua uma habilidade de fase final ou escalada para evitar combate estatico.")
    return qualities


def _build_generated_threat_abilities(
    *,
    role: str,
    challenge_level: str,
    combat_stats: JsonObject,
    has_mana_points: bool,
) -> list[JsonObject]:
    _, nd_value = _parse_threat_nd_value(challenge_level)
    role_key = str(role or "Solo").strip().casefold()
    effect_dc = int(combat_stats.get("standard_effect_dc", 10) or 10)
    avg_damage = int(combat_stats.get("average_damage", 1) or 1)
    mana_cost = int(combat_stats.get("mana_points", 0) or 0)
    abilities: list[JsonObject] = [
        {
            "category": "ofensiva",
            "name": "Golpe Assolador",
            "summary": f"Causa cerca de {avg_damage} de dano e pressiona a linha de frente.",
            "action_type": "Padrao",
            "pm_cost": max(0, mana_cost // 6) if has_mana_points else 0,
        },
        {
            "category": "controle",
            "name": "Pressao Tatica",
            "summary": f"Impõe condição relevante com CD {effect_dc} e quebra o ritmo do alvo.",
            "action_type": "Padrao",
            "pm_cost": max(0, mana_cost // 8) if has_mana_points else 0,
        },
    ]
    if role_key != "lacaio":
        abilities.append(
            {
                "category": "mobilidade",
                "name": "Reposicionamento Hostil",
                "summary": "Move-se ou desloca inimigos para punir posicionamento ruim.",
                "action_type": "Livre" if role_key == "especial" else "Movimento",
                "pm_cost": max(0, mana_cost // 10) if has_mana_points else 0,
            }
        )
    if role_key in {"solo", "especial"}:
        abilities.append(
            {
                "category": "defesa",
                "name": "Resposta Instintiva",
                "summary": "Reação defensiva para reduzir dano, evitar acerto ou punir foco excessivo.",
                "action_type": "Reacao",
                "pm_cost": max(0, mana_cost // 12) if has_mana_points else 0,
            }
        )
    if nd_value >= 11:
        abilities.append(
            {
                "category": "fase",
                "name": "Escalada de Confronto",
                "summary": "Ao perder PV suficientes, entra em fase mais agressiva com mais dano ou CD.",
                "action_type": "Livre",
                "pm_cost": max(0, mana_cost // 5) if has_mana_points else 0,
            }
        )
    return abilities


def _build_generated_boss_features(
    *,
    challenge_level: str,
    combat_stats: JsonObject,
    has_mana_points: bool,
) -> JsonObject:
    _, nd_value = _parse_threat_nd_value(challenge_level)
    effect_dc = int(combat_stats.get("standard_effect_dc", 10) or 10)
    avg_damage = int(combat_stats.get("average_damage", 1) or 1)
    hit_points = int(combat_stats.get("hit_points", 1) or 1)
    mana_points = int(combat_stats.get("mana_points", 0) or 0)
    return {
        "reactions": [
            {
                "name": "Contra-Golpe Instintivo",
                "summary": f"Quando sofre pico de dano, reage impondo teste de resistência CD {effect_dc} ou contra-pressão imediata.",
                "uses_per_round": 3,
                "pm_cost": max(0, mana_points // 12) if has_mana_points else 0,
            }
        ],
        "legendary_actions": [
            {
                "name": "Pressão Lendária",
                "cost": 1,
                "summary": f"Causa cerca de {max(1, avg_damage // 3)} de dano ou desloca um alvo fora de posição.",
            },
            {
                "name": "Ruptura de Ritmo",
                "cost": 2,
                "summary": f"Força teste CD {effect_dc - 2} ou reduz a eficiência ofensiva do grupo até a próxima rodada.",
            },
            {
                "name": "Impulso Final",
                "cost": 3,
                "summary": "Ativa poder de área, limpa pressão do mapa ou acelera a fase final.",
            },
        ],
        "phases": [
            {
                "threshold": "66%",
                "summary": f"Ao cair abaixo de {int(hit_points * 0.66)}, entra em fase de pressão crescente, com foco em controle e reposicionamento.",
            },
            {
                "threshold": "33%",
                "summary": f"Ao cair abaixo de {int(hit_points * 0.33)}, destrava pico ofensivo, aumenta dano e torna o combate mais agressivo.",
            },
        ],
        "defeat_condition": (
            f"Ao cair, desencadeia um efeito residual final com teste CD {effect_dc}. "
            "Quem falhar sofre consequência narrativa ou condição persistente ligada ao tema da ameaça."
        ),
        "boss_tuning": {
            "recommended_hit_point_breakpoints": [int(hit_points * 0.66), int(hit_points * 0.33)],
            "nd_is_high": nd_value >= 11,
        },
    }


def _build_threat_skills(challenge_level: str, attributes: JsonObject) -> list[JsonObject]:
    _, nd_value = _parse_threat_nd_value(challenge_level)
    training_bonus = 2 if nd_value <= 6 else 4 if nd_value <= 14 else 6
    skill_map = [
        ("Percepcao", "sabedoria", True, 2),
        ("Iniciativa", "destreza", True, 0),
        ("Fortitude", "constituicao", True, 0),
        ("Reflexos", "destreza", True, 0),
        ("Vontade", "sabedoria", True, 0),
        ("Intimidacao", "carisma", False, 2),
    ]
    skills: list[JsonObject] = []
    half_nd = int(math.floor(nd_value / 2))
    for name, attr, trained, custom_bonus in skill_map:
        attr_mod = int(attributes.get(attr, 0) or 0)
        total = half_nd + attr_mod + (training_bonus if trained else 0) + custom_bonus
        skills.append(
            {
                "name": name,
                "attribute": attr,
                "trained": trained,
                "custom_bonus": custom_bonus,
                "total": total,
            }
        )
    return skills


def _default_threat_attacks(name: str, combat_stats: JsonObject, role: str) -> list[JsonObject]:
    attack_bonus = int(combat_stats.get("attack_value", 0) or 0)
    average_damage = int(combat_stats.get("average_damage", 0) or 0)
    role_key = str(role or "Solo").strip().casefold()
    if role_key == "lacaio":
        attacks = [
            {
                "name": "Golpe de Investida",
                "attack_bonus": attack_bonus,
                "damage": f"{max(1, average_damage - 4)} dano",
                "action_type": "Padrao",
            }
        ]
    elif role_key == "especial":
        attacks = [
            {
                "name": "Ataque Principal",
                "attack_bonus": attack_bonus,
                "damage": f"{average_damage} dano",
                "action_type": "Padrao",
            },
            {
                "name": "Efeito Especial",
                "attack_bonus": attack_bonus - 2,
                "damage": f"{max(1, average_damage - 6)} dano + condicao",
                "action_type": "Completa",
            },
        ]
    else:
        attacks = [
            {
                "name": "Ataque Principal",
                "attack_bonus": attack_bonus,
                "damage": f"{average_damage} dano",
                "action_type": "Padrao",
            },
            {
                "name": "Golpe Devastador",
                "attack_bonus": attack_bonus - 2,
                "damage": f"{max(1, average_damage + 8)} dano",
                "action_type": "Completa",
            },
        ]
    for item in attacks:
        item["source_hint"] = f"Gerado automaticamente para {name}"
    return attacks


def _build_tormenta20_threat_data(
    *,
    name: str,
    world: str,
    threat_type: str,
    size: str,
    role: str,
    challenge_level: str,
    concept: str,
    has_mana_points: bool,
    displacement: str,
    is_boss: bool,
    attributes: JsonObject | None = None,
) -> JsonObject:
    normalized_challenge, nd_value = _parse_threat_nd_value(challenge_level)
    combat_stats = _calculate_threat_combat_stats(role, normalized_challenge, has_mana_points)
    threat_attributes = _default_threat_attributes(role)
    resistance_assignments = _default_threat_resistance_assignments(role)
    if isinstance(attributes, dict):
        for key, value in attributes.items():
            if key in threat_attributes and isinstance(value, int):
                threat_attributes[key] = max(-5, min(15, value))
    skills = _build_threat_skills(normalized_challenge, threat_attributes)
    attacks = _default_threat_attacks(name, combat_stats, role)
    ability_recommendation = _recommended_threat_ability_count(normalized_challenge, role)
    qualities = _build_threat_qualities(role, normalized_challenge, combat_stats)
    generated_abilities = _build_generated_threat_abilities(
        role=role,
        challenge_level=normalized_challenge,
        combat_stats=combat_stats,
        has_mana_points=has_mana_points,
    )
    boss_features = _build_generated_boss_features(
        challenge_level=normalized_challenge,
        combat_stats=combat_stats,
        has_mana_points=has_mana_points,
    ) if is_boss else {}
    return {
        "system": "tormenta20-threat-generator",
        "builder": "jarvez-threat-generator",
        "name": name,
        "world": world,
        "type": threat_type,
        "size": size,
        "role": role,
        "challenge_level": normalized_challenge,
        "challenge_tier": _threat_challenge_tier(nd_value),
        "concept": concept,
        "is_boss": is_boss,
        "has_mana_points": has_mana_points,
        "displacement": displacement,
        "combat_stats": combat_stats,
        "attributes": threat_attributes,
        "resistance_assignments": resistance_assignments,
        "skills": skills,
        "attacks": attacks,
        "ability_recommendation": ability_recommendation,
        "qualities": qualities,
        "generated_abilities": generated_abilities,
        "boss_features": boss_features,
        "treasure_level": "Padrao",
        "source_reference": "Inspired by Fichas de Nimb threat generator tables",
        "updated_at": _now_iso(),
    }


def _build_tormenta20_threat_markdown(threat: JsonObject) -> str:
    combat = threat.get("combat_stats") if isinstance(threat.get("combat_stats"), dict) else {}
    attrs = threat.get("attributes") if isinstance(threat.get("attributes"), dict) else {}
    resistance_assignments = threat.get("resistance_assignments") if isinstance(threat.get("resistance_assignments"), dict) else {}
    skills = threat.get("skills") if isinstance(threat.get("skills"), list) else []
    attacks = threat.get("attacks") if isinstance(threat.get("attacks"), list) else []
    qualities = threat.get("qualities") if isinstance(threat.get("qualities"), list) else []
    generated_abilities = threat.get("generated_abilities") if isinstance(threat.get("generated_abilities"), list) else []
    ability_recommendation = threat.get("ability_recommendation") if isinstance(threat.get("ability_recommendation"), dict) else {}
    boss_features = threat.get("boss_features") if isinstance(threat.get("boss_features"), dict) else {}
    reactions = boss_features.get("reactions") if isinstance(boss_features.get("reactions"), list) else []
    legendary_actions = boss_features.get("legendary_actions") if isinstance(boss_features.get("legendary_actions"), list) else []
    phases = boss_features.get("phases") if isinstance(boss_features.get("phases"), list) else []
    return "\n".join(
        [
            f"# Amea?a Tormenta20 - {threat.get('name', '')}",
            "",
            f"- Mundo: {threat.get('world', '')}",
            f"- Tipo: {threat.get('type', '')}",
            f"- Tamanho: {threat.get('size', '')}",
            f"- Papel: {threat.get('role', '')}",
            f"- ND: {threat.get('challenge_level', '')}",
            f"- Tier: {threat.get('challenge_tier', '')}",
            f"- Conceito: {threat.get('concept', '')}",
            f"- Builder: {threat.get('builder', '')}",
            "",
            "## Estatisticas de Combate",
            f"- Ataque base: {combat.get('attack_value')}",
            f"- Dano medio: {combat.get('average_damage')}",
            f"- Defesa: {combat.get('defense')}",
            f"- Fortitude forte: {combat.get('strong_save')}",
            f"- Reflexos medio: {combat.get('medium_save')}",
            f"- Vontade fraca: {combat.get('weak_save')}",
            f"- PV: {combat.get('hit_points')}",
            f"- CD padrao: {combat.get('standard_effect_dc')}",
            f"- PM: {combat.get('mana_points', 0)}",
            "",
            "## Resistencias",
            f"- Fortitude: {resistance_assignments.get('Fortitude', '')}",
            f"- Reflexos: {resistance_assignments.get('Reflexos', '')}",
            f"- Vontade: {resistance_assignments.get('Vontade', '')}",
            "",
            "## Atributos",
            *(f"- {key.capitalize()}: {value}" for key, value in attrs.items()),
            "",
            "## Pericias",
            *(
                f"- {item.get('name')}: {item.get('total')} ({item.get('attribute')})"
                for item in skills
                if isinstance(item, dict)
            ),
            "",
            "## Ataques Sugeridos",
            *(
                f"- {item.get('name')}: +{item.get('attack_bonus')} / {item.get('damage')} [{item.get('action_type')}]"
                for item in attacks
                if isinstance(item, dict)
            ),
            "",
            "## Recomendacao de Habilidades",
            f"- Minimo: {ability_recommendation.get('min', 0)}",
            f"- Maximo: {ability_recommendation.get('max', 0)}",
            "",
            "## Qualidades Sugeridas",
            *(f"- {item}" for item in qualities if str(item).strip()),
            "",
            "## Habilidades Geradas",
            *(
                f"- {item.get('name')} [{item.get('category')}]: {item.get('summary')}"
                + (f" (acao: {item.get('action_type')}, PM: {item.get('pm_cost')})" if isinstance(item, dict) else "")
                for item in generated_abilities
                if isinstance(item, dict)
            ),
            "",
            "## Reacoes de Chefe",
            *(
                f"- {item.get('name')}: {item.get('summary')} (usos/rodada: {item.get('uses_per_round')}, PM: {item.get('pm_cost')})"
                for item in reactions
                if isinstance(item, dict)
            ),
            "",
            "## Acoes Lendarias",
            *(
                f"- {item.get('name')} [{item.get('cost')}]: {item.get('summary')}"
                for item in legendary_actions
                if isinstance(item, dict)
            ),
            "",
            "## Fases",
            *(
                f"- {item.get('threshold')}: {item.get('summary')}"
                for item in phases
                if isinstance(item, dict)
            ),
            "",
            "## Derrota",
            str(boss_features.get("defeat_condition", "")).strip(),
        ]
    )


def _export_tormenta20_threat_pdf(threat: JsonObject, output_path: Path) -> tuple[bool, str | None]:
    if (
        SimpleDocTemplate is None
        or Table is None
        or TableStyle is None
        or Paragraph is None
        or Spacer is None
        or getSampleStyleSheet is None
        or ParagraphStyle is None
        or colors is None
        or A4 is None
        or mm is None
    ):
        return False, "reportlab unavailable"

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        styles = getSampleStyleSheet()
        styles.add(
            ParagraphStyle(
                name="ThreatTitle",
                parent=styles["Title"],
                fontName="Helvetica-Bold",
                fontSize=18,
                leading=22,
                textColor=colors.HexColor("#1f2430"),
                spaceAfter=4,
            )
        )
        styles.add(
            ParagraphStyle(
                name="ThreatMeta",
                parent=styles["BodyText"],
                fontName="Helvetica-Bold",
                fontSize=9,
                leading=12,
                textColor=colors.HexColor("#4f5b66"),
                spaceAfter=6,
            )
        )
        styles.add(
            ParagraphStyle(
                name="ThreatSection",
                parent=styles["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=10,
                leading=13,
                textColor=colors.white,
                backColor=colors.HexColor("#242b38"),
                borderPadding=(3, 5, 3),
                spaceBefore=8,
                spaceAfter=4,
            )
        )
        styles.add(
            ParagraphStyle(
                name="ThreatBody",
                parent=styles["BodyText"],
                fontName="Helvetica",
                fontSize=8.4,
                leading=10.5,
                spaceAfter=3,
            )
        )

        combat = threat.get("combat_stats") if isinstance(threat.get("combat_stats"), dict) else {}
        attrs = threat.get("attributes") if isinstance(threat.get("attributes"), dict) else {}
        resistance_assignments = threat.get("resistance_assignments") if isinstance(threat.get("resistance_assignments"), dict) else {}
        attacks = threat.get("attacks") if isinstance(threat.get("attacks"), list) else []
        skills = threat.get("skills") if isinstance(threat.get("skills"), list) else []
        qualities = threat.get("qualities") if isinstance(threat.get("qualities"), list) else []
        generated_abilities = threat.get("generated_abilities") if isinstance(threat.get("generated_abilities"), list) else []
        ability_recommendation = threat.get("ability_recommendation") if isinstance(threat.get("ability_recommendation"), dict) else {}
        boss_features = threat.get("boss_features") if isinstance(threat.get("boss_features"), dict) else {}
        reactions = boss_features.get("reactions") if isinstance(boss_features.get("reactions"), list) else []
        legendary_actions = boss_features.get("legendary_actions") if isinstance(boss_features.get("legendary_actions"), list) else []
        phases = boss_features.get("phases") if isinstance(boss_features.get("phases"), list) else []

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=14 * mm,
            leftMargin=14 * mm,
            topMargin=12 * mm,
            bottomMargin=12 * mm,
        )

        story: list[Any] = [
            Paragraph(str(threat.get("name", "Ameaca")), styles["ThreatTitle"]),
            Paragraph(
                f"ND {threat.get('challenge_level', '')} - {threat.get('role', '')} - {threat.get('type', '')} - {threat.get('size', '')}",
                styles["ThreatMeta"],
            ),
            Paragraph(f"Conceito: {str(threat.get('concept', '')).strip()}", styles["ThreatBody"]),
        ]

        summary = Table(
            [
                ["Ataque", str(combat.get("attack_value", "")), "Dano medio", str(combat.get("average_damage", "")), "Defesa", str(combat.get("defense", ""))],
                ["PV", str(combat.get("hit_points", "")), "PM", str(combat.get("mana_points", 0)), "CD", str(combat.get("standard_effect_dc", ""))],
                ["Forte", str(combat.get("strong_save", "")), "Media", str(combat.get("medium_save", "")), "Fraca", str(combat.get("weak_save", ""))],
            ],
            colWidths=[23 * mm, 16 * mm, 25 * mm, 18 * mm, 21 * mm, 16 * mm],
        )
        summary.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f6f8fb")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ced4da")),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.extend([summary, Spacer(1, 4)])

        story.append(Paragraph("Resistencias", styles["ThreatSection"]))
        for label in ("Fortitude", "Reflexos", "Vontade"):
            story.append(Paragraph(f"- {label}: {resistance_assignments.get(label, '')}", styles["ThreatBody"]))

        story.append(Paragraph("Atributos", styles["ThreatSection"]))
        attr_rows = [
            [key.capitalize(), str(value)]
            for key, value in attrs.items()
        ]
        attr_table = Table(attr_rows, colWidths=[35 * mm, 18 * mm])
        attr_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fbfcfe")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9dee3")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.extend([attr_table, Spacer(1, 4)])

        story.append(Paragraph("Pericias", styles["ThreatSection"]))
        for item in skills[:10]:
            if not isinstance(item, dict):
                continue
            story.append(
                Paragraph(
                    f"- {item.get('name')}: {item.get('total')} ({item.get('attribute')})",
                    styles["ThreatBody"],
                )
            )

        story.append(Paragraph("Ataques Sugeridos", styles["ThreatSection"]))
        for item in attacks[:6]:
            if not isinstance(item, dict):
                continue
            story.append(
                Paragraph(
                    f"- {item.get('name')}: +{item.get('attack_bonus')} / {item.get('damage')} [{item.get('action_type')}]",
                    styles["ThreatBody"],
                )
            )

        story.append(Paragraph("Recomendacao de Habilidades", styles["ThreatSection"]))
        story.append(Paragraph(f"- Minimo: {ability_recommendation.get('min', 0)}", styles["ThreatBody"]))
        story.append(Paragraph(f"- Maximo: {ability_recommendation.get('max', 0)}", styles["ThreatBody"]))

        if qualities:
            story.append(Paragraph("Qualidades", styles["ThreatSection"]))
            for item in qualities[:10]:
                text = str(item).strip()
                if text:
                    story.append(Paragraph(f"- {text}", styles["ThreatBody"]))

        if generated_abilities:
            story.append(Paragraph("Habilidades Geradas", styles["ThreatSection"]))
            for item in generated_abilities[:8]:
                if not isinstance(item, dict):
                    continue
                pm_cost = item.get("pm_cost", 0)
                suffix = f" (acao: {item.get('action_type')}, PM: {pm_cost})"
                story.append(
                    Paragraph(
                        f"- {item.get('name')} [{item.get('category')}]: {item.get('summary')}{suffix}",
                        styles["ThreatBody"],
                    )
                )

        if reactions:
            story.append(Paragraph("Reacoes de Chefe", styles["ThreatSection"]))
            for item in reactions[:6]:
                if not isinstance(item, dict):
                    continue
                story.append(
                    Paragraph(
                        f"- {item.get('name')}: {item.get('summary')} (usos/rodada: {item.get('uses_per_round')}, PM: {item.get('pm_cost')})",
                        styles["ThreatBody"],
                    )
                )

        if legendary_actions:
            story.append(Paragraph("Acoes Lendarias", styles["ThreatSection"]))
            for item in legendary_actions[:6]:
                if not isinstance(item, dict):
                    continue
                story.append(
                    Paragraph(
                        f"- {item.get('name')} [{item.get('cost')}]: {item.get('summary')}",
                        styles["ThreatBody"],
                    )
                )

        if phases:
            story.append(Paragraph("Fases", styles["ThreatSection"]))
            for item in phases[:4]:
                if not isinstance(item, dict):
                    continue
                story.append(
                    Paragraph(
                        f"- {item.get('threshold')}: {item.get('summary')}",
                        styles["ThreatBody"],
                    )
                )

        defeat_condition = str(boss_features.get("defeat_condition", "")).strip()
        if defeat_condition:
            story.append(Paragraph("Derrota", styles["ThreatSection"]))
            story.append(Paragraph(defeat_condition, styles["ThreatBody"]))

        def on_page(canvas, _doc):
            canvas.saveState()
            canvas.setStrokeColor(colors.HexColor("#d9dee3"))
            canvas.setLineWidth(0.6)
            canvas.line(_doc.leftMargin, A4[1] - 9 * mm, A4[0] - _doc.rightMargin, A4[1] - 9 * mm)
            canvas.line(_doc.leftMargin, 10 * mm, A4[0] - _doc.rightMargin, 10 * mm)
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(colors.HexColor("#5b6470"))
            canvas.drawString(_doc.leftMargin, 6.5 * mm, "Threat Sheet - Jarvez")
            canvas.drawRightString(A4[0] - _doc.rightMargin, 6.5 * mm, f"Pagina {canvas.getPageNumber()}")
            canvas.restoreState()

        doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    except Exception as error:
        return False, str(error)
    return True, None


def _normalize_class_name(raw_value: str) -> str:
    normalized = raw_value.strip().casefold()
    aliases = {
        "arcanista": "arcanista",
        "mago": "arcanista",
        "feiticeiro": "arcanista",
        "bruxo": "arcanista",
        "barbaro": "barbaro",
        "bardo": "bardo",
        "bucaneiro": "bucaneiro",
        "cacador": "cacador",
        "cavaleiro": "cavaleiro",
        "clerigo": "clerigo",
        "druida": "druida",
        "guerreiro": "guerreiro",
        "inventor": "inventor",
        "ladino": "ladino",
        "lutador": "lutador",
        "nobre": "nobre",
        "paladino": "paladino",
    }
    return aliases.get(normalized, normalized)


def _ability_modifier(score: int) -> int:
    return (int(score) - 10) // 2


def _tormenta20_class_profile(class_name: str) -> JsonObject:
    profiles: dict[str, JsonObject] = {
        "arcanista": {"pv_base": 8, "pm_base": 6, "key_ability": "inteligencia", "skills": ["Misticismo", "Conhecimento", "Vontade"]},
        "barbaro": {"pv_base": 20, "pm_base": 3, "key_ability": "forca", "skills": ["Atletismo", "Fortitude", "Sobrevivencia"]},
        "bardo": {"pv_base": 12, "pm_base": 4, "key_ability": "carisma", "skills": ["Atuacao", "Diplomacia", "Enganacao"]},
        "bucaneiro": {"pv_base": 16, "pm_base": 3, "key_ability": "destreza", "skills": ["Acrobacia", "Enganacao", "Reflexos"]},
        "cacador": {"pv_base": 16, "pm_base": 4, "key_ability": "sabedoria", "skills": ["Sobrevivencia", "Percepcao", "Pontaria"]},
        "cavaleiro": {"pv_base": 20, "pm_base": 3, "key_ability": "carisma", "skills": ["Fortitude", "Guerra", "Intimidacao"]},
        "clerigo": {"pv_base": 16, "pm_base": 5, "key_ability": "sabedoria", "skills": ["Religiao", "Vontade", "Cura"]},
        "druida": {"pv_base": 16, "pm_base": 4, "key_ability": "sabedoria", "skills": ["Sobrevivencia", "Adestramento", "Vontade"]},
        "guerreiro": {"pv_base": 20, "pm_base": 3, "key_ability": "forca", "skills": ["Luta", "Fortitude", "Iniciativa"]},
        "inventor": {"pv_base": 12, "pm_base": 4, "key_ability": "inteligencia", "skills": ["Oficio", "Conhecimento", "Investigacao"]},
        "ladino": {"pv_base": 12, "pm_base": 4, "key_ability": "destreza", "skills": ["Furtividade", "Ladinagem", "Reflexos"]},
        "lutador": {"pv_base": 20, "pm_base": 3, "key_ability": "forca", "skills": ["Luta", "Atletismo", "Fortitude"]},
        "nobre": {"pv_base": 16, "pm_base": 4, "key_ability": "carisma", "skills": ["Diplomacia", "Intuicao", "Nobreza"]},
        "paladino": {"pv_base": 20, "pm_base": 3, "key_ability": "carisma", "skills": ["Luta", "Vontade", "Religiao"]},
    }
    return profiles.get(_normalize_class_name(class_name), {"pv_base": 16, "pm_base": 3, "key_ability": "carisma", "skills": ["Percepcao", "Vontade", "Iniciativa"]})


def _build_tormenta20_sheet_data(
    *,
    name: str,
    world: str,
    race: str,
    class_name: str,
    level: int,
    concept: str,
    attrs: JsonObject,
) -> JsonObject:
    profile = _tormenta20_class_profile(class_name)
    con_mod = _ability_modifier(int(attrs["constituicao"]))
    dex_mod = _ability_modifier(int(attrs["destreza"]))
    key_ability = str(profile["key_ability"])
    key_mod = _ability_modifier(int(attrs.get(key_ability, 10)))
    half_level = max(0, level // 2)
    pv_total = max(1, int(profile["pv_base"]) + con_mod + max(0, level - 1) * max(1, int(profile["pv_base"]) // 2 + con_mod))
    pm_total = max(0, int(profile["pm_base"]) + max(0, level - 1) * max(1, int(profile["pm_base"]) // 2))
    defense = 10 + dex_mod + half_level
    initiative = dex_mod + half_level
    perception = _ability_modifier(int(attrs["sabedoria"])) + half_level
    attack = max(_ability_modifier(int(attrs["forca"])), dex_mod, key_mod) + half_level
    resistances = {
        "fortitude": con_mod + half_level,
        "reflexes": dex_mod + half_level,
        "will": _ability_modifier(int(attrs["sabedoria"])) + half_level,
    }
    return {
        "system": "tormenta20-base",
        "builder": "fallback",
        "name": name,
        "world": world,
        "race": race,
        "class_name": class_name,
        "origin": "acolyte",
        "level": level,
        "concept": concept,
        "attributes": attrs,
        "modifiers": {
            "forca": _ability_modifier(int(attrs["forca"])),
            "destreza": dex_mod,
            "constituicao": con_mod,
            "inteligencia": _ability_modifier(int(attrs["inteligencia"])),
            "sabedoria": _ability_modifier(int(attrs["sabedoria"])),
            "carisma": _ability_modifier(int(attrs["carisma"])),
        },
        "derived": {
            "pv": pv_total,
            "pm": pm_total,
            "defense": defense,
            "initiative": initiative,
            "perception": perception,
            "attack_base": attack,
            "resistances": resistances,
        },
        "trained_skills": [{"name": skill, "total": 0, "trained": True, "attribute": key_ability} for skill in list(profile["skills"])[:8]],
        "top_skills": [{"name": skill, "total": 0, "trained": True, "attribute": key_ability} for skill in list(profile["skills"])[:8]],
        "attacks": [],
        "build_steps": [],
        "recommended_skills": list(profile["skills"]),
        "serialized_character": {},
        "displacement": 9,
        "current_cargo": 0,
        "max_cargo": 10 + max(0, _ability_modifier(int(attrs["forca"]))) * 5,
        "carry_capacity": (10 + max(0, _ability_modifier(int(attrs["forca"]))) * 5) * 2,
        "proficiencies": [],
        "spells": [],
        "powers": [],
        "key_ability": key_ability,
        "updated_at": _now_iso(),
    }


def _normalize_sheet_data(sheet: JsonObject) -> JsonObject:
    attrs = sheet.get("attributes")
    if not isinstance(attrs, dict):
        attrs = {}
    raw_attr_values = [value for value in attrs.values() if isinstance(value, (int, float))]
    attrs_are_modifiers = bool(raw_attr_values) and all(-5 <= float(value) <= 10 for value in raw_attr_values)

    def _score_value(*keys: str) -> int:
        for key in keys:
            raw = attrs.get(key)
            if isinstance(raw, (int, float)):
                if attrs_are_modifiers:
                    return int(10 + int(raw) * 2)
                return int(raw)
        return 0

    normalized_attrs = {
        "forca": _score_value("forca", "strength"),
        "destreza": _score_value("destreza", "dexterity"),
        "constituicao": _score_value("constituicao", "constitution"),
        "inteligencia": _score_value("inteligencia", "intelligence"),
        "sabedoria": _score_value("sabedoria", "wisdom"),
        "carisma": _score_value("carisma", "charisma"),
    }
    modifiers = sheet.get("modifiers")
    if not isinstance(modifiers, dict):
        modifiers = {key: normalized_attrs[key] for key in normalized_attrs}

    derived = sheet.get("derived")
    if not isinstance(derived, dict):
        derived = {}

    normalized: JsonObject = dict(sheet)
    normalized["builder"] = str(normalized.get("builder") or "fallback")
    normalized["system"] = str(normalized.get("system") or "tormenta20-base")
    normalized["attributes"] = normalized_attrs
    normalized["modifiers"] = {
        "forca": int(modifiers.get("forca", normalized_attrs["forca"]) or 0),
        "destreza": int(modifiers.get("destreza", normalized_attrs["destreza"]) or 0),
        "constituicao": int(modifiers.get("constituicao", normalized_attrs["constituicao"]) or 0),
        "inteligencia": int(modifiers.get("inteligencia", normalized_attrs["inteligencia"]) or 0),
        "sabedoria": int(modifiers.get("sabedoria", normalized_attrs["sabedoria"]) or 0),
        "carisma": int(modifiers.get("carisma", normalized_attrs["carisma"]) or 0),
    }
    normalized["derived"] = {
        "pv": derived.get("pv"),
        "pm": derived.get("pm"),
        "defense": derived.get("defense"),
        "initiative": derived.get("initiative"),
        "perception": derived.get("perception"),
        "attack_base": derived.get("attack_base"),
        "resistances": derived.get("resistances", {}),
    }
    for key in ("trained_skills", "top_skills", "attacks", "build_steps", "recommended_skills", "proficiencies", "spells", "powers"):
        normalized[key] = _json_list(normalized.get(key))
    if not isinstance(normalized.get("serialized_character"), dict):
        normalized["serialized_character"] = {}
    normalized["displacement"] = int(normalized.get("displacement", 9) or 9)
    normalized["current_cargo"] = int(normalized.get("current_cargo", 0) or 0)
    normalized["max_cargo"] = int(normalized.get("max_cargo", 0) or 0)
    normalized["carry_capacity"] = int(normalized.get("carry_capacity", 0) or 0)
    normalized["updated_at"] = str(normalized.get("updated_at") or _now_iso())
    return normalized


def _build_tormenta20_sheet_markdown(sheet: JsonObject) -> str:
    attrs = sheet["attributes"]
    mods = sheet["modifiers"]
    derived = sheet["derived"]
    resistances = derived["resistances"]
    skills = sheet["recommended_skills"]
    return f"""# Ficha Tormenta20 Base - {sheet['name']}

- Mundo: {sheet['world']}
- Raca: {sheet['race']}
- Classe: {sheet['class_name']}
- Nivel: {sheet['level']}
- Conceito: {sheet['concept']}
- Atributo-chave sugerido: {sheet['key_ability']}

## Atributos
- Forca: {attrs['forca']} ({mods['forca']:+d})
- Destreza: {attrs['destreza']} ({mods['destreza']:+d})
- Constituicao: {attrs['constituicao']} ({mods['constituicao']:+d})
- Inteligencia: {attrs['inteligencia']} ({mods['inteligencia']:+d})
- Sabedoria: {attrs['sabedoria']} ({mods['sabedoria']:+d})
- Carisma: {attrs['carisma']} ({mods['carisma']:+d})

## Derivados
- PV: {derived['pv']}
- PM: {derived['pm']}
- Defesa base: {derived['defense']}
- Iniciativa base: {derived['initiative']}
- Percepcao base: {derived['perception']}
- Ataque base sugerido: {derived['attack_base']}

## Resistencias
- Fortitude: {resistances['fortitude']}
- Reflexos: {resistances['reflexes']}
- Vontade: {resistances['will']}

## Pericias Recomendadas
""" + "\n".join(f"- {skill}" for skill in skills) + """

## Ajustes pendentes
- Equipamentos, poderes e talentos dependem da construcao final.
- Revise a ficha antes de uso em mesa.
"""


def _infer_character_session_notes(messages: list[dict[str, str]]) -> JsonObject:
    notes: JsonObject = {
        "summary": "",
        "objectives": [],
        "relations": [],
        "secrets": [],
    }
    user_lines = [str(item.get("content", "")).strip() for item in messages if item.get("role") == "user"]
    assistant_lines = [str(item.get("content", "")).strip() for item in messages if item.get("role") == "assistant"]
    opening = " ".join(line for line in user_lines[:2] if line).strip()
    closing = " ".join(line for line in assistant_lines[-2:] if line).strip()
    notes["summary"] = _summarize_character_text(" ".join(part for part in [opening, closing] if part), max_len=320)

    for line in user_lines:
        folded = line.casefold()
        short_line = _summarize_character_text(line, max_len=180)
        if any(token in folded for token in ["objetivo", "quero", "preciso", "vamos", "missao"]):
            notes["objectives"].append(short_line)
        if any(token in folded for token in ["aliado", "inimigo", "confia", "odeia", "familia", "grupo"]):
            notes["relations"].append(short_line)
        if any(token in folded for token in ["segredo", "nao conte", "ninguem pode saber", "oculto"]):
            notes["secrets"].append(short_line)

    for key in ("objectives", "relations", "secrets"):
        unique: list[str] = []
        for item in notes[key][:3]:
            if item and item not in unique:
                unique.append(item)
        notes[key] = unique
    return notes


def _recording_key(participant_identity: str, room: str) -> str:
    return f"{participant_identity}:{room}"


def _safe_file_part(value: str) -> str:
    safe = re.sub(r"[^\w\-]+", "_", value, flags=re.UNICODE).strip("_")
    return safe or "sessao"


def _extract_history_since(session: Any | None, start_index: int) -> list[dict[str, str]]:
    history = getattr(session, "history", None) if session is not None else None
    items = getattr(history, "items", None)
    if not isinstance(items, list):
        return []

    extracted: list[dict[str, str]] = []
    for item in items[start_index:]:
        role = getattr(item, "role", None)
        if role not in {"user", "assistant"}:
            continue
        content = getattr(item, "content", None)
        text = ""
        if isinstance(content, list):
            text = " ".join(part for part in content if isinstance(part, str)).strip()
        elif isinstance(content, str):
            text = content.strip()
        if not text:
            continue
        extracted.append({"role": str(role), "content": text})
    return extracted


def _build_session_markdown(
    *,
    state: RPGSessionRecordingState,
    messages: list[dict[str, str]],
) -> str:
    lines = [
        f"# Sessao RPG: {state.title}",
        "",
        f"- Mundo: {state.world}",
        f"- Sala: {state.room}",
        f"- Participante: {state.participant_identity}",
        f"- Inicio: {state.started_at.isoformat()}",
        f"- Fim: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Transcricao",
        "",
    ]
    for msg in messages:
        speaker = "Jogador" if msg["role"] == "user" else "Jarvez"
        lines.append(f"**{speaker}:** {msg['content']}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _build_session_summary(title: str, messages: list[dict[str, str]], max_items: int = 8) -> str:
    user_msgs = [m["content"] for m in messages if m["role"] == "user"]
    assistant_msgs = [m["content"] for m in messages if m["role"] == "assistant"]
    highlights: list[str] = []
    for text in user_msgs[: max_items // 2]:
        if len(text) > 180:
            text = text[:180].rstrip() + "..."
        highlights.append(f"- Jogador: {text}")
    for text in assistant_msgs[: max_items - len(highlights)]:
        if len(text) > 180:
            text = text[:180].rstrip() + "..."
        highlights.append(f"- Jarvez: {text}")

    lines = [
        f"# Resumo da Sessao: {title}",
        "",
        f"- Total de falas: {len(messages)}",
        f"- Falas do jogador: {len(user_msgs)}",
        f"- Falas do Jarvez: {len(assistant_msgs)}",
        "",
        "## Destaques",
        "",
    ]
    lines.extend(highlights or ["- Sem eventos relevantes registrados."])
    return "\n".join(lines).strip() + "\n"


def _get_rpg_index() -> RPGKnowledgeIndex:
    global RPG_KNOWLEDGE_INDEX
    if RPG_KNOWLEDGE_INDEX is None:
        RPG_KNOWLEDGE_INDEX = RPGKnowledgeIndex(_rpg_db_path())
    return RPG_KNOWLEDGE_INDEX


def _normalize_whatsapp_to(raw_to: str) -> str:
    digits = re.sub(r"\D+", "", raw_to or "")
    if not digits:
        return ""
    if digits.startswith("0"):
        digits = digits.lstrip("0")
    if not digits.startswith(_whatsapp_default_country_code()):
        digits = f"{_whatsapp_default_country_code()}{digits}"
    return digits


def _whatsapp_api_request(
    method: str,
    endpoint: str,
    *,
    body: JsonObject | None = None,
    timeout: float = 10.0,
) -> tuple[JsonObject | list[Any] | None, ActionResult | None]:
    token = _whatsapp_access_token()
    if not token:
        return None, ActionResult(
            success=False,
            message="WhatsApp nao configurado: faltando WHATSAPP_ACCESS_TOKEN.",
            error="missing token",
        )

    url = f"{WHATSAPP_GRAPH_BASE}/{_whatsapp_graph_version().strip('/')}/{endpoint.lstrip('/')}"
    headers = {"Authorization": f"Bearer {token}"}
    if body is not None:
        headers["Content-Type"] = "application/json"

    try:
        response = requests.request(method, url, headers=headers, json=body, timeout=timeout)
    except requests.RequestException as error:
        return None, ActionResult(success=False, message="Erro de comunicacao com WhatsApp.", error=str(error))

    if not (200 <= response.status_code < 300):
        return None, ActionResult(
            success=False,
            message=f"WhatsApp retornou erro ({response.status_code}).",
            error=response.text[:500],
        )

    if not response.content:
        return {}, None
    try:
        payload = response.json()
        if isinstance(payload, (dict, list)):
            return payload, None
        return {}, None
    except ValueError:
        return {}, None


def _whatsapp_send_message(payload: JsonObject) -> ActionResult:
    phone_number_id = _whatsapp_phone_number_id()
    if not phone_number_id:
        return ActionResult(
            success=False,
            message="WhatsApp nao configurado: faltando WHATSAPP_PHONE_NUMBER_ID.",
            error="missing phone number id",
        )
    response_payload, error = _whatsapp_api_request("POST", f"{phone_number_id}/messages", body=payload)
    if error is not None:
        return error
    return ActionResult(success=True, message="Mensagem enviada no WhatsApp.", data={"whatsapp_response": response_payload})


def _whatsapp_read_inbox() -> list[JsonObject]:
    path = _whatsapp_inbox_path()
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


async def _build_jarvez_tts_file(text: str) -> tuple[Path | None, ActionResult | None]:
    tts_text = text.strip()
    if not tts_text:
        return None, ActionResult(success=False, message="Texto vazio para audio.", error="empty text")
    if len(tts_text) > 1200:
        return None, ActionResult(success=False, message="Texto muito longo para audio WhatsApp.", error="text too long")
    if edge_tts is None:
        return None, ActionResult(
            success=False,
            message="TTS indisponivel no servidor. Instale edge-tts.",
            error="edge-tts not installed",
        )

    temp_dir = Path(tempfile.gettempdir()) / "jarvez_tts"
    temp_dir.mkdir(parents=True, exist_ok=True)
    target = temp_dir / f"jarvez_whatsapp_{int(time.time() * 1000)}.mp3"
    try:
        voice_name = os.getenv("JARVEZ_TTS_VOICE", "pt-BR-AntonioNeural").strip() or "pt-BR-AntonioNeural"
        communicate = edge_tts.Communicate(text=tts_text, voice=voice_name)
        await communicate.save(str(target))
        return target, None
    except Exception as error:
        return None, ActionResult(success=False, message="Falha ao gerar audio TTS.", error=str(error))


def _upload_whatsapp_media(file_path: Path, mime_type: str = "audio/mpeg") -> tuple[str | None, ActionResult | None]:
    phone_number_id = _whatsapp_phone_number_id()
    token = _whatsapp_access_token()
    if not phone_number_id or not token:
        return None, ActionResult(
            success=False,
            message="WhatsApp nao configurado para upload de midia.",
            error="missing whatsapp credentials",
        )
    url = f"{WHATSAPP_GRAPH_BASE}/{_whatsapp_graph_version().strip('/')}/{phone_number_id}/media"
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": (file_path.name, file_path.read_bytes(), mime_type)}
    data = {"messaging_product": "whatsapp", "type": "audio"}
    try:
        response = requests.post(url, headers=headers, files=files, data=data, timeout=20)
    except requests.RequestException as error:
        return None, ActionResult(success=False, message="Erro no upload de audio para WhatsApp.", error=str(error))
    if not (200 <= response.status_code < 300):
        return None, ActionResult(
            success=False,
            message=f"WhatsApp recusou upload de audio ({response.status_code}).",
            error=response.text[:500],
        )
    payload = response.json() if response.content else {}
    media_id = str(payload.get("id", "")).strip() if isinstance(payload, dict) else ""
    if not media_id:
        return None, ActionResult(success=False, message="WhatsApp nao retornou media id.", error="missing media id")
    return media_id, None


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

    if name.startswith("rpg_"):
        current_mode = get_persona_mode(ctx.participant_identity, ctx.room)
        if current_mode != "rpg":
            result = ActionResult(
                success=False,
                message="As ferramentas de RPG ficam disponiveis apenas no modo RPG.",
                data={
                    "persona_mode_required": "rpg",
                    "current_persona_mode": current_mode,
                },
                error="rpg_mode_required",
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

    if spec.requires_auth and not _is_authenticated(ctx.participant_identity, ctx.room):
        result = ActionResult(
            success=False,
            message="Esta acao exige modo privado. So peca PIN quando o usuario realmente quiser acessar algo privado ou sensivel.",
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


async def _list_persona_modes(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    current_mode = get_persona_mode(ctx.participant_identity, ctx.room)
    return ActionResult(
        success=True,
        message="Modos de personalidade disponiveis listados.",
        data={
            "available_persona_modes": PERSONA_MODES,
            "current_persona_mode": current_mode,
            **_persona_payload(current_mode),
        },
    )


async def _get_persona_mode_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    current_mode = get_persona_mode(ctx.participant_identity, ctx.room)
    profile = PERSONA_MODES.get(current_mode, PERSONA_MODES[DEFAULT_PERSONA_MODE])
    return ActionResult(
        success=True,
        message=f"Modo atual: {profile.get('label', current_mode)}.",
        data={"current_persona_mode": current_mode, **_persona_payload(current_mode)},
    )


async def _set_persona_mode_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    requested_mode = str(params.get("mode", "")).strip()
    normalized = _normalize_persona_mode(requested_mode)
    if normalized not in PERSONA_MODES:
        available = ", ".join(sorted(PERSONA_MODES.keys()))
        return ActionResult(
            success=False,
            message=f"Modo '{requested_mode}' nao existe. Use um destes: {available}.",
            data={"available_modes": sorted(PERSONA_MODES.keys())},
            error="invalid persona mode",
        )

    applied = set_persona_mode(ctx.participant_identity, ctx.room, normalized)
    if applied != "rpg":
        clear_active_character(ctx.participant_identity, ctx.room)
    profile = PERSONA_MODES.get(applied, PERSONA_MODES[DEFAULT_PERSONA_MODE])
    return ActionResult(
        success=True,
        message=f"Modo de personalidade alterado para {profile.get('label', applied)}.",
        data={
            "applied_persona_mode": applied,
            "style_guidance": profile.get("style"),
            **_persona_payload(applied),
        },
    )


async def _rpg_get_character_mode(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    active = get_active_character(ctx.participant_identity, ctx.room)
    if active is None:
        return ActionResult(
            success=True,
            message="Nenhum personagem ativo no momento.",
            data=_active_character_payload(ctx.participant_identity, ctx.room),
        )
    return ActionResult(
        success=True,
        message=f"Personagem ativo: {active.name}.",
        data=_active_character_payload(ctx.participant_identity, ctx.room),
    )


async def _rpg_assume_character(params: JsonObject, ctx: ActionContext) -> ActionResult:
    name = str(params.get("name", "")).strip()
    source = str(params.get("source", "auto")).strip().lower() or "auto"
    section_name = str(params.get("section_name", "")).strip() or None
    visual_reference_url = str(params.get("referencia_visual_url", "")).strip() or None
    pinterest_pin_url = str(params.get("pinterest_pin_url", "")).strip() or None
    visual_description = str(params.get("descricao_visual", "")).strip() or None
    if not name:
        return ActionResult(success=False, message="Informe o nome do personagem.", error="missing name")

    resolved_source = source if source in {"auto", "onenote", "pdf", "manual"} else "auto"
    summary = ""
    profile: JsonObject = {}
    page_id: str | None = None
    page_title: str | None = None
    resolved_section_name: str | None = None
    one_note_url: str | None = None
    used_source = "manual"
    one_note_sync_status = "skipped"
    one_note_sync_error: str | None = None
    existing_sheet, existing_sheet_path = _find_existing_character_sheet_by_name(name)
    sheet_json_path: str | None = str(existing_sheet_path.resolve()) if existing_sheet_path else None
    sheet_markdown_path: str | None = None
    sheet_pdf_path: str | None = None
    if existing_sheet_path:
        md_candidate = existing_sheet_path.with_suffix(".md")
        if md_candidate.exists():
            sheet_markdown_path = str(md_candidate.resolve())
        pdf_candidate = _rpg_character_pdfs_dir() / existing_sheet_path.parent.name / f"{existing_sheet_path.stem}.pdf"
        if pdf_candidate.exists():
            sheet_pdf_path = str(pdf_candidate.resolve())
    if existing_sheet and not summary:
        derived = existing_sheet.get("derived", {}) if isinstance(existing_sheet.get("derived"), dict) else {}
        class_label = str(existing_sheet.get("class_name", "")).strip()
        race_label = str(existing_sheet.get("race", "")).strip()
        summary = _summarize_character_text(
            " ".join(
                part
                for part in [
                    f"{name}.",
                    f"Raca {race_label}." if race_label else "",
                    f"Classe {class_label}." if class_label else "",
                    f"Nivel {existing_sheet.get('level')}." if existing_sheet.get("level") else "",
                    f"Conceito: {existing_sheet.get('concept')}." if existing_sheet.get("concept") else "",
                    f"Defesa {derived.get('defense')}." if derived.get("defense") is not None else "",
                ]
                if part
            )
        )
        profile = {
            "summary": summary,
            "sheet_reference": {
                "sheet_json_path": sheet_json_path,
                "sheet_markdown_path": sheet_markdown_path,
                "sheet_pdf_path": sheet_pdf_path,
                "sheet_builder_source": existing_sheet.get("builder"),
            },
        }
        used_source = "sheet"

    if resolved_source in {"auto", "onenote"}:
        match = _find_onenote_character_page(name, section_name)
        if match and isinstance(match, dict):
            page = match.get("page")
            if isinstance(page, dict):
                page_id = str(page.get("id", "")).strip() or None
                page_title = str(page.get("title", "")).strip() or None
                resolved_section_name = str(match.get("section_name", "")).strip() or None
                links = page.get("links", {})
                if isinstance(links, dict):
                    one_note = links.get("oneNoteClientUrl")
                    if isinstance(one_note, dict):
                        one_note_url = str(one_note.get("href", "")).strip() or None
                if page_id:
                    encoded_page_id = _quote_path_segment(page_id)
                    content, error = _onenote_api_request(
                        "GET",
                        f"me/onenote/pages/{encoded_page_id}/content",
                        extra_headers={"Accept": "text/html"},
                    )
                    if error is None:
                        html_content = str(content or "")
                        profile = _extract_onenote_character_profile(html_content)
                        summary = str(profile.get("summary", "")).strip() or _summarize_character_text(
                            _strip_html_for_preview(html_content)
                        )
                        if not visual_reference_url:
                            visual_reference_url = str(profile.get("visual_reference_url", "")).strip() or None
                        if not pinterest_pin_url:
                            pinterest_pin_url = str(profile.get("pinterest_pin_url", "")).strip() or None
                        if not visual_description:
                            visual_description = str(profile.get("visual_description", "")).strip() or None
                        used_source = "onenote"

    if not summary and resolved_source in {"auto", "pdf"}:
        results = _get_rpg_index().search(name, limit=3)
        if results:
            first = results[0]
            summary = _summarize_character_text(str(first.get("content", "")))
            profile = {
                "summary": summary,
                "knowledge_limits": "Baseado em trechos indexados de PDFs e lore local. Se faltar informacao, assuma incerteza.",
            }
            used_source = "pdf"

    if not summary:
        summary = (
            f"Assuma o papel de {name}. Mantenha consistencia de personalidade, voz e objetivos. "
            "Se faltar contexto, improvise com coerencia e confirme lacunas quando necessario."
        )
        used_source = "manual" if resolved_source == "manual" else resolved_source
        profile = {
            "summary": summary,
            "knowledge_limits": "Contexto manual e incompleto. Nao invente fatos canonicos sem marcar como improviso.",
        }

    page_sync_payload, page_sync_error = _ensure_onenote_character_page(
        title=name,
        summary=summary,
        source=used_source,
        preferred_section_name=resolved_section_name or section_name,
        visual_reference_url=visual_reference_url,
        pinterest_pin_url=pinterest_pin_url,
        visual_description=visual_description,
    )
    if page_sync_error is None and isinstance(page_sync_payload, dict):
        page_id = str(page_sync_payload.get("page_id", "")).strip() or page_id
        page_title = str(page_sync_payload.get("title", "")).strip() or page_title or name
        resolved_section_name = str(page_sync_payload.get("section_name", "")).strip() or resolved_section_name
        one_note_url = str(page_sync_payload.get("one_note_url", "")).strip() or one_note_url
        one_note_sync_status = "created" if page_sync_payload.get("created") else "reused"
    elif page_sync_error is not None:
        one_note_sync_status = "failed"
        one_note_sync_error = page_sync_error.message

    if visual_reference_url and not profile.get("visual_reference_url"):
        profile["visual_reference_url"] = visual_reference_url
    if pinterest_pin_url and not profile.get("pinterest_pin_url"):
        profile["pinterest_pin_url"] = pinterest_pin_url
    if visual_description and not profile.get("visual_description"):
        profile["visual_description"] = visual_description
    if summary and not profile.get("summary"):
        profile["summary"] = summary
    prompt_hint = _build_character_prompt_hint(name, summary, profile)

    active = ActiveCharacterMode(
        name=name,
        source=used_source,
        summary=summary,
        activated_at=_now_iso(),
        page_id=page_id,
        page_title=page_title,
        section_name=resolved_section_name,
        one_note_url=one_note_url,
        visual_reference_url=visual_reference_url,
        pinterest_pin_url=pinterest_pin_url,
        visual_description=visual_description,
        profile=profile,
        prompt_hint=prompt_hint,
        sheet_json_path=sheet_json_path,
        sheet_markdown_path=sheet_markdown_path,
        sheet_pdf_path=sheet_pdf_path,
    )
    set_active_character(ctx.participant_identity, ctx.room, active)
    return ActionResult(
        success=True,
        message=(
            f"Modo personagem ativado para {name}."
            if one_note_sync_status != "failed"
            else f"Modo personagem ativado para {name}, mas a pagina dedicada no OneNote nao foi sincronizada."
        ),
        data={
            **_active_character_payload(ctx.participant_identity, ctx.room),
            "character_prompt_hint": prompt_hint,
            "one_note_character_page_sync": one_note_sync_status,
            "one_note_character_page_error": one_note_sync_error,
        },
    )


async def _rpg_clear_character_mode(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    active = get_active_character(ctx.participant_identity, ctx.room)
    clear_active_character(ctx.participant_identity, ctx.room)
    if active is None:
        return ActionResult(
            success=True,
            message="Nenhum modo personagem estava ativo.",
            data={**_active_character_payload(ctx.participant_identity, ctx.room), "active_character_cleared": True},
        )
    return ActionResult(
        success=True,
        message=f"Modo personagem encerrado para {active.name}.",
        data={**_active_character_payload(ctx.participant_identity, ctx.room), "active_character_cleared": True},
    )


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

    embedding = get_recent_voice_embedding(ctx.participant_identity)
    if embedding is None:
        return ActionResult(
            success=False,
            message="Nao detectei audio suficiente. Fale por 2 a 4 segundos e tente novamente.",
            error="insufficient voice sample",
        )

    VOICE_PROFILE_STORE.enroll_profile(name=name, participant_identity=ctx.participant_identity, embedding=embedding)
    return ActionResult(
        success=True,
        message=f"Perfil de voz '{name}' salvo com sucesso.",
        data={"voice_embedding_size": len(embedding)},
    )


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

    embedding = get_recent_voice_embedding(ctx.participant_identity)
    if embedding is None:
        return ActionResult(
            success=False,
            message="Nao detectei audio suficiente para verificar sua voz. Fale por alguns segundos e repita.",
            error="insufficient voice sample",
            data={"step_up_required": True},
        )

    verify = VOICE_PROFILE_STORE.verify_identity(participant_identity=ctx.participant_identity, embedding=embedding)
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
                "voice_method": verify.method,
                "compared_profiles": verify.compared_profiles,
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
                "voice_method": verify.method,
                "compared_profiles": verify.compared_profiles,
                **_security_status_payload(ctx.participant_identity, ctx.room),
            },
            error="voice_step_up_required",
        )

    _clear_authentication(ctx.participant_identity)
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


async def _spotify_status(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    _spotify_initialize_cache()
    me, error = _spotify_api_request("GET", "me")
    if error is not None:
        return error

    devices_payload, _ = _spotify_api_request("GET", "me/player/devices")
    devices = devices_payload.get("devices", []) if isinstance(devices_payload, dict) else []
    active_devices = []
    if isinstance(devices, list):
        active_devices = [str(d.get("name", "")) for d in devices if isinstance(d, dict) and d.get("is_active")]

    return ActionResult(
        success=True,
        message="Spotify conectado e pronto para uso.",
        data={
            "spotify_connected": True,
            "user_id": me.get("id") if isinstance(me, dict) else None,
            "display_name": me.get("display_name") if isinstance(me, dict) else None,
            "active_devices": active_devices,
        },
    )


async def _spotify_get_devices(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    payload, error = _spotify_api_request("GET", "me/player/devices")
    if error is not None:
        return error
    devices = payload.get("devices", []) if isinstance(payload, dict) else []
    if not isinstance(devices, list):
        devices = []
    mapped = [
        {
            "id": str(device.get("id", "")),
            "name": str(device.get("name", "")),
            "type": str(device.get("type", "")),
            "is_active": bool(device.get("is_active")),
            "volume_percent": device.get("volume_percent"),
        }
        for device in devices
        if isinstance(device, dict)
    ]
    return ActionResult(success=True, message=f"{len(mapped)} device(s) Spotify encontrados.", data={"devices": mapped})


async def _spotify_transfer_playback(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    requested_device_name = str(params.get("device_name", "")).strip() or None
    requested_device_id = str(params.get("device_id", "")).strip() or None
    play_now = bool(params.get("play", True))
    device, error = _spotify_find_device(requested_device_name, requested_device_id)
    if error is not None:
        return error
    if device is None:
        return ActionResult(success=False, message="Nao consegui resolver o device Spotify.", error="device not found")

    _, request_error = _spotify_api_request(
        "PUT",
        "me/player",
        body={"device_ids": [str(device.get("id"))], "play": play_now},
    )
    if request_error is not None:
        return request_error

    return ActionResult(
        success=True,
        message=f"Playback transferido para {device.get('name', 'device desconhecido')}.",
        data={"device_id": device.get("id"), "device_name": device.get("name"), "is_active": True},
    )


async def _spotify_play(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    requested_device_name = str(params.get("device_name", "")).strip() or str(
        os.getenv("SPOTIFY_DEFAULT_DEVICE_NAME", "")
    ).strip() or None
    requested_device_id = str(params.get("device_id", "")).strip() or None
    query = str(params.get("query", "")).strip()
    uri = str(params.get("uri", "")).strip()

    if requested_device_name or requested_device_id:
        transfer_result = await _spotify_transfer_playback(
            {"device_name": requested_device_name, "device_id": requested_device_id, "play": True},
            ctx,
        )
        if not transfer_result.success:
            return transfer_result

    resolved_uri = uri
    resolved_title = None
    if query and not resolved_uri:
        search_payload, search_error = _spotify_api_request(
            "GET",
            "search",
            params={"q": query, "type": "track", "limit": 1},
        )
        if search_error is not None:
            return search_error
        tracks = search_payload.get("tracks", {}).get("items", []) if isinstance(search_payload, dict) else []
        if not isinstance(tracks, list) or not tracks:
            return ActionResult(success=False, message=f"Nao encontrei musica para '{query}'.", error="track not found")
        first = tracks[0]
        if not isinstance(first, dict):
            return ActionResult(success=False, message=f"Nao encontrei musica para '{query}'.", error="track not found")
        resolved_uri = str(first.get("uri", "")).strip()
        artist_names = ", ".join(
            str(artist.get("name", "")) for artist in first.get("artists", []) if isinstance(artist, dict)
        )
        resolved_title = f"{first.get('name', 'Faixa')} - {artist_names}".strip(" -")

    body: JsonObject | None = None
    if resolved_uri:
        body = {"uris": [resolved_uri]}

    _, play_error = _spotify_api_request("PUT", "me/player/play", body=body)
    if play_error is not None:
        return play_error

    if resolved_uri:
        return ActionResult(
            success=True,
            message=f"Tocando agora: {resolved_title or resolved_uri}.",
            data={"uri": resolved_uri, "title": resolved_title},
        )
    return ActionResult(success=True, message="Playback retomado no Spotify.")


async def _spotify_pause(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    _, error = _spotify_api_request("PUT", "me/player/pause")
    if error is not None:
        return error
    return ActionResult(success=True, message="Playback pausado.")


async def _spotify_next_track(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    _, error = _spotify_api_request("POST", "me/player/next")
    if error is not None:
        return error
    return ActionResult(success=True, message="Faixa avancada.")


async def _spotify_previous_track(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    _, error = _spotify_api_request("POST", "me/player/previous")
    if error is not None:
        return error
    return ActionResult(success=True, message="Voltando para a faixa anterior.")


async def _spotify_set_volume(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    volume = int(params.get("volume_percent", 50))
    requested_device_name = str(params.get("device_name", "")).strip() or None
    requested_device_id = str(params.get("device_id", "")).strip() or None
    request_params: JsonObject = {"volume_percent": volume}

    if requested_device_name or requested_device_id:
        device, error = _spotify_find_device(requested_device_name, requested_device_id)
        if error is not None:
            return error
        if device and device.get("id"):
            request_params["device_id"] = str(device.get("id"))

    _, request_error = _spotify_api_request("PUT", "me/player/volume", params=request_params)
    if request_error is not None:
        return request_error
    return ActionResult(success=True, message=f"Volume do Spotify ajustado para {volume}%.")


async def _spotify_create_surprise_playlist(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    playlist_name = str(params.get("name", "")).strip() or f"Jarvez Surprise {datetime.now().strftime('%Y-%m-%d')}"
    public = bool(params.get("public", False))

    me_payload, me_error = _spotify_api_request("GET", "me")
    if me_error is not None:
        return me_error
    user_id = str(me_payload.get("id", "")).strip() if isinstance(me_payload, dict) else ""
    if not user_id:
        return ActionResult(success=False, message="Nao consegui identificar sua conta Spotify.", error="missing user id")

    top_tracks_payload, _ = _spotify_api_request(
        "GET",
        "me/top/tracks",
        params={"time_range": "long_term", "limit": 20},
    )
    selected_uris = _spotify_pick_surprise_tracks(top_tracks_payload if isinstance(top_tracks_payload, dict) else None)

    playlist_payload, create_error = _spotify_api_request(
        "POST",
        f"users/{user_id}/playlists",
        body={
            "name": playlist_name,
            "description": "Playlist surpresa criada pelo Jarvez.",
            "public": public,
        },
    )
    if create_error is not None:
        return create_error

    playlist_id = str(playlist_payload.get("id", "")).strip() if isinstance(playlist_payload, dict) else ""
    if not playlist_id:
        return ActionResult(success=False, message="Spotify nao retornou id da playlist criada.", error="playlist id missing")

    _, add_error = _spotify_api_request("POST", f"playlists/{playlist_id}/tracks", body={"uris": selected_uris})
    if add_error is not None:
        return add_error

    playlist_url = ""
    if isinstance(playlist_payload, dict):
        external_urls = playlist_payload.get("external_urls", {})
        if isinstance(external_urls, dict):
            playlist_url = str(external_urls.get("spotify", ""))

    return ActionResult(
        success=True,
        message=f"Playlist surpresa criada: {playlist_name}.",
        data={
            "playlist_id": playlist_id,
            "playlist_name": playlist_name,
            "playlist_url": playlist_url,
            "tracks_added": len(selected_uris),
            "tracks": selected_uris,
        },
    )


async def _onenote_status(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    _onenote_initialize_cache()
    me_payload, me_error = _onenote_api_request("GET", "me")
    if me_error is not None:
        return me_error

    notebooks_payload, notebooks_error = _onenote_api_request("GET", "me/onenote/notebooks", params={"$top": 20})
    if notebooks_error is not None:
        return notebooks_error

    notebooks: list[JsonObject] = []
    if isinstance(notebooks_payload, dict):
        values = notebooks_payload.get("value", [])
        if isinstance(values, list):
            notebooks = [item for item in values if isinstance(item, dict)]

    return ActionResult(
        success=True,
        message="OneNote conectado e pronto para uso.",
        data={
            "onenote_connected": True,
            "display_name": me_payload.get("displayName") if isinstance(me_payload, dict) else None,
            "user_principal_name": me_payload.get("userPrincipalName") if isinstance(me_payload, dict) else None,
            "notebooks_count": len(notebooks),
            "notebooks": [
                {"id": str(nb.get("id", "")), "displayName": str(nb.get("displayName", ""))}
                for nb in notebooks[:10]
            ],
        },
    )


async def _onenote_list_notebooks(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    payload, error = _onenote_api_request("GET", "me/onenote/notebooks", params={"$top": 100})
    if error is not None:
        return error
    notebooks = payload.get("value", []) if isinstance(payload, dict) else []
    if not isinstance(notebooks, list):
        notebooks = []

    query = str(params.get("query", "")).strip().casefold()
    mapped: list[JsonObject] = []
    for notebook in notebooks:
        if not isinstance(notebook, dict):
            continue
        display_name = str(notebook.get("displayName", "")).strip()
        if query and query not in display_name.casefold():
            continue
        mapped.append(
            {
                "id": str(notebook.get("id", "")),
                "displayName": display_name,
                "createdDateTime": notebook.get("createdDateTime"),
                "lastModifiedDateTime": notebook.get("lastModifiedDateTime"),
                "isDefault": bool(notebook.get("isDefault")),
            }
        )
    limited = mapped[:20]
    return ActionResult(
        success=True,
        message=f"{len(mapped)} caderno(s) OneNote encontrado(s).",
        data={
            "notebooks": limited,
            "total_found": len(mapped),
            "truncated": len(mapped) > len(limited),
        },
    )


async def _onenote_list_sections(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    payload, error = _onenote_api_request("GET", "me/onenote/sections", params={"$top": 100})
    if error is not None:
        return error
    sections = payload.get("value", []) if isinstance(payload, dict) else []
    if not isinstance(sections, list):
        sections = []

    notebook_name = str(params.get("notebook_name", "")).strip().casefold()
    notebook_id = str(params.get("notebook_id", "")).strip()
    mapped: list[JsonObject] = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        parent_name = ""
        parent_id = ""
        parent = section.get("parentNotebook")
        if isinstance(parent, dict):
            parent_name = str(parent.get("displayName", ""))
            parent_id = str(parent.get("id", ""))
        if notebook_name and notebook_name not in parent_name.casefold():
            continue
        if notebook_id and notebook_id != parent_id:
            continue
        mapped.append(
            {
                "id": str(section.get("id", "")),
                "displayName": str(section.get("displayName", "")),
                "createdDateTime": section.get("createdDateTime"),
                "lastModifiedDateTime": section.get("lastModifiedDateTime"),
                "parentNotebook": parent_name,
                "parentNotebookId": parent_id,
            }
        )
    limited = mapped[:20]
    return ActionResult(
        success=True,
        message=f"{len(mapped)} secao(oes) OneNote encontradas.",
        data={
            "sections": limited,
            "total_found": len(mapped),
            "truncated": len(mapped) > len(limited),
        },
    )


async def _onenote_list_pages(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    section_id = str(params.get("section_id", "")).strip()
    section_name = str(params.get("section_name", "")).strip().casefold()
    title_query = str(params.get("query", "")).strip().casefold()

    if not section_id and not section_name:
        return ActionResult(
            success=False,
            message="Informe section_id ou section_name para listar paginas com seguranca.",
            error="missing section",
        )

    sections_payload, sections_error = _onenote_api_request("GET", "me/onenote/sections", params={"$top": 100})
    if sections_error is not None:
        return sections_error
    sections = sections_payload.get("value", []) if isinstance(sections_payload, dict) else []
    if not isinstance(sections, list):
        sections = []

    target_section: JsonObject | None = None
    for section in sections:
        if not isinstance(section, dict):
            continue
        current_id = str(section.get("id", "")).strip()
        current_name = str(section.get("displayName", "")).strip()
        if section_id and current_id == section_id:
            target_section = section
            break
        if section_name and section_name in current_name.casefold():
            target_section = section
            break

    if target_section is None:
        return ActionResult(
            success=False,
            message="Nao encontrei a secao OneNote informada.",
            error="section not found",
        )

    target_section_id = str(target_section.get("id", "")).strip()
    target_section_name = str(target_section.get("displayName", "")).strip()
    encoded_section_id = _quote_path_segment(target_section_id)
    pages_payload, pages_error = _onenote_api_request(
        "GET",
        f"me/onenote/sections/{encoded_section_id}/pages",
        params={"$top": 100},
    )
    if pages_error is not None:
        return pages_error
    pages = pages_payload.get("value", []) if isinstance(pages_payload, dict) else []
    if not isinstance(pages, list):
        pages = []

    mapped: list[JsonObject] = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        title = str(page.get("title", "")).strip()
        if title_query and title_query not in title.casefold():
            continue
        mapped.append(
            {
                "id": str(page.get("id", "")),
                "title": title,
                "createdDateTime": page.get("createdDateTime"),
                "lastModifiedDateTime": page.get("lastModifiedDateTime"),
                "contentUrl": page.get("contentUrl"),
                "sectionId": target_section_id,
                "sectionName": target_section_name,
            }
        )

    limited = mapped[:20]
    return ActionResult(
        success=True,
        message=f"{len(mapped)} pagina(s) encontradas na secao {target_section_name}.",
        data={
            "pages": limited,
            "sectionId": target_section_id,
            "sectionName": target_section_name,
            "total_found": len(mapped),
            "truncated": len(mapped) > len(limited),
        },
    )


async def _onenote_search_pages(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    query = (
        str(params.get("query", "")).strip()
        or str(params.get("title", "")).strip()
        or str(params.get("name", "")).strip()
    )
    if not query:
        return ActionResult(success=False, message="Informe uma busca para OneNote.", error="missing query")

    section_id = str(params.get("section_id", "")).strip()
    section_name = str(params.get("section_name", "")).strip().casefold()

    sections_payload, sections_error = _onenote_api_request("GET", "me/onenote/sections", params={"$top": 100})
    if sections_error is not None:
        return sections_error
    sections = sections_payload.get("value", []) if isinstance(sections_payload, dict) else []
    if not isinstance(sections, list):
        sections = []

    filtered_sections: list[JsonObject] = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        current_section_id = str(section.get("id", "")).strip()
        current_section_name = str(section.get("displayName", "")).strip()
        if section_id and section_id != current_section_id:
            continue
        if section_name and section_name not in current_section_name.casefold():
            continue
        filtered_sections.append(section)

    if not filtered_sections:
        return ActionResult(
            success=False,
            message="Nao encontrei secao OneNote compativel para fazer a busca.",
            data={"query": query},
            error="section not found",
        )

    q = query.casefold()
    filtered = []
    for section in filtered_sections[:40]:
        current_section_id = str(section.get("id", "")).strip()
        current_section_name = str(section.get("displayName", "")).strip()
        encoded_section_id = _quote_path_segment(current_section_id)
        pages_payload, pages_error = _onenote_api_request(
            "GET",
            f"me/onenote/sections/{encoded_section_id}/pages",
            params={"$top": 100},
        )
        if pages_error is not None:
            return pages_error
        pages = pages_payload.get("value", []) if isinstance(pages_payload, dict) else []
        if not isinstance(pages, list):
            continue

        for page in pages:
            if not isinstance(page, dict):
                continue
            title = str(page.get("title", ""))
            if q in title.casefold():
                filtered.append(
                    {
                        "id": str(page.get("id", "")),
                        "title": title,
                        "createdDateTime": page.get("createdDateTime"),
                        "lastModifiedDateTime": page.get("lastModifiedDateTime"),
                        "contentUrl": page.get("contentUrl"),
                        "sectionId": current_section_id,
                        "sectionName": current_section_name,
                    }
                )
        if len(filtered) >= 20:
            break

    limited = filtered[:20]
    return ActionResult(
        success=True,
        message=f"{len(filtered)} pagina(s) encontradas para '{query}'.",
        data={
            "query": query,
            "pages": limited,
            "total_found": len(filtered),
            "truncated": len(filtered) > len(limited),
        },
    )


async def _onenote_get_page_content(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    page_id = str(params.get("page_id", "")).strip()
    if not page_id:
        return ActionResult(success=False, message="Informe o page_id do OneNote.", error="missing page_id")
    encoded_page_id = _quote_path_segment(page_id)

    content, error = _onenote_api_request(
        "GET",
        f"me/onenote/pages/{encoded_page_id}/content",
        extra_headers={"Accept": "text/html"},
    )
    if error is not None:
        return error
    html_content = str(content or "")
    return ActionResult(
        success=True,
        message="Conteudo da pagina OneNote carregado.",
        data={
            "page_id": page_id,
            "content_html": html_content,
            "content_preview": _strip_html_for_preview(html_content),
        },
    )


async def _onenote_create_character_page(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    section_id = str(params.get("section_id", "")).strip()
    title = str(params.get("title", "")).strip()
    body = str(params.get("body", "")).strip()
    if not section_id or not title:
        return ActionResult(success=False, message="section_id e title sao obrigatorios.", error="missing params")

    safe_title = html.escape(title)
    safe_body = html.escape(body) if body else "Sem descricao inicial."
    encoded_section_id = _quote_path_segment(section_id)
    html_doc = (
        "<!DOCTYPE html><html><head><title>"
        f"{safe_title}"
        "</title></head><body>"
        f"<h1>{safe_title}</h1><p>{safe_body}</p>"
        "</body></html>"
    )
    payload, error = _onenote_api_request(
        "POST",
        f"me/onenote/sections/{encoded_section_id}/pages",
        raw_body=html_doc,
        extra_headers={"Content-Type": "text/html"},
    )
    if error is not None:
        return error

    page_id = str(payload.get("id", "")).strip() if isinstance(payload, dict) else ""
    links = payload.get("links", {}) if isinstance(payload, dict) else {}
    one_note_url = ""
    if isinstance(links, dict):
        one_note = links.get("oneNoteClientUrl")
        if isinstance(one_note, dict):
            one_note_url = str(one_note.get("href", ""))

    return ActionResult(
        success=True,
        message=f"Pagina de personagem '{title}' criada no OneNote.",
        data={"page_id": page_id, "title": title, "one_note_url": one_note_url},
    )


async def _onenote_append_to_page(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    page_id = str(params.get("page_id", "")).strip()
    content = str(params.get("content", "")).strip()
    if not page_id or not content:
        return ActionResult(success=False, message="page_id e content sao obrigatorios.", error="missing params")

    encoded_page_id = _quote_path_segment(page_id)
    commands = [
        {
            "target": "body",
            "action": "append",
            "content": f"<p>{html.escape(content)}</p>",
        }
    ]
    _, error = _onenote_api_request(
        "PATCH",
        f"me/onenote/pages/{encoded_page_id}/content",
        body=commands,
        extra_headers={"Content-Type": "application/json"},
    )
    if error is not None:
        return error
    return ActionResult(
        success=True,
        message="Conteudo anexado na pagina OneNote com sucesso.",
        data={"page_id": page_id},
    )


async def _whatsapp_get_recent_messages(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    contact = _normalize_whatsapp_to(str(params.get("contact", "")).strip()) if params.get("contact") else None
    limit = int(params.get("limit", 10))
    entries = _whatsapp_read_inbox()
    if contact:
        entries = [item for item in entries if str(item.get("from", "")).strip() == contact]
    entries = sorted(entries, key=lambda item: str(item.get("timestamp", "")), reverse=True)
    sliced = entries[: max(1, min(limit, 50))]
    return ActionResult(
        success=True,
        message=f"{len(sliced)} mensagem(ns) recuperada(s) do WhatsApp.",
        data={"messages": sliced},
    )


async def _whatsapp_send_text(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    to = _normalize_whatsapp_to(str(params.get("to", "")).strip())
    text = str(params.get("text", "")).strip()
    if not to or not text:
        return ActionResult(success=False, message="Parametros invalidos para WhatsApp.", error="missing to/text")
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    }
    result = _whatsapp_send_message(payload)
    if result.success:
        result.message = f"Mensagem enviada para {to}."
    return result


async def _whatsapp_send_audio_tts(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    to = _normalize_whatsapp_to(str(params.get("to", "")).strip())
    text = str(params.get("text", "")).strip()
    if not to or not text:
        return ActionResult(success=False, message="Parametros invalidos para audio WhatsApp.", error="missing to/text")

    audio_file, tts_error = await _build_jarvez_tts_file(text)
    if tts_error is not None:
        return tts_error
    if audio_file is None:
        return ActionResult(success=False, message="Falha ao gerar audio do Jarvez.", error="tts generation failed")

    media_id, media_error = _upload_whatsapp_media(audio_file, "audio/mpeg")
    try:
        audio_file.unlink(missing_ok=True)
    except Exception:
        pass

    if media_error is not None:
        return media_error
    if not media_id:
        return ActionResult(success=False, message="Nao consegui enviar audio ao WhatsApp.", error="missing media id")

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "audio",
        "audio": {"id": media_id},
    }
    result = _whatsapp_send_message(payload)
    if result.success:
        result.message = f"Audio do Jarvez enviado para {to}."
        if result.data is None:
            result.data = {}
        result.data["media_id"] = media_id
    return result


async def _rpg_reindex_sources(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    index = _get_rpg_index()
    configured = _rpg_sources()
    extra_paths_raw = params.get("paths", [])
    extra_paths: list[Path] = []
    if isinstance(extra_paths_raw, list):
        for item in extra_paths_raw:
            if isinstance(item, str) and item.strip():
                extra_paths.append(Path(item.strip()))

    sources = configured + extra_paths
    if not sources:
        return ActionResult(
            success=False,
            message="Nenhuma fonte RPG configurada para indexar.",
            error="missing RPG_SOURCE_PATHS",
        )

    summary = index.ingest_paths(sources)
    stats = index.stats()
    return ActionResult(
        success=True,
        message="Base RPG reindexada com sucesso.",
        data={"ingest_summary": summary, "knowledge_stats": stats},
    )


async def _rpg_search_knowledge(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    query = str(params.get("query", "")).strip()
    limit = int(params.get("limit", 5))
    if not query:
        return ActionResult(success=False, message="Informe uma consulta RPG.", error="missing query")

    index = _get_rpg_index()
    results = index.search(query, limit=limit)
    if not results:
        return ActionResult(
            success=False,
            message="Nao encontrei trechos na base RPG para essa pergunta.",
            data={"query": query},
            error="not found",
        )
    return ActionResult(
        success=True,
        message=f"Encontrei {len(results)} trecho(s) da base RPG.",
        data={"query": query, "results": results},
    )


async def _rpg_get_knowledge_stats(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    index = _get_rpg_index()
    return ActionResult(success=True, message="Estatisticas da base RPG.", data={"knowledge_stats": index.stats()})


async def _rpg_save_lore_note(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    title = str(params.get("title", "")).strip()
    content = str(params.get("content", "")).strip()
    world = str(params.get("world", "geral")).strip() or "geral"
    if not content:
        return ActionResult(success=False, message="Conteudo vazio para nota de lore.", error="missing content")

    index = _get_rpg_index()
    try:
        saved = index.save_note(title=title or "nota_rpg", content=content, world=world, notes_dir=_rpg_notes_dir())
    except ValueError as error:
        return ActionResult(success=False, message="Nao consegui salvar a nota RPG.", error=str(error))

    reindex_summary = index.ingest_paths([Path(saved["file_path"])])
    return ActionResult(
        success=True,
        message=f"Nota de lore salva em {saved['world']} e indexada.",
        data={"saved_note": saved, "ingest_summary": reindex_summary, "knowledge_stats": index.stats()},
    )


async def _rpg_create_character_sheet(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    name = str(params.get("name", "")).strip()
    world = str(params.get("world", "tormenta20")).strip() or "tormenta20"
    race = str(params.get("race", "")).strip() or "A definir"
    class_name = str(params.get("class_name", "")).strip() or "A definir"
    origin = str(params.get("origin", "acolyte")).strip() or "acolyte"
    concept = str(params.get("concept", "")).strip() or "A definir"
    level = int(params.get("level", 1))
    if not name:
        return ActionResult(success=False, message="Informe o nome do personagem.", error="missing name")

    attrs = {
        "forca": 10,
        "destreza": 10,
        "constituicao": 10,
        "inteligencia": 10,
        "sabedoria": 10,
        "carisma": 10,
    }
    incoming_attrs = params.get("attributes")
    if isinstance(incoming_attrs, dict):
        for key, value in incoming_attrs.items():
            if key in attrs and isinstance(value, int):
                attrs[key] = max(1, min(30, value))

    safe_world = _safe_file_part(world)
    safe_name = _safe_file_part(name)
    target_dir = _rpg_characters_dir() / safe_world
    target_dir.mkdir(parents=True, exist_ok=True)
    md_path = target_dir / f"{safe_name}.md"
    json_path = target_dir / f"{safe_name}.json"
    pdf_dir = _rpg_character_pdfs_dir() / safe_world
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / f"{safe_name}.pdf"

    bridge_payload, bridge_error = _run_t20_sheet_builder(
        {
            "name": name,
            "world": world,
            "race": race,
            "class_name": class_name,
            "origin": origin,
            "level": level,
            "concept": concept,
            "attributes": attrs,
        }
    )
    builder_source = "fallback"
    trained_names: list[str] = []
    if bridge_payload is not None:
        serialized_character = bridge_payload.get("serialized_character", {})
        serialized_sheet = serialized_character.get("sheet", {}) if isinstance(serialized_character, dict) else {}
        sheet_data = {
            "system": str(bridge_payload.get("system", "tormenta20-t20-sheet-builder")),
            "builder": str(bridge_payload.get("builder", "t20-sheet-builder")),
            "name": name,
            "world": world,
            "race": race,
            "class_name": class_name,
            "origin": origin,
            "level": int(bridge_payload.get("level", level) or level),
            "concept": concept,
            "attributes": bridge_payload.get("attributes", {}),
            "modifiers": {
                "forca": int((bridge_payload.get("attributes", {}) or {}).get("strength", 0) or 0),
                "destreza": int((bridge_payload.get("attributes", {}) or {}).get("dexterity", 0) or 0),
                "constituicao": int((bridge_payload.get("attributes", {}) or {}).get("constitution", 0) or 0),
                "inteligencia": int((bridge_payload.get("attributes", {}) or {}).get("intelligence", 0) or 0),
                "sabedoria": int((bridge_payload.get("attributes", {}) or {}).get("wisdom", 0) or 0),
                "carisma": int((bridge_payload.get("attributes", {}) or {}).get("charisma", 0) or 0),
            },
            "derived": {
                "pv": bridge_payload.get("life_points"),
                "pm": bridge_payload.get("mana_points"),
                "defense": bridge_payload.get("defense"),
            },
            "trained_skills": bridge_payload.get("trained_skills", []),
            "top_skills": bridge_payload.get("top_skills", []),
            "attacks": bridge_payload.get("attacks", []),
            "build_steps": bridge_payload.get("build_steps", []),
            "recommended_skills": [item.get("name") for item in bridge_payload.get("trained_skills", []) if isinstance(item, dict) and item.get("name")],
            "serialized_character": serialized_character,
            "displacement": serialized_sheet.get("displacement", 9) if isinstance(serialized_sheet, dict) else 9,
            "current_cargo": int(serialized_sheet.get("money", 0) or 0) if isinstance(serialized_sheet, dict) else 0,
            "max_cargo": 10 + max(0, int((bridge_payload.get("attributes", {}) or {}).get("strength", 0) or 0)) * 5,
            "carry_capacity": (10 + max(0, int((bridge_payload.get("attributes", {}) or {}).get("strength", 0) or 0)) * 5) * 2,
            "proficiencies": serialized_sheet.get("proficiencies", []) if isinstance(serialized_sheet, dict) else [],
            "spells": serialized_sheet.get("spells", []) if isinstance(serialized_sheet, dict) else [],
            "powers": (
                _json_list(serialized_sheet.get("generalPowers")) +
                _json_list(serialized_sheet.get("rolePowers")) +
                _json_list(serialized_sheet.get("originPowers")) +
                _json_list(serialized_sheet.get("grantedPowers"))
            ) if isinstance(serialized_sheet, dict) else [],
            "updated_at": _now_iso(),
        }
        trained_skills = sheet_data.get("trained_skills", [])
        if isinstance(trained_skills, list):
            for item in trained_skills[:12]:
                if isinstance(item, dict):
                    skill_name = str(item.get("name", "")).strip()
                    total = item.get("total")
                    if skill_name:
                        trained_names.append(f"{skill_name} ({total})")
        attacks = sheet_data.get("attacks", [])
        attack_names = []
        if isinstance(attacks, list):
            for item in attacks[:4]:
                if not isinstance(item, dict):
                    continue
                attack = item.get("attack", {})
                if isinstance(attack, dict):
                    attack_name = str(attack.get("name", "")).strip()
                    if attack_name:
                        attack_names.append(attack_name)
        sheet_md = "\n".join(
            [
                f"# Ficha Tormenta20 - {name}",
                "",
                f"- Mundo: {world}",
                f"- Raca: {race}",
                f"- Classe: {class_name}",
                f"- Origem: {origin}",
                f"- Nivel: {sheet_data['level']}",
                f"- Conceito: {concept}",
                f"- Builder: {sheet_data['builder']}",
                "",
                "## Derivados",
                f"- PV: {sheet_data['derived'].get('pv')}",
                f"- PM: {sheet_data['derived'].get('pm')}",
                f"- Defesa: {sheet_data['derived'].get('defense')}",
                "",
                "## Pericias Treinadas",
                *(f"- {item}" for item in trained_names),
                "",
                "## Ataques",
                *(f"- {item}" for item in attack_names),
                "",
                "## Build Steps",
                *(
                    f"- {str(step.get('action', {}).get('description', '')).strip()}"
                    for step in sheet_data.get("build_steps", [])[:20]
                    if isinstance(step, dict)
                ),
            ]
        )
        builder_source = "t20-sheet-builder"
    else:
        sheet_data = _build_tormenta20_sheet_data(
            name=name,
            world=world,
            race=race,
            class_name=class_name,
            level=level,
            concept=concept,
            attrs=attrs,
        )
        sheet_data["origin"] = origin
        sheet_data["bridge_error"] = f"bridge unsupported: {bridge_error}" if bridge_error else None
        sheet_md = _build_tormenta20_sheet_markdown(sheet_data)
    sheet_data = _normalize_sheet_data(sheet_data)
    md_path.write_text(sheet_md, encoding="utf-8")
    json_path.write_text(
        json.dumps(sheet_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    pdf_exported = False
    pdf_error: str | None = None
    if _rpg_pdf_export_enabled():
        pdf_exported, pdf_error = _export_tormenta20_sheet_pdf(sheet_data, pdf_path)
    template_paths = [
        item.strip()
        for item in os.getenv("RPG_CHARACTER_TEMPLATE_PDFS", "").split(";")
        if item.strip()
    ]
    existing_templates = [path for path in template_paths if Path(path).exists()]
    one_note_sync_status = "skipped"
    one_note_sync_error: str | None = None
    active_character = get_active_character(ctx.participant_identity, ctx.room)
    target_page_id: str | None = None
    if active_character and active_character.page_id and active_character.name.casefold() == name.casefold():
        target_page_id = active_character.page_id
    else:
        match = _find_onenote_character_page(name)
        if match and isinstance(match, dict):
            page = match.get("page")
            if isinstance(page, dict):
                target_page_id = str(page.get("id", "")).strip() or None
    if target_page_id:
        skill_summary = sheet_data.get("recommended_skills")
        if not isinstance(skill_summary, list) or not skill_summary:
            skill_summary = trained_names
        artifact_summary = (
            f"Arquivos locais: JSON {json_path.resolve()} | MD {md_path.resolve()} | "
            f"PDF {pdf_path.resolve() if pdf_exported else 'indisponivel'}."
        )
        append_text = (
            f"Ficha Tormenta20 atualizada. Classe: {class_name}. Nivel: {level}. "
            f"Builder: {builder_source}. "
            f"PV {sheet_data['derived']['pv']}, PM {sheet_data['derived']['pm']}, Defesa {sheet_data['derived']['defense']}. "
            f"Pericias recomendadas: {', '.join(str(item) for item in skill_summary[:6])}. "
            f"{artifact_summary}"
        )
        append_result = await _onenote_append_to_page({"page_id": target_page_id, "content": append_text}, ctx)
        if append_result.success:
            one_note_sync_status = "appended"
        else:
            one_note_sync_status = "failed"
            one_note_sync_error = append_result.message
    if active_character and active_character.name.casefold() == name.casefold():
        active_character.sheet_json_path = str(json_path.resolve())
        active_character.sheet_markdown_path = str(md_path.resolve())
        active_character.sheet_pdf_path = str(pdf_path.resolve()) if pdf_exported else None
        set_active_character(ctx.participant_identity, ctx.room, active_character)

    pdf_status = "created" if pdf_exported else ("skipped" if not _rpg_pdf_export_enabled() else "failed")
    logger.info(
        "rpg_sheet_pipeline %s",
        json.dumps(
            {
                "character_name": name,
                "world": world,
                "builder_source": builder_source,
                "pdf_status": pdf_status,
                "pdf_error": pdf_error,
                "one_note_sync_status": one_note_sync_status,
            },
            ensure_ascii=False,
        ),
    )

    return ActionResult(
        success=True,
        message=f"Ficha Tormenta20 base de {name} criada.",
        data={
            "character_name": name,
            "sheet_markdown_path": str(md_path.resolve()),
            "sheet_json_path": str(json_path.resolve()),
            "sheet_pdf_path": str(pdf_path.resolve()) if pdf_exported else None,
            "sheet_pdf_status": pdf_status,
            "sheet_pdf_error": pdf_error,
            "sheet_pdf_template_path": str(_tormenta20_pdf_template_path().resolve()) if _rpg_pdf_export_enabled() else None,
            "sheet_data": sheet_data,
            "sheet_builder_source": builder_source,
            "sheet_builder_error": (f"bridge unsupported: {bridge_error}" if bridge_error else None),
            "template_references": existing_templates,
            "one_note_character_page_sync": one_note_sync_status,
            "one_note_character_page_error": one_note_sync_error,
        },
    )


async def _rpg_create_threat_sheet(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    name = str(params.get("name", "")).strip()
    if not name:
        return ActionResult(success=False, message="Informe o nome da ameaça.", error="missing name")

    challenge_level_raw = str(params.get("challenge_level", "")).strip()
    if not challenge_level_raw:
        return ActionResult(success=False, message="Informe o ND da ameaça.", error="missing challenge_level")
    try:
        challenge_level, _ = _parse_threat_nd_value(challenge_level_raw)
    except ValueError as error:
        return ActionResult(success=False, message="ND inválido para a ameaça.", error=str(error))

    world = str(params.get("world", "tormenta20")).strip() or "tormenta20"
    threat_type = str(params.get("threat_type", "Monstro")).strip() or "Monstro"
    size = str(params.get("size", "Grande")).strip() or "Grande"
    role = str(params.get("role", "Solo")).strip() or "Solo"
    concept = str(params.get("concept", "")).strip() or "A definir"
    has_mana_points = bool(params.get("has_mana_points", True))
    displacement = str(params.get("displacement", "9 m")).strip() or "9 m"
    is_boss = bool(params.get("is_boss", False))
    attributes = params.get("attributes") if isinstance(params.get("attributes"), dict) else None

    threat_data = _build_tormenta20_threat_data(
        name=name,
        world=world,
        threat_type=threat_type,
        size=size,
        role=role,
        challenge_level=challenge_level,
        concept=concept,
        has_mana_points=has_mana_points,
        displacement=displacement,
        is_boss=is_boss,
        attributes=attributes,
    )

    safe_world = _safe_file_part(world)
    safe_name = _safe_file_part(name)
    target_dir = _rpg_threats_dir() / safe_world
    target_dir.mkdir(parents=True, exist_ok=True)
    md_path = target_dir / f"{safe_name}.md"
    json_path = target_dir / f"{safe_name}.json"
    pdf_dir = _rpg_threat_pdfs_dir() / safe_world
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / f"{safe_name}.pdf"

    md_path.write_text(_build_tormenta20_threat_markdown(threat_data), encoding="utf-8")
    json_path.write_text(json.dumps(threat_data, ensure_ascii=False, indent=2), encoding="utf-8")
    pdf_exported, pdf_error = _export_tormenta20_threat_pdf(threat_data, pdf_path)
    pdf_status = "created" if pdf_exported else "failed"

    logger.info(
        "rpg_threat_pipeline %s",
        json.dumps(
            {
                "threat_name": name,
                "world": world,
                "challenge_level": challenge_level,
                "role": role,
                "builder_source": threat_data.get("builder"),
                "pdf_status": pdf_status,
                "pdf_error": pdf_error,
            },
            ensure_ascii=False,
        ),
    )

    return ActionResult(
        success=True,
        message=f"Ameaça Tormenta20 base de {name} criada.",
        data={
            "threat_name": name,
            "threat_markdown_path": str(md_path.resolve()),
            "threat_json_path": str(json_path.resolve()),
            "threat_pdf_path": str(pdf_path.resolve()) if pdf_exported else None,
            "threat_pdf_status": pdf_status,
            "threat_pdf_error": pdf_error,
            "threat_data": threat_data,
            "threat_builder_source": str(threat_data.get("builder", "jarvez-threat-generator")),
        },
    )


async def _rpg_session_recording(params: JsonObject, ctx: ActionContext) -> ActionResult:
    mode = str(params.get("mode", "status")).strip().lower()
    world = str(params.get("world", "geral")).strip() or "geral"
    title = str(params.get("title", "")).strip() or f"sessao_{datetime.now().strftime('%Y%m%d_%H%M')}"
    key = _recording_key(ctx.participant_identity, ctx.room)
    current = RPG_ACTIVE_RECORDINGS.get(key)

    if mode == "status":
        if current and current.active:
            return ActionResult(
                success=True,
                message="Gravacao de sessao ativa.",
                data={
                    "recording_active": True,
                    "title": current.title,
                    "world": current.world,
                    "started_at": current.started_at.isoformat(),
                },
            )
        return ActionResult(success=True, message="Nenhuma gravacao ativa.", data={"recording_active": False})

    if mode == "start":
        history_items = getattr(getattr(ctx.session, "history", None), "items", None)
        start_index = len(history_items) if isinstance(history_items, list) else 0
        RPG_ACTIVE_RECORDINGS[key] = RPGSessionRecordingState(
            participant_identity=ctx.participant_identity,
            room=ctx.room,
            title=title,
            world=world,
            started_at=datetime.now(timezone.utc),
            start_history_index=start_index,
            active=True,
        )
        return ActionResult(
            success=True,
            message=f"Gravacao da sessao '{title}' iniciada.",
            data={"recording_active": True, "title": title, "world": world},
        )

    if mode == "stop":
        if not current or not current.active:
            return ActionResult(success=False, message="Nao ha gravacao ativa para parar.", error="no active recording")
        messages = _extract_history_since(ctx.session, current.start_history_index)
        safe_world = _safe_file_part(current.world)
        safe_title = _safe_file_part(current.title)
        out_dir = _rpg_session_logs_dir() / safe_world
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        out_file.write_text(_build_session_markdown(state=current, messages=messages), encoding="utf-8")

        current.output_file = str(out_file.resolve())
        current.active = False
        RPG_ACTIVE_RECORDINGS.pop(key, None)
        RPG_LAST_SESSION_FILES[key] = str(out_file.resolve())
        active_character = get_active_character(ctx.participant_identity, ctx.room)
        one_note_sync_status = "skipped"
        one_note_sync_error: str | None = None
        if active_character and active_character.page_id:
            session_notes = _infer_character_session_notes(messages)
            first_user_lines = [
                item.get("content", "").strip()
                for item in messages
                if item.get("role") == "user" and str(item.get("content", "")).strip()
            ]
            excerpt = " ".join(first_user_lines[:2]).strip()
            if len(excerpt) > 240:
                excerpt = excerpt[:240].rstrip() + "..."
            sync_line = (
                f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] Sessao '{current.title}' encerrada. "
                f"Mundo: {current.world}. Falas registradas: {len(messages)}. "
                f"Arquivo local: {out_file.resolve()}."
            )
            if excerpt:
                sync_line += f" Abertura da sessao: {excerpt}"
            inferred_chunks: list[str] = []
            summary = str(session_notes.get("summary", "")).strip()
            if summary:
                inferred_chunks.append(f"Resumo: {summary}")
            objectives = session_notes.get("objectives", [])
            if isinstance(objectives, list) and objectives:
                inferred_chunks.append(f"Objetivos observados: {' | '.join(str(item) for item in objectives)}")
            relations = session_notes.get("relations", [])
            if isinstance(relations, list) and relations:
                inferred_chunks.append(f"Relacoes observadas: {' | '.join(str(item) for item in relations)}")
            secrets = session_notes.get("secrets", [])
            if isinstance(secrets, list) and secrets:
                inferred_chunks.append(f"Segredos citados: {' | '.join(str(item) for item in secrets)}")
            if inferred_chunks:
                sync_line += " " + " ".join(inferred_chunks)
            sync_line += " Revise a ficha do personagem se houve mudanca mecanica nesta sessao."
            append_result = await _onenote_append_to_page(
                {"page_id": active_character.page_id, "content": sync_line},
                ctx,
            )
            if append_result.success:
                one_note_sync_status = "appended"
            else:
                one_note_sync_status = "failed"
                one_note_sync_error = append_result.message

        return ActionResult(
            success=True,
            message=f"Gravacao encerrada e salva em {out_file.name}.",
            data={
                "recording_active": False,
                "session_file": str(out_file.resolve()),
                "messages_recorded": len(messages),
                "active_character_name": active_character.name if active_character else None,
                "one_note_character_page_sync": one_note_sync_status,
                "one_note_character_page_error": one_note_sync_error,
            },
        )

    return ActionResult(success=False, message="Modo invalido. Use start, stop ou status.", error="invalid mode")


async def _rpg_write_session_summary(params: JsonObject, ctx: ActionContext) -> ActionResult:
    key = _recording_key(ctx.participant_identity, ctx.room)
    session_file = str(params.get("session_file", "")).strip() or RPG_LAST_SESSION_FILES.get(key, "")
    if not session_file:
        return ActionResult(success=False, message="Nao encontrei sessao para resumir.", error="missing session file")
    path = Path(session_file)
    if not path.exists():
        return ActionResult(success=False, message="Arquivo de sessao nao encontrado.", error="file not found")

    content = path.read_text(encoding="utf-8", errors="ignore")
    messages: list[dict[str, str]] = []
    for line in content.splitlines():
        text = line.strip()
        if text.startswith("**Jogador:**"):
            messages.append({"role": "user", "content": text.replace("**Jogador:**", "", 1).strip()})
        elif text.startswith("**Jarvez:**"):
            messages.append({"role": "assistant", "content": text.replace("**Jarvez:**", "", 1).strip()})

    summary_md = _build_session_summary(path.stem, messages)
    summary_file = path.with_name(path.stem + "_resumo.md")
    summary_file.write_text(summary_md, encoding="utf-8")
    return ActionResult(
        success=True,
        message="Resumo da sessao criado com sucesso.",
        data={"summary_file": str(summary_file.resolve()), "session_file": str(path.resolve())},
    )


async def _rpg_ideate_next_session(params: JsonObject, ctx: ActionContext) -> ActionResult:
    key = _recording_key(ctx.participant_identity, ctx.room)
    session_file = str(params.get("session_file", "")).strip() or RPG_LAST_SESSION_FILES.get(key, "")
    if not session_file:
        return ActionResult(success=False, message="Nao encontrei sessao anterior para gerar ideias.", error="missing session file")
    path = Path(session_file)
    if not path.exists():
        return ActionResult(success=False, message="Arquivo de sessao nao encontrado.", error="file not found")

    raw = path.read_text(encoding="utf-8", errors="ignore")
    seed = raw.lower()
    ideas = [
        "Abrir com consequencia direta da ultima decisao do grupo.",
        "Introduzir um NPC com motivacao ambigua e informacao incompleta.",
        "Criar um conflito com limite de tempo para aumentar tensao.",
        "Conectar um gancho pessoal de um personagem ao arco principal.",
    ]
    if "morreu" in seed or "morte" in seed:
        ideas.append("Explorar impacto da perda com chance de vinganca, luto ou legado.")
    if "drag" in seed or "dragao" in seed:
        ideas.append("Escalar para uma ameaca ancestral com pistas progressivas.")

    ideas_dir = _rpg_notes_dir() / "next_session_ideas"
    ideas_dir.mkdir(parents=True, exist_ok=True)
    ideas_file = ideas_dir / f"ideias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    ideas_file.write_text("# Ideias para Proxima Sessao\n\n" + "\n".join(f"- {idea}" for idea in ideas) + "\n", encoding="utf-8")
    return ActionResult(
        success=True,
        message="Ideias da proxima sessao geradas.",
        data={"ideas": ideas, "ideas_file": str(ideas_file.resolve()), "session_file": str(path.resolve())},
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
            name="list_persona_modes",
            description="Lista os modos de personalidade disponiveis.",
            params_schema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_list_persona_modes,
        )
    )

    register_action(
        ActionSpec(
            name="get_persona_mode",
            description="Retorna o modo de personalidade atual da sessao.",
            params_schema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_get_persona_mode_action,
        )
    )

    register_action(
        ActionSpec(
            name="set_persona_mode",
            description="Altera o modo de personalidade do Jarvez para a sessao atual.",
            params_schema={
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["default", "faria_lima", "mona", "rpg", "hetero_top"],
                    }
                },
                "required": ["mode"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_set_persona_mode_action,
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
            name="rpg_get_knowledge_stats",
            description="Retorna estatisticas da base de conhecimento RPG local.",
            params_schema={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_rpg_get_knowledge_stats,
        )
    )

    register_action(
        ActionSpec(
            name="rpg_get_character_mode",
            description="Retorna o personagem atualmente ativo para interpretacao na sessao.",
            params_schema={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_rpg_get_character_mode,
        )
    )

    register_action(
        ActionSpec(
            name="rpg_assume_character",
            description="Ativa interpretacao persistente de um personagem, tenta sincronizar uma pagina dedicada no OneNote e usa fallback para PDFs.",
            params_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "minLength": 1, "maxLength": 180},
                    "source": {"type": "string", "enum": ["auto", "onenote", "pdf", "manual"]},
                    "section_name": {"type": "string", "minLength": 1, "maxLength": 180},
                    "referencia_visual_url": {"type": "string", "minLength": 1, "maxLength": 500},
                    "pinterest_pin_url": {"type": "string", "minLength": 1, "maxLength": 500},
                    "descricao_visual": {"type": "string", "minLength": 1, "maxLength": 1000},
                },
                "required": ["name"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_rpg_assume_character,
        )
    )

    register_action(
        ActionSpec(
            name="rpg_clear_character_mode",
            description="Encerra a interpretacao persistente de personagem na sessao.",
            params_schema={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_rpg_clear_character_mode,
        )
    )

    register_action(
        ActionSpec(
            name="rpg_reindex_sources",
            description="Reindexa os PDFs e arquivos de lore das fontes RPG configuradas.",
            params_schema={
                "type": "object",
                "properties": {
                    "paths": {
                        "type": "array",
                    }
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_rpg_reindex_sources,
        )
    )

    register_action(
        ActionSpec(
            name="rpg_search_knowledge",
            description="Busca regras, lore e historia nos documentos RPG indexados.",
            params_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "minLength": 2, "maxLength": 300},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_rpg_search_knowledge,
        )
    )

    register_action(
        ActionSpec(
            name="rpg_save_lore_note",
            description="Salva nova informacao de lore em arquivo local e indexa automaticamente.",
            params_schema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "minLength": 1, "maxLength": 120},
                    "world": {"type": "string", "minLength": 1, "maxLength": 120},
                    "content": {"type": "string", "minLength": 1, "maxLength": 4000},
                },
                "required": ["content"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_rpg_save_lore_note,
        )
    )

    register_action(
        ActionSpec(
            name="rpg_create_character_sheet",
            description="Cria uma ficha Tormenta20 base e salva em arquivo markdown/json, com sincronizacao resumida no OneNote quando possivel.",
            params_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "minLength": 1, "maxLength": 120},
                    "world": {"type": "string", "minLength": 1, "maxLength": 120},
                    "race": {"type": "string", "minLength": 1, "maxLength": 120},
                    "class_name": {"type": "string", "minLength": 1, "maxLength": 120},
                    "origin": {"type": "string", "minLength": 1, "maxLength": 120},
                    "level": {"type": "integer", "minimum": 1, "maximum": 20},
                    "concept": {"type": "string", "minLength": 1, "maxLength": 400},
                    "attributes": {"type": "object"},
                },
                "required": ["name"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_rpg_create_character_sheet,
        )
    )

    register_action(
        ActionSpec(
            name="rpg_create_threat_sheet",
            description="Cria uma ameaca Tormenta20 base em markdown/json, inspirada na logica de geracao de ameacas do Fichas de Nimb.",
            params_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "minLength": 1, "maxLength": 120},
                    "world": {"type": "string", "minLength": 1, "maxLength": 120},
                    "threat_type": {"type": "string", "minLength": 1, "maxLength": 120},
                    "size": {"type": "string", "minLength": 1, "maxLength": 120},
                    "role": {"type": "string", "enum": ["Solo", "Lacaio", "Especial"]},
                    "challenge_level": {"type": "string", "minLength": 1, "maxLength": 8},
                    "concept": {"type": "string", "minLength": 1, "maxLength": 400},
                    "has_mana_points": {"type": "boolean"},
                    "is_boss": {"type": "boolean"},
                    "displacement": {"type": "string", "minLength": 1, "maxLength": 80},
                    "attributes": {"type": "object"},
                },
                "required": ["name", "challenge_level"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_rpg_create_threat_sheet,
        )
    )

    register_action(
        ActionSpec(
            name="rpg_session_recording",
            description="Controla gravacao da sessao RPG: start, stop ou status.",
            params_schema={
                "type": "object",
                "properties": {
                    "mode": {"type": "string", "enum": ["start", "stop", "status"]},
                    "title": {"type": "string", "minLength": 1, "maxLength": 200},
                    "world": {"type": "string", "minLength": 1, "maxLength": 120},
                },
                "required": ["mode"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_rpg_session_recording,
        )
    )

    register_action(
        ActionSpec(
            name="rpg_write_session_summary",
            description="Gera arquivo de resumo da ultima sessao gravada.",
            params_schema={
                "type": "object",
                "properties": {
                    "session_file": {"type": "string", "minLength": 5, "maxLength": 600},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_rpg_write_session_summary,
        )
    )

    register_action(
        ActionSpec(
            name="rpg_ideate_next_session",
            description="Gera ideias para a proxima sessao com base no historico gravado.",
            params_schema={
                "type": "object",
                "properties": {
                    "session_file": {"type": "string", "minLength": 5, "maxLength": 600},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_rpg_ideate_next_session,
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
            name="onenote_status",
            description="Verifica status da conexao OneNote e cadernos basicos.",
            params_schema={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_onenote_status,
        )
    )

    register_action(
        ActionSpec(
            name="onenote_list_notebooks",
            description="Lista cadernos do OneNote para localizar o caderno correto.",
            params_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "minLength": 1, "maxLength": 200},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_onenote_list_notebooks,
        )
    )

    register_action(
        ActionSpec(
            name="onenote_list_sections",
            description="Lista secoes do OneNote para escolher onde salvar personagens e lore.",
            params_schema={
                "type": "object",
                "properties": {
                    "notebook_name": {"type": "string", "minLength": 1, "maxLength": 120},
                    "notebook_id": {"type": "string", "minLength": 8, "maxLength": 200},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_onenote_list_sections,
        )
    )

    register_action(
        ActionSpec(
            name="onenote_list_pages",
            description="Lista paginas de uma secao especifica do OneNote.",
            params_schema={
                "type": "object",
                "properties": {
                    "section_id": {"type": "string", "minLength": 8, "maxLength": 200},
                    "section_name": {"type": "string", "minLength": 1, "maxLength": 200},
                    "query": {"type": "string", "minLength": 1, "maxLength": 200},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_onenote_list_pages,
        )
    )

    register_action(
        ActionSpec(
            name="onenote_search_pages",
            description="Busca paginas no OneNote por titulo (ex: nome de personagem).",
            params_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "minLength": 2, "maxLength": 200},
                    "title": {"type": "string", "minLength": 2, "maxLength": 200},
                    "name": {"type": "string", "minLength": 2, "maxLength": 200},
                    "section_id": {"type": "string", "minLength": 8, "maxLength": 200},
                    "section_name": {"type": "string", "minLength": 1, "maxLength": 200},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_onenote_search_pages,
        )
    )

    register_action(
        ActionSpec(
            name="onenote_get_page_content",
            description="Carrega o conteudo de uma pagina OneNote pelo page_id.",
            params_schema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "minLength": 8, "maxLength": 200},
                },
                "required": ["page_id"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_onenote_get_page_content,
        )
    )

    register_action(
        ActionSpec(
            name="onenote_create_character_page",
            description="Cria pagina de personagem no OneNote em uma secao especifica.",
            params_schema={
                "type": "object",
                "properties": {
                    "section_id": {"type": "string", "minLength": 8, "maxLength": 200},
                    "title": {"type": "string", "minLength": 1, "maxLength": 180},
                    "body": {"type": "string", "minLength": 1, "maxLength": 8000},
                },
                "required": ["section_id", "title"],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_onenote_create_character_page,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="onenote_append_to_page",
            description="Adiciona texto ao fim de uma pagina existente do OneNote.",
            params_schema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "minLength": 8, "maxLength": 200},
                    "content": {"type": "string", "minLength": 1, "maxLength": 8000},
                },
                "required": ["page_id", "content"],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_onenote_append_to_page,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="spotify_status",
            description="Verifica status da conexao Spotify e dispositivos ativos.",
            params_schema={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_spotify_status,
        )
    )

    register_action(
        ActionSpec(
            name="spotify_get_devices",
            description="Lista devices disponiveis no Spotify Connect (incluindo Alexa).",
            params_schema={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_spotify_get_devices,
        )
    )

    register_action(
        ActionSpec(
            name="spotify_transfer_playback",
            description="Troca o speaker ativo do Spotify para um device especifico.",
            params_schema={
                "type": "object",
                "properties": {
                    "device_name": {"type": "string", "minLength": 2, "maxLength": 128},
                    "device_id": {"type": "string", "minLength": 8, "maxLength": 256},
                    "play": {"type": "boolean"},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_spotify_transfer_playback,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="spotify_play",
            description="Toca musica no Spotify por busca textual ou URI; pode escolher speaker.",
            params_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "minLength": 2, "maxLength": 256},
                    "uri": {"type": "string", "minLength": 10, "maxLength": 256},
                    "device_name": {"type": "string", "minLength": 2, "maxLength": 128},
                    "device_id": {"type": "string", "minLength": 8, "maxLength": 256},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_spotify_play,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="spotify_pause",
            description="Pausa a reproducao atual do Spotify.",
            params_schema={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_spotify_pause,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="spotify_next_track",
            description="Pula para a proxima faixa no Spotify.",
            params_schema={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_spotify_next_track,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="spotify_previous_track",
            description="Volta para a faixa anterior no Spotify.",
            params_schema={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_spotify_previous_track,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="spotify_set_volume",
            description="Ajusta volume do Spotify (0-100).",
            params_schema={
                "type": "object",
                "properties": {
                    "volume_percent": {"type": "integer", "minimum": 0, "maximum": 100},
                    "device_name": {"type": "string", "minLength": 2, "maxLength": 128},
                    "device_id": {"type": "string", "minLength": 8, "maxLength": 256},
                },
                "required": ["volume_percent"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_spotify_set_volume,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="spotify_create_surprise_playlist",
            description="Cria uma playlist surpresa baseada no seu historico e faixas curadas.",
            params_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "minLength": 2, "maxLength": 120},
                    "public": {"type": "boolean"},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_spotify_create_surprise_playlist,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="whatsapp_get_recent_messages",
            description="Lista mensagens recentes recebidas no WhatsApp via webhook.",
            params_schema={
                "type": "object",
                "properties": {
                    "contact": {"type": "string", "minLength": 8, "maxLength": 32},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_whatsapp_get_recent_messages,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="whatsapp_send_text",
            description="Envia mensagem de texto no WhatsApp para um contato.",
            params_schema={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "minLength": 8, "maxLength": 32},
                    "text": {"type": "string", "minLength": 1, "maxLength": 4096},
                },
                "required": ["to", "text"],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_whatsapp_send_text,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="whatsapp_send_audio_tts",
            description="Envia audio com a voz do Jarvez (TTS) no WhatsApp para um contato.",
            params_schema={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "minLength": 8, "maxLength": 32},
                    "text": {"type": "string", "minLength": 1, "maxLength": 1200},
                },
                "required": ["to", "text"],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_whatsapp_send_audio_tts,
            requires_auth=True,
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
