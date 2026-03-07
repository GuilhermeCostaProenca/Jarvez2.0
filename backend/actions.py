from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import random
import re
import secrets
import shutil
import subprocess
import tempfile
import time
import webbrowser
import html
import hashlib
import unicodedata
import uuid
from difflib import SequenceMatcher
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Awaitable, Callable
from urllib.parse import parse_qs, quote, unquote, urlencode, urlparse

import requests
from actions_core import (
    ACTION_REGISTRY,
    ACTIVE_CHARACTER_BY_PARTICIPANT,
    ACTIVE_CODEX_TASK_BY_PARTICIPANT,
    ACTIVE_PROJECT_BY_PARTICIPANT,
    AUTHENTICATED_SESSIONS,
    AUTO_REMEDIATION_LAST_EXECUTION,
    CANARY_PROMOTION_LAST_EXECUTION,
    CANARY_ROLLOUT_PERCENT_OVERRIDE,
    CANARY_SESSION_OVERRIDES,
    CAPABILITY_MODE_BY_PARTICIPANT,
    CODEX_RUNNING_PROCESSES,
    CODEX_TASK_HISTORY_BY_PARTICIPANT,
    CONTROL_LOOP_BREACH_HISTORY,
    CONTROL_LOOP_FREEZE_LAST_TRIGGER,
    FEATURE_FLAG_OVERRIDES,
    MEMORY_SCOPE_OVERRIDES,
    PARTICIPANT_PENDING_TOKENS,
    PENDING_CONFIRMATIONS,
    PERSONA_MODE_BY_PARTICIPANT,
    RPG_ACTIVE_RECORDINGS,
    RPG_LAST_SESSION_FILES,
    VOICE_STEP_UP_PENDING,
    ActionContext,
    ActionResult,
    ActionSpec,
    ActiveCharacterMode,
    ActiveCodexTask,
    ActiveProjectMode,
    AuthenticatedSession,
    PendingConfirmation,
    RPGSessionRecordingState,
    get_action,
    get_exposed_actions,
    get_state_store,
    publish_session_event,
    register_action,
)
from actions_core.dispatch import merge_event_state
from voice_biometrics import VoiceProfileStore, get_recent_voice_embedding
from code_knowledge import CodeKnowledgeIndex
from codex_cli import is_codex_available, run_exec_streaming
from code_worker_client import CodeWorkerClient
from coding_llm import explain_project_state, propose_patch_plan, summarize_diff
from evals import append_metric, baseline_scenarios, read_metrics, summarize_action_metrics, summarize_slo
from github_catalog import GitHubCatalogClient, GitHubRepo
from orchestration import (
    build_provider_registry,
    build_task_plan,
    cancel_subagent,
    complete_subagent,
    list_subagents,
    route_orchestration,
    spawn_subagent,
    start_subagent_task,
)
from policy import (
    ALLOWED_AUTONOMY_MODES,
    classify_action_risk,
    clear_domain_autonomy_mode,
    clear_domain_trust,
    clear_trust_drift,
    get_domain_autonomy_details,
    get_domain_trust,
    get_domain_autonomy_mode,
    get_effective_autonomy_mode,
    get_trust_drift,
    evaluate_policy,
    get_autonomy_mode,
    get_killswitch_status,
    infer_action_domain,
    is_blocked,
    list_domain_autonomy_modes,
    list_domain_trust,
    list_trust_drift,
    record_domain_outcome,
    replace_trust_drift,
    set_domain_autonomy_mode,
    set_autonomy_mode,
    set_killswitch_domain,
    set_killswitch_global,
)
from providers.provider_router import TaskType, preview_route
from project_catalog import ProjectCatalog, ProjectRecord
from rpg_knowledge import RPGKnowledgeIndex
from rpg_engine import generate_character_sheet, generate_threat_sheet
from rpg_engine.contracts import InvalidCharacterBuildError, InvalidThreatDefinitionError
from skills import get_skill, list_skills

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
STATE_STORE = get_state_store()
SESSION_STATE_NAMESPACES = {
    "memory_scope",
    "persona_mode",
    "capability_mode",
    "active_project",
    "active_character",
    "active_codex_task",
    "codex_history",
}
EVENT_STATE_NAMESPACES = {
    "research_schedules",
    "model_route",
    "subagent_states",
    "policy_events",
    "execution_traces",
    "eval_baseline_summary",
    "eval_metrics",
    "eval_metrics_summary",
    "slo_report",
    "providers_health",
    "feature_flags",
    "canary_state",
    "incident_snapshot",
    "playbook_report",
    "auto_remediation",
    "canary_promotion",
    "control_tick",
    "browser_tasks",
    "workflow_state",
    "automation_state",
    "whatsapp_channel",
}

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
BOOL_FALSE_VALUES = {"0", "false", "off", "no", "nao", "não"}

VOICE_PROFILE_STORE = VoiceProfileStore.from_env()
PROJECT_CATALOG_SINGLETON: ProjectCatalog | None = None
CODE_WORKER_CLIENT: CodeWorkerClient | None = None
GITHUB_CATALOG_CLIENT: GitHubCatalogClient | None = None
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"
SPOTIFY_ACCOUNTS_URL = "https://accounts.spotify.com/api/token"
THINQ_DEFAULT_API_BASE_URL = "https://api-aic.lgthinq.com"
THINQ_API_KEY = "v6GFvkweNo7DK7yD3ylIZ9w52aKBU0eJ7wLXkSR3"
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
SPOTIFY_DEVICE_ALIAS_CACHE: JsonObject = {}
ONENOTE_TOKEN_CACHE: JsonObject = {}
THINQ_SESSION_CLIENT_ID = f"jarvez-{secrets.token_hex(8)}"
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
CODE_KNOWLEDGE_INDEX: CodeKnowledgeIndex | None = None


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _persist_session_namespace(participant_identity: str, room: str, namespace: str, payload: Any) -> None:
    try:
        STATE_STORE.upsert_session_state(
            participant_identity=participant_identity,
            room=room,
            namespace=namespace,
            payload=payload,
        )
    except Exception:
        logger.warning("failed to persist session namespace=%s", namespace, exc_info=True)


def _load_session_namespace(participant_identity: str, room: str, namespace: str) -> Any | None:
    try:
        return STATE_STORE.get_session_state(
            participant_identity=participant_identity,
            room=room,
            namespace=namespace,
        )
    except Exception:
        logger.warning("failed to load session namespace=%s", namespace, exc_info=True)
        return None


def _delete_session_namespace(participant_identity: str, room: str, namespace: str) -> None:
    try:
        STATE_STORE.upsert_session_state(
            participant_identity=participant_identity,
            room=room,
            namespace=namespace,
            payload=None,
        )
    except Exception:
        logger.warning("failed to clear session namespace=%s", namespace, exc_info=True)


def _persist_event_namespace(participant_identity: str, room: str, namespace: str, payload: Any) -> None:
    try:
        STATE_STORE.upsert_event_state(
            participant_identity=participant_identity,
            room=room,
            namespace=namespace,
            payload=payload,
        )
    except Exception:
        logger.warning("failed to persist event namespace=%s", namespace, exc_info=True)


def _load_event_namespace(participant_identity: str, room: str, namespace: str) -> Any | None:
    try:
        return STATE_STORE.get_event_state(
            participant_identity=participant_identity,
            room=room,
            namespace=namespace,
        )
    except Exception:
        logger.warning("failed to load event namespace=%s", namespace, exc_info=True)
        return None


def _active_project_from_payload(payload: Any) -> ActiveProjectMode | None:
    if not isinstance(payload, dict):
        return None
    project_id = str(payload.get("project_id") or "").strip()
    name = str(payload.get("name") or "").strip()
    root_path = str(payload.get("root_path") or "").strip()
    if not (project_id and name and root_path):
        return None
    aliases = payload.get("aliases")
    return ActiveProjectMode(
        project_id=project_id,
        name=name,
        root_path=root_path,
        aliases=[str(item) for item in aliases] if isinstance(aliases, list) else [],
        selected_at=str(payload.get("selected_at") or _now_iso()),
        selection_reason=str(payload.get("selection_reason") or ""),
        index_status=str(payload.get("index_status") or ""),
    )


def _active_character_from_payload(payload: Any) -> ActiveCharacterMode | None:
    if not isinstance(payload, dict):
        return None
    name = str(payload.get("name") or "").strip()
    source = str(payload.get("source") or "").strip()
    if not (name and source):
        return None
    return ActiveCharacterMode(
        name=name,
        source=source,
        summary=str(payload.get("summary") or ""),
        activated_at=str(payload.get("activated_at") or _now_iso()),
        page_id=str(payload.get("page_id") or ""),
        page_title=str(payload.get("page_title") or ""),
        section_name=str(payload.get("section_name") or ""),
        one_note_url=str(payload.get("one_note_url") or "") or None,
        visual_reference_url=str(payload.get("visual_reference_url") or "") or None,
        pinterest_pin_url=str(payload.get("pinterest_pin_url") or "") or None,
        visual_description=str(payload.get("visual_description") or "") or None,
        profile=payload.get("profile") if isinstance(payload.get("profile"), dict) else None,
        prompt_hint=str(payload.get("prompt_hint") or "") or None,
        sheet_json_path=str(payload.get("sheet_json_path") or "") or None,
        sheet_markdown_path=str(payload.get("sheet_markdown_path") or "") or None,
        sheet_pdf_path=str(payload.get("sheet_pdf_path") or "") or None,
    )


def _active_codex_task_from_payload(payload: Any) -> ActiveCodexTask | None:
    if not isinstance(payload, dict):
        return None
    task_id = str(payload.get("task_id") or "").strip()
    status = str(payload.get("status") or "").strip()
    project_id = str(payload.get("project_id") or "").strip()
    project_name = str(payload.get("project_name") or "").strip()
    working_directory = str(payload.get("working_directory") or "").strip()
    request = str(payload.get("request") or "").strip()
    started_at = str(payload.get("started_at") or "").strip()
    if not (task_id and status and project_id and project_name and working_directory and request and started_at):
        return None
    raw_last_event = payload.get("raw_last_event")
    return ActiveCodexTask(
        task_id=task_id,
        status=status,
        project_id=project_id,
        project_name=project_name,
        working_directory=working_directory,
        request=request,
        started_at=started_at,
        finished_at=str(payload.get("finished_at") or "") or None,
        current_phase=str(payload.get("current_phase") or "") or None,
        summary=str(payload.get("summary") or "") or None,
        exit_code=payload.get("exit_code") if isinstance(payload.get("exit_code"), int) else None,
        raw_last_event=raw_last_event if isinstance(raw_last_event, dict) else None,
        command_preview=str(payload.get("command_preview") or "") or None,
        error=str(payload.get("error") or "") or None,
    )


def _known_feature_flags() -> list[str]:
    return ["skills_v1", "subagents_v1", "policy_v1", "multi_model_router_v1", "canary_v1"]


def _feature_value_from_env(flag_name: str, *, default: bool = True) -> bool:
    normalized = flag_name.strip().lower()
    specific = str(os.getenv(f"JARVEZ_FEATURE_{normalized.upper()}", "")).strip().lower()
    if specific:
        return specific not in BOOL_FALSE_VALUES

    raw = str(os.getenv("JARVEZ_FEATURE_FLAGS", "")).strip()
    if not raw:
        return default
    enabled = {item.strip().lower() for item in raw.split(",") if item.strip()}
    return normalized in enabled


def _is_feature_enabled(flag_name: str, *, default: bool = True) -> bool:
    normalized = flag_name.strip().lower()
    if normalized in FEATURE_FLAG_OVERRIDES:
        return bool(FEATURE_FLAG_OVERRIDES[normalized])
    return _feature_value_from_env(normalized, default=default)


def _require_feature(flag_name: str) -> ActionResult | None:
    if _is_feature_enabled(flag_name):
        return None
    return ActionResult(
        success=False,
        message=f"Feature `{flag_name}` desativada nesta instancia.",
        error="feature disabled",
    )


def _feature_flags_snapshot() -> JsonObject:
    known_flags = _known_feature_flags()
    values: JsonObject = {}
    for flag in known_flags:
        values[flag] = _is_feature_enabled(flag, default=False if flag == "canary_v1" else True)
    overrides = {key: value for key, value in FEATURE_FLAG_OVERRIDES.items()}
    return {"values": values, "overrides": overrides}


def _canary_key(participant_identity: str, room: str) -> str:
    return f"{participant_identity}:{room}"


def _is_canary_session_enrolled(participant_identity: str, room: str) -> bool:
    key = _canary_key(participant_identity, room)
    return bool(CANARY_SESSION_OVERRIDES.get(key, False))


def _set_canary_session_enrollment(participant_identity: str, room: str, *, enrolled: bool) -> None:
    key = _canary_key(participant_identity, room)
    if enrolled:
        CANARY_SESSION_OVERRIDES[key] = True
    else:
        CANARY_SESSION_OVERRIDES.pop(key, None)


def _get_canary_rollout_percent() -> int:
    if CANARY_ROLLOUT_PERCENT_OVERRIDE is not None:
        return max(0, min(100, int(CANARY_ROLLOUT_PERCENT_OVERRIDE)))
    raw = str(os.getenv("JARVEZ_CANARY_ROLLOUT_PERCENT", "0")).strip()
    try:
        return max(0, min(100, int(raw)))
    except Exception:
        return 0


def _set_canary_rollout_percent(percent: int) -> int:
    global CANARY_ROLLOUT_PERCENT_OVERRIDE
    normalized = max(0, min(100, int(percent)))
    CANARY_ROLLOUT_PERCENT_OVERRIDE = normalized
    return normalized


def _stable_bucket_for_session(participant_identity: str, room: str) -> int:
    token = f"{participant_identity}:{room}".encode("utf-8", errors="ignore")
    digest = hashlib.sha256(token).hexdigest()
    return int(digest[:8], 16) % 100


def _canary_state_payload(participant_identity: str, room: str) -> JsonObject:
    global_enabled = _is_feature_enabled("canary_v1", default=False)
    manual_enrolled = _is_canary_session_enrolled(participant_identity, room)
    rollout_percent = _get_canary_rollout_percent()
    bucket = _stable_bucket_for_session(participant_identity, room)
    eligible_by_rollout = bucket < rollout_percent
    active = bool(global_enabled and (manual_enrolled or eligible_by_rollout))
    return {
        "global_enabled": global_enabled,
        "session_enrolled": manual_enrolled,
        "manual_enrolled": manual_enrolled,
        "rollout_percent": rollout_percent,
        "assignment_bucket": bucket,
        "eligible_by_rollout": eligible_by_rollout,
        "active": active,
        "cohort": "canary" if active else "stable",
    }


def is_authenticated_session(participant_identity: str, room: str) -> bool:
    return _is_authenticated(participant_identity, room)


def _memory_override_key(participant_identity: str, room: str) -> str:
    return f"{participant_identity}:{room}"


def set_memory_scope_override(participant_identity: str, room: str, scope: str) -> None:
    key = _memory_override_key(participant_identity, room)
    MEMORY_SCOPE_OVERRIDES[key] = scope
    _persist_session_namespace(participant_identity, room, "memory_scope", scope)


def get_memory_scope_override(participant_identity: str, room: str) -> str | None:
    key = _memory_override_key(participant_identity, room)
    in_memory = MEMORY_SCOPE_OVERRIDES.get(key)
    if in_memory is not None:
        return in_memory
    stored = _load_session_namespace(participant_identity, room, "memory_scope")
    if isinstance(stored, str) and stored in {PUBLIC_SCOPE, PRIVATE_SCOPE}:
        MEMORY_SCOPE_OVERRIDES[key] = stored
        return stored
    return None


def _persona_key(participant_identity: str, room: str) -> str:
    return f"{participant_identity}:{room}"


def _normalize_persona_mode(value: str) -> str:
    raw = value.strip().lower().replace("-", "_")
    return PERSONA_MODE_ALIASES.get(raw, raw)


def get_persona_mode(participant_identity: str, room: str) -> str:
    key = _persona_key(participant_identity, room)
    mode = PERSONA_MODE_BY_PARTICIPANT.get(key)
    if mode is None:
        stored = _load_session_namespace(participant_identity, room, "persona_mode")
        if isinstance(stored, str):
            mode = stored
            PERSONA_MODE_BY_PARTICIPANT[key] = stored
        else:
            mode = DEFAULT_PERSONA_MODE
    if mode not in PERSONA_MODES:
        return DEFAULT_PERSONA_MODE
    return mode


def set_persona_mode(participant_identity: str, room: str, mode: str) -> str:
    normalized = _normalize_persona_mode(mode)
    if normalized not in PERSONA_MODES:
        return DEFAULT_PERSONA_MODE
    PERSONA_MODE_BY_PARTICIPANT[_persona_key(participant_identity, room)] = normalized
    _persist_session_namespace(participant_identity, room, "persona_mode", normalized)
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
    key = _character_key(participant_identity, room)
    active = ACTIVE_CHARACTER_BY_PARTICIPANT.get(key)
    if active is not None:
        return active
    stored = _load_session_namespace(participant_identity, room, "active_character")
    loaded = _active_character_from_payload(stored)
    if loaded is not None:
        ACTIVE_CHARACTER_BY_PARTICIPANT[key] = loaded
    return loaded


def set_active_character(participant_identity: str, room: str, character: ActiveCharacterMode) -> None:
    key = _character_key(participant_identity, room)
    ACTIVE_CHARACTER_BY_PARTICIPANT[key] = character
    _persist_session_namespace(participant_identity, room, "active_character", asdict(character))


def clear_active_character(participant_identity: str, room: str) -> None:
    ACTIVE_CHARACTER_BY_PARTICIPANT.pop(_character_key(participant_identity, room), None)
    _delete_session_namespace(participant_identity, room, "active_character")


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


def _get_project_catalog() -> ProjectCatalog:
    global PROJECT_CATALOG_SINGLETON
    if PROJECT_CATALOG_SINGLETON is None:
        PROJECT_CATALOG_SINGLETON = ProjectCatalog()
    return PROJECT_CATALOG_SINGLETON


def _get_code_worker_client() -> CodeWorkerClient:
    global CODE_WORKER_CLIENT
    if CODE_WORKER_CLIENT is None:
        CODE_WORKER_CLIENT = CodeWorkerClient()
    return CODE_WORKER_CLIENT


def _get_github_catalog_client() -> GitHubCatalogClient:
    global GITHUB_CATALOG_CLIENT
    if GITHUB_CATALOG_CLIENT is None:
        GITHUB_CATALOG_CLIENT = GitHubCatalogClient()
    return GITHUB_CATALOG_CLIENT


def _capability_key(participant_identity: str, room: str) -> str:
    return f"{participant_identity}:{room}"


def get_capability_mode(participant_identity: str, room: str) -> str:
    key = _capability_key(participant_identity, room)
    mode = CAPABILITY_MODE_BY_PARTICIPANT.get(key)
    if mode is None:
        stored = _load_session_namespace(participant_identity, room, "capability_mode")
        if isinstance(stored, str):
            mode = stored
            CAPABILITY_MODE_BY_PARTICIPANT[key] = stored
        else:
            mode = "default"
    return mode if mode in {"default", "coding"} else "default"


def set_capability_mode(participant_identity: str, room: str, mode: str) -> str:
    normalized = mode.strip().casefold().replace("-", "_")
    resolved = "coding" if normalized in {"coding", "codex"} else "default"
    CAPABILITY_MODE_BY_PARTICIPANT[_capability_key(participant_identity, room)] = resolved
    _persist_session_namespace(participant_identity, room, "capability_mode", resolved)
    return resolved


def _capability_payload(participant_identity: str, room: str) -> JsonObject:
    return {"coding_mode": get_capability_mode(participant_identity, room)}


def _project_key(participant_identity: str, room: str) -> str:
    return f"{participant_identity}:{room}"


def get_active_project(participant_identity: str, room: str) -> ActiveProjectMode | None:
    key = _project_key(participant_identity, room)
    active = ACTIVE_PROJECT_BY_PARTICIPANT.get(key)
    if active is not None:
        return active
    stored = _load_session_namespace(participant_identity, room, "active_project")
    loaded = _active_project_from_payload(stored)
    if loaded is not None:
        ACTIVE_PROJECT_BY_PARTICIPANT[key] = loaded
    return loaded


def set_active_project(participant_identity: str, room: str, project: ActiveProjectMode) -> None:
    key = _project_key(participant_identity, room)
    ACTIVE_PROJECT_BY_PARTICIPANT[key] = project
    _persist_session_namespace(participant_identity, room, "active_project", asdict(project))


def clear_active_project(participant_identity: str, room: str) -> None:
    ACTIVE_PROJECT_BY_PARTICIPANT.pop(_project_key(participant_identity, room), None)
    _delete_session_namespace(participant_identity, room, "active_project")


def _active_project_payload(participant_identity: str, room: str) -> JsonObject:
    active = get_active_project(participant_identity, room)
    if active is None:
        return {
            "active_project": None,
            "active_project_name": None,
        }
    return {
        "active_project": {
            "project_id": active.project_id,
            "name": active.name,
            "root_path": active.root_path,
            "aliases": active.aliases,
            "selected_at": active.selected_at,
            "selection_reason": active.selection_reason,
            "index_status": active.index_status,
        },
        "active_project_name": active.name,
    }


def _codex_key(participant_identity: str, room: str) -> str:
    return f"{participant_identity}:{room}"


def _codex_task_to_payload(task: ActiveCodexTask) -> JsonObject:
    payload: JsonObject = {
        "task_id": task.task_id,
        "status": task.status,
        "project_id": task.project_id,
        "project_name": task.project_name,
        "working_directory": task.working_directory,
        "request": task.request,
        "started_at": task.started_at,
    }
    if task.finished_at is not None:
        payload["finished_at"] = task.finished_at
    if task.current_phase is not None:
        payload["current_phase"] = task.current_phase
    if task.summary is not None:
        payload["summary"] = task.summary
    if task.exit_code is not None:
        payload["exit_code"] = task.exit_code
    if task.raw_last_event is not None:
        payload["raw_last_event"] = task.raw_last_event
    if task.command_preview is not None:
        payload["command_preview"] = task.command_preview
    if task.error is not None:
        payload["error"] = task.error
    return payload


def get_active_codex_task(participant_identity: str, room: str) -> ActiveCodexTask | None:
    key = _codex_key(participant_identity, room)
    active = ACTIVE_CODEX_TASK_BY_PARTICIPANT.get(key)
    if active is not None:
        return active
    stored = _load_session_namespace(participant_identity, room, "active_codex_task")
    loaded = _active_codex_task_from_payload(stored)
    if loaded is not None:
        ACTIVE_CODEX_TASK_BY_PARTICIPANT[key] = loaded
    return loaded


def set_active_codex_task(participant_identity: str, room: str, task: ActiveCodexTask) -> None:
    key = _codex_key(participant_identity, room)
    ACTIVE_CODEX_TASK_BY_PARTICIPANT[key] = task
    _persist_session_namespace(
        participant_identity,
        room,
        "active_codex_task",
        _codex_task_to_payload(task),
    )


def _codex_history_payload(participant_identity: str, room: str) -> list[JsonObject]:
    key = _codex_key(participant_identity, room)
    history = CODEX_TASK_HISTORY_BY_PARTICIPANT.get(key)
    if history is None:
        stored = _load_session_namespace(participant_identity, room, "codex_history")
        if isinstance(stored, list):
            history = [dict(item) for item in stored if isinstance(item, dict)]
            CODEX_TASK_HISTORY_BY_PARTICIPANT[key] = history
        else:
            history = []
    return [dict(item) for item in history[:8]]


def _push_codex_history(participant_identity: str, room: str, task: ActiveCodexTask) -> None:
    key = _codex_key(participant_identity, room)
    entry = _codex_task_to_payload(task)
    current = CODEX_TASK_HISTORY_BY_PARTICIPANT.get(key, [])
    filtered = [item for item in current if str(item.get("task_id", "")) != task.task_id]
    next_history = [entry, *filtered][:8]
    CODEX_TASK_HISTORY_BY_PARTICIPANT[key] = next_history
    _persist_session_namespace(participant_identity, room, "codex_history", next_history)


async def _publish_agent_event(ctx: ActionContext, payload: JsonObject) -> None:
    await publish_session_event(ctx.session, payload)


async def _emit_codex_task_event(
    ctx: ActionContext,
    *,
    event_type: str,
    task: ActiveCodexTask,
    phase: str,
    message: str,
    raw_event_type: str | None = None,
) -> None:
    await _publish_agent_event(
        ctx,
        {
            "type": event_type,
            "codex_task": _codex_task_to_payload(task),
            "codex_event": {
                "task_id": task.task_id,
                "phase": phase,
                "message": message,
                "timestamp": _now_iso(),
                "raw_event_type": raw_event_type,
            },
            "codex_history": _codex_history_payload(ctx.participant_identity, ctx.room),
        },
    )


def _append_event_state_list(
    participant_identity: str,
    room: str,
    namespace: str,
    entry: JsonObject,
    *,
    key: str | None = None,
    limit: int = 40,
) -> None:
    current = _load_event_namespace(participant_identity, room, namespace)
    rows = [dict(item) for item in current] if isinstance(current, list) else []
    if key:
        entry_key = str(entry.get(key) or "").strip()
        if entry_key:
            rows = [item for item in rows if str(item.get(key) or "").strip() != entry_key]
    next_rows = [entry, *rows][:limit]
    _persist_event_namespace(participant_identity, room, namespace, next_rows)


def _persist_result_state(ctx: ActionContext, action_name: str, result: ActionResult) -> None:
    data = result.data if isinstance(result.data, dict) else {}
    if not data:
        return

    participant_identity = ctx.participant_identity
    room = ctx.room

    if isinstance(data.get("model_route"), dict):
        _persist_event_namespace(participant_identity, room, "model_route", data.get("model_route"))

    subagent_states = data.get("subagent_states")
    if isinstance(subagent_states, list):
        _persist_event_namespace(
            participant_identity,
            room,
            "subagent_states",
            [item for item in subagent_states if isinstance(item, dict)],
        )
    else:
        subagent_state = data.get("subagent_state")
        if isinstance(subagent_state, dict):
            _append_event_state_list(
                participant_identity,
                room,
                "subagent_states",
                subagent_state,
                key="subagent_id",
            )

    if isinstance(data.get("policy"), dict):
        policy_entry = dict(data["policy"])
        policy_entry.setdefault("action_name", action_name)
        _append_event_state_list(
            participant_identity,
            room,
            "policy_events",
            policy_entry,
            key="signature",
        )

    if result.trace_id:
        trace_entry = {
            "traceId": result.trace_id,
            "actionName": action_name,
            "timestamp": int(time.time() * 1000),
            "risk": result.risk,
            "policyDecision": result.policy_decision,
            "provider": result.evidence.get("provider") if isinstance(result.evidence, dict) else None,
            "fallbackUsed": result.fallback_used,
            "success": result.success,
            "message": result.message,
        }
        _append_event_state_list(
            participant_identity,
            room,
            "execution_traces",
            trace_entry,
            key="traceId",
            limit=120,
        )

    if isinstance(data.get("web_dashboard_schedule"), dict):
        schedule = dict(data["web_dashboard_schedule"])
        current = _load_event_namespace(participant_identity, room, "research_schedules")
        rows = [dict(item) for item in current] if isinstance(current, list) else []
        schedule_id = str(schedule.get("id") or "").strip()
        next_rows = [schedule, *[item for item in rows if str(item.get("id") or "").strip() != schedule_id]]
        _persist_event_namespace(participant_identity, room, "research_schedules", next_rows[:40])

    for source_key, namespace in (
        ("eval_baseline_summary", "eval_baseline_summary"),
        ("eval_metrics", "eval_metrics"),
        ("eval_metrics_summary", "eval_metrics_summary"),
        ("slo_report", "slo_report"),
        ("providers_health", "providers_health"),
        ("feature_flags", "feature_flags"),
        ("canary_state", "canary_state"),
        ("ops_incident_snapshot", "incident_snapshot"),
        ("ops_playbook_report", "playbook_report"),
        ("ops_auto_remediation", "auto_remediation"),
        ("ops_canary_promotion", "canary_promotion"),
        ("ops_control_tick", "control_tick"),
        ("browser_task", "browser_tasks"),
        ("workflow_state", "workflow_state"),
        ("automation_state", "automation_state"),
        ("whatsapp_channel", "whatsapp_channel"),
    ):
        payload = data.get(source_key)
        if payload is not None:
            _persist_event_namespace(participant_identity, room, namespace, payload)


async def _publish_session_snapshot_for_context(ctx: ActionContext) -> None:
    if ctx.session is None:
        return
    try:
        from session_snapshot import publish_session_snapshot

        await publish_session_snapshot(
            ctx.session,
            participant_identity=ctx.participant_identity,
            room=ctx.room,
        )
    except Exception:
        logger.warning("failed to publish session snapshot", exc_info=True)


def _project_record_to_payload(record: ProjectRecord) -> JsonObject:
    return {
        "project_id": record.project_id,
        "name": record.name,
        "root_path": record.root_path,
        "aliases": list(record.aliases),
        "git_remote_url": record.git_remote_url,
        "stack_tags": list(record.stack_tags or []),
        "last_indexed_at": record.last_indexed_at,
        "last_scanned_at": record.last_scanned_at,
        "is_active": record.is_active,
        "priority_score": record.priority_score,
        "notes": record.notes,
    }


def _detect_git_branch(root_path: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=root_path,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception:  # noqa: BLE001
        return None

    if completed.returncode != 0:
        return None
    branch = completed.stdout.strip()
    return branch or None


def _build_codex_request_prompt(*, record: ProjectRecord, user_request: str, review_mode: bool = False) -> str:
    branch = _detect_git_branch(record.root_path) or "desconhecida"
    mode_label = "review tecnico" if review_mode else "analise tecnica"
    return (
        "Voce esta operando para o Jarvez em modo de leitura.\n"
        f"Projeto: {record.name}\n"
        f"Diretorio: {record.root_path}\n"
        f"Branch atual: {branch}\n"
        f"Tarefa: {mode_label}\n\n"
        f"Pedido do usuario:\n{user_request}\n\n"
        "Regras obrigatorias:\n"
        "- Nao faca mudancas em arquivos.\n"
        "- Nao rode comandos mutaveis.\n"
        "- Trabalhe apenas com analise, planejamento, explicacao ou review.\n"
        "- Baseie-se no repositorio local atual.\n"
        "- Responda com: resumo, arquivos provaveis, riscos e proximos passos.\n"
    )


def _codex_progress_message(event: JsonObject) -> str:
    for key in ("message", "summary", "text", "content", "delta"):
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    item = event.get("item")
    if isinstance(item, dict):
        for key in ("text", "content", "summary"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    event_type = str(event.get("type", "")).strip() or "evento"
    return f"Codex enviou {event_type}."


def _github_repo_to_payload(repo: GitHubRepo) -> JsonObject:
    return {
        "repo_id": repo.repo_id,
        "name": repo.name,
        "full_name": repo.full_name,
        "owner": repo.owner,
        "private": repo.private,
        "default_branch": repo.default_branch,
        "clone_url": repo.clone_url,
        "html_url": repo.html_url,
        "description": repo.description,
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
    session = AUTHENTICATED_SESSIONS.pop(identity, None)
    if session is not None:
        try:
            STATE_STORE.delete_authenticated_session(
                participant_identity=identity,
                room=session.room,
            )
        except Exception:
            logger.warning("failed to delete authenticated session", exc_info=True)
    VOICE_STEP_UP_PENDING.pop(identity, None)


def _set_authenticated(identity: str, room: str, auth_method: str) -> None:
    now = datetime.now(timezone.utc)
    session = AuthenticatedSession(
        participant_identity=identity,
        room=room,
        expires_at=now + timedelta(seconds=_security_ttl_seconds()),
        auth_method=auth_method,
        last_activity_at=now,
    )
    AUTHENTICATED_SESSIONS[identity] = session
    try:
        STATE_STORE.save_authenticated_session(
            participant_identity=identity,
            room=room,
            auth_method=auth_method,
            expires_at=session.expires_at,
            last_activity_at=session.last_activity_at,
        )
    except Exception:
        logger.warning("failed to persist authenticated session", exc_info=True)
    VOICE_STEP_UP_PENDING.pop(identity, None)


def _touch_authenticated(identity: str) -> None:
    session = AUTHENTICATED_SESSIONS.get(identity)
    if session is None:
        return
    session.last_activity_at = datetime.now(timezone.utc)
    try:
        STATE_STORE.save_authenticated_session(
            participant_identity=identity,
            room=session.room,
            auth_method=session.auth_method,
            expires_at=session.expires_at,
            last_activity_at=session.last_activity_at,
        )
    except Exception:
        logger.warning("failed to update authenticated session", exc_info=True)


def _is_authenticated(identity: str, room: str) -> bool:
    session = AUTHENTICATED_SESSIONS.get(identity)
    if session is None:
        stored = STATE_STORE.get_authenticated_session(participant_identity=identity, room=room)
        if isinstance(stored, dict):
            expires_at = _parse_datetime(stored.get("expires_at"))
            last_activity_at = _parse_datetime(stored.get("last_activity_at"))
            auth_method = str(stored.get("auth_method") or "").strip()
            if expires_at is not None and last_activity_at is not None and auth_method:
                session = AuthenticatedSession(
                    participant_identity=identity,
                    room=room,
                    expires_at=expires_at,
                    auth_method=auth_method,
                    last_activity_at=last_activity_at,
                )
                AUTHENTICATED_SESSIONS[identity] = session
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
        **_active_project_payload(identity, room),
        **_capability_payload(identity, room),
    }


def _workspace_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _normalize_alias_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.strip().casefold())


def _desktop_allowed_apps() -> set[str]:
    raw = os.getenv(
        "JARVEZ_ALLOWED_DESKTOP_APPS",
        "chrome,chrome.exe,msedge,msedge.exe,firefox,firefox.exe,explorer,explorer.exe,"
        "code,code.cmd,notepad,notepad.exe,wt,wt.exe,cmd,cmd.exe,powershell,powershell.exe,pwsh,pwsh.exe",
    ).strip()
    values = [item.strip().casefold() for item in raw.split(",") if item.strip()]
    return set(values)


def _desktop_allowed_commands() -> set[str]:
    raw = os.getenv(
        "JARVEZ_ALLOWED_LOCAL_COMMANDS",
        "git,git.exe,python,python.exe,node,node.exe,npm,npm.cmd,npx,npx.cmd,pnpm,pnpm.cmd,"
        "code,code.cmd,explorer,explorer.exe,notepad,notepad.exe,wt,wt.exe",
    ).strip()
    values = [item.strip().casefold() for item in raw.split(",") if item.strip()]
    return set(values)


def _unsafe_shell_enabled() -> bool:
    raw = os.getenv("JARVEZ_ALLOW_UNSAFE_SHELL", "").strip().casefold()
    return raw in {"1", "true", "yes", "on"}


def _desktop_site_aliases() -> dict[str, str]:
    return {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "gmail": "https://mail.google.com",
        "github": "https://github.com",
        "whatsapp": "https://web.whatsapp.com",
        "spotify": "https://open.spotify.com",
        "notion": "https://www.notion.so",
        "linear": "https://linear.app",
    }


def _desktop_folder_aliases() -> dict[str, Path]:
    home = Path.home()
    one_drive_raw = os.getenv("OneDrive", "").strip()
    one_drive = Path(one_drive_raw).expanduser() if one_drive_raw else None
    desktop_root = one_drive if one_drive and one_drive.exists() else home
    workspace = _workspace_root()
    return {
        "desktop": desktop_root / "Desktop",
        "downloads": home / "Downloads",
        "documents": home / "Documents",
        "pictures": home / "Pictures",
        "music": home / "Music",
        "videos": home / "Videos",
        "repo": workspace,
        "project": workspace,
        "workspace": workspace,
    }


def _desktop_app_aliases() -> dict[str, str]:
    return {
        "chrome": "chrome.exe",
        "edge": "msedge.exe",
        "firefox": "firefox.exe",
        "explorer": "explorer.exe",
        "vscode": "code.cmd",
        "code": "code.cmd",
        "notepad": "notepad.exe",
        "terminal": "wt.exe",
        "wt": "wt.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
        "pwsh": "pwsh.exe",
    }


def _local_command_aliases() -> dict[str, str]:
    return {
        "vscode": "code.cmd",
        "code": "code.cmd",
        "terminal": "wt.exe",
        "wt": "wt.exe",
        "git": "git",
        "python": "python",
        "node": "node",
        "npm": "npm.cmd",
        "npx": "npx.cmd",
        "pnpm": "pnpm.cmd",
        "explorer": "explorer.exe",
        "notepad": "notepad.exe",
    }


def _looks_like_url(value: str) -> bool:
    text = value.strip()
    if not text:
        return False
    if re.fullmatch(r"[a-zA-Z]:[\\/].+", text):
        return False
    if "\\" in text:
        return False
    parsed = urlparse(text)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return True
    if text.startswith("www."):
        return True
    if " " in text:
        return False
    if "." in text and "/" not in text:
        suffix = text.rsplit(".", 1)[-1].casefold()
        return suffix in {"com", "br", "dev", "app", "ai", "org", "net", "io", "gg", "tv", "co"}
    return False


def _normalize_url(value: str) -> str:
    text = value.strip()
    if text.startswith(("http://", "https://")):
        return text
    return f"https://{text.lstrip('/')}"


def _resolve_local_path(raw_path: str, *, must_exist: bool = False) -> Path | None:
    candidate_raw = os.path.expandvars(raw_path.strip())
    if not candidate_raw:
        return None
    candidate = Path(candidate_raw).expanduser()
    if not candidate.is_absolute():
        candidate = _workspace_root() / candidate
    candidate = candidate.resolve(strict=False)
    if must_exist and not candidate.exists():
        return None
    return candidate


def _github_default_clone_root() -> Path:
    raw = os.getenv("GITHUB_DEFAULT_CLONE_ROOT", "external-repos").strip()
    resolved = _resolve_local_path(raw, must_exist=False)
    target = resolved or (_workspace_root() / "external-repos")
    target.mkdir(parents=True, exist_ok=True)
    return target


def _resolve_open_resource_target(target: str, target_kind: str) -> tuple[str | None, Any, str | None]:
    normalized = _normalize_alias_token(target)

    if target_kind in {"auto", "url"}:
        site_url = _desktop_site_aliases().get(normalized)
        if site_url:
            return "url", site_url, None
        if _looks_like_url(target):
            return "url", _normalize_url(target), None
        if target_kind == "url":
            return None, None, "URL invalida ou nao reconhecida."

    if target_kind in {"auto", "path"}:
        folder = _desktop_folder_aliases().get(normalized)
        if folder and folder.exists():
            return "path", str(folder.resolve(strict=False)), None
        resolved_path = _resolve_local_path(target, must_exist=True)
        if resolved_path is not None:
            return "path", str(resolved_path), None
        if target_kind == "path":
            return None, None, "Caminho nao encontrado."

    if target_kind in {"auto", "app"}:
        alias = _desktop_app_aliases().get(normalized)
        candidate = alias or target.strip()
        if candidate:
            basename = Path(candidate).name.casefold()
            if basename in _desktop_allowed_apps():
                return "app", [shutil.which(candidate) or candidate], None
        if target_kind == "app":
            return None, None, "Aplicativo nao permitido ou nao reconhecido."

    return None, None, "Nao consegui identificar se isso e site, pasta/arquivo ou aplicativo."


def _resolve_local_command(raw_command: str) -> tuple[str | None, str | None]:
    normalized = _normalize_alias_token(raw_command)
    candidate = _local_command_aliases().get(normalized) or raw_command.strip()
    if not candidate:
        return None, "Comando ausente."
    basename = Path(candidate).name.casefold()
    if basename in {"cmd", "cmd.exe", "powershell", "powershell.exe", "pwsh", "pwsh.exe"} and not _unsafe_shell_enabled():
        return None, "Shell interativo bloqueado por seguranca. Defina JARVEZ_ALLOW_UNSAFE_SHELL=1 se quiser liberar."
    if basename not in _desktop_allowed_commands():
        return None, f"Comando nao permitido: {basename}."
    return shutil.which(candidate) or candidate, None


def _detached_creation_flags() -> int:
    return getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)


def _launch_detached(command: list[str], *, cwd: Path | None = None) -> None:
    subprocess.Popen(
        command,
        cwd=str(cwd) if cwd else None,
        creationflags=_detached_creation_flags(),
        close_fds=True,
    )


def _trim_process_output(value: str, limit: int = 1200) -> str:
    text = value.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _collapse_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _strip_html_tags(value: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", value, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return _collapse_spaces(html.unescape(text))


def _truncate_text(value: str, limit: int = 240) -> str:
    text = _collapse_spaces(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


class _DuckDuckGoSearchParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[JsonObject] = []
        self._capture_title = False
        self._capture_snippet = False
        self._title_depth = 0
        self._snippet_depth = 0
        self._title_parts: list[str] = []
        self._snippet_parts: list[str] = []
        self._current_href = ""
        self._current_result: JsonObject | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: value or "" for key, value in attrs}
        css_class = attributes.get("class", "")

        if tag == "a" and "result__a" in css_class and not self._capture_title:
            self._capture_title = True
            self._title_depth = 1
            self._title_parts = []
            self._current_href = attributes.get("href", "")
            return

        if self._capture_title:
            self._title_depth += 1

        if "result__snippet" in css_class and not self._capture_snippet:
            self._capture_snippet = True
            self._snippet_depth = 1
            self._snippet_parts = []
            return

        if self._capture_snippet:
            self._snippet_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self._capture_title:
            self._title_depth -= 1
            if self._title_depth <= 0:
                self._capture_title = False
                title = _collapse_spaces(html.unescape("".join(self._title_parts)))
                if title and self._current_href:
                    self._current_result = {
                        "title": title,
                        "url": self._current_href,
                    }
                    self.results.append(self._current_result)
                self._title_parts = []
                self._current_href = ""
                return

        if self._capture_snippet:
            self._snippet_depth -= 1
            if self._snippet_depth <= 0:
                self._capture_snippet = False
                snippet = _collapse_spaces(html.unescape("".join(self._snippet_parts)))
                if snippet and self._current_result is not None and not self._current_result.get("snippet"):
                    self._current_result["snippet"] = snippet
                self._snippet_parts = []

    def handle_data(self, data: str) -> None:
        if self._capture_title:
            self._title_parts.append(data)
        if self._capture_snippet:
            self._snippet_parts.append(data)


def _normalize_search_url(raw_url: str) -> str:
    url = raw_url.strip()
    if not url:
        return ""
    if url.startswith("//"):
        url = "https:" + url
    parsed = urlparse(url)
    if parsed.netloc.endswith("duckduckgo.com"):
        target = parse_qs(parsed.query).get("uddg", [])
        if target:
            return unquote(target[0]).strip()
    return url


def _duckduckgo_blocked(search_html: str) -> bool:
    haystack = search_html.casefold()
    return "anomaly-modal" in haystack or "bots use duckduckgo too" in haystack


def _fetch_web_text(url: str, *, timeout: int = 8) -> str | None:
    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
                )
            },
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.RequestException:
        return None
    response.encoding = response.encoding or response.apparent_encoding or "utf-8"
    return response.text


def _fetch_web_json(url: str, *, params: JsonObject | None = None, timeout: int = 8) -> Any | None:
    try:
        response = requests.get(
            url,
            params=params,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
                )
            },
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        return None


def _extract_meta_content(page_html: str, *patterns: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, page_html, flags=re.IGNORECASE)
        if not match:
            continue
        value = _collapse_spaces(html.unescape(match.group(1)))
        if value:
            return value
    return None


def _page_preview_from_url(url: str) -> JsonObject:
    page_html = _fetch_web_text(url, timeout=5)
    if not page_html:
        return {}

    title = _extract_meta_content(page_html, r"<title[^>]*>(.*?)</title>")
    description = _extract_meta_content(
        page_html,
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
        r'<meta[^>]+content=["\'](.*?)["\'][^>]+name=["\']description["\']',
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']',
    )
    image_url = _extract_meta_content(
        page_html,
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](.*?)["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\'](.*?)["\']',
    )
    return {
        "page_title": _truncate_text(title or "", 160) if title else None,
        "page_description": _truncate_text(description or "", 220) if description else None,
        "image_url": image_url,
    }


def _frontend_dashboard_url() -> str:
    base_url = os.getenv("JARVEZ_FRONTEND_URL", "http://127.0.0.1:3001").strip().rstrip("/")
    if not base_url:
        base_url = "http://127.0.0.1:3001"
    return f"{base_url}/research-dashboard"


def _gemini_web_search_model() -> str:
    return os.getenv("JARVEZ_WEB_SEARCH_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"


def _run_gemini_google_search(query: str, *, max_results: int = 5) -> tuple[str, list[JsonObject], ActionResult | None]:
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        return (
            "",
            [],
            ActionResult(
                success=False,
                message="GOOGLE_API_KEY nao configurada para pesquisa web.",
                error="missing google api key",
            ),
        )

    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{_gemini_web_search_model()}:generateContent"
    )
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "Pesquise no Google e responda de forma objetiva, citando fatos verificaveis. "
                            "Pedido do usuario: "
                            f"{query}"
                        )
                    }
                ],
            }
        ],
        "tools": [{"google_search": {}}],
    }

    try:
        response = requests.post(
            endpoint,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        response_payload = response.json()
    except (requests.RequestException, ValueError) as error:
        return (
            "",
            [],
            ActionResult(
                success=False,
                message="Falha ao pesquisar com Google Search no Gemini.",
                error=str(error),
            ),
        )

    candidates = response_payload.get("candidates", [])
    if not isinstance(candidates, list) or not candidates:
        return (
            "",
            [],
            ActionResult(
                success=False,
                message="O Gemini nao retornou candidatos para a pesquisa.",
                error="missing candidates",
            ),
        )

    candidate = candidates[0] if isinstance(candidates[0], dict) else {}
    parts = candidate.get("content", {}).get("parts", [])
    answer_text_parts = [
        _collapse_spaces(str(part.get("text", "")))
        for part in parts
        if isinstance(part, dict) and str(part.get("text", "")).strip()
    ]
    answer_text = _collapse_spaces("\n".join(answer_text_parts))

    grounding = candidate.get("groundingMetadata", {})
    grounding_chunks = grounding.get("groundingChunks", [])
    grounding_supports = grounding.get("groundingSupports", [])

    results: list[JsonObject] = []
    seen_urls: set[str] = set()
    chunk_snippets: dict[int, list[str]] = {}
    if isinstance(grounding_supports, list):
        for support in grounding_supports:
            if not isinstance(support, dict):
                continue
            segment = support.get("segment", {})
            snippet = _collapse_spaces(str(segment.get("text", "")).strip())
            if not snippet:
                continue
            indices = support.get("groundingChunkIndices", [])
            if not isinstance(indices, list):
                continue
            for index in indices:
                if isinstance(index, int):
                    chunk_snippets.setdefault(index, []).append(snippet)

    if isinstance(grounding_chunks, list):
        for index, chunk in enumerate(grounding_chunks):
            if not isinstance(chunk, dict):
                continue
            web_chunk = chunk.get("web", {})
            if not isinstance(web_chunk, dict):
                continue
            url = str(web_chunk.get("uri", "")).strip()
            title = _collapse_spaces(str(web_chunk.get("title", "")).strip())
            if not url or url in seen_urls:
                continue

            seen_urls.add(url)
            preview = _page_preview_from_url(url)
            snippet_parts = chunk_snippets.get(index, [])
            snippet = _truncate_text(" ".join(snippet_parts), 280) if snippet_parts else ""
            if not snippet:
                snippet = str(preview.get("page_description") or "").strip()

            parsed = urlparse(url)
            results.append(
                {
                    "title": _truncate_text(title or str(preview.get("page_title") or "Resultado"), 160),
                    "url": url,
                    "domain": parsed.netloc.replace("www.", "").strip() or "site",
                    "snippet": snippet,
                    "page_title": preview.get("page_title") or (title if title else None),
                    "page_description": preview.get("page_description"),
                    "image_url": preview.get("image_url"),
                }
            )
            if len(results) >= max_results:
                break

    return answer_text, results, None


def _run_web_search(query: str, *, max_results: int = 5) -> tuple[list[JsonObject], ActionResult | None]:
    answer_text, results, error = _run_gemini_google_search(query, max_results=max_results)
    if error is not None:
        return [], error
    if not results:
        return (
            [],
            ActionResult(
                success=bool(answer_text),
                message=answer_text or f"Nao encontrei resultados confiaveis para '{query}'.",
                data={
                    "web_dashboard": {
                        "query": query,
                        "summary": answer_text or "",
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "results": [],
                        "images": [],
                    }
                }
                if answer_text
                else None,
                error=None if answer_text else "no search results",
            ),
        )

    return results, None


def _build_web_dashboard_summary(query: str, results: list[JsonObject]) -> str:
    lead_points: list[str] = []
    for item in results[:3]:
        title = str(item.get("title", "")).strip()
        snippet = str(item.get("snippet") or item.get("page_description") or "").strip()
        domain = str(item.get("domain", "")).strip()
        if title and snippet:
            lead_points.append(f"{title}: {snippet}")
        elif snippet:
            lead_points.append(f"{domain}: {snippet}")
        elif title:
            lead_points.append(f"{domain}: {title}")

    if not lead_points:
        return f"Resumo web pronto para '{query}', mas os sites retornaram pouco contexto textual."

    summary = " | ".join(lead_points)
    return _truncate_text(f"Resumo consolidado para '{query}': {summary}", 900)


async def _web_search_dashboard(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    query = _collapse_spaces(str(params.get("query", "")))
    max_results = int(params.get("max_results", 5))
    if not query:
        return ActionResult(success=False, message="Informe o que devo pesquisar na web.", error="missing query")

    max_results = max(3, min(max_results, 8))
    results, search_error = _run_web_search(query, max_results=max_results)
    if search_error is not None:
        return search_error

    image_urls = [
        str(item["image_url"])
        for item in results
        if isinstance(item.get("image_url"), str) and str(item.get("image_url")).strip()
    ][:4]
    summary = _build_web_dashboard_summary(query, results)
    generated_at = datetime.now(timezone.utc).isoformat()
    dashboard_url = _frontend_dashboard_url()
    dashboard_opened = False

    try:
        dashboard_opened = bool(webbrowser.open(dashboard_url, new=2))
    except OSError:
        dashboard_opened = False

    return ActionResult(
        success=True,
        message=f"Pesquisa web compilada para '{query}'.",
        data={
            "web_dashboard": {
                "query": query,
                "summary": summary,
                "generated_at": generated_at,
                "results": results,
                "images": image_urls,
                "dashboard_url": dashboard_url,
                "dashboard_opened": dashboard_opened,
            }
        },
    )


async def _save_web_briefing_schedule(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    query = _collapse_spaces(str(params.get("query", "")))
    time_of_day = _collapse_spaces(str(params.get("time_of_day", "08:00"))) or "08:00"

    if not query:
        return ActionResult(success=False, message="Informe o tema da pesquisa recorrente.", error="missing query")

    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", time_of_day):
        return ActionResult(success=False, message="Horario invalido. Use HH:MM.", error="invalid time_of_day")

    schedule_id = f"research-{secrets.token_hex(6)}"
    schedule = {
        "id": schedule_id,
        "query": query,
        "cadence": "daily",
        "time_of_day": time_of_day,
        "prompt": (
            "Faça uma pesquisa na internet e gere um dashboard completo com resumo, links e imagens sobre: "
            f"{query}"
        ),
    }

    return ActionResult(
        success=True,
        message=f"Briefing diario salvo para {time_of_day}.",
        data={"web_dashboard_schedule": schedule},
    )


async def _open_desktop_resource(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    target = str(params.get("target", "")).strip()
    target_kind = str(params.get("target_kind", "auto")).strip().casefold() or "auto"
    if not target:
        return ActionResult(success=False, message="Informe o recurso que devo abrir.", error="missing target")

    resolved_kind, resolved_value, resolution_error = _resolve_open_resource_target(target, target_kind)
    if resolved_kind is None:
        return ActionResult(success=False, message=resolution_error or "Nao consegui abrir o recurso.", error="invalid target")

    try:
        if resolved_kind == "url":
            opened = webbrowser.open(str(resolved_value), new=2)
            if not opened:
                return ActionResult(success=False, message="O navegador nao aceitou abrir o link.", error="browser open failed")
        elif resolved_kind == "path":
            if not hasattr(os, "startfile"):
                return ActionResult(success=False, message="Abrir arquivos/pastas so esta disponivel no Windows.", error="startfile unavailable")
            os.startfile(str(resolved_value))
        else:
            _launch_detached(list(resolved_value), cwd=_workspace_root())
    except OSError as error:
        return ActionResult(success=False, message=f"Falha ao abrir o recurso: {error}", error=str(error))

    return ActionResult(
        success=True,
        message=f"Recurso aberto: {target}.",
        data={
            "target": target,
            "resolved_target": str(resolved_value),
            "target_kind": resolved_kind,
        },
    )


async def _run_local_command(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    command = str(params.get("command", "")).strip()
    arguments = params.get("arguments", [])
    working_directory = str(params.get("working_directory", "")).strip()
    wait_for_exit = bool(params.get("wait_for_exit", True))
    timeout_seconds = int(params.get("timeout_seconds", 60))

    if not isinstance(arguments, list) or any(not isinstance(item, str) for item in arguments):
        return ActionResult(success=False, message="`arguments` precisa ser uma lista de textos.", error="invalid arguments")

    resolved_command, command_error = _resolve_local_command(command)
    if resolved_command is None:
        return ActionResult(success=False, message=command_error or "Comando nao permitido.", error="command blocked")

    if working_directory:
        cwd = _resolve_local_path(working_directory, must_exist=True)
        if cwd is None or not cwd.is_dir():
            return ActionResult(success=False, message="Diretorio de trabalho nao encontrado.", error="invalid working directory")
    else:
        cwd = _workspace_root()

    command_line = [resolved_command, *arguments]

    try:
        if not wait_for_exit:
            _launch_detached(command_line, cwd=cwd)
            return ActionResult(
                success=True,
                message="Comando iniciado em segundo plano.",
                data={
                    "command_line": command_line,
                    "working_directory": str(cwd),
                    "wait_for_exit": False,
                },
            )

        completed = subprocess.run(
            command_line,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=max(1, min(timeout_seconds, 600)),
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return ActionResult(success=False, message=f"Falha ao executar o comando: {error}", error=str(error))

    stdout = _trim_process_output(completed.stdout or "")
    stderr = _trim_process_output(completed.stderr or "")
    success = completed.returncode == 0
    return ActionResult(
        success=success,
        message="Comando executado com sucesso." if success else "O comando terminou com erro.",
        data={
            "command_line": command_line,
            "working_directory": str(cwd),
            "returncode": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "wait_for_exit": True,
        },
        error=None if success else stderr or f"exit code {completed.returncode}",
    )


async def _git_clone_repository(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    repository_url = str(params.get("repository_url", "")).strip()
    destination = str(params.get("destination", "")).strip()
    branch = str(params.get("branch", "")).strip()
    depth = params.get("depth")

    if not repository_url:
        return ActionResult(success=False, message="Informe a URL do repositorio.", error="missing repository url")

    destination_path: Path | None = None
    if destination:
        destination_path = _resolve_local_path(destination, must_exist=False)
        if destination_path is None:
            return ActionResult(success=False, message="Destino invalido.", error="invalid destination")
        if destination_path.exists():
            return ActionResult(success=False, message="O destino informado ja existe.", error="destination exists")
        destination_path.parent.mkdir(parents=True, exist_ok=True)

    command_line = ["git", "clone"]
    if branch:
        command_line.extend(["--branch", branch])
    if isinstance(depth, int) and depth > 0:
        command_line.extend(["--depth", str(depth)])
    command_line.append(repository_url)
    if destination_path is not None:
        command_line.append(str(destination_path))

    try:
        completed = subprocess.run(
            command_line,
            cwd=str(_workspace_root()),
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return ActionResult(success=False, message=f"Falha ao executar git clone: {error}", error=str(error))

    stdout = _trim_process_output(completed.stdout or "")
    stderr = _trim_process_output(completed.stderr or "")
    if completed.returncode != 0:
        return ActionResult(
            success=False,
            message="O git clone falhou.",
            data={
                "command_line": command_line,
                "stdout": stdout,
                "stderr": stderr,
                "returncode": completed.returncode,
            },
            error=stderr or f"exit code {completed.returncode}",
        )

    return ActionResult(
        success=True,
        message="Repositorio clonado com sucesso.",
        data={
            "command_line": command_line,
            "destination": str(destination_path) if destination_path is not None else str(_workspace_root()),
            "stdout": stdout,
            "stderr": stderr,
            "returncode": completed.returncode,
        },
    )


async def _git_commit_and_push_project_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    record, error = _resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None

    commit_message = (
        str(params.get("message", "")).strip()
        or str(params.get("commit_message", "")).strip()
        or str(params.get("summary", "")).strip()
    )
    if not commit_message:
        return ActionResult(success=False, message="Informe a mensagem do commit.", error="missing commit message")

    root = Path(record.root_path).resolve(strict=False)
    if not root.exists():
        return ActionResult(success=False, message="A raiz do projeto nao existe.", error="missing project root")

    def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )

    try:
        status = run_git(["status", "--porcelain"])
        if status.returncode != 0:
            return ActionResult(
                success=False,
                message="Nao consegui ler o estado do git.",
                data={
                    "project": _project_record_to_payload(record),
                    "git_status": {
                        "returncode": status.returncode,
                        "stdout": _trim_process_output(status.stdout or ""),
                        "stderr": _trim_process_output(status.stderr or ""),
                        "success": False,
                    },
                    **_active_project_payload(ctx.participant_identity, ctx.room),
                },
                error=_trim_process_output(status.stderr or "") or f"exit code {status.returncode}",
            )

        if not (status.stdout or "").strip():
            return ActionResult(
                success=True,
                message=f"Nao ha mudancas para commit em {record.name}.",
                data={
                    "project": _project_record_to_payload(record),
                    "git_status": {
                        "returncode": status.returncode,
                        "stdout": _trim_process_output(status.stdout or ""),
                        "stderr": _trim_process_output(status.stderr or ""),
                        "success": True,
                    },
                    **_active_project_payload(ctx.participant_identity, ctx.room),
                },
            )

        add_result = run_git(["add", "-A"])
        if add_result.returncode != 0:
            return ActionResult(
                success=False,
                message="Falha ao adicionar arquivos no git.",
                data={
                    "project": _project_record_to_payload(record),
                    "command_execution": {
                        "returncode": add_result.returncode,
                        "stdout": _trim_process_output(add_result.stdout or ""),
                        "stderr": _trim_process_output(add_result.stderr or ""),
                        "success": False,
                        "command_line": ["git", "add", "-A"],
                    },
                    **_active_project_payload(ctx.participant_identity, ctx.room),
                },
                error=_trim_process_output(add_result.stderr or "") or f"exit code {add_result.returncode}",
            )

        commit_result = run_git(["commit", "-m", commit_message])
        if commit_result.returncode != 0:
            commit_stdout = _trim_process_output(commit_result.stdout or "")
            commit_stderr = _trim_process_output(commit_result.stderr or "")
            combined = f"{commit_stdout}\n{commit_stderr}".strip()
            if "nothing to commit" in combined.casefold():
                return ActionResult(
                    success=True,
                    message=f"Nao havia nada novo para commitar em {record.name}.",
                    data={
                        "project": _project_record_to_payload(record),
                        "command_execution": {
                            "returncode": commit_result.returncode,
                            "stdout": commit_stdout,
                            "stderr": commit_stderr,
                            "success": True,
                            "command_line": ["git", "commit", "-m", commit_message],
                        },
                        **_active_project_payload(ctx.participant_identity, ctx.room),
                    },
                )
            return ActionResult(
                success=False,
                message="Falha ao criar o commit.",
                data={
                    "project": _project_record_to_payload(record),
                    "command_execution": {
                        "returncode": commit_result.returncode,
                        "stdout": commit_stdout,
                        "stderr": commit_stderr,
                        "success": False,
                        "command_line": ["git", "commit", "-m", commit_message],
                    },
                    **_active_project_payload(ctx.participant_identity, ctx.room),
                },
                error=commit_stderr or commit_stdout or f"exit code {commit_result.returncode}",
            )

        push_result = run_git(["push"])
        push_stdout = _trim_process_output(push_result.stdout or "")
        push_stderr = _trim_process_output(push_result.stderr or "")
        if push_result.returncode != 0:
            return ActionResult(
                success=False,
                message="O commit foi criado, mas o push falhou.",
                data={
                    "project": _project_record_to_payload(record),
                    "command_execution": {
                        "returncode": push_result.returncode,
                        "stdout": push_stdout,
                        "stderr": push_stderr,
                        "success": False,
                        "command_line": ["git", "push"],
                    },
                    "git_commit_message": commit_message,
                    **_active_project_payload(ctx.participant_identity, ctx.room),
                },
                error=push_stderr or f"exit code {push_result.returncode}",
            )
    except (OSError, subprocess.SubprocessError) as exc:
        return ActionResult(success=False, message="Falha ao executar git localmente.", error=str(exc))

    return ActionResult(
        success=True,
        message=f"Commit e push concluidos em {record.name}.",
        data={
            "project": _project_record_to_payload(record),
            "git_commit_message": commit_message,
            "command_execution": {
                "returncode": push_result.returncode,
                "stdout": push_stdout,
                "stderr": push_stderr,
                "success": True,
                "command_line": ["git", "push"],
            },
            **_active_project_payload(ctx.participant_identity, ctx.room),
        },
    )


def _resolve_github_repo(params: JsonObject) -> tuple[GitHubRepo | None, ActionResult | None]:
    client = _get_github_catalog_client()
    if not client.is_configured():
        return (
            None,
            ActionResult(
                success=False,
                message="Configure GITHUB_TOKEN ou GH_TOKEN no backend para usar repositorios do GitHub.",
                error="github not configured",
            ),
        )

    query = (
        str(params.get("repository", "")).strip()
        or str(params.get("full_name", "")).strip()
        or str(params.get("name", "")).strip()
        or str(params.get("query", "")).strip()
    )
    if not query:
        return (
            None,
            ActionResult(
                success=False,
                message="Informe o repositorio do GitHub que devo usar.",
                error="missing repository",
            ),
        )

    try:
        repo, candidates = client.resolve_repo(query)
    except requests.RequestException as error:
        return (
            None,
            ActionResult(
                success=False,
                message=f"Falha ao consultar o GitHub: {error}",
                error=str(error),
            ),
        )

    if repo is None and not candidates:
        return (
            None,
            ActionResult(
                success=False,
                message="Nao encontrei esse repositorio no GitHub conectado.",
                error="github repo not found",
            ),
        )

    if repo is None:
        return (
            None,
            ActionResult(
                success=False,
                message="Encontrei mais de um repositorio plausivel. Escolha pelo nome completo.",
                data={"candidates": [_github_repo_to_payload(item) for item in candidates]},
                error="github repo ambiguous",
            ),
        )

    return repo, None


async def _github_list_repos_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    client = _get_github_catalog_client()
    if not client.is_configured():
        return ActionResult(
            success=False,
            message="Configure GITHUB_TOKEN ou GH_TOKEN no backend para listar repositorios.",
            error="github not configured",
        )

    limit = int(params.get("limit", 10) or 10)
    visibility = str(params.get("visibility", "all")).strip().casefold() or "all"
    query = str(params.get("query", "")).strip()

    try:
        repos = client.find_repos(query, limit=limit) if query else client.list_repos(visibility=visibility, limit=limit)
    except requests.RequestException as error:
        return ActionResult(
            success=False,
            message=f"Falha ao consultar o GitHub: {error}",
            error=str(error),
        )

    return ActionResult(
        success=True,
        message=f"{len(repos)} repositorio(s) carregado(s) do GitHub.",
        data={
            "github_repos": [_github_repo_to_payload(item) for item in repos],
            "query": query or None,
            "visibility": visibility,
        },
    )


async def _github_find_repo_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    repo, error = _resolve_github_repo(params)
    if error is not None:
        return error
    assert repo is not None
    return ActionResult(
        success=True,
        message=f"Repositorio encontrado: {repo.full_name}.",
        data={"github_repo": _github_repo_to_payload(repo)},
    )


async def _github_clone_and_register_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    repo, error = _resolve_github_repo(params)
    if error is not None:
        return error
    assert repo is not None

    destination = str(params.get("destination", "")).strip()
    destination_root_raw = str(params.get("destination_root", "")).strip()
    branch = str(params.get("branch", "")).strip() or repo.default_branch
    depth = params.get("depth")

    destination_path: Path
    if destination:
        resolved_destination = _resolve_local_path(destination, must_exist=False)
        if resolved_destination is None:
            return ActionResult(success=False, message="Destino invalido para o clone.", error="invalid destination")
        destination_path = resolved_destination
    else:
        clone_root = (
            _resolve_local_path(destination_root_raw, must_exist=False)
            if destination_root_raw
            else _github_default_clone_root()
        )
        if clone_root is None:
            return ActionResult(success=False, message="Pasta base invalida para clonar o repositorio.", error="invalid destination root")
        clone_root.mkdir(parents=True, exist_ok=True)
        destination_path = clone_root / repo.name

    clone_result = await _git_clone_repository(
        {
            "repository_url": repo.clone_url,
            "destination": str(destination_path),
            "branch": branch,
            "depth": depth,
        },
        ctx,
    )
    if not clone_result.success:
        clone_data = dict(clone_result.data or {})
        clone_data["github_repo"] = _github_repo_to_payload(repo)
        clone_result.data = clone_data
        return clone_result

    record = _get_project_catalog().create_or_update_project(
        root_path=destination_path,
        name=repo.name,
        aliases=[repo.full_name, repo.owner],
        priority_score=20,
    )
    index_status = _ensure_project_index(record)
    _set_active_project_from_record(record, ctx, selection_reason=repo.full_name, index_status=index_status)

    return ActionResult(
        success=True,
        message=f"Repositorio {repo.full_name} clonado e registrado no catalogo.",
        data={
            "github_repo": _github_repo_to_payload(repo),
            "project": _project_record_to_payload(record),
            **_active_project_payload(ctx.participant_identity, ctx.room),
        },
    )


def _cleanup_expired_confirmations() -> None:
    now = datetime.now(timezone.utc)
    expired_tokens = [token for token, pending in PENDING_CONFIRMATIONS.items() if pending.expires_at <= now]
    for token in expired_tokens:
        pending = PENDING_CONFIRMATIONS.pop(token, None)
        if pending:
            PARTICIPANT_PENDING_TOKENS.pop(pending.participant_identity, None)
            try:
                STATE_STORE.delete_pending_confirmation(token)
            except Exception:
                logger.warning("failed to delete expired pending confirmation", exc_info=True)


def _remaining_seconds(expires_at: datetime) -> int:
    now = datetime.now(timezone.utc)
    return max(0, int((expires_at - now).total_seconds()))


def _store_confirmation(action_name: str, params: JsonObject, ctx: ActionContext) -> PendingConfirmation:
    _cleanup_expired_confirmations()

    previous_token = PARTICIPANT_PENDING_TOKENS.get(ctx.participant_identity)
    if previous_token is None:
        previous_token = STATE_STORE.find_pending_confirmation_token(ctx.participant_identity)
    if previous_token:
        PENDING_CONFIRMATIONS.pop(previous_token, None)
        try:
            STATE_STORE.delete_pending_confirmation(previous_token)
        except Exception:
            logger.warning("failed to replace previous pending confirmation", exc_info=True)

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
    try:
        STATE_STORE.save_pending_confirmation(
            token=token,
            participant_identity=ctx.participant_identity,
            room=ctx.room,
            action_name=action_name,
            params=params,
            expires_at=expires_at,
        )
    except Exception:
        logger.warning("failed to persist pending confirmation", exc_info=True)
    return pending


def _pop_confirmation(token: str) -> PendingConfirmation | None:
    pending = PENDING_CONFIRMATIONS.pop(token, None)
    if pending is None:
        stored = STATE_STORE.get_pending_confirmation(token)
        if isinstance(stored, dict):
            expires_at = _parse_datetime(stored.get("expires_at"))
            if expires_at is not None:
                pending = PendingConfirmation(
                    token=str(stored.get("token") or token),
                    action_name=str(stored.get("action_name") or ""),
                    params=stored.get("params") if isinstance(stored.get("params"), dict) else {},
                    participant_identity=str(stored.get("participant_identity") or ""),
                    room=str(stored.get("room") or ""),
                    expires_at=expires_at,
                )
    if pending:
        PARTICIPANT_PENDING_TOKENS.pop(pending.participant_identity, None)
        try:
            STATE_STORE.delete_pending_confirmation(token)
        except Exception:
            logger.warning("failed to delete pending confirmation", exc_info=True)
    return pending


def _peek_confirmation(token: str) -> PendingConfirmation | None:
    _cleanup_expired_confirmations()
    pending = PENDING_CONFIRMATIONS.get(token)
    if pending is not None:
        return pending
    stored = STATE_STORE.get_pending_confirmation(token)
    if not isinstance(stored, dict):
        return None
    expires_at = _parse_datetime(stored.get("expires_at"))
    if expires_at is None or expires_at <= datetime.now(timezone.utc):
        try:
            STATE_STORE.delete_pending_confirmation(token)
        except Exception:
            logger.warning("failed to delete stale pending confirmation", exc_info=True)
        return None
    pending = PendingConfirmation(
        token=str(stored.get("token") or token),
        action_name=str(stored.get("action_name") or ""),
        params=stored.get("params") if isinstance(stored.get("params"), dict) else {},
        participant_identity=str(stored.get("participant_identity") or ""),
        room=str(stored.get("room") or ""),
        expires_at=expires_at,
    )
    PENDING_CONFIRMATIONS[token] = pending
    PARTICIPANT_PENDING_TOKENS[pending.participant_identity] = token
    return pending


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


def _thinq_pat() -> str:
    return os.getenv("THINQ_PAT", "").strip()


def _thinq_country() -> str:
    return os.getenv("THINQ_COUNTRY", "BR").strip().upper() or "BR"


def _thinq_service_phase() -> str:
    return os.getenv("THINQ_SERVICE_PHASE", "OP").strip().upper() or "OP"


def _thinq_api_base() -> str:
    return os.getenv("THINQ_API_BASE", THINQ_DEFAULT_API_BASE_URL).strip().rstrip("/") or THINQ_DEFAULT_API_BASE_URL


def _thinq_client_id() -> str:
    return os.getenv("THINQ_CLIENT_ID", THINQ_SESSION_CLIENT_ID).strip() or THINQ_SESSION_CLIENT_ID


def _thinq_default_ac_name() -> str:
    return os.getenv("THINQ_DEFAULT_AC_NAME", "").strip()


def _thinq_message_id() -> str:
    encoded = base64.urlsafe_b64encode(uuid.uuid4().bytes).decode("ascii").rstrip("=")
    return encoded[:22]


def _thinq_headers(*, require_auth: bool) -> dict[str, str] | ActionResult:
    headers = {
        "x-message-id": _thinq_message_id(),
        "x-country": _thinq_country(),
        "x-api-key": THINQ_API_KEY,
    }
    if require_auth:
        pat = _thinq_pat()
        if not pat:
            return ActionResult(
                success=False,
                message="ThinQ nao configurado.",
                error="missing THINQ_PAT",
            )
        headers["Authorization"] = f"Bearer {pat}"
        headers["x-client-id"] = _thinq_client_id()
    else:
        headers["x-service-phase"] = _thinq_service_phase()
    return headers


def _thinq_unwrap_response(payload: Any) -> Any:
    if isinstance(payload, dict) and "response" in payload:
        return payload.get("response")
    return payload


def _thinq_api_request(
    method: str,
    endpoint: str,
    *,
    params: JsonObject | None = None,
    body: JsonObject | None = None,
    extra_headers: dict[str, str] | None = None,
    require_auth: bool = True,
) -> tuple[Any | None, ActionResult | None]:
    headers_or_error = _thinq_headers(require_auth=require_auth)
    if isinstance(headers_or_error, ActionResult):
        return None, headers_or_error

    if extra_headers:
        headers_or_error.update(extra_headers)

    try:
        response = requests.request(
            method=method.upper(),
            url=f"{_thinq_api_base()}/{endpoint.lstrip('/')}",
            headers=headers_or_error,
            params=params,
            json=body,
            timeout=10,
        )
    except requests.RequestException as error:
        return (
            None,
            ActionResult(
                success=False,
                message="Erro de comunicacao com ThinQ.",
                error=str(error),
            ),
        )

    payload: Any
    try:
        payload = response.json()
    except ValueError:
        payload = {"raw": response.text}

    if 200 <= response.status_code < 300:
        return _thinq_unwrap_response(payload), None

    return (
        None,
        ActionResult(
            success=False,
            message=f"Falha ao chamar ThinQ ({response.status_code}).",
            error=json.dumps(payload, ensure_ascii=False)[:1200] if not isinstance(payload, str) else payload[:1200],
        ),
    )


def _thinq_extract_device_id(device: JsonObject) -> str:
    return str(device.get("deviceId", "")).strip()


def _thinq_extract_device_info(device: JsonObject) -> JsonObject:
    info = device.get("deviceInfo", {})
    return info if isinstance(info, dict) else {}


def _thinq_extract_device_alias(device: JsonObject) -> str:
    info = _thinq_extract_device_info(device)
    for key in ("alias", "nickname", "name"):
        value = info.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        value = device.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return _thinq_extract_device_id(device)


def _thinq_extract_device_type(device: JsonObject) -> str:
    info = _thinq_extract_device_info(device)
    for key in ("deviceType", "type"):
        value = info.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        value = device.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _thinq_is_air_device(device: JsonObject) -> bool:
    label = _normalize_spotify_device_label(f"{_thinq_extract_device_type(device)} {_thinq_extract_device_alias(device)}")
    return any(token in label.split() for token in ("air", "conditioner", "ac", "climatizador"))


def _thinq_list_devices_payload() -> tuple[list[JsonObject] | None, ActionResult | None]:
    payload, error = _thinq_api_request("GET", "devices")
    if error is not None:
        return None, error
    devices = payload if isinstance(payload, list) else []
    normalized = [item for item in devices if isinstance(item, dict)]
    return normalized, None


def _thinq_simplify_device(device: JsonObject) -> JsonObject:
    info = _thinq_extract_device_info(device)
    return {
        "device_id": _thinq_extract_device_id(device),
        "alias": _thinq_extract_device_alias(device),
        "device_type": _thinq_extract_device_type(device),
        "model_name": str(info.get("modelName", device.get("modelName", ""))).strip(),
        "platform_type": str(info.get("platformType", "")).strip(),
        "raw": device,
    }


def _thinq_find_device(
    *,
    device_name: str | None = None,
    device_id: str | None = None,
    require_air: bool = False,
) -> tuple[JsonObject | None, ActionResult | None]:
    devices, error = _thinq_list_devices_payload()
    if error is not None:
        return None, error
    assert devices is not None

    filtered = [device for device in devices if not require_air or _thinq_is_air_device(device)]

    if device_id:
        exact = next((item for item in filtered if _thinq_extract_device_id(item) == device_id.strip()), None)
        if exact is not None:
            return exact, None

    requested_name = (device_name or "").strip()
    if requested_name:
        normalized = _normalize_spotify_device_label(requested_name)
        exact = next(
            (item for item in filtered if _normalize_spotify_device_label(_thinq_extract_device_alias(item)) == normalized),
            None,
        )
        if exact is not None:
            return exact, None

        contains = next(
            (
                item
                for item in filtered
                if normalized
                and normalized in _normalize_spotify_device_label(_thinq_extract_device_alias(item))
            ),
            None,
        )
        if contains is not None:
            return contains, None

        best_match: JsonObject | None = None
        best_score = 0.0
        for item in filtered:
            alias_normalized = _normalize_spotify_device_label(_thinq_extract_device_alias(item))
            score = SequenceMatcher(None, normalized, alias_normalized).ratio()
            if score > best_score:
                best_score = score
                best_match = item
        if best_match is not None and best_score >= 0.62:
            return best_match, None

    if require_air and len(filtered) == 1:
        return filtered[0], None

    if not requested_name and _thinq_default_ac_name() and require_air:
        return _thinq_find_device(device_name=_thinq_default_ac_name(), require_air=True)

    available = ", ".join(_thinq_extract_device_alias(item) for item in filtered[:8]) or "nenhum"
    return (
        None,
        ActionResult(
            success=False,
            message="Dispositivo ThinQ nao encontrado.",
            error=f"device not found; disponiveis agora: {available}",
        ),
    )


def _spotify_tokens_path() -> Path:
    raw = os.getenv("SPOTIFY_TOKENS_PATH", "data/spotify_tokens.json").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _spotify_device_aliases_path() -> Path:
    raw = os.getenv("SPOTIFY_DEVICE_ALIASES_PATH", "data/spotify_device_aliases.json").strip()
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


def _ac_arrival_prefs_path() -> Path:
    raw = os.getenv("AC_ARRIVAL_PREFS_PATH", "data/ac_arrival_prefs.json").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _load_ac_arrival_prefs() -> JsonObject:
    path = _ac_arrival_prefs_path()
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass
    return {}


def _save_ac_arrival_prefs(payload: JsonObject) -> None:
    path = _ac_arrival_prefs_path()
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


def _normalize_spotify_device_label(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value.casefold())
    without_marks = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", without_marks).strip()


def _read_spotify_device_aliases_file() -> JsonObject:
    path = _spotify_device_aliases_path()
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass
    return {}


def _write_spotify_device_aliases_file(payload: JsonObject) -> None:
    _spotify_device_aliases_path().write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _spotify_initialize_device_aliases_cache() -> None:
    if SPOTIFY_DEVICE_ALIAS_CACHE:
        return
    stored = _read_spotify_device_aliases_file()
    aliases = stored.get("aliases", {})
    if isinstance(aliases, dict):
        SPOTIFY_DEVICE_ALIAS_CACHE["aliases"] = {
            _normalize_spotify_device_label(str(key)): str(value).strip()
            for key, value in aliases.items()
            if str(key).strip() and str(value).strip()
        }
    else:
        SPOTIFY_DEVICE_ALIAS_CACHE["aliases"] = {}


def _spotify_remember_device_alias(alias: str, device_id: str) -> None:
    normalized_alias = _normalize_spotify_device_label(alias)
    if not normalized_alias or not device_id:
        return
    _spotify_initialize_device_aliases_cache()
    aliases = SPOTIFY_DEVICE_ALIAS_CACHE.setdefault("aliases", {})
    if not isinstance(aliases, dict):
        aliases = {}
        SPOTIFY_DEVICE_ALIAS_CACHE["aliases"] = aliases
    aliases[normalized_alias] = device_id
    _write_spotify_device_aliases_file({"aliases": aliases})


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
        normalized = _normalize_spotify_device_label(device_name)
        _spotify_initialize_device_aliases_cache()
        aliases = SPOTIFY_DEVICE_ALIAS_CACHE.get("aliases", {})
        reserved_aliases = {
            "alexa",
            "echo",
            "pc",
            "computador",
            "notebook",
            "desktop",
            "iphone",
            "celular",
            "telefone",
            "mobile",
        }
        if isinstance(aliases, dict) and normalized not in reserved_aliases:
            remembered_device_id = _coerce_optional_str(aliases.get(normalized))
            if remembered_device_id:
                for device in devices:
                    if isinstance(device, dict) and str(device.get("id", "")).strip() == remembered_device_id:
                        return device, None
        exact = [
            d
            for d in devices
            if isinstance(d, dict) and _normalize_spotify_device_label(str(d.get("name", ""))) == normalized
        ]
        if exact:
            return exact[0], None
        partial = [
            d
            for d in devices
            if isinstance(d, dict) and normalized and normalized in _normalize_spotify_device_label(str(d.get("name", "")))
        ]
        if partial:
            return partial[0], None

        requested_tokens_list = normalized.split()
        requested_tokens = set(requested_tokens_list)

        def select_single_device(candidates: list[JsonObject]) -> JsonObject | None:
            if len(candidates) == 1:
                return candidates[0]
            return None

        def select_preferred_device(candidates: list[JsonObject]) -> JsonObject | None:
            if not candidates:
                return None
            single = select_single_device(candidates)
            if single is not None:
                return single

            def score(device: JsonObject) -> tuple[int, int]:
                normalized_name = _normalize_spotify_device_label(str(device.get("name", "")))
                score_value = 0
                if bool(device.get("is_active")):
                    score_value += 4
                if "guih" in normalized_name:
                    score_value += 5
                if "echo" in normalized_name:
                    score_value += 3
                if "iphone" in normalized_name:
                    score_value += 3
                if str(device.get("type", "")).casefold() == "speaker":
                    score_value += 2
                if "amzn" in str(device.get("id", "")).casefold():
                    score_value += 2
                if "todo lugar" in normalized_name:
                    score_value -= 3
                return score_value, len(normalized_name)

            ranked = sorted(candidates, key=score, reverse=True)
            return ranked[0]

        if {"alexa", "echo"} & requested_tokens:
            alexa_candidates = [
                d
                for d in devices
                if isinstance(d, dict)
                and (
                    "amzn" in str(d.get("id", "")).casefold()
                    or str(d.get("type", "")).casefold() == "speaker"
                )
            ]
            selected = select_preferred_device(alexa_candidates)
            if selected is not None:
                return selected, None

        if {"pc", "computador", "notebook", "desktop"} & requested_tokens:
            computer_candidates = [
                d
                for d in devices
                if isinstance(d, dict) and str(d.get("type", "")).casefold() == "computer"
            ]
            selected = select_preferred_device(computer_candidates)
            if selected is not None:
                return selected, None

        if {"iphone", "celular", "telefone", "mobile"} & requested_tokens:
            mobile_candidates = [
                d
                for d in devices
                if isinstance(d, dict)
                and (
                    str(d.get("type", "")).casefold() in {"smartphone", "tablet"}
                    or "iphone" in _normalize_spotify_device_label(str(d.get("name", ""))).split()
                )
            ]
            selected = select_preferred_device(mobile_candidates)
            if selected is not None:
                return selected, None

        token_overlap = []
        if requested_tokens:
            for device in devices:
                if not isinstance(device, dict):
                    continue
                device_name_normalized = _normalize_spotify_device_label(str(device.get("name", "")))
                device_tokens = set(device_name_normalized.split())
                overlap = len(requested_tokens & device_tokens)
                if overlap:
                    token_overlap.append((overlap, device))
        if token_overlap:
            token_overlap.sort(key=lambda item: item[0], reverse=True)
            return token_overlap[0][1], None
        if any(token in {"echo", "alexa"} for token in requested_tokens_list):
            amazon_devices = [
                d
                for d in devices
                if isinstance(d, dict)
                and (
                    "amzn" in str(d.get("id", "")).casefold()
                    or "echo" in _normalize_spotify_device_label(str(d.get("name", ""))).split()
                    or "alexa" in _normalize_spotify_device_label(str(d.get("name", ""))).split()
                )
            ]
            if len(amazon_devices) == 1:
                return amazon_devices[0], None

        fuzzy_scored: list[tuple[float, JsonObject]] = []
        for device in devices:
            if not isinstance(device, dict):
                continue
            device_name_normalized = _normalize_spotify_device_label(str(device.get("name", "")))
            if not device_name_normalized:
                continue
            similarity = SequenceMatcher(None, normalized, device_name_normalized).ratio()
            if similarity >= 0.55:
                fuzzy_scored.append((similarity, device))
        if fuzzy_scored:
            fuzzy_scored.sort(key=lambda item: item[0], reverse=True)
            return fuzzy_scored[0][1], None
        available = [str(d.get("name", "")) for d in devices if isinstance(d, dict)]
        if len(devices) == 1 and isinstance(devices[0], dict):
            return devices[0], None
        available_list = ", ".join(name for name in available if name) or "nenhum device visivel"
        return None, ActionResult(
            success=False,
            message=f"Nao encontrei o speaker '{device_name}' no Spotify Connect. Disponiveis agora: {available_list}.",
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


def _normalize_spotify_uri(raw_uri: str) -> str:
    value = raw_uri.strip()
    if not value:
        return ""

    if value.startswith(("https://open.spotify.com/", "http://open.spotify.com/")):
        parsed = urlparse(value)
        path_parts = [part for part in parsed.path.split("/") if part]
        if len(path_parts) >= 2:
            return f"spotify:{path_parts[0]}:{path_parts[1]}"
        return value

    if value.startswith("spotify:"):
        return value.split("?", 1)[0]

    return value


def _coerce_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _is_spotify_restriction_error(result: ActionResult | None) -> bool:
    if result is None or not result.error:
        return False
    return "Restriction violated" in result.error


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


def _code_knowledge_db_path() -> Path:
    raw = os.getenv("CODE_KNOWLEDGE_DB_PATH", "data/code_knowledge.db").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _code_repo_root() -> Path:
    raw = os.getenv("CODE_REPO_ROOT", "").strip()
    if raw:
        path = Path(raw)
        if not path.is_absolute():
            path = Path(__file__).resolve().parent.parent / path
        return path
    return Path(__file__).resolve().parent.parent


def _project_index_stale_seconds() -> int:
    raw = os.getenv("PROJECT_INDEX_STALE_SECONDS", "1800").strip()
    try:
        return max(60, min(86400, int(raw)))
    except ValueError:
        return 1800


def _project_is_stale(record: ProjectRecord) -> bool:
    if not record.last_indexed_at:
        return True
    try:
        last = datetime.fromisoformat(record.last_indexed_at.replace("Z", "+00:00"))
    except ValueError:
        return True
    return (datetime.now(timezone.utc) - last).total_seconds() > _project_index_stale_seconds()


def _set_active_project_from_record(
    record: ProjectRecord,
    ctx: ActionContext,
    *,
    selection_reason: str,
    index_status: str,
) -> ActiveProjectMode:
    active = ActiveProjectMode(
        project_id=record.project_id,
        name=record.name,
        root_path=record.root_path,
        aliases=list(record.aliases),
        selected_at=_now_iso(),
        selection_reason=selection_reason,
        index_status=index_status,
    )
    set_active_project(ctx.participant_identity, ctx.room, active)
    return active


def _ensure_project_index(record: ProjectRecord) -> str:
    if not record.is_active:
        return "inactive"
    root = Path(record.root_path).resolve(strict=False)
    if not root.exists():
        return "missing_root"
    if not _project_is_stale(record):
        return "fresh"
    summary = _get_code_index().index_project(
        record.project_id,
        root,
        project_name=record.name,
        aliases=record.aliases,
    )
    _get_project_catalog().update_last_indexed(record.project_id)
    if summary.get("documents_failed"):
        return "reindexed_with_failures"
    return "reindexed"


def _resolve_project_record(params: JsonObject, ctx: ActionContext) -> tuple[ProjectRecord | None, ActionResult | None]:
    project_id = str(params.get("project_id", "")).strip()
    catalog = _get_project_catalog()
    if project_id:
        record = catalog.get_project(project_id)
        if record is None or not record.is_active:
            return None, ActionResult(success=False, message="Projeto nao encontrado.", error="unknown project")
        index_status = _ensure_project_index(record)
        _set_active_project_from_record(record, ctx, selection_reason="project_id", index_status=index_status)
        return record, None

    active = get_active_project(ctx.participant_identity, ctx.room)
    query = (
        str(params.get("query", "")).strip()
        or str(params.get("project_query", "")).strip()
        or str(params.get("fuzzy_query", "")).strip()
        or str(params.get("project", "")).strip()
        or str(params.get("project_name", "")).strip()
        or str(params.get("name", "")).strip()
    )
    if not query and active is not None:
        record = catalog.get_project(active.project_id)
        if record is not None and record.is_active:
            return record, None

    if not query:
        return None, ActionResult(
            success=False,
            message="Informe qual projeto devo usar.",
            data={"projects": [_project_record_to_payload(item) for item in catalog.list_projects()[:5]]},
            error="missing project",
        )

    match, confidence, candidates = catalog.resolve(
        query,
        active_project_id=active.project_id if active else None,
        limit=3,
    )
    if match is None:
        return None, ActionResult(
            success=False,
            message="Nao consegui identificar o projeto com seguranca.",
            data={
                "project_resolution_required": True,
                "confidence": confidence,
                "candidates": [_project_record_to_payload(item) for item in candidates],
            },
            error="project resolution failed",
        )
    if confidence == "medium":
        return None, ActionResult(
            success=False,
            message="Encontrei mais de um projeto plausivel. Escolha um pelo nome ou project_id.",
            data={
                "project_resolution_required": True,
                "confidence": confidence,
                "candidates": [_project_record_to_payload(item) for item in candidates],
            },
            error="ambiguous project",
        )

    index_status = _ensure_project_index(match)
    _set_active_project_from_record(match, ctx, selection_reason=query, index_status=index_status)
    return match, None


def _code_worker_request(path: str, payload: JsonObject | None = None) -> tuple[JsonObject | None, ActionResult | None]:
    client = _get_code_worker_client()
    try:
        if path == "/health":
            response = client.health()
        elif path == "/read-file":
            response = client.read_file(payload or {})
        elif path == "/search-files":
            response = client.search_files(payload or {})
        elif path == "/git-status":
            response = client.git_status(payload or {})
        elif path == "/git-diff":
            response = client.git_diff(payload or {})
        elif path == "/apply-patch":
            response = client.apply_patch(payload or {})
        elif path == "/run-command":
            response = client.run_command(payload or {})
        else:
            return None, ActionResult(success=False, message="Endpoint do code worker invalido.", error="invalid worker path")
    except requests.RequestException as error:
        return None, ActionResult(
            success=False,
            message="Code worker indisponivel. Inicie o processo do worker local.",
            error=str(error),
        )

    if not isinstance(response, dict):
        return None, ActionResult(success=False, message="Resposta invalida do code worker.", error="invalid worker response")
    if not response.get("success"):
        return None, ActionResult(
            success=False,
            message=str(response.get("message", "Code worker retornou erro.")),
            data=response.get("data") if isinstance(response.get("data"), dict) else None,
            error=str(response.get("error", "worker error")),
        )
    return response, None


def _build_confirmation_message(name: str, params: JsonObject) -> str:
    explicit = str(params.get("confirmation_summary", "")).strip()
    if explicit:
        return explicit

    if name == "code_apply_patch":
        changes = params.get("changes", [])
        file_labels: list[str] = []
        if isinstance(changes, list):
            for item in changes[:3]:
                if not isinstance(item, dict):
                    continue
                path = str(item.get("path", "")).strip()
                if path:
                    file_labels.append(path)
        suffix = ", ".join(file_labels) if file_labels else "arquivos do projeto ativo"
        return f"Confirma aplicar patch em {suffix}?"

    if name == "code_run_command":
        command = str(params.get("command", "")).strip()
        arguments = params.get("arguments", [])
        command_parts = [command] + [item for item in arguments if isinstance(item, str)]
        readable = " ".join(part for part in command_parts if part).strip() or "comando"
        return f"Confirma executar `{readable}` no projeto ativo?"

    if name == "git_clone_repository":
        repo = str(params.get("repository_url", "")).strip() or "repositorio informado"
        return f"Confirma clonar {repo}?"

    if name == "git_commit_and_push_project":
        message = (
            str(params.get("message", "")).strip()
            or str(params.get("commit_message", "")).strip()
            or "commit no projeto ativo"
        )
        return f'Confirma criar commit e fazer push com a mensagem "{message}"?'

    if name == "github_clone_and_register":
        repo = (
            str(params.get("repository", "")).strip()
            or str(params.get("full_name", "")).strip()
            or str(params.get("name", "")).strip()
            or "repositorio informado"
        )
        return f"Confirma clonar {repo} do GitHub e registrar no catalogo?"

    if name == "run_local_command":
        command = str(params.get("command", "")).strip() or "comando local"
        arguments = params.get("arguments", [])
        command_parts = [command] + [item for item in arguments if isinstance(item, str)]
        readable = " ".join(part for part in command_parts if part).strip()
        return f"Confirma executar `{readable}`?"

    return f"Confirma executar {name} com os parametros informados?"


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


def _get_code_index() -> CodeKnowledgeIndex:
    global CODE_KNOWLEDGE_INDEX
    if CODE_KNOWLEDGE_INDEX is None:
        CODE_KNOWLEDGE_INDEX = CodeKnowledgeIndex(_code_knowledge_db_path())
    return CODE_KNOWLEDGE_INDEX


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


def _action_domain(action_name: str) -> str | None:
    domain = infer_action_domain(action_name)
    if domain == "general":
        return None
    return domain


def _integration_provider_for_action(action_name: str) -> str:
    if action_name.startswith("codex_"):
        return "codex_cli"
    if action_name.startswith("code_"):
        return "code_worker"
    if action_name.startswith("spotify_"):
        return "spotify_api"
    if action_name.startswith("whatsapp_"):
        return "whatsapp_api"
    if action_name.startswith("thinq_") or action_name.startswith("ac_"):
        return "lg_thinq"
    if action_name.startswith("onenote_"):
        return "onenote_graph"
    if action_name.startswith("web_search_"):
        return "gemini_google_search"
    return "internal"


def _ensure_result_envelope(
    *,
    result: ActionResult,
    trace_id: str,
    action_name: str,
    started_at: str,
    risk: str,
    policy_decision: str,
) -> ActionResult:
    if not result.trace_id:
        result.trace_id = trace_id
    if not result.risk:
        result.risk = risk
    if not result.policy_decision:
        result.policy_decision = policy_decision
    if result.evidence is None:
        result.evidence = {
            "provider": _integration_provider_for_action(action_name),
            "executed_at": _now_iso(),
            "started_at": started_at,
        }
    if result.fallback_used is None and isinstance(result.data, dict):
        model_route = result.data.get("model_route")
        if isinstance(model_route, dict) and isinstance(model_route.get("fallback_used"), bool):
            result.fallback_used = bool(model_route.get("fallback_used"))
    if isinstance(result.data, dict):
        result.data.setdefault(
            "policy",
            {
                "risk": risk,
                "decision": result.policy_decision,
            },
        )
        result.data.setdefault(
            "trace",
            {
                "trace_id": trace_id,
                "started_at": started_at,
            },
        )
    return result


def _workspace_root() -> Path:
    configured = str(os.getenv("JARVEZ_WORKSPACE_ROOT", "")).strip()
    if configured:
        return Path(configured).expanduser().resolve(strict=False)
    return Path(__file__).resolve().parents[1]


def _workspace_only_enforced() -> bool:
    raw = str(os.getenv("JARVEZ_ENFORCE_WORKSPACE_ONLY", "0")).strip().lower()
    return raw not in BOOL_FALSE_VALUES


def _is_path_inside_workspace(raw_path: str) -> bool:
    workspace_root = _workspace_root()
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = (workspace_root / candidate).resolve(strict=False)
    else:
        candidate = candidate.resolve(strict=False)
    try:
        candidate.relative_to(workspace_root)
        return True
    except ValueError:
        return False


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
    if _workspace_only_enforced():
        if name == "run_local_command":
            working_directory = params.get("working_directory")
            if isinstance(working_directory, str) and working_directory.strip():
                if not _is_path_inside_workspace(working_directory):
                    return ActionResult(
                        success=False,
                        message="Comando bloqueado: working_directory fora do workspace permitido.",
                        error="workspace policy violation",
                    )
        if name in {"git_clone_repository", "github_clone_and_register"}:
            destination = params.get("destination")
            destination_root = params.get("destination_root")
            if isinstance(destination, str) and destination.strip() and not _is_path_inside_workspace(destination):
                return ActionResult(
                    success=False,
                    message="Clone bloqueado: destination fora do workspace permitido.",
                    error="workspace policy violation",
                )
            if (
                isinstance(destination_root, str)
                and destination_root.strip()
                and not _is_path_inside_workspace(destination_root)
            ):
                return ActionResult(
                    success=False,
                    message="Clone bloqueado: destination_root fora do workspace permitido.",
                    error="workspace policy violation",
                )
    return None


NON_EXECUTION_ERRORS = {
    "policy denied",
    "not authenticated",
    "workspace policy violation",
    "rpg_mode_required",
}


def _record_domain_trust_from_result(*, action_name: str, result: ActionResult) -> None:
    if action_name in {"confirm_action"}:
        return
    if result.data and isinstance(result.data, dict) and result.data.get("confirmation_required"):
        return
    if result.error and result.error in NON_EXECUTION_ERRORS:
        return
    domain = infer_action_domain(action_name)
    if result.success:
        record_domain_outcome(domain, "success")
        return
    if result.error and result.error.startswith("unknown action"):
        return
    record_domain_outcome(domain, "failure")


def _build_trust_drift_autonomy_notice(
    *,
    domain: str,
    policy_decision: str,
    trust_drift: Any | None,
) -> JsonObject | None:
    if trust_drift is None or not getattr(trust_drift, "active", False):
        return None
    if policy_decision not in {"allow_with_log", "allow_with_guardrail", "require_confirmation", "deny"}:
        return None
    level = "warning"
    if policy_decision == "deny":
        level = "critical"
    elif policy_decision == "require_confirmation":
        level = "warning"
    else:
        level = "info"
    domain_label = domain or "general"
    spoken_message = (
        f"Atencao. Reduzi a autonomia no dominio {domain_label} porque backend e cliente estao fora de sincronia."
    )
    if policy_decision == "deny":
        spoken_message = (
            f"Atencao. Bloqueei a autonomia no dominio {domain_label} porque backend e cliente estao fora de sincronia."
        )
    return {
        "active": True,
        "level": level,
        "title": "Autonomia reduzida por trust drift",
        "message": (
            f"O dominio {domain_label} esta com drift entre confianca local e backend; "
            f"a politica atual reduziu a autonomia para `{policy_decision}`."
        ),
        "domain": domain_label,
        "scenario": "trust_drift_breach",
        "decision": policy_decision,
        "signature": f"trust_drift_breach:{domain_label}:{policy_decision}",
        "spoken_message": spoken_message,
    }


async def _emit_autonomy_notice_event(ctx: ActionContext, notice: JsonObject | None) -> None:
    if notice is None or notice.get("active") is False:
        return
    await _publish_agent_event(
        ctx,
        {
            "type": "autonomy_notice",
            "notice": notice,
            "timestamp": _now_iso(),
        },
    )


def record_autonomy_notice_delivery(
    *,
    participant_identity: str,
    room: str,
    trace_id: str | None,
    signature: str | None,
    channel: str,
    level: str | None = None,
    domain: str | None = None,
    scenario: str | None = None,
) -> None:
    payload = {
        "participant_identity": participant_identity,
        "room": room,
        "trace_id": trace_id,
        "signature": signature,
        "channel": channel,
        "level": level,
        "domain": domain,
        "scenario": scenario,
    }
    try:
        append_metric(
            {
                "type": "autonomy_notice_delivery",
                "timestamp": _now_iso(),
                "payload": payload,
            }
        )
    except Exception:  # noqa: BLE001
        logger.debug("failed to append autonomy_notice_delivery metric", exc_info=True)


def _speak_autonomy_notice(ctx: ActionContext, notice: JsonObject | None) -> str | None:
    if notice is None or notice.get("active") is False:
        return None
    spoken_message = str(notice.get("spoken_message", "")).strip()
    if not spoken_message:
        return None
    session = ctx.session
    if session is None:
        return None
    say = getattr(session, "say", None)
    if not callable(say):
        return None
    try:
        say(
            spoken_message,
            allow_interruptions=True,
            add_to_chat_ctx=False,
        )
        return "agent_audio"
    except Exception:  # noqa: BLE001
        logger.warning("failed to speak autonomy notice", exc_info=True)
        return None


async def dispatch_action(
    name: str,
    params: JsonObject,
    ctx: ActionContext,
    *,
    skip_confirmation: bool = False,
    bypass_auth: bool = False,
) -> ActionResult:
    started_at = time.perf_counter()
    started_at_iso = _now_iso()
    trace_id = f"trace_{uuid.uuid4().hex[:12]}"
    spec = get_action(name)
    risk = classify_action_risk(name)
    action_domain = infer_action_domain(name)
    domain_trust = get_domain_trust(action_domain)
    trust_drift = get_trust_drift(ctx.participant_identity, ctx.room, action_domain)
    autonomy_mode = get_autonomy_mode(ctx.participant_identity, ctx.room)
    domain_autonomy_mode = get_domain_autonomy_mode(ctx.participant_identity, ctx.room, action_domain)
    effective_autonomy_mode = get_effective_autonomy_mode(
        ctx.participant_identity,
        ctx.room,
        domain=action_domain,
    )
    blocked, block_reason = is_blocked(domain=_action_domain(name))
    policy_eval = evaluate_policy(
        risk=risk,
        mode=effective_autonomy_mode,
        requires_confirmation=bool(spec.requires_confirmation) if spec is not None else False,
        kill_switch_active=blocked,
        kill_switch_reason=block_reason,
        domain=action_domain,
        domain_trust_score=domain_trust.score,
        trust_drift_active=bool(trust_drift and trust_drift.active),
        trust_drift_reason=trust_drift.reason if trust_drift is not None else None,
    )
    autonomy_notice = _build_trust_drift_autonomy_notice(
        domain=action_domain,
        policy_decision=policy_eval.decision,
        trust_drift=trust_drift,
    )
    if autonomy_notice is not None:
        autonomy_notice["trace_id"] = trace_id
    if autonomy_notice is not None and autonomy_notice.get("level") in {"warning", "critical"}:
        spoken_channel = _speak_autonomy_notice(ctx, autonomy_notice)
        if spoken_channel is not None:
            autonomy_notice["spoken_channel"] = spoken_channel
        await _emit_autonomy_notice_event(ctx, autonomy_notice)

    async def _finalize(result: ActionResult) -> ActionResult:
        _record_domain_trust_from_result(action_name=name, result=result)
        _persist_result_state(ctx, name, result)
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        _log_action_result(
            ctx=ctx,
            action_name=name,
            params=params,
            started_at=started_at_iso,
            elapsed_ms=elapsed_ms,
            result=result,
        )
        await _publish_session_snapshot_for_context(ctx)
        return result

    if spec is None:
        result = ActionResult(success=False, message="Action not allowed", error=f"unknown action '{name}'")
        result = _ensure_result_envelope(
            result=result,
            trace_id=trace_id,
            action_name=name,
            started_at=started_at_iso,
            risk=risk,
            policy_decision="deny",
        )
        return await _finalize(result)

    valid, validation_error = validate_params(params, spec.params_schema)
    if not valid:
        result = ActionResult(success=False, message="Invalid parameters", error=validation_error)
        result = _ensure_result_envelope(
            result=result,
            trace_id=trace_id,
            action_name=name,
            started_at=started_at_iso,
            risk=risk,
            policy_decision=policy_eval.decision,
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

    if policy_eval.decision == "deny":
        result = ActionResult(
            success=False,
            message=policy_eval.reason,
            error="policy denied",
            data={
                "policy": {
                    "mode": autonomy_mode,
                    "effective_mode": effective_autonomy_mode,
                    "domain_autonomy_mode": domain_autonomy_mode,
                    "domain": action_domain,
                    "domain_trust_score": round(domain_trust.score, 4),
                    "trust_drift_active": bool(trust_drift and trust_drift.active),
                    "trust_drift": trust_drift.to_payload() if trust_drift is not None else None,
                    "risk": risk,
                    "decision": policy_eval.decision,
                    "reason": policy_eval.reason,
                }
                | ({"autonomy_notice": autonomy_notice} if autonomy_notice is not None else {})
            },
        )
        result = _ensure_result_envelope(
            result=result,
            trace_id=trace_id,
            action_name=name,
            started_at=started_at_iso,
            risk=risk,
            policy_decision=policy_eval.decision,
        )
        return await _finalize(result)

    gate_result = _policy_gate(name, params)
    if gate_result is not None:
        gate_result = _ensure_result_envelope(
            result=gate_result,
            trace_id=trace_id,
            action_name=name,
            started_at=started_at_iso,
            risk=risk,
            policy_decision=policy_eval.decision,
        )
        return await _finalize(gate_result)

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
            result = _ensure_result_envelope(
                result=result,
                trace_id=trace_id,
                action_name=name,
                started_at=started_at_iso,
                risk=risk,
                policy_decision=policy_eval.decision,
            )
            return await _finalize(result)

    if spec.requires_auth and not bypass_auth and not _is_authenticated(ctx.participant_identity, ctx.room):
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
        result = _ensure_result_envelope(
            result=result,
            trace_id=trace_id,
            action_name=name,
            started_at=started_at_iso,
            risk=risk,
            policy_decision=policy_eval.decision,
        )
        return await _finalize(result)

    if spec.requires_auth and not bypass_auth:
        _touch_authenticated(ctx.participant_identity)

    requires_confirmation = spec.requires_confirmation or policy_eval.decision == "require_confirmation"
    if requires_confirmation and not skip_confirmation and name != "confirm_action":
        pending = _store_confirmation(name, params, ctx)
        confirmation_message = _build_confirmation_message(name, params)
        result = ActionResult(
            success=False,
            message=confirmation_message,
            data={
                "confirmation_required": True,
                "confirmation_token": pending.token,
                "expires_in": _remaining_seconds(pending.expires_at),
                "action_name": pending.action_name,
                "params": pending.params,
                "policy": {
                    "mode": autonomy_mode,
                    "effective_mode": effective_autonomy_mode,
                    "domain_autonomy_mode": domain_autonomy_mode,
                    "domain": action_domain,
                    "domain_trust_score": round(domain_trust.score, 4),
                    "trust_drift_active": bool(trust_drift and trust_drift.active),
                    "trust_drift": trust_drift.to_payload() if trust_drift is not None else None,
                    "risk": risk,
                    "decision": policy_eval.decision,
                    "reason": policy_eval.reason,
                },
                **({"autonomy_notice": autonomy_notice} if autonomy_notice is not None else {}),
            },
        )
        result = _ensure_result_envelope(
            result=result,
            trace_id=trace_id,
            action_name=name,
            started_at=started_at_iso,
            risk=risk,
            policy_decision="require_confirmation",
        )
        return await _finalize(result)

    try:
        result = await spec.handler(params, ctx)
    except Exception as error:  # noqa: BLE001
        logger.exception("action dispatch failed", extra={"action": name})
        result = ActionResult(success=False, message="Action execution failed", error=str(error))
    result = _ensure_result_envelope(
        result=result,
        trace_id=trace_id,
        action_name=name,
        started_at=started_at_iso,
        risk=risk,
        policy_decision=policy_eval.decision,
    )
    if autonomy_notice is not None and result.data is None:
        result.data = {"autonomy_notice": autonomy_notice}
    if isinstance(result.data, dict):
        policy_payload = result.data.get("policy")
        if isinstance(policy_payload, dict):
            policy_payload.setdefault("mode", autonomy_mode)
            policy_payload.setdefault("effective_mode", effective_autonomy_mode)
            policy_payload.setdefault("domain_autonomy_mode", domain_autonomy_mode)
            policy_payload.setdefault("domain", action_domain)
            policy_payload.setdefault("domain_trust_score", round(domain_trust.score, 4))
            policy_payload.setdefault("trust_drift_active", bool(trust_drift and trust_drift.active))
            policy_payload.setdefault("trust_drift", trust_drift.to_payload() if trust_drift is not None else None)
            policy_payload.setdefault("reason", policy_eval.reason)
        if autonomy_notice is not None:
            result.data.setdefault("autonomy_notice", autonomy_notice)

    return await _finalize(result)


def _log_action_result(
    *,
    ctx: ActionContext,
    action_name: str,
    params: JsonObject,
    started_at: str,
    elapsed_ms: int,
    result: ActionResult,
) -> None:
    canary_state = _canary_state_payload(ctx.participant_identity, ctx.room)
    trust_drift_active = False
    trust_drift_domain: str | None = None
    trust_drift_signature: str | None = None
    autonomy_notice_active = False
    autonomy_notice_level: str | None = None
    autonomy_notice_channel: str | None = None
    autonomy_notice_domain: str | None = None
    if isinstance(result.data, dict):
        policy_payload = result.data.get("policy")
        if isinstance(policy_payload, dict):
            trust_drift_active = bool(policy_payload.get("trust_drift_active"))
            trust_drift = policy_payload.get("trust_drift")
            if isinstance(trust_drift, dict):
                trust_drift_domain = str(trust_drift.get("domain") or "").strip() or None
                trust_drift_signature = str(trust_drift.get("signature") or "").strip() or None
        autonomy_notice = result.data.get("autonomy_notice")
        if isinstance(autonomy_notice, dict):
            autonomy_notice_active = bool(autonomy_notice.get("active"))
            autonomy_notice_level = str(autonomy_notice.get("level") or "").strip() or None
            autonomy_notice_channel = str(autonomy_notice.get("spoken_channel") or "").strip() or None
            autonomy_notice_domain = str(autonomy_notice.get("domain") or "").strip().lower() or None
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
        "trace_id": result.trace_id,
        "risk": result.risk,
        "policy_decision": result.policy_decision,
        "fallback_used": result.fallback_used,
        "evidence_provider": result.evidence.get("provider") if isinstance(result.evidence, dict) else None,
        "canary_active": bool(canary_state.get("active")),
        "canary_cohort": str(canary_state.get("cohort") or "stable"),
        "canary_global_enabled": bool(canary_state.get("global_enabled")),
        "canary_session_enrolled": bool(canary_state.get("session_enrolled")),
        "trust_drift_active": trust_drift_active,
        "trust_drift_domain": trust_drift_domain,
        "trust_drift_signature": trust_drift_signature,
        "autonomy_notice_active": autonomy_notice_active,
        "autonomy_notice_level": autonomy_notice_level,
        "autonomy_notice_channel": autonomy_notice_channel,
        "autonomy_notice_domain": autonomy_notice_domain,
    }
    logger.info("tool_call %s", json.dumps(payload, ensure_ascii=False))
    try:
        append_metric(
            {
                "type": "action_result",
                "timestamp": _now_iso(),
                "payload": payload,
            }
        )
    except Exception:  # noqa: BLE001
        logger.debug("failed to append local metrics", exc_info=True)


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


def _browser_task_payload(
    *,
    task_id: str,
    status: str,
    request: str,
    allowed_domains: list[str],
    read_only: bool,
    summary: str | None = None,
    error: str | None = None,
    started_at: str | None = None,
    finished_at: str | None = None,
) -> JsonObject:
    payload: JsonObject = {
        "task_id": task_id,
        "status": status,
        "request": request,
        "allowed_domains": allowed_domains,
        "read_only": read_only,
        "started_at": started_at or _now_iso(),
    }
    if summary is not None:
        payload["summary"] = summary
    if error is not None:
        payload["error"] = error
    if finished_at is not None:
        payload["finished_at"] = finished_at
    return payload


async def _browser_agent_run(params: JsonObject, ctx: ActionContext) -> ActionResult:
    request = str(params.get("request") or "").strip()
    allowed_domains = params.get("allowed_domains", [])
    read_only = bool(params.get("read_only", True))
    task_id = f"browser_{uuid.uuid4().hex[:10]}"
    from browser_agent.runner import run_browser_task

    browser_task_state, ok, error_code = run_browser_task(
        task_id=task_id,
        request=request,
        allowed_domains=allowed_domains if isinstance(allowed_domains, list) else [],
        read_only=read_only,
        mcp_url=str(os.getenv("JARVEZ_PLAYWRIGHT_MCP_URL", "")).strip(),
    )
    browser_task = browser_task_state.to_payload()
    if not ok:
        _persist_event_namespace(ctx.participant_identity, ctx.room, "browser_tasks", browser_task)
        await _publish_agent_event(ctx, {"type": "browser_task_failed", "browser_task": browser_task})
        return ActionResult(
            success=False,
            message=str(browser_task.get("summary") or "Browser agent indisponivel."),
            data={"browser_task": browser_task},
            error=error_code or "browser_agent_error",
        )

    _persist_event_namespace(ctx.participant_identity, ctx.room, "browser_tasks", browser_task)
    await _publish_agent_event(ctx, {"type": "browser_task_started", "browser_task": browser_task})
    return ActionResult(
        success=True,
        message="Browser agent enfileirado com guardrails de dominio.",
        data={"browser_task": browser_task},
    )


async def _browser_agent_status(params: JsonObject, ctx: ActionContext) -> ActionResult:
    _ = params
    browser_task = _load_event_namespace(ctx.participant_identity, ctx.room, "browser_tasks")
    return ActionResult(
        success=True,
        message="Status do browser agent carregado.",
        data={"browser_task": browser_task if isinstance(browser_task, dict) else None},
    )


async def _browser_agent_cancel(params: JsonObject, ctx: ActionContext) -> ActionResult:
    _ = params
    current = _load_event_namespace(ctx.participant_identity, ctx.room, "browser_tasks")
    if not isinstance(current, dict):
        return ActionResult(success=False, message="Nenhuma tarefa de browser ativa.", error="browser_task_missing")
    current = dict(current)
    current["status"] = "cancelled"
    current["finished_at"] = _now_iso()
    current["summary"] = "Cancelada pelo usuario."
    _persist_event_namespace(ctx.participant_identity, ctx.room, "browser_tasks", current)
    await _publish_agent_event(ctx, {"type": "browser_task_failed", "browser_task": current})
    return ActionResult(success=True, message="Tarefa de browser cancelada.", data={"browser_task": current})


def _workflow_state_payload(
    *,
    workflow_id: str,
    workflow_type: str,
    status: str,
    summary: str,
    project_id: str | None = None,
    project_name: str | None = None,
    current_step: str | None = None,
    started_at: str | None = None,
    finished_at: str | None = None,
    error: str | None = None,
) -> JsonObject:
    payload: JsonObject = {
        "workflow_id": workflow_id,
        "workflow_type": workflow_type,
        "status": status,
        "summary": summary,
        "started_at": started_at or _now_iso(),
    }
    if project_id is not None:
        payload["project_id"] = project_id
    if project_name is not None:
        payload["project_name"] = project_name
    if current_step is not None:
        payload["current_step"] = current_step
    if finished_at is not None:
        payload["finished_at"] = finished_at
    if error is not None:
        payload["error"] = error
    return payload


async def _workflow_run(params: JsonObject, ctx: ActionContext) -> ActionResult:
    request = str(params.get("request") or "").strip()
    if not request:
        return ActionResult(success=False, message="Pedido do workflow ausente.", error="missing request")

    workflow_id = f"wf_{uuid.uuid4().hex[:10]}"
    active_project = get_active_project(ctx.participant_identity, ctx.room)
    from workflows.engine import build_idea_to_code_workflow

    workflow_state_obj, task_plan = build_idea_to_code_workflow(
        workflow_id=workflow_id,
        request=request,
        project_id=active_project.project_id if active_project is not None else None,
        project_name=active_project.name if active_project is not None else None,
    )
    workflow_state = workflow_state_obj.to_payload()
    _persist_event_namespace(ctx.participant_identity, ctx.room, "workflow_state", workflow_state)
    await _publish_agent_event(
        ctx,
        {
            "type": "workflow_started",
            "workflow_state": workflow_state,
        },
    )
    return ActionResult(
        success=True,
        message="Workflow planejado com checkpoint antes de escrever codigo.",
        data={
            "workflow_state": workflow_state,
            "orchestration": {
                "request": request,
                "task_plan": task_plan,
            },
        },
    )


async def _workflow_status(params: JsonObject, ctx: ActionContext) -> ActionResult:
    _ = params
    workflow_state = _load_event_namespace(ctx.participant_identity, ctx.room, "workflow_state")
    return ActionResult(
        success=True,
        message="Status do workflow carregado.",
        data={"workflow_state": workflow_state if isinstance(workflow_state, dict) else None},
    )


async def _workflow_cancel(params: JsonObject, ctx: ActionContext) -> ActionResult:
    _ = params
    workflow_state = _load_event_namespace(ctx.participant_identity, ctx.room, "workflow_state")
    if not isinstance(workflow_state, dict):
        return ActionResult(success=False, message="Nenhum workflow ativo.", error="workflow_missing")
    from workflows.state import cancel_workflow_state

    next_state = cancel_workflow_state(workflow_state)
    _persist_event_namespace(ctx.participant_identity, ctx.room, "workflow_state", next_state)
    await _publish_agent_event(ctx, {"type": "workflow_failed", "workflow_state": next_state})
    return ActionResult(success=True, message="Workflow cancelado.", data={"workflow_state": next_state})


async def _whatsapp_channel_status(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    from actions_domains.whatsapp_channel import build_whatsapp_channel_status

    status = build_whatsapp_channel_status()
    return ActionResult(
        success=True,
        message="Status do canal WhatsApp carregado.",
        data={"whatsapp_channel": status},
    )


async def _automation_status(params: JsonObject, ctx: ActionContext) -> ActionResult:
    _ = params
    automation_state = _load_event_namespace(ctx.participant_identity, ctx.room, "automation_state")
    research_schedules = _load_event_namespace(ctx.participant_identity, ctx.room, "research_schedules")
    return ActionResult(
        success=True,
        message="Estado das automacoes carregado.",
        data={
            "automation_state": automation_state if isinstance(automation_state, dict) else None,
            "research_schedules": research_schedules if isinstance(research_schedules, list) else [],
        },
    )


async def _automation_run_now(params: JsonObject, ctx: ActionContext) -> ActionResult:
    automation_type = str(params.get("automation_type") or "manual").strip().lower()
    summary = "Execucao manual solicitada."
    if automation_type == "daily_briefing":
        schedules = _load_event_namespace(ctx.participant_identity, ctx.room, "research_schedules")
        if not isinstance(schedules, list) or not schedules:
            return ActionResult(
                success=False,
                message="Nenhum briefing diario configurado para executar agora.",
                error="research_schedule_missing",
            )
        summary = "Briefing diario enfileirado para execucao manual."
    automation_state = {
        "automation_id": f"auto_{uuid.uuid4().hex[:10]}",
        "automation_type": automation_type,
        "status": "scheduled",
        "summary": summary,
        "dry_run": bool(params.get("dry_run", True)),
        "last_run_at": _now_iso(),
    }
    _persist_event_namespace(ctx.participant_identity, ctx.room, "automation_state", automation_state)
    return ActionResult(
        success=True,
        message=summary,
        data={"automation_state": automation_state},
    )


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


async def _thinq_status(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    route_payload, route_error = _thinq_api_request("GET", "route", require_auth=False)
    devices, devices_error = _thinq_list_devices_payload()
    if route_error is not None and devices_error is not None:
        return devices_error

    return ActionResult(
        success=True,
        message="ThinQ configurado." if devices_error is None else "ThinQ parcialmente configurado.",
        data={
            "thinq_configured": bool(_thinq_pat()),
            "country": _thinq_country(),
            "api_base": _thinq_api_base(),
            "route": route_payload if route_error is None else None,
            "devices_count": len(devices or []),
            "devices_error": devices_error.error if devices_error is not None else None,
        },
    )


async def _thinq_list_devices(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    devices, error = _thinq_list_devices_payload()
    if error is not None:
        return error
    simplified = [_thinq_simplify_device(item) for item in devices or []]
    return ActionResult(
        success=True,
        message=f"Encontrei {len(simplified)} dispositivo(s) no ThinQ.",
        data={"devices": simplified},
    )


async def _thinq_get_device_profile(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    device, error = _thinq_find_device(
        device_name=_coerce_optional_str(params.get("device_name")),
        device_id=_coerce_optional_str(params.get("device_id")),
    )
    if error is not None:
        return error
    assert device is not None
    payload, request_error = _thinq_api_request("GET", f"devices/{quote(_thinq_extract_device_id(device), safe='')}/profile")
    if request_error is not None:
        return request_error
    return ActionResult(
        success=True,
        message=f"Perfil carregado para {_thinq_extract_device_alias(device)}.",
        data={
            "device": _thinq_simplify_device(device),
            "profile": payload if isinstance(payload, dict) else {"raw": payload},
        },
    )


async def _thinq_get_device_state(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    device, error = _thinq_find_device(
        device_name=_coerce_optional_str(params.get("device_name")),
        device_id=_coerce_optional_str(params.get("device_id")),
    )
    if error is not None:
        return error
    assert device is not None
    payload, request_error = _thinq_api_request("GET", f"devices/{quote(_thinq_extract_device_id(device), safe='')}/state")
    if request_error is not None:
        return request_error
    return ActionResult(
        success=True,
        message=f"Estado carregado para {_thinq_extract_device_alias(device)}.",
        data={
            "device": _thinq_simplify_device(device),
            "state": payload if isinstance(payload, dict) else {"raw": payload},
        },
    )


async def _thinq_control_device(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    device, error = _thinq_find_device(
        device_name=_coerce_optional_str(params.get("device_name")),
        device_id=_coerce_optional_str(params.get("device_id")),
    )
    if error is not None:
        return error
    assert device is not None

    command = params.get("command")
    if not isinstance(command, dict) or not command:
        return ActionResult(
            success=False,
            message="Comando ThinQ invalido.",
            error="missing or invalid command object",
        )

    conditional = bool(params.get("conditional"))
    _, request_error = _thinq_api_request(
        "POST",
        f"devices/{quote(_thinq_extract_device_id(device), safe='')}/control",
        body=command,
        extra_headers={"x-conditional-control": "true"} if conditional else None,
    )
    if request_error is not None:
        return request_error

    return ActionResult(
        success=True,
        message=f"Comando enviado para {_thinq_extract_device_alias(device)}.",
        data={
            "device": _thinq_simplify_device(device),
            "conditional": conditional,
            "command": command,
        },
    )


async def _ac_get_status(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    device, error = _thinq_find_device(
        device_name=_coerce_optional_str(params.get("device_name")),
        device_id=_coerce_optional_str(params.get("device_id")),
        require_air=True,
    )
    if error is not None:
        return error
    assert device is not None
    payload, request_error = _thinq_api_request("GET", f"devices/{quote(_thinq_extract_device_id(device), safe='')}/state")
    if request_error is not None:
        return request_error
    return ActionResult(
        success=True,
        message=f"Estado do ar carregado para {_thinq_extract_device_alias(device)}.",
        data={
            "device": _thinq_simplify_device(device),
            "state": payload if isinstance(payload, dict) else {"raw": payload},
        },
    )


async def _ac_send_command(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    device, error = _thinq_find_device(
        device_name=_coerce_optional_str(params.get("device_name")),
        device_id=_coerce_optional_str(params.get("device_id")),
        require_air=True,
    )
    if error is not None:
        return error
    assert device is not None

    command = params.get("command")
    if not isinstance(command, dict) or not command:
        return ActionResult(
            success=False,
            message="Comando do ar invalido.",
            error="missing or invalid command object",
        )

    conditional = bool(params.get("conditional"))
    _, request_error = _thinq_api_request(
        "POST",
        f"devices/{quote(_thinq_extract_device_id(device), safe='')}/control",
        body=command,
        extra_headers={"x-conditional-control": "true"} if conditional else None,
    )
    if request_error is not None:
        return request_error

    return ActionResult(
        success=True,
        message=f"Comando enviado para o ar {_thinq_extract_device_alias(device)}.",
        data={
            "device": _thinq_simplify_device(device),
            "conditional": conditional,
            "command": command,
        },
    )


def _thinq_build_air_command(*, section: str, payload: JsonObject) -> JsonObject:
    return {section: payload}


def _normalize_ac_mode(value: str) -> str:
    normalized = _normalize_spotify_device_label(value)
    mapping = {
        "auto": "AUTO",
        "automatico": "AUTO",
        "automatic": "AUTO",
        "secar": "AIR_DRY",
        "dry": "AIR_DRY",
        "desumidificar": "AIR_DRY",
        "aquecer": "HEAT",
        "heat": "HEAT",
        "ventilar": "FAN",
        "fan": "FAN",
        "frio": "COOL",
        "cool": "COOL",
        "refrigerar": "COOL",
    }
    return mapping.get(normalized.replace(" ", ""), mapping.get(normalized, value.strip().upper()))


def _normalize_ac_fan_speed(value: str) -> str:
    normalized = _normalize_spotify_device_label(value)
    mapping = {
        "auto": "AUTO",
        "automatico": "AUTO",
        "baixo": "LOW",
        "low": "LOW",
        "medio": "MID",
        "medio alto": "MID_HIGH",
        "mid": "MID",
        "mid high": "MID_HIGH",
        "alto": "HIGH",
        "high": "HIGH",
        "natural": "NATURE",
        "nature": "NATURE",
        "baixo medio": "LOW_MID",
        "low mid": "LOW_MID",
    }
    compact = normalized.replace(" ", "")
    return mapping.get(compact, mapping.get(normalized, value.strip().upper()))


async def _ac_turn_on(params: JsonObject, ctx: ActionContext) -> ActionResult:
    return await _ac_send_command(
        {
            "device_name": params.get("device_name"),
            "device_id": params.get("device_id"),
            "conditional": params.get("conditional"),
            "command": _thinq_build_air_command(section="operation", payload={"airConOperationMode": "POWER_ON"}),
        },
        ctx,
    )


async def _ac_turn_off(params: JsonObject, ctx: ActionContext) -> ActionResult:
    return await _ac_send_command(
        {
            "device_name": params.get("device_name"),
            "device_id": params.get("device_id"),
            "conditional": params.get("conditional"),
            "command": _thinq_build_air_command(section="operation", payload={"airConOperationMode": "POWER_OFF"}),
        },
        ctx,
    )


async def _ac_set_mode(params: JsonObject, ctx: ActionContext) -> ActionResult:
    raw_mode = _coerce_optional_str(params.get("mode"))
    if not raw_mode:
        return ActionResult(success=False, message="Informe o modo do ar.", error="missing mode")
    mode = _normalize_ac_mode(raw_mode)
    return await _ac_send_command(
        {
            "device_name": params.get("device_name"),
            "device_id": params.get("device_id"),
            "conditional": params.get("conditional"),
            "command": _thinq_build_air_command(section="airConJobMode", payload={"currentJobMode": mode}),
        },
        ctx,
    )


async def _ac_set_fan_speed(params: JsonObject, ctx: ActionContext) -> ActionResult:
    raw_speed = _coerce_optional_str(params.get("fan_speed"))
    if not raw_speed:
        return ActionResult(success=False, message="Informe a velocidade do vento.", error="missing fan_speed")
    speed = _normalize_ac_fan_speed(raw_speed)
    detail = bool(params.get("detail"))
    key = "windStrengthDetail" if detail else "windStrength"
    return await _ac_send_command(
        {
            "device_name": params.get("device_name"),
            "device_id": params.get("device_id"),
            "conditional": params.get("conditional"),
            "command": _thinq_build_air_command(section="airFlow", payload={key: speed}),
        },
        ctx,
    )


async def _ac_set_temperature(params: JsonObject, ctx: ActionContext) -> ActionResult:
    device, error = _thinq_find_device(
        device_name=_coerce_optional_str(params.get("device_name")),
        device_id=_coerce_optional_str(params.get("device_id")),
        require_air=True,
    )
    if error is not None:
        return error
    assert device is not None

    temperature = params.get("temperature")
    if not isinstance(temperature, (int, float)):
        return ActionResult(success=False, message="Informe a temperatura alvo.", error="missing temperature")

    profile_payload, profile_error = _thinq_api_request(
        "GET",
        f"devices/{quote(_thinq_extract_device_id(device), safe='')}/profile",
    )
    if profile_error is not None:
        return profile_error

    profile = profile_payload if isinstance(profile_payload, dict) else {}
    temperature_property = (
        ((profile.get("property") or {}).get("temperature") or {})
        if isinstance(profile.get("property"), dict)
        else {}
    )
    target_schema = temperature_property.get("targetTemperature") if isinstance(temperature_property, dict) else {}
    range_info = (target_schema.get("value") or {}).get("w", {}) if isinstance(target_schema, dict) else {}
    min_value = float(range_info.get("min", 18))
    max_value = float(range_info.get("max", 30))
    step = float(range_info.get("step", 0.5))

    desired = max(min_value, min(max_value, float(temperature)))
    if step > 0:
        desired = round(round((desired - min_value) / step) * step + min_value, 2)

    unit = _coerce_optional_str(params.get("unit")) or "C"
    return await _ac_send_command(
        {
            "device_name": _thinq_extract_device_alias(device),
            "device_id": _thinq_extract_device_id(device),
            "conditional": params.get("conditional"),
            "command": _thinq_build_air_command(
                section="temperature",
                payload={"targetTemperature": desired, "unit": unit.upper()},
            ),
        },
        ctx,
    )


async def _ac_set_swing(params: JsonObject, ctx: ActionContext) -> ActionResult:
    enabled = params.get("enabled")
    if not isinstance(enabled, bool):
        return ActionResult(success=False, message="Informe se a oscilacao fica ligada ou desligada.", error="missing enabled")
    return await _ac_send_command(
        {
            "device_name": params.get("device_name"),
            "device_id": params.get("device_id"),
            "conditional": params.get("conditional"),
            "command": _thinq_build_air_command(section="windDirection", payload={"rotateUpDown": enabled}),
        },
        ctx,
    )


def _thinq_profile_write_enum_values(profile: JsonObject, section: str, key: str) -> set[str]:
    properties = profile.get("property")
    if not isinstance(properties, dict):
        return set()
    section_payload = properties.get(section)
    if not isinstance(section_payload, dict):
        return set()
    entry = section_payload.get(key)
    if not isinstance(entry, dict):
        return set()
    value = entry.get("value")
    if not isinstance(value, dict):
        return set()
    writable = value.get("w")
    if not isinstance(writable, list):
        return set()
    return {str(item).strip() for item in writable if str(item).strip()}


async def _ac_set_sleep_timer(params: JsonObject, ctx: ActionContext) -> ActionResult:
    hours = params.get("hours", 0)
    minutes = params.get("minutes", 0)
    target_name = params.get("device_name") or _thinq_default_ac_name()
    target_id = params.get("device_id")
    try:
        total_minutes = max(0, int(hours) * 60 + int(minutes))
    except Exception:
        return ActionResult(success=False, message="Timer invalido.", error="invalid timer")

    profile_result = await _thinq_get_device_profile(
        {"device_name": target_name, "device_id": target_id},
        ctx,
    )
    profile = (profile_result.data or {}).get("profile") if profile_result.success and isinstance(profile_result.data, dict) else {}
    writable_values = _thinq_profile_write_enum_values(profile if isinstance(profile, dict) else {}, "sleepTimer", "relativeStopTimer")

    if total_minutes == 0:
        payload = {"relativeStopTimer": "UNSET"}
        message = "Timer de desligamento removido."
    else:
        if writable_values and "SET" not in writable_values:
            return ActionResult(
                success=False,
                message="Este modelo de ar nao suporta programar timer de desligamento pela API ThinQ.",
                error="sleep timer set unsupported",
            )
        payload = {
            "relativeStopTimer": "SET",
            "relativeHourToStop": total_minutes // 60,
            "relativeMinuteToStop": total_minutes % 60,
        }
        message = f"Timer de desligamento ajustado para {total_minutes // 60}h {total_minutes % 60}min."

    result = await _ac_send_command(
        {
            "device_name": target_name,
            "device_id": target_id,
            "conditional": params.get("conditional"),
            "command": _thinq_build_air_command(section="sleepTimer", payload=payload),
        },
        ctx,
    )
    if result.success:
        result.message = message
    return result


async def _ac_set_start_timer(params: JsonObject, ctx: ActionContext) -> ActionResult:
    hours = params.get("hours", 0)
    minutes = params.get("minutes", 0)
    target_name = params.get("device_name") or _thinq_default_ac_name()
    target_id = params.get("device_id")
    try:
        total_minutes = max(0, int(hours) * 60 + int(minutes))
    except Exception:
        return ActionResult(success=False, message="Timer de ligar invalido.", error="invalid timer")

    profile_result = await _thinq_get_device_profile(
        {"device_name": target_name, "device_id": target_id},
        ctx,
    )
    profile = (profile_result.data or {}).get("profile") if profile_result.success and isinstance(profile_result.data, dict) else {}
    writable_values = _thinq_profile_write_enum_values(profile if isinstance(profile, dict) else {}, "timer", "relativeStartTimer")

    if total_minutes == 0:
        payload = {"relativeStartTimer": "UNSET"}
        message = "Timer de ligamento removido."
    else:
        if writable_values and "SET" not in writable_values:
            return ActionResult(
                success=False,
                message="Este modelo de ar nao suporta programar timer de ligamento pela API ThinQ.",
                error="start timer set unsupported",
            )
        payload = {
            "relativeStartTimer": "SET",
            "relativeHourToStart": total_minutes // 60,
            "relativeMinuteToStart": total_minutes % 60,
        }
        message = f"Timer de ligamento ajustado para {total_minutes // 60}h {total_minutes % 60}min."

    result = await _ac_send_command(
        {
            "device_name": target_name,
            "device_id": target_id,
            "conditional": params.get("conditional"),
            "command": _thinq_build_air_command(section="timer", payload=payload),
        },
        ctx,
    )
    if result.success:
        result.message = message
    return result


async def _ac_set_power_save(params: JsonObject, ctx: ActionContext) -> ActionResult:
    enabled = params.get("enabled")
    if not isinstance(enabled, bool):
        return ActionResult(success=False, message="Informe se o modo economia fica ligado ou desligado.", error="missing enabled")
    result = await _ac_send_command(
        {
            "device_name": params.get("device_name"),
            "device_id": params.get("device_id"),
            "conditional": params.get("conditional"),
            "command": _thinq_build_air_command(section="powerSave", payload={"powerSaveEnabled": enabled}),
        },
        ctx,
    )
    if result.success:
        result.message = "Modo economia ligado." if enabled else "Modo economia desligado."
    return result


async def _ac_apply_preset(params: JsonObject, ctx: ActionContext) -> ActionResult:
    preset_raw = _coerce_optional_str(params.get("preset"))
    if not preset_raw:
        return ActionResult(success=False, message="Informe qual preset aplicar.", error="missing preset")

    preset = _normalize_spotify_device_label(preset_raw)
    base_params = {
        "device_name": params.get("device_name"),
        "device_id": params.get("device_id"),
        "conditional": params.get("conditional"),
    }

    if preset in {"modo dormir", "dormir", "sleep"}:
        sequence = [
            ("modo", await _ac_set_mode({**base_params, "mode": "COOL"}, ctx)),
            ("temperatura", await _ac_set_temperature({**base_params, "temperature": 23}, ctx)),
            ("vento", await _ac_set_fan_speed({**base_params, "fan_speed": "LOW"}, ctx)),
            ("timer", await _ac_set_sleep_timer({**base_params, "hours": 8}, ctx)),
        ]
    elif preset in {"gelar sala", "turbo", "resfriar rapido", "resfriar rapido"}:
        sequence = [
            ("modo", await _ac_set_mode({**base_params, "mode": "COOL"}, ctx)),
            ("temperatura", await _ac_set_temperature({**base_params, "temperature": 18}, ctx)),
            ("vento", await _ac_set_fan_speed({**base_params, "fan_speed": "HIGH"}, ctx)),
        ]
    elif preset in {"modo visita", "visita"}:
        sequence = [
            ("ligar", await _ac_turn_on(base_params, ctx)),
            ("modo", await _ac_set_mode({**base_params, "mode": "COOL"}, ctx)),
            ("temperatura", await _ac_set_temperature({**base_params, "temperature": 22}, ctx)),
            ("vento", await _ac_set_fan_speed({**base_params, "fan_speed": "MID"}, ctx)),
            ("oscilacao", await _ac_set_swing({**base_params, "enabled": True}, ctx)),
        ]
    elif preset in {"economia", "eco", "modo economia"}:
        sequence = [
            ("ligar", await _ac_turn_on(base_params, ctx)),
            ("modo", await _ac_set_mode({**base_params, "mode": "AUTO"}, ctx)),
            ("temperatura", await _ac_set_temperature({**base_params, "temperature": 24}, ctx)),
            ("vento", await _ac_set_fan_speed({**base_params, "fan_speed": "AUTO"}, ctx)),
            ("economia", await _ac_set_power_save({**base_params, "enabled": True}, ctx)),
        ]
    elif preset in {"ventilar leve", "ventilar", "brisa"}:
        sequence = [
            ("ligar", await _ac_turn_on(base_params, ctx)),
            ("modo", await _ac_set_mode({**base_params, "mode": "FAN"}, ctx)),
            ("vento", await _ac_set_fan_speed({**base_params, "fan_speed": "LOW"}, ctx)),
            ("oscilacao", await _ac_set_swing({**base_params, "enabled": True}, ctx)),
        ]
    else:
        return ActionResult(
            success=False,
            message="Preset desconhecido.",
            error="unsupported preset; use 'modo dormir', 'gelar sala', 'modo visita', 'economia' ou 'ventilar leve'",
        )

    failed = [f"{label}: {result.error or result.message}" for label, result in sequence if not result.success]
    if failed:
        return ActionResult(
            success=False,
            message="Preset executado parcialmente.",
            data={"steps": [{"label": label, "success": result.success, "message": result.message} for label, result in sequence]},
            error="; ".join(failed),
        )

    return ActionResult(
        success=True,
        message=f"Preset aplicado: {preset_raw}.",
        data={"steps": [{"label": label, "success": result.success, "message": result.message} for label, result in sequence]},
    )


def _ac_current_temperature_from_status(status_data: JsonObject) -> float | None:
    state = status_data.get("state")
    if not isinstance(state, dict):
        return None
    temperature = state.get("temperature")
    if not isinstance(temperature, dict):
        return None
    current = temperature.get("currentTemperature")
    if isinstance(current, (int, float)):
        return float(current)
    return None


def _resolve_ac_arrival_prefs(params: JsonObject) -> JsonObject:
    stored = _load_ac_arrival_prefs()
    defaults: JsonObject = {
        "desired_temperature": 23.0,
        "hot_threshold": 28.0,
        "vent_only_threshold": 25.0,
        "eta_minutes": 20,
        "enable_swing": True,
        "device_name": _thinq_default_ac_name(),
    }
    resolved = {**defaults, **(stored if isinstance(stored, dict) else {})}
    for key in ("desired_temperature", "hot_threshold", "vent_only_threshold"):
        value = params.get(key)
        if isinstance(value, (int, float)):
            resolved[key] = float(value)
    eta = params.get("eta_minutes")
    if isinstance(eta, int) and eta >= 0:
        resolved["eta_minutes"] = eta
    if isinstance(params.get("enable_swing"), bool):
        resolved["enable_swing"] = params["enable_swing"]
    device_name = _coerce_optional_str(params.get("device_name"))
    if device_name:
        resolved["device_name"] = device_name
    return resolved


async def _ac_configure_arrival_prefs(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    prefs = _resolve_ac_arrival_prefs(params)
    if float(prefs["vent_only_threshold"]) > float(prefs["hot_threshold"]):
        return ActionResult(
            success=False,
            message="O limite de ventilacao nao pode ser maior que o limite de calor forte.",
            error="invalid thresholds",
        )
    _save_ac_arrival_prefs(prefs)
    return ActionResult(
        success=True,
        message="Preferencias de chegada em casa salvas.",
        data={"preferences": prefs},
    )


async def _ac_prepare_arrival(params: JsonObject, ctx: ActionContext) -> ActionResult:
    prefs = _resolve_ac_arrival_prefs(params)
    target_name = _coerce_optional_str(params.get("device_name")) or _coerce_optional_str(prefs.get("device_name")) or _thinq_default_ac_name()
    target_id = _coerce_optional_str(params.get("device_id"))
    dry_run = bool(params.get("dry_run"))

    status_result = await _ac_get_status({"device_name": target_name, "device_id": target_id}, ctx)
    if not status_result.success:
        return status_result

    status_data = status_result.data if isinstance(status_result.data, dict) else {}
    current_temperature = _ac_current_temperature_from_status(status_data)
    if current_temperature is None:
        return ActionResult(
            success=False,
            message="Nao consegui ler a temperatura atual do ambiente pelo ar.",
            error="missing current temperature",
        )

    desired_temperature = float(prefs["desired_temperature"])
    hot_threshold = float(prefs["hot_threshold"])
    vent_only_threshold = float(prefs["vent_only_threshold"])
    eta_minutes = int(prefs["eta_minutes"])
    enable_swing = bool(prefs["enable_swing"])

    if current_temperature >= hot_threshold:
        strategy = "cool"
        fan_speed = "HIGH" if current_temperature - desired_temperature >= 3 else "MID"
        actions_to_run: list[tuple[str, Any]] = [
            ("ligar", lambda: _ac_turn_on({"device_name": target_name, "device_id": target_id}, ctx)),
            ("modo", lambda: _ac_set_mode({"device_name": target_name, "device_id": target_id, "mode": "COOL"}, ctx)),
            (
                "temperatura",
                lambda: _ac_set_temperature(
                    {"device_name": target_name, "device_id": target_id, "temperature": desired_temperature},
                    ctx,
                ),
            ),
            ("vento", lambda: _ac_set_fan_speed({"device_name": target_name, "device_id": target_id, "fan_speed": fan_speed}, ctx)),
        ]
        if enable_swing:
            actions_to_run.append(("oscilacao", lambda: _ac_set_swing({"device_name": target_name, "device_id": target_id, "enabled": True}, ctx)))
        message = (
            f"Ambiente a {current_temperature:.1f}C: esta quente. "
            f"Vou resfriar para {desired_temperature:.1f}C (ETA {eta_minutes} min)."
        )
    elif current_temperature >= vent_only_threshold:
        strategy = "fan"
        actions_to_run = [
            ("ligar", lambda: _ac_turn_on({"device_name": target_name, "device_id": target_id}, ctx)),
            ("modo", lambda: _ac_set_mode({"device_name": target_name, "device_id": target_id, "mode": "FAN"}, ctx)),
            ("vento", lambda: _ac_set_fan_speed({"device_name": target_name, "device_id": target_id, "fan_speed": "LOW"}, ctx)),
        ]
        if enable_swing:
            actions_to_run.append(("oscilacao", lambda: _ac_set_swing({"device_name": target_name, "device_id": target_id, "enabled": True}, ctx)))
        message = (
            f"Ambiente a {current_temperature:.1f}C: esta morno. "
            f"So ventilar ja deve bastar (ETA {eta_minutes} min)."
        )
    else:
        strategy = "hold"
        actions_to_run = []
        message = f"Ambiente a {current_temperature:.1f}C: temperatura aceitavel. Nao precisa mexer no ar agora."

    if dry_run or not actions_to_run:
        return ActionResult(
            success=True,
            message=message + (" (dry-run)" if dry_run else ""),
            data={
                "strategy": strategy,
                "current_temperature": current_temperature,
                "preferences": prefs,
                "applied": False,
                "device_name": target_name,
            },
        )

    results: list[tuple[str, ActionResult]] = []
    for label, runner in actions_to_run:
        results.append((label, await runner()))

    failed = [f"{label}: {result.error or result.message}" for label, result in results if not result.success]
    if failed:
        return ActionResult(
            success=False,
            message="Falha ao preparar a chegada em casa.",
            error="; ".join(failed),
            data={
                "strategy": strategy,
                "current_temperature": current_temperature,
                "preferences": prefs,
                "steps": [label for label, _ in results],
                "device_name": target_name,
            },
        )

    return ActionResult(
        success=True,
        message=message,
        data={
            "strategy": strategy,
            "current_temperature": current_temperature,
            "preferences": prefs,
            "applied": True,
            "steps": [label for label, _ in results],
            "device_name": target_name,
        },
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
    requested_device_name = _coerce_optional_str(params.get("device_name"))
    requested_device_id = _coerce_optional_str(params.get("device_id"))
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
    if requested_device_name:
        _spotify_remember_device_alias(requested_device_name, str(device.get("id", "")).strip())

    return ActionResult(
        success=True,
        message=f"Playback transferido para {device.get('name', 'device desconhecido')}.",
        data={"device_id": device.get("id"), "device_name": device.get("name"), "is_active": True},
    )


async def _spotify_play(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    requested_device_name = _coerce_optional_str(params.get("device_name")) or _coerce_optional_str(
        os.getenv("SPOTIFY_DEFAULT_DEVICE_NAME", "")
    )
    requested_device_id = _coerce_optional_str(params.get("device_id"))
    query = str(params.get("query", "")).strip()
    uri = _normalize_spotify_uri(str(params.get("uri", "")))
    target_device: JsonObject | None = None
    if requested_device_name or requested_device_id:
        target_device, target_error = _spotify_find_device(requested_device_name, requested_device_id)
        if target_error is not None:
            return target_error

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
        if resolved_uri.startswith("spotify:track:"):
            body = {"uris": [resolved_uri]}
        else:
            body = {"context_uri": resolved_uri}

    play_params: JsonObject | None = None
    if target_device and target_device.get("id"):
        play_params = {"device_id": str(target_device.get("id"))}

    _, play_error = _spotify_api_request("PUT", "me/player/play", params=play_params, body=body)
    if play_error is not None:
        if target_device and _is_spotify_restriction_error(play_error):
            fallback_body = {"device_ids": [str(target_device.get("id"))], "play": True}
            _, transfer_error = _spotify_api_request("PUT", "me/player", body=fallback_body)
            if transfer_error is None:
                if requested_device_name:
                    _spotify_remember_device_alias(requested_device_name, str(target_device.get("id", "")).strip())
                return ActionResult(
                    success=True,
                    message=f"Playback transferido e retomado em {target_device.get('name', 'device desconhecido')}.",
                    data={
                        "device_id": target_device.get("id"),
                        "device_name": target_device.get("name"),
                        "uri": resolved_uri,
                        "title": resolved_title,
                    },
                )
        return play_error

    if resolved_uri:
        if requested_device_name and target_device:
            _spotify_remember_device_alias(requested_device_name, str(target_device.get("id", "")).strip())
        return ActionResult(
            success=True,
            message=f"Tocando agora: {resolved_title or resolved_uri}.",
            data={
                "uri": resolved_uri,
                "title": resolved_title,
                "device_id": target_device.get("id") if target_device else None,
                "device_name": target_device.get("name") if target_device else None,
            },
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
    requested_device_name = _coerce_optional_str(params.get("device_name"))
    requested_device_id = _coerce_optional_str(params.get("device_id"))
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
    if requested_device_name and "device_id" in request_params:
        _spotify_remember_device_alias(requested_device_name, str(request_params["device_id"]))
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


async def _code_reindex_repo(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    catalog = _get_project_catalog()
    target_project_id = str(params.get("project_id", "")).strip()
    records: list[ProjectRecord]
    if target_project_id:
        record = catalog.get_project(target_project_id)
        if record is None:
            return ActionResult(success=False, message="Projeto nao encontrado para reindexacao.", error="unknown project")
        records = [record]
    else:
        records = catalog.list_projects()
        if not records:
            catalog.scan()
            records = catalog.list_projects()

    summaries: list[JsonObject] = []
    for record in records:
        root = Path(record.root_path).resolve(strict=False)
        if not root.exists():
            summaries.append({"project_id": record.project_id, "name": record.name, "status": "missing_root"})
            continue
        summary = _get_code_index().index_project(
            record.project_id,
            root,
            project_name=record.name,
            aliases=record.aliases,
        )
        catalog.update_last_indexed(record.project_id)
        summaries.append(
            {
                "project_id": record.project_id,
                "name": record.name,
                "summary": summary,
                "knowledge_stats": _get_code_index().stats(project_id=record.project_id),
            }
        )

    return ActionResult(
        success=True,
        message="Indice global de codigo atualizado.",
        data={
            "projects_reindexed": summaries,
            "knowledge_stats": _get_code_index().stats(),
            **_active_project_payload(ctx.participant_identity, ctx.room),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _code_search_repo(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    query = str(params.get("query", "")).strip()
    limit = int(params.get("limit", 5))
    if not query:
        return ActionResult(success=False, message="Informe uma consulta de codigo.", error="missing query")

    active = get_active_project(ctx.participant_identity, ctx.room)
    results = _get_code_index().search(query, limit=limit, project_id=active.project_id if active else None)
    if not results:
        return ActionResult(
            success=False,
            message="Nao encontrei trechos de codigo para essa pergunta.",
            data={
                "query": query,
                "repo_root": str(_code_repo_root()),
                **_active_project_payload(ctx.participant_identity, ctx.room),
            },
            error="not found",
        )
    return ActionResult(
        success=True,
        message=f"Encontrei {len(results)} trecho(s) relevantes do codigo.",
        data={
            "query": query,
            "repo_root": str(_code_repo_root()),
            "results": results,
            **_active_project_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _project_list_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    include_inactive = bool(params.get("include_inactive", False))
    projects = _get_project_catalog().list_projects(include_inactive=include_inactive)
    return ActionResult(
        success=True,
        message=f"{len(projects)} projeto(s) no catalogo.",
        data={
            "projects": [_project_record_to_payload(item) for item in projects],
            **_active_project_payload(ctx.participant_identity, ctx.room),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _project_scan_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    discovered = _get_project_catalog().scan()
    return ActionResult(
        success=True,
        message=f"Scan finalizado. {len(discovered)} projeto(s) detectado(s).",
        data={
            "projects": [_project_record_to_payload(item) for item in discovered],
            "catalog_size": len(_get_project_catalog().list_projects(include_inactive=True)),
            **_active_project_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _project_update_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    project_id = str(params.get("project_id", "")).strip()
    if not project_id:
        return ActionResult(success=False, message="Informe o project_id para atualizar.", error="missing project_id")

    catalog = _get_project_catalog()
    record = catalog.get_project(project_id)
    if record is None:
        return ActionResult(success=False, message="Projeto nao encontrado para atualizacao.", error="unknown project")

    updated = False
    if "name" in params:
        name = str(params.get("name", "")).strip()
        if name:
            catalog.rename_project(project_id, name)
            updated = True
    if "aliases" in params:
        aliases = params.get("aliases", [])
        if isinstance(aliases, list):
            catalog.set_aliases(project_id, [str(item) for item in aliases if str(item).strip()])
            updated = True
    if "priority_score" in params:
        catalog.set_priority(project_id, int(params.get("priority_score", 0) or 0))
        updated = True
    if "is_active" in params:
        catalog.set_active(project_id, is_active=bool(params.get("is_active")))
        updated = True

    refreshed = catalog.get_project(project_id)
    if refreshed is None:
        return ActionResult(success=False, message="Projeto indisponivel apos atualizacao.", error="project missing after update")

    if not refreshed.is_active:
        active = get_active_project(ctx.participant_identity, ctx.room)
        if active and active.project_id == project_id:
            clear_active_project(ctx.participant_identity, ctx.room)
    elif get_active_project(ctx.participant_identity, ctx.room) and get_active_project(ctx.participant_identity, ctx.room).project_id == project_id:
        _set_active_project_from_record(refreshed, ctx, selection_reason="project_update", index_status=get_active_project(ctx.participant_identity, ctx.room).index_status)

    return ActionResult(
        success=True,
        message="Projeto atualizado no catalogo." if updated else "Nenhuma mudanca aplicada ao projeto.",
        data={
            "project": _project_record_to_payload(refreshed),
            **_active_project_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _project_remove_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    project_id = str(params.get("project_id", "")).strip()
    if not project_id:
        return ActionResult(success=False, message="Informe o project_id para remover.", error="missing project_id")
    removed = _get_project_catalog().remove_project(project_id)
    if removed is None:
        return ActionResult(success=False, message="Projeto nao encontrado para remocao.", error="unknown project")
    active = get_active_project(ctx.participant_identity, ctx.room)
    if active and active.project_id == project_id:
        clear_active_project(ctx.participant_identity, ctx.room)
    return ActionResult(
        success=True,
        message=f"Projeto {removed.name} removido do catalogo.",
        data={
            "removed_project": _project_record_to_payload(removed),
            **_active_project_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _project_select_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    record, error = _resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None
    active = get_active_project(ctx.participant_identity, ctx.room)
    return ActionResult(
        success=True,
        message=f"Projeto ativo definido para {record.name}.",
        data={
            "selected_project": _project_record_to_payload(record),
            **_active_project_payload(ctx.participant_identity, ctx.room),
            "active_project": {
                **(_active_project_payload(ctx.participant_identity, ctx.room).get("active_project") or {}),
                "index_status": active.index_status if active else "unknown",
            },
        },
    )


async def _project_get_active_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    active = get_active_project(ctx.participant_identity, ctx.room)
    if active is None:
        return ActionResult(
            success=False,
            message="Nenhum projeto ativo na sessao.",
            data=_active_project_payload(ctx.participant_identity, ctx.room),
            error="no active project",
        )
    return ActionResult(
        success=True,
        message=f"Projeto ativo: {active.name}.",
        data={**_active_project_payload(ctx.participant_identity, ctx.room)},
    )


async def _project_clear_active_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    clear_active_project(ctx.participant_identity, ctx.room)
    return ActionResult(
        success=True,
        message="Projeto ativo removido da sessao.",
        data={**_active_project_payload(ctx.participant_identity, ctx.room)},
    )


async def _project_refresh_index_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    record, error = _resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None
    root = Path(record.root_path).resolve(strict=False)
    if not root.exists():
        return ActionResult(success=False, message="A raiz do projeto nao existe.", error="missing project root")
    summary = _get_code_index().index_project(record.project_id, root, project_name=record.name, aliases=record.aliases)
    _get_project_catalog().update_last_indexed(record.project_id)
    _set_active_project_from_record(record, ctx, selection_reason="refresh_index", index_status="reindexed")
    return ActionResult(
        success=True,
        message=f"Indice atualizado para {record.name}.",
        data={
            "project": _project_record_to_payload(record),
            "ingest_summary": summary,
            "knowledge_stats": _get_code_index().stats(project_id=record.project_id),
            **_active_project_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _project_search_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    query = str(params.get("query", "")).strip()
    limit = int(params.get("limit", 5))
    if not query:
        return ActionResult(success=False, message="Informe o que devo procurar no projeto.", error="missing query")
    record, error = _resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None
    results = _get_code_index().search(query, limit=limit, project_id=record.project_id)
    if not results:
        return ActionResult(
            success=False,
            message=f"Nao encontrei trechos para '{query}' em {record.name}.",
            data={"query": query, "project": _project_record_to_payload(record), **_active_project_payload(ctx.participant_identity, ctx.room)},
            error="not found",
        )
    return ActionResult(
        success=True,
        message=f"Encontrei {len(results)} trecho(s) em {record.name}.",
        data={
            "query": query,
            "project": _project_record_to_payload(record),
            "results": results,
            **_active_project_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _coding_mode_get_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    return ActionResult(
        success=True,
        message="Modo funcional atual carregado.",
        data={**_capability_payload(ctx.participant_identity, ctx.room), **_active_project_payload(ctx.participant_identity, ctx.room)},
    )


async def _coding_mode_set_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    mode = str(params.get("mode", "default")).strip()
    applied = set_capability_mode(ctx.participant_identity, ctx.room, mode)
    return ActionResult(
        success=True,
        message=f"Modo funcional alterado para {applied}.",
        data={**_capability_payload(ctx.participant_identity, ctx.room), **_active_project_payload(ctx.participant_identity, ctx.room)},
    )


async def _run_codex_task(
    *,
    params: JsonObject,
    ctx: ActionContext,
    default_request: str,
    review_mode: bool,
) -> ActionResult:
    user_request = (
        str(params.get("request", "")).strip()
        or str(params.get("query", "")).strip()
        or str(params.get("prompt", "")).strip()
        or default_request
    )
    if not user_request:
        return ActionResult(success=False, message="Descreva a tarefa para o Codex.", error="missing request")

    if not is_codex_available():
        return ActionResult(success=False, message="Codex CLI nao esta disponivel neste ambiente.", error="codex unavailable")

    record, error = _resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None

    root = Path(record.root_path).resolve(strict=False)
    if not root.exists():
        return ActionResult(success=False, message="A raiz do projeto nao existe.", error="missing project root")

    prompt = _build_codex_request_prompt(record=record, user_request=user_request, review_mode=review_mode)
    command_preview = (
        "codex exec --json --skip-git-repo-check --sandbox read-only "
        f'--ephemeral -C "{root}" "<prompt>"'
    )
    task = ActiveCodexTask(
        task_id=f"codex_{uuid.uuid4().hex[:12]}",
        status="running",
        project_id=record.project_id,
        project_name=record.name,
        working_directory=str(root),
        request=user_request,
        started_at=_now_iso(),
        current_phase="starting",
        command_preview=command_preview,
    )
    set_active_codex_task(ctx.participant_identity, ctx.room, task)
    await _emit_codex_task_event(
        ctx,
        event_type="codex_task_started",
        task=task,
        phase="starting",
        message=f"Iniciando Codex em {record.name}.",
    )

    async def on_progress(event: JsonObject) -> None:
        task.current_phase = str(event.get("type", "")).strip() or "progress"
        task.raw_last_event = event
        task.summary = _codex_progress_message(event)
        await _emit_codex_task_event(
            ctx,
            event_type="codex_task_progress",
            task=task,
            phase=task.current_phase,
            message=task.summary,
            raw_event_type=str(event.get("type", "")).strip() or None,
        )

    key = _codex_key(ctx.participant_identity, ctx.room)
    try:
        result = await run_exec_streaming(
            prompt=prompt,
            working_directory=root,
            on_progress=on_progress,
            process_registry=CODEX_RUNNING_PROCESSES,
            registry_key=key,
        )
    except FileNotFoundError:
        task.status = "failed"
        task.finished_at = _now_iso()
        task.current_phase = "missing_cli"
        task.error = "codex unavailable"
        task.summary = "Codex CLI nao esta disponivel neste ambiente."
        _push_codex_history(ctx.participant_identity, ctx.room, task)
        await _emit_codex_task_event(
            ctx,
            event_type="codex_task_failed",
            task=task,
            phase="missing_cli",
            message=task.summary,
        )
        return ActionResult(success=False, message=task.summary, error=task.error)
    except Exception as error:  # noqa: BLE001
        task.status = "failed"
        task.finished_at = _now_iso()
        task.current_phase = "runtime_error"
        task.error = str(error)
        task.summary = "A tarefa do Codex falhou durante a execucao."
        _push_codex_history(ctx.participant_identity, ctx.room, task)
        await _emit_codex_task_event(
            ctx,
            event_type="codex_task_failed",
            task=task,
            phase="runtime_error",
            message=task.summary,
        )
        return ActionResult(success=False, message=task.summary, error=str(error))

    if task.status == "cancelled":
        task.exit_code = result.exit_code
        task.raw_last_event = result.last_event
        return ActionResult(
            success=False,
            message="Tarefa do Codex cancelada.",
            data={
                "codex_task": _codex_task_to_payload(task),
                "codex_history": _codex_history_payload(ctx.participant_identity, ctx.room),
                **_active_project_payload(ctx.participant_identity, ctx.room),
                **_capability_payload(ctx.participant_identity, ctx.room),
            },
            error="cancelled",
        )

    task.status = "completed" if result.success else "failed"
    task.finished_at = _now_iso()
    task.current_phase = "completed" if result.success else "failed"
    task.summary = result.summary
    task.exit_code = result.exit_code
    task.raw_last_event = result.last_event
    if not result.success:
        task.error = result.stderr[:400] or f"exit code {result.exit_code}"
    _push_codex_history(ctx.participant_identity, ctx.room, task)

    await _emit_codex_task_event(
        ctx,
        event_type="codex_task_completed" if result.success else "codex_task_failed",
        task=task,
        phase=task.current_phase,
        message=result.summary,
        raw_event_type=str(result.last_event.get("type", "")).strip() if isinstance(result.last_event, dict) else None,
    )

    data = {
        "codex_task": _codex_task_to_payload(task),
        "codex_history": _codex_history_payload(ctx.participant_identity, ctx.room),
        **_active_project_payload(ctx.participant_identity, ctx.room),
        **_capability_payload(ctx.participant_identity, ctx.room),
    }
    if result.success:
        return ActionResult(success=True, message=f"Codex concluiu a tarefa em {record.name}.", data=data)
    return ActionResult(
        success=False,
        message=f"Codex falhou na tarefa em {record.name}.",
        data=data,
        error=task.error,
    )


async def _codex_exec_task_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    return await _run_codex_task(
        params=params,
        ctx=ctx,
        default_request="Analise o projeto atual e explique o estado tecnico com proximos passos.",
        review_mode=False,
    )


async def _codex_exec_review_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    return await _run_codex_task(
        params=params,
        ctx=ctx,
        default_request="Revise o estado atual do projeto e destaque riscos e pontos de atencao sem editar arquivos.",
        review_mode=True,
    )


async def _codex_exec_status_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    task = get_active_codex_task(ctx.participant_identity, ctx.room)
    if task is None:
        return ActionResult(
            success=False,
            message="Nenhuma tarefa do Codex na sessao.",
            data={"codex_task": None, "codex_history": _codex_history_payload(ctx.participant_identity, ctx.room)},
            error="no codex task",
        )
    return ActionResult(
        success=True,
        message=f"Tarefa do Codex em estado {task.status}.",
        data={
            "codex_task": _codex_task_to_payload(task),
            "codex_history": _codex_history_payload(ctx.participant_identity, ctx.room),
            **_active_project_payload(ctx.participant_identity, ctx.room),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _codex_cancel_task_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    key = _codex_key(ctx.participant_identity, ctx.room)
    process = CODEX_RUNNING_PROCESSES.get(key)
    task = get_active_codex_task(ctx.participant_identity, ctx.room)
    if process is None or task is None or task.status != "running":
        return ActionResult(success=False, message="Nenhuma tarefa do Codex em andamento.", error="no running task")

    process.terminate()
    task.status = "cancelled"
    task.finished_at = _now_iso()
    task.current_phase = "cancelled"
    task.summary = "Tarefa cancelada pelo usuario."
    task.error = None
    CODEX_RUNNING_PROCESSES.pop(key, None)
    _push_codex_history(ctx.participant_identity, ctx.room, task)
    await _emit_codex_task_event(
        ctx,
        event_type="codex_task_cancelled",
        task=task,
        phase="cancelled",
        message=task.summary,
    )
    return ActionResult(
        success=True,
        message="Tarefa do Codex cancelada.",
        data={
            "codex_task": _codex_task_to_payload(task),
            "codex_history": _codex_history_payload(ctx.participant_identity, ctx.room),
            **_active_project_payload(ctx.participant_identity, ctx.room),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _skills_list_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    feature_error = _require_feature("skills_v1")
    if feature_error is not None:
        return feature_error
    query = str(params.get("query", "")).strip() or None
    refresh = bool(params.get("refresh", False))
    items = list_skills(query=query, refresh=refresh)
    payload = [item.to_payload() for item in items]
    return ActionResult(
        success=True,
        message=f"Encontrei {len(payload)} skill(s) disponiveis.",
        data={
            "skills": payload,
            "skills_total": len(payload),
            "query": query,
            **_active_project_payload(ctx.participant_identity, ctx.room),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _skills_read_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    feature_error = _require_feature("skills_v1")
    if feature_error is not None:
        return feature_error
    skill_id = str(params.get("skill_id", "")).strip() or None
    skill_name = str(params.get("skill_name", "")).strip() or None
    doc = get_skill(skill_id=skill_id, skill_name=skill_name)
    if doc is None:
        return ActionResult(
            success=False,
            message="Skill nao encontrada. Use skills_list para conferir os ids.",
            error="skill not found",
        )
    return ActionResult(
        success=True,
        message=f"Skill carregada: {doc.metadata.name}.",
        data={
            "skill_document": doc.to_payload(),
            **_active_project_payload(ctx.participant_identity, ctx.room),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _orchestrate_task_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    feature_error = _require_feature("multi_model_router_v1")
    if feature_error is not None:
        return feature_error
    request_text = (
        str(params.get("request", "")).strip()
        or str(params.get("query", "")).strip()
        or str(params.get("prompt", "")).strip()
    )
    if not request_text:
        return ActionResult(success=False, message="Descreva a tarefa para orquestrar.", error="missing request")

    plan = build_task_plan(request_text)
    task_type: TaskType = plan.task_type
    risk = classify_action_risk(str(params.get("action_hint", "")).strip() or "orchestrate_task")
    response_text, route_decision = route_orchestration(request=request_text, task_type=task_type, risk=risk)
    orchestration_payload = {
        "request": request_text,
        "task_plan": plan.to_payload(),
        "model_route": route_decision.to_payload(),
        "response_preview": response_text,
    }
    return ActionResult(
        success=True,
        message=f"Tarefa orquestrada com provider {route_decision.used_provider}.",
        data={
            "orchestration": orchestration_payload,
            "model_route": route_decision.to_payload(),
            **_active_project_payload(ctx.participant_identity, ctx.room),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
        evidence={
            "provider": route_decision.used_provider,
            "request_id": route_decision.generated_at,
            "executed_at": _now_iso(),
        },
        fallback_used=route_decision.fallback_used,
    )


async def _subagent_spawn_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    feature_error = _require_feature("subagents_v1")
    if feature_error is not None:
        return feature_error
    request_text = str(params.get("request", "")).strip()
    if not request_text:
        return ActionResult(success=False, message="Descreva a tarefa do subagente.", error="missing request")
    plan = build_task_plan(request_text)
    risk = classify_action_risk(str(params.get("action_hint", "")).strip() or "subagent_spawn")
    primary_provider, fallback_provider = preview_route(plan.task_type, risk)
    state = spawn_subagent(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        request=request_text,
        task_type=plan.task_type,
        risk=risk,
        route_provider=primary_provider,
        initial_summary="Subagente iniciado.",
    )
    wait_for_completion_raw = params.get("wait_for_completion")
    if isinstance(wait_for_completion_raw, bool):
        wait_for_completion = wait_for_completion_raw
    else:
        wait_for_completion = bool(params.get("auto_complete", False))

    route_payload: JsonObject = {
        "task_type": plan.task_type,
        "risk": risk,
        "primary_provider": primary_provider,
        "fallback_provider": fallback_provider,
        "used_provider": primary_provider,
        "fallback_used": False,
        "reason": "Subagente enfileirado para execucao assincrona.",
        "generated_at": _now_iso(),
    }
    fallback_used = False

    async def _runner() -> str:
        text, decision = route_orchestration(request=request_text, task_type=plan.task_type, risk=risk)
        state.route_provider = decision.used_provider
        state.updated_at = _now_iso()
        return text[:1200]

    if wait_for_completion:
        response_text, route_decision = route_orchestration(request=request_text, task_type=plan.task_type, risk=risk)
        state.route_provider = route_decision.used_provider
        completed = complete_subagent(
            participant_identity=ctx.participant_identity,
            room=ctx.room,
            subagent_id=state.subagent_id,
            summary=response_text[:1200],
        )
        if completed is not None:
            state = completed
        route_payload = route_decision.to_payload()
        fallback_used = route_decision.fallback_used
    else:
        start_subagent_task(
            participant_identity=ctx.participant_identity,
            room=ctx.room,
            state=state,
            runner=_runner,
        )

    return ActionResult(
        success=True,
        message=f"Subagente {state.subagent_id} em estado {state.status}.",
        data={
            "subagent_state": state.to_payload(),
            "subagent_states": [item.to_payload() for item in list_subagents(participant_identity=ctx.participant_identity, room=ctx.room)],
            "model_route": route_payload,
            **_active_project_payload(ctx.participant_identity, ctx.room),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
        evidence={
            "provider": state.route_provider or primary_provider,
            "request_id": state.subagent_id,
            "executed_at": _now_iso(),
        },
        fallback_used=fallback_used,
    )


async def _subagent_status_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    feature_error = _require_feature("subagents_v1")
    if feature_error is not None:
        return feature_error
    subagent_id = str(params.get("subagent_id", "")).strip()
    if subagent_id:
        target = None
        for item in list_subagents(participant_identity=ctx.participant_identity, room=ctx.room):
            if item.subagent_id == subagent_id:
                target = item
                break
        if target is None:
            return ActionResult(success=False, message="Subagente nao encontrado.", error="subagent not found")
        return ActionResult(
            success=True,
            message=f"Subagente {target.subagent_id} em estado {target.status}.",
            data={"subagent_state": target.to_payload()},
        )

    states = [item.to_payload() for item in list_subagents(participant_identity=ctx.participant_identity, room=ctx.room)]
    return ActionResult(
        success=True,
        message=f"{len(states)} subagente(s) neste contexto.",
        data={"subagent_states": states},
    )


async def _subagent_cancel_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    feature_error = _require_feature("subagents_v1")
    if feature_error is not None:
        return feature_error
    subagent_id = str(params.get("subagent_id", "")).strip()
    if not subagent_id:
        return ActionResult(success=False, message="Informe o subagent_id para cancelar.", error="missing subagent id")
    cancelled = cancel_subagent(participant_identity=ctx.participant_identity, room=ctx.room, subagent_id=subagent_id)
    if cancelled is None:
        return ActionResult(success=False, message="Subagente nao encontrado.", error="subagent not found")
    return ActionResult(
        success=True,
        message=f"Subagente {cancelled.subagent_id} cancelado.",
        data={
            "subagent_state": cancelled.to_payload(),
            "subagent_states": [item.to_payload() for item in list_subagents(participant_identity=ctx.participant_identity, room=ctx.room)],
        },
    )


async def _policy_explain_decision_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    feature_error = _require_feature("policy_v1")
    if feature_error is not None:
        return feature_error
    action_name = str(params.get("action_name", "")).strip()
    if not action_name:
        return ActionResult(success=False, message="Informe o nome da action para analisar politica.", error="missing action name")
    spec = get_action(action_name)
    risk = classify_action_risk(action_name)
    domain = infer_action_domain(action_name)
    domain_trust = get_domain_trust(domain)
    trust_drift = get_trust_drift(ctx.participant_identity, ctx.room, domain)
    mode = get_autonomy_mode(ctx.participant_identity, ctx.room)
    domain_details = get_domain_autonomy_details(ctx.participant_identity, ctx.room, domain) or {}
    domain_mode = get_domain_autonomy_mode(ctx.participant_identity, ctx.room, domain)
    effective_mode = get_effective_autonomy_mode(ctx.participant_identity, ctx.room, domain=domain)
    blocked, reason = is_blocked(domain=_action_domain(action_name))
    policy_eval = evaluate_policy(
        risk=risk,
        mode=effective_mode,
        requires_confirmation=bool(spec.requires_confirmation) if spec is not None else False,
        kill_switch_active=blocked,
        kill_switch_reason=reason,
        domain=domain,
        domain_trust_score=domain_trust.score,
        trust_drift_active=bool(trust_drift and trust_drift.active),
        trust_drift_reason=trust_drift.reason if trust_drift is not None else None,
    )
    payload = {
        "action_name": action_name,
        "domain": domain,
        "domain_trust": domain_trust.to_payload(),
        "trust_drift": trust_drift.to_payload() if trust_drift is not None else None,
        "risk": risk,
        "autonomy_mode": mode,
        "effective_autonomy_mode": effective_mode,
        "domain_autonomy_mode": domain_mode,
        "domain_autonomy_reason": str(domain_details.get("reason") or "") or None,
        "domain_autonomy_source": str(domain_details.get("source") or "") or None,
        "domain_autonomy_updated_at": str(domain_details.get("updated_at") or "") or None,
        "decision": policy_eval.decision,
        "reason": policy_eval.reason,
        "kill_switch": get_killswitch_status().to_payload(),
    }
    return ActionResult(success=True, message=f"Politica para {action_name}: {policy_eval.decision}.", data={"policy": payload})


async def _autonomy_set_mode_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    feature_error = _require_feature("policy_v1")
    if feature_error is not None:
        return feature_error
    mode = str(params.get("mode", "")).strip().lower()
    if not mode:
        return ActionResult(success=False, message="Informe o modo de autonomia.", error="missing mode")
    if mode not in ALLOWED_AUTONOMY_MODES:
        return ActionResult(
            success=False,
            message=f"Modo invalido. Use: {', '.join(sorted(ALLOWED_AUTONOMY_MODES))}.",
            error="invalid mode",
        )
    applied = set_autonomy_mode(ctx.participant_identity, ctx.room, mode)
    return ActionResult(
        success=True,
        message=f"Modo de autonomia ajustado para {applied}.",
        data={
            "autonomy_mode": applied,
            "kill_switch": get_killswitch_status().to_payload(),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _autonomy_killswitch_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    feature_error = _require_feature("policy_v1")
    if feature_error is not None:
        return feature_error
    operation = str(params.get("operation", "status")).strip().lower()
    domain = str(params.get("domain", "")).strip().lower()
    reason = str(params.get("reason", "")).strip() or None
    if operation == "enable":
        state = set_killswitch_global(True, reason=reason)
    elif operation == "disable":
        state = set_killswitch_global(False, reason=None)
    elif operation == "enable_domain":
        if not domain:
            return ActionResult(success=False, message="Informe `domain` para enable_domain.", error="missing domain")
        state = set_killswitch_domain(domain, True, reason=reason)
    elif operation == "disable_domain":
        if not domain:
            return ActionResult(success=False, message="Informe `domain` para disable_domain.", error="missing domain")
        state = set_killswitch_domain(domain, False)
    else:
        state = get_killswitch_status()

    return ActionResult(
        success=True,
        message="Kill switch atualizado.",
        data={
            "kill_switch": state.to_payload(),
            "autonomy_mode": get_autonomy_mode(ctx.participant_identity, ctx.room),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _policy_action_risk_matrix_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    query = str(params.get("query", "")).strip().lower()
    include_internal = bool(params.get("include_internal", False))
    rows: list[JsonObject] = []
    for spec in ACTION_REGISTRY.values():
        if not include_internal and not spec.expose_to_model:
            continue
        risk = classify_action_risk(spec.name)
        domain = infer_action_domain(spec.name)
        domain_trust = get_domain_trust(domain)
        row: JsonObject = {
            "action_name": spec.name,
            "risk": risk,
            "requires_confirmation": spec.requires_confirmation,
            "requires_auth": spec.requires_auth,
            "expose_to_model": spec.expose_to_model,
            "domain": domain,
            "domain_trust_score": round(domain_trust.score, 4),
        }
        if query:
            haystack = f"{spec.name} {risk} {domain}".lower()
            if query not in haystack:
                continue
        rows.append(row)
    rows.sort(key=lambda item: (str(item.get("risk", "")), str(item.get("action_name", ""))))
    return ActionResult(
        success=True,
        message=f"Matriz de risco com {len(rows)} action(s).",
        data={
            "risk_matrix": rows,
            "query": query or None,
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _policy_domain_trust_status_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    domain = str(params.get("domain", "")).strip().lower()
    if domain:
        snapshots = [get_domain_trust(domain)]
    else:
        snapshots = list_domain_trust()
    drift_rows = {item.domain: item for item in list_trust_drift(ctx.participant_identity, ctx.room)}
    domain_mode_rows = {
        str(item.get("domain") or ""): item
        for item in list_domain_autonomy_modes(ctx.participant_identity, ctx.room)
        if isinstance(item, dict)
    }
    rows: list[JsonObject] = []
    for snapshot in snapshots:
        row = snapshot.to_payload()
        drift = drift_rows.get(snapshot.domain)
        domain_details = domain_mode_rows.get(snapshot.domain, {})
        row["trust_drift_active"] = bool(drift and drift.active)
        row["trust_drift"] = drift.to_payload() if drift is not None else None
        row["autonomy_mode"] = get_autonomy_mode(ctx.participant_identity, ctx.room)
        row["domain_autonomy_mode"] = str(domain_details.get("mode") or "") or None
        row["effective_autonomy_mode"] = get_effective_autonomy_mode(
            ctx.participant_identity,
            ctx.room,
            domain=snapshot.domain,
        )
        row["domain_autonomy_reason"] = str(domain_details.get("reason") or "") or None
        row["domain_autonomy_source"] = str(domain_details.get("source") or "") or None
        row["domain_autonomy_updated_at"] = str(domain_details.get("updated_at") or "") or None
        rows.append(row)
    return ActionResult(
        success=True,
        message=f"Trust score em {len(rows)} dominio(s).",
        data={
            "domain_trust": rows,
            "domain": domain or None,
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _policy_trust_drift_report_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    rows_param = params.get("rows")
    if rows_param is None:
        rows: list[JsonObject] = []
    elif isinstance(rows_param, list):
        rows = [item for item in rows_param if isinstance(item, dict)]
    else:
        return ActionResult(
            success=False,
            message="`rows` precisa ser uma lista de objetos.",
            error="invalid rows",
        )
    signature = str(params.get("signature", "")).strip() or None
    updated = replace_trust_drift(
        ctx.participant_identity,
        ctx.room,
        rows,
        source="frontend",
        signature=signature,
    )
    return ActionResult(
        success=True,
        message=f"Trust drift sincronizado para {len(updated)} dominio(s).",
        data={
            "trust_drift": [item.to_payload() for item in updated],
            "signature": signature,
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _evals_list_scenarios_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    scenarios = [scenario.to_payload() for scenario in baseline_scenarios()]
    return ActionResult(
        success=True,
        message=f"Suite baseline com {len(scenarios)} cenario(s).",
        data={
            "eval_scenarios": scenarios,
            "eval_scenarios_total": len(scenarios),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _evals_run_baseline_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    feature_error = _require_feature("multi_model_router_v1")
    if feature_error is not None:
        return feature_error
    task_type_raw = str(params.get("task_type", "unknown")).strip().lower()
    forced_task_type: TaskType | None
    if task_type_raw in {"chat", "code", "review", "research", "automation", "unknown"}:
        forced_task_type = task_type_raw  # type: ignore[assignment]
    else:
        forced_task_type = None

    executions: list[JsonObject] = []
    success_count = 0
    for scenario in baseline_scenarios():
        task_plan = build_task_plan(scenario.prompt)
        task_type = forced_task_type or task_plan.task_type
        risk = "R1"
        response_text, route_decision = route_orchestration(request=scenario.prompt, task_type=task_type, risk=risk)
        passed = all(token in " ".join([response_text, json.dumps(route_decision.to_payload(), ensure_ascii=False)]) for token in scenario.expected)
        if passed:
            success_count += 1
        executions.append(
            {
                "scenario_id": scenario.scenario_id,
                "name": scenario.name,
                "task_type": task_type,
                "passed": passed,
                "route": route_decision.to_payload(),
                "response_preview": response_text[:280],
            }
        )

    total = len(executions)
    score = float(success_count) / float(total) if total else 0.0
    summary = {
        "total": total,
        "passed": success_count,
        "failed": max(total - success_count, 0),
        "score": round(score, 4),
        "ran_at": _now_iso(),
    }
    append_metric(
        {
            "type": "eval_baseline_run",
            "summary": summary,
            "executions": executions,
            "participant_identity": ctx.participant_identity,
            "room": ctx.room,
        }
    )
    return ActionResult(
        success=True,
        message=f"Baseline executado: {success_count}/{total} cenarios passaram.",
        data={
            "eval_baseline_summary": summary,
            "eval_baseline_results": executions,
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _evals_get_metrics_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    limit = int(params.get("limit", 30))
    limit = max(1, min(limit, 200))
    payload = read_metrics()
    items = list(payload.get("items", []))[:limit]
    return ActionResult(
        success=True,
        message=f"Retornei {len(items)} metrica(s).",
        data={
            "eval_metrics": items,
            "eval_metrics_updated_at": payload.get("updated_at"),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _evals_metrics_summary_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    limit = int(params.get("limit", 300))
    limit = max(10, min(limit, 1000))
    payload = read_metrics()
    items = list(payload.get("items", []))[:limit]
    summary = summarize_action_metrics([item for item in items if isinstance(item, dict)])
    return ActionResult(
        success=True,
        message="Resumo de metricas calculado.",
        data={
            "eval_metrics_summary": summary,
            "eval_metrics_updated_at": payload.get("updated_at"),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _evals_slo_report_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    limit = int(params.get("limit", 400))
    limit = max(20, min(limit, 1200))
    payload = read_metrics()
    items = list(payload.get("items", []))[:limit]
    report = summarize_slo([item for item in items if isinstance(item, dict)])
    return ActionResult(
        success=True,
        message="Relatorio de SLO calculado.",
        data={
            "slo_report": report,
            "eval_metrics_updated_at": payload.get("updated_at"),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


def _collect_provider_health(*, include_ping: bool, ping_prompt: str) -> list[JsonObject]:
    providers = build_provider_registry()
    rows: list[JsonObject] = []
    for provider_name, client in providers.items():
        supports_tools = bool(getattr(client, "supports_tools", lambda: False)())
        supports_realtime = bool(getattr(client, "supports_realtime", lambda: False)())
        configured = provider_name == "local_mock"
        if provider_name == "openai":
            configured = bool(str(os.getenv("OPENAI_API_KEY", "")).strip())
        elif provider_name == "anthropic":
            configured = bool(str(os.getenv("ANTHROPIC_API_KEY", "")).strip())
        elif provider_name == "google":
            configured = bool(str(os.getenv("GOOGLE_API_KEY", "")).strip() or str(os.getenv("GEMINI_API_KEY", "")).strip())
        health: JsonObject = {
            "provider": provider_name,
            "configured": configured,
            "supports_tools": supports_tools,
            "supports_realtime": supports_realtime,
            "status": "ok" if configured else "missing_config",
        }
        if include_ping:
            try:
                response_text, error = client.generate_text(ping_prompt)  # type: ignore[attr-defined]
                if response_text:
                    health["ping_ok"] = True
                    health["status"] = "ok"
                    health["ping_preview"] = response_text[:120]
                else:
                    health["ping_ok"] = False
                    health["status"] = "degraded"
                    health["error"] = error or "empty response"
            except Exception as error:  # noqa: BLE001
                health["ping_ok"] = False
                health["status"] = "degraded"
                health["error"] = str(error)
        rows.append(health)

    rows.sort(key=lambda item: str(item.get("provider", "")))
    return rows


def _summarize_canary_cohorts(metrics_items: list[dict[str, Any]]) -> JsonObject:
    cohorts: dict[str, dict[str, int]] = {
        "canary": {"total": 0, "success": 0, "failed": 0},
        "stable": {"total": 0, "success": 0, "failed": 0},
    }
    for item in metrics_items:
        if item.get("type") != "action_result":
            continue
        payload = item.get("payload")
        if not isinstance(payload, dict):
            continue
        cohort = str(payload.get("canary_cohort") or "stable").strip().lower()
        if cohort not in cohorts:
            cohort = "stable"
        success = bool(payload.get("success"))
        entry = cohorts[cohort]
        entry["total"] += 1
        if success:
            entry["success"] += 1
        else:
            entry["failed"] += 1

    def _with_rate(entry: dict[str, int]) -> JsonObject:
        total = int(entry.get("total", 0))
        success = int(entry.get("success", 0))
        rate = (float(success) / float(total)) if total else 0.0
        return {
            "total": total,
            "success": success,
            "failed": int(entry.get("failed", 0)),
            "success_rate": round(rate, 4),
        }

    return {
        "canary": _with_rate(cohorts["canary"]),
        "stable": _with_rate(cohorts["stable"]),
    }


def _build_domain_autonomy_audit_rows(
    *,
    participant_identity: str,
    room: str,
    metrics_summary: JsonObject | None = None,
    domain_mode_rows_override: list[JsonObject] | None = None,
    autonomy_mode_override: str | None = None,
) -> list[JsonObject]:
    metrics_summary = metrics_summary if isinstance(metrics_summary, dict) else {}
    autonomy_notice = (
        metrics_summary.get("autonomy_notice")
        if isinstance(metrics_summary.get("autonomy_notice"), dict)
        else {}
    )
    unconfirmed_by_domain = (
        autonomy_notice.get("unconfirmed_by_domain")
        if isinstance(autonomy_notice.get("unconfirmed_by_domain"), dict)
        else {}
    )
    trust_drift_by_domain = {
        item.domain: item
        for item in list_trust_drift(participant_identity, room)
        if getattr(item, "domain", None)
    }
    domain_mode_rows = {
        str(item.get("domain") or ""): item
        for item in (
            domain_mode_rows_override
            if isinstance(domain_mode_rows_override, list)
            else list_domain_autonomy_modes(participant_identity, room)
        )
        if isinstance(item, dict) and str(item.get("domain") or "")
    }
    known_domains = set(domain_mode_rows.keys()) | set(trust_drift_by_domain.keys()) | set(
        str(key).strip().lower()
        for key, value in dict(unconfirmed_by_domain).items()
        if str(key).strip() and int(value or 0) > 0
    )
    known_domains.update(snapshot.domain for snapshot in list_domain_trust())
    base_mode = autonomy_mode_override or get_autonomy_mode(participant_identity, room)
    rows: list[JsonObject] = []
    for domain in sorted(known_domains):
        details = domain_mode_rows.get(domain, {})
        trust_drift = trust_drift_by_domain.get(domain)
        unconfirmed_total = int(dict(unconfirmed_by_domain).get(domain) or 0)
        domain_mode = str(details.get("mode") or "").strip().lower() or None
        if isinstance(domain_mode_rows_override, list) or autonomy_mode_override is not None:
            if base_mode == "manual" or domain_mode == "manual":
                effective_mode = "manual"
            elif domain_mode == "safe":
                effective_mode = "safe"
            else:
                effective_mode = base_mode
        else:
            effective_mode = get_effective_autonomy_mode(participant_identity, room, domain=domain)
        reasons: list[str] = []
        detail_reason = str(details.get("reason") or "").strip()
        if detail_reason:
            reasons.append(detail_reason)
        if bool(trust_drift and trust_drift.active):
            reasons.append("trust_drift_active")
        if unconfirmed_total > 0:
            reasons.append("autonomy_notice_delivery_unconfirmed")
        if not reasons and effective_mode != base_mode:
            reasons.append("global_autonomy_mode")
        rows.append(
            {
                "domain": domain,
                "autonomy_mode": base_mode,
                "domain_autonomy_mode": domain_mode,
                "effective_autonomy_mode": effective_mode,
                "domain_autonomy_active": bool(domain_mode),
                "containment_reason": reasons[0] if reasons else None,
                "containment_reasons": reasons,
                "containment_source": (
                    str(details.get("source") or "").strip()
                    or ("ops_auto_remediation" if unconfirmed_total > 0 else None)
                    or ("policy" if bool(trust_drift and trust_drift.active) else None)
                ),
                "domain_autonomy_updated_at": str(details.get("updated_at") or "").strip() or None,
                "trust_drift_active": bool(trust_drift and trust_drift.active),
                "autonomy_notice_unconfirmed": unconfirmed_total,
            }
        )
    return rows


def _build_ops_incident_snapshot(
    *,
    participant_identity: str,
    room: str,
    include_ping: bool,
    ping_prompt: str,
    metrics_limit: int,
) -> JsonObject:
    metrics_limit = max(20, min(metrics_limit, 1200))
    payload = read_metrics()
    items = list(payload.get("items", []))[:metrics_limit]
    metrics_items = [item for item in items if isinstance(item, dict)]
    metrics_summary = summarize_action_metrics(metrics_items)
    slo_report = summarize_slo(metrics_items)
    providers_health = _collect_provider_health(include_ping=include_ping, ping_prompt=ping_prompt)
    feature_flags = _feature_flags_snapshot()
    kill_switch = get_killswitch_status().to_payload()
    autonomy_mode = get_autonomy_mode(participant_identity, room)
    domain_autonomy_modes = list_domain_autonomy_modes(participant_identity, room)
    canary_state = _canary_state_payload(participant_identity, room)
    canary_metrics = _summarize_canary_cohorts(metrics_items)
    trust_drift_rows = [item.to_payload() for item in list_trust_drift(participant_identity, room)]
    domain_autonomy_status = _build_domain_autonomy_audit_rows(
        participant_identity=participant_identity,
        room=room,
        metrics_summary=metrics_summary,
    )

    alerts: list[str] = []
    reliability = slo_report.get("reliability")
    latency = slo_report.get("latency")
    if isinstance(reliability, dict):
        low_risk_success = float(reliability.get("low_risk_success_rate") or 0.0)
        false_success_rate = float(reliability.get("false_success_proxy_rate") or 0.0)
        autonomy_notice_browser_tts_rate = float(
            reliability.get("autonomy_notice_browser_tts_rate") or 0.0
        )
        autonomy_notice_unconfirmed_rate = float(
            reliability.get("autonomy_notice_unconfirmed_rate") or 0.0
        )
        if false_success_rate > 0.0:
            alerts.append(
                f"false_success_proxy_rate acima de 0 ({round(false_success_rate * 100, 2)}%)."
            )
        if low_risk_success < 0.95:
            alerts.append(
                f"low_risk_success_rate abaixo de 95% ({round(low_risk_success * 100, 2)}%)."
            )
        if autonomy_notice_browser_tts_rate > 0.0:
            alerts.append(
                "autonomy_notice entregue por browser_tts em "
                f"{round(autonomy_notice_browser_tts_rate * 100, 2)}% dos casos."
            )
        if autonomy_notice_unconfirmed_rate > 0.0:
            alerts.append(
                "autonomy_notice sem confirmacao de entrega em "
                f"{round(autonomy_notice_unconfirmed_rate * 100, 2)}% dos casos."
            )
    if isinstance(latency, dict):
        fallback_p95 = int(latency.get("fallback_p95_ms") or 0)
        if fallback_p95 > 3000:
            alerts.append(f"fallback_p95_ms acima da meta ({fallback_p95}ms).")
    if trust_drift_rows:
        alerts.append(f"trust_drift ativo em {len(trust_drift_rows)} dominio(s).")
    for row in providers_health:
        if str(row.get("status") or "") != "ok":
            alerts.append(
                f"provider {str(row.get('provider') or 'unknown')} com status {str(row.get('status') or 'unknown')}."
            )
    canary_row = canary_metrics.get("canary")
    if isinstance(canary_row, dict):
        canary_total = int(canary_row.get("total") or 0)
        canary_success_rate = float(canary_row.get("success_rate") or 0.0)
        if canary_total >= 10 and canary_success_rate < 0.9:
            alerts.append(
                f"canary success_rate abaixo de 90% ({round(canary_success_rate * 100, 2)}%)."
            )

    return {
        "generated_at": _now_iso(),
        "autonomy_mode": autonomy_mode,
        "domain_autonomy_modes": domain_autonomy_modes,
        "domain_autonomy_status": domain_autonomy_status,
        "feature_flags": feature_flags,
        "canary_state": canary_state,
        "canary_metrics": canary_metrics,
        "kill_switch": kill_switch,
        "providers_health": providers_health,
        "trust_drift": {
            "active_total": len(trust_drift_rows),
            "domains": trust_drift_rows,
        },
        "autonomy_notice": metrics_summary.get("autonomy_notice"),
        "metrics_summary": metrics_summary,
        "slo_report": slo_report,
        "alerts": alerts,
    }


async def _providers_health_check_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    include_ping = bool(params.get("include_ping", False))
    ping_prompt = str(params.get("ping_prompt", "")).strip() or "Responda apenas: ok"
    rows = _collect_provider_health(include_ping=include_ping, ping_prompt=ping_prompt)
    return ActionResult(
        success=True,
        message=f"Health check de {len(rows)} provider(s) concluido.",
        data={
            "providers_health": rows,
            "feature_flags": _feature_flags_snapshot(),
            "canary_state": _canary_state_payload(ctx.participant_identity, ctx.room),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _ops_incident_snapshot_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    include_ping = bool(params.get("include_ping", False))
    ping_prompt = str(params.get("ping_prompt", "")).strip() or "Responda apenas: ok"
    metrics_limit = int(params.get("metrics_limit", 300))
    snapshot = _build_ops_incident_snapshot(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        include_ping=include_ping,
        ping_prompt=ping_prompt,
        metrics_limit=metrics_limit,
    )
    return ActionResult(
        success=True,
        message="Snapshot operacional gerado.",
        data={
            "ops_incident_snapshot": snapshot,
            "canary_state": snapshot.get("canary_state"),
            "autonomy_mode": snapshot.get("autonomy_mode"),
            "feature_flags": snapshot.get("feature_flags"),
            "kill_switch": snapshot.get("kill_switch"),
            "providers_health": snapshot.get("providers_health"),
            "eval_metrics_summary": snapshot.get("metrics_summary"),
            "slo_report": snapshot.get("slo_report"),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _ops_canary_status_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    metrics_limit = int(params.get("metrics_limit", 300))
    snapshot = _build_ops_incident_snapshot(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        include_ping=False,
        ping_prompt="Responda apenas: ok",
        metrics_limit=metrics_limit,
    )
    canary_state = snapshot.get("canary_state") if isinstance(snapshot.get("canary_state"), dict) else {}
    return ActionResult(
        success=True,
        message=(
            f"Canario {'ativo' if bool(canary_state.get('active')) else 'inativo'} "
            f"para a sessao ({str(canary_state.get('cohort') or 'stable')})."
        ),
        data={
            "canary_state": canary_state,
            "ops_incident_snapshot": snapshot,
            "feature_flags": snapshot.get("feature_flags"),
            "eval_metrics_summary": snapshot.get("metrics_summary"),
            "slo_report": snapshot.get("slo_report"),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _ops_canary_set_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    operation = str(params.get("operation", "")).strip().lower()
    allowed = {"enroll", "unenroll", "enable_global", "disable_global"}
    if operation not in allowed:
        return ActionResult(
            success=False,
            message=f"Operacao invalida. Opcoes: {', '.join(sorted(allowed))}.",
            error="invalid operation",
        )

    if operation == "enroll":
        _set_canary_session_enrollment(ctx.participant_identity, ctx.room, enrolled=True)
    elif operation == "unenroll":
        _set_canary_session_enrollment(ctx.participant_identity, ctx.room, enrolled=False)
    elif operation == "enable_global":
        _set_runtime_feature_override("canary_v1", True)
    elif operation == "disable_global":
        _set_runtime_feature_override("canary_v1", False)

    snapshot = _build_ops_incident_snapshot(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        include_ping=False,
        ping_prompt="Responda apenas: ok",
        metrics_limit=300,
    )
    canary_state = snapshot.get("canary_state") if isinstance(snapshot.get("canary_state"), dict) else {}
    return ActionResult(
        success=True,
        message=f"Canario atualizado via `{operation}`.",
        data={
            "canary_state": canary_state,
            "ops_incident_snapshot": snapshot,
            "feature_flags": snapshot.get("feature_flags"),
            "eval_metrics_summary": snapshot.get("metrics_summary"),
            "slo_report": snapshot.get("slo_report"),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


def _rollout_step_percent(current: int, *, direction: str) -> int:
    ladder = [0, 10, 25, 50, 100]
    normalized = max(0, min(100, int(current)))
    if direction == "up":
        for target in ladder:
            if target > normalized:
                return target
        return 100
    for target in reversed(ladder):
        if target < normalized:
            return target
    return 0


async def _ops_canary_rollout_set_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    operation = str(params.get("operation", "")).strip().lower()
    percent_param = params.get("percent")
    dry_run = bool(params.get("dry_run", False))
    allowed = {"set_percent", "step_up", "step_down", "pause", "resume"}
    if operation not in allowed:
        return ActionResult(
            success=False,
            message=f"Operacao invalida. Opcoes: {', '.join(sorted(allowed))}.",
            error="invalid operation",
        )

    current_percent = _get_canary_rollout_percent()
    next_percent = current_percent
    before_enabled = _is_feature_enabled("canary_v1", default=False)
    next_enabled = before_enabled

    if operation == "set_percent":
        if not isinstance(percent_param, int):
            return ActionResult(success=False, message="Informe `percent` (0..100).", error="missing percent")
        next_percent = max(0, min(100, int(percent_param)))
        if next_percent > 0:
            next_enabled = True
    elif operation == "step_up":
        next_percent = _rollout_step_percent(current_percent, direction="up")
        if next_percent > 0:
            next_enabled = True
    elif operation == "step_down":
        next_percent = _rollout_step_percent(current_percent, direction="down")
    elif operation == "pause":
        next_enabled = False
    elif operation == "resume":
        next_enabled = True
        if current_percent <= 0:
            next_percent = 10

    if not dry_run:
        _set_canary_rollout_percent(next_percent)
        _set_runtime_feature_override("canary_v1", next_enabled)

    snapshot = _build_ops_incident_snapshot(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        include_ping=False,
        ping_prompt="Responda apenas: ok",
        metrics_limit=300,
    )
    canary_state = snapshot.get("canary_state") if isinstance(snapshot.get("canary_state"), dict) else {}
    report: JsonObject = {
        "playbook": "canary_rollout",
        "dry_run": dry_run,
        "applied": not dry_run,
        "changes": [
            {
                "type": "canary_rollout",
                "target": "rollout_percent",
                "from": current_percent,
                "to": next_percent,
                "note": f"Operacao {operation}",
            },
            {
                "type": "feature_flag_override",
                "target": "canary_v1",
                "from": before_enabled,
                "to": next_enabled if dry_run else bool(_is_feature_enabled("canary_v1", default=False)),
                "note": "Controle global de canario.",
            },
        ],
        "generated_at": _now_iso(),
    }
    return ActionResult(
        success=True,
        message=f"Rollout canario {'simulado' if dry_run else 'atualizado'} via `{operation}`.",
        data={
            "ops_playbook_report": report,
            "canary_state": canary_state,
            "ops_incident_snapshot": snapshot,
            "feature_flags": snapshot.get("feature_flags"),
            "eval_metrics_summary": snapshot.get("metrics_summary"),
            "slo_report": snapshot.get("slo_report"),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


def _ops_slo_signal(snapshot: JsonObject) -> JsonObject:
    providers = snapshot.get("providers_health")
    slo_report = snapshot.get("slo_report")
    canary_metrics = snapshot.get("canary_metrics")
    trust_drift = snapshot.get("trust_drift")
    metrics_summary = snapshot.get("metrics_summary")
    provider_outage = False
    if isinstance(providers, list):
        for row in providers:
            if isinstance(row, dict) and str(row.get("status") or "ok") in {"degraded", "missing_config"}:
                provider_outage = True
                break

    reliability_breach = False
    latency_spike = False
    canary_degraded = False
    trust_drift_breach = False
    autonomy_notice_delivery_breach = False
    autonomy_notice_unconfirmed_rate = 0.0
    autonomy_notice_delivery_domains: list[str] = []
    trust_drift_active_domains: list[str] = []
    reasons: list[str] = []
    if isinstance(slo_report, dict):
        reliability = slo_report.get("reliability")
        latency = slo_report.get("latency")
        if isinstance(reliability, dict):
            false_success = float(reliability.get("false_success_proxy_rate") or 0.0)
            low_risk = float(reliability.get("low_risk_success_rate") or 0.0)
            autonomy_notice_unconfirmed_rate = float(
                reliability.get("autonomy_notice_unconfirmed_rate") or 0.0
            )
            if false_success > 0.0:
                reliability_breach = True
                reasons.append(f"false_success_proxy_rate={round(false_success, 4)}")
            if low_risk < 0.95:
                reliability_breach = True
                reasons.append(f"low_risk_success_rate={round(low_risk, 4)}")
            if autonomy_notice_unconfirmed_rate > 0.0:
                autonomy_notice_delivery_breach = True
                reliability_breach = True
                reasons.append(
                    "autonomy_notice_unconfirmed_rate="
                    f"{round(autonomy_notice_unconfirmed_rate, 4)}"
                )
        if isinstance(latency, dict):
            fallback_p95 = int(latency.get("fallback_p95_ms") or 0)
            if fallback_p95 > 3000:
                latency_spike = True
                reasons.append(f"fallback_p95_ms={fallback_p95}")
    if isinstance(trust_drift, dict):
        active_total = int(trust_drift.get("active_total") or 0)
        domains = trust_drift.get("domains")
        if isinstance(domains, list):
            trust_drift_active_domains = [
                str(row.get("domain") or "").strip()
                for row in domains
                if isinstance(row, dict) and str(row.get("domain") or "").strip()
            ]
        trust_drift_rate = 0.0
        if isinstance(slo_report, dict):
            reliability = slo_report.get("reliability")
            if isinstance(reliability, dict):
                trust_drift_rate = float(reliability.get("trust_drift_active_rate") or 0.0)
        if active_total > 0:
            trust_drift_breach = True
            reasons.append(f"trust_drift_active_total={active_total}")
            if trust_drift_rate > 0.0:
                reasons.append(f"trust_drift_active_rate={round(trust_drift_rate, 4)}")
    if isinstance(metrics_summary, dict):
        autonomy_notice = metrics_summary.get("autonomy_notice")
        if isinstance(autonomy_notice, dict):
            unconfirmed_by_domain = autonomy_notice.get("unconfirmed_by_domain")
            if isinstance(unconfirmed_by_domain, dict):
                autonomy_notice_delivery_domains = sorted(
                    [
                        str(domain).strip().lower()
                        for domain, total in unconfirmed_by_domain.items()
                        if str(domain).strip() and int(total or 0) > 0
                    ]
                )
    if isinstance(canary_metrics, dict):
        row = canary_metrics.get("canary")
        if isinstance(row, dict):
            total = int(row.get("total") or 0)
            success_rate = float(row.get("success_rate") or 0.0)
            if total >= 10 and success_rate < 0.9:
                canary_degraded = True
                reasons.append(f"canary_success_rate={round(success_rate, 4)}")

    scenario: str | None = None
    if provider_outage:
        scenario = "provider_outage"
    elif trust_drift_breach:
        scenario = "trust_drift_breach"
    elif reliability_breach or canary_degraded:
        scenario = "reliability_breach"
    elif latency_spike:
        scenario = "latency_spike"

    return {
        "provider_outage": provider_outage,
        "reliability_breach": reliability_breach,
        "latency_spike": latency_spike,
        "canary_degraded": canary_degraded,
        "trust_drift_breach": trust_drift_breach,
        "autonomy_notice_delivery_breach": autonomy_notice_delivery_breach,
        "autonomy_notice_unconfirmed_rate": round(autonomy_notice_unconfirmed_rate, 4),
        "autonomy_notice_delivery_domains": autonomy_notice_delivery_domains,
        "trust_drift_active_domains": trust_drift_active_domains,
        "recommended_scenario": scenario,
        "reasons": reasons,
    }


async def _ops_auto_remediate_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    dry_run = bool(params.get("dry_run", True))
    force = bool(params.get("force", False))
    domain = str(params.get("domain", "")).strip().lower()
    metrics_limit = int(params.get("metrics_limit", 400))
    cooldown_seconds = int(
        params.get("cooldown_seconds", int(str(os.getenv("JARVEZ_AUTO_REMEDIATION_COOLDOWN_SECONDS", "180"))))
    )
    cooldown_seconds = max(30, min(cooldown_seconds, 3600))

    snapshot = _build_ops_incident_snapshot(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        include_ping=False,
        ping_prompt="Responda apenas: ok",
        metrics_limit=metrics_limit,
    )
    signal = _ops_slo_signal(snapshot)
    scenario = str(signal.get("recommended_scenario") or "").strip()
    signal_domains = signal.get("trust_drift_active_domains") if isinstance(signal.get("trust_drift_active_domains"), list) else []
    notice_delivery_domains = (
        signal.get("autonomy_notice_delivery_domains")
        if isinstance(signal.get("autonomy_notice_delivery_domains"), list)
        else []
    )
    resolved_domain = domain
    if (
        not resolved_domain
        and scenario == "trust_drift_breach"
        and len(signal_domains) == 1
        and isinstance(signal_domains[0], str)
        and signal_domains[0].strip()
    ):
        resolved_domain = str(signal_domains[0]).strip().lower()
    if (
        not resolved_domain
        and scenario == "reliability_breach"
        and bool(signal.get("autonomy_notice_delivery_breach"))
        and len(notice_delivery_domains) == 1
        and isinstance(notice_delivery_domains[0], str)
        and notice_delivery_domains[0].strip()
    ):
        resolved_domain = str(notice_delivery_domains[0]).strip().lower()
    now_ts = time.time()
    room_key = _canary_key(ctx.participant_identity, ctx.room)
    last_run = float(AUTO_REMEDIATION_LAST_EXECUTION.get(room_key, 0.0))
    remaining_cooldown = max(0, int(cooldown_seconds - (now_ts - last_run)))

    if not scenario and not force:
        return ActionResult(
            success=True,
            message="Sem violacao de SLO para auto-remediacao.",
            data={
                "ops_auto_remediation": {
                    "executed": False,
                    "dry_run": dry_run,
                    "reason": "no signal",
                    "signal": signal,
                    "cooldown_remaining_seconds": remaining_cooldown,
                    "generated_at": _now_iso(),
                },
                "ops_incident_snapshot": snapshot,
                "canary_state": snapshot.get("canary_state"),
                "feature_flags": snapshot.get("feature_flags"),
                "kill_switch": snapshot.get("kill_switch"),
                "eval_metrics_summary": snapshot.get("metrics_summary"),
                "slo_report": snapshot.get("slo_report"),
                **_capability_payload(ctx.participant_identity, ctx.room),
            },
        )

    if force and not scenario:
        scenario = "reliability_breach"

    if not dry_run and remaining_cooldown > 0:
        return ActionResult(
            success=False,
            message=f"Cooldown ativo para auto-remediacao ({remaining_cooldown}s).",
            data={
                "ops_auto_remediation": {
                    "executed": False,
                    "dry_run": dry_run,
                    "reason": "cooldown",
                    "signal": signal,
                    "cooldown_remaining_seconds": remaining_cooldown,
                    "generated_at": _now_iso(),
                },
                "ops_incident_snapshot": snapshot,
                "canary_state": snapshot.get("canary_state"),
                "feature_flags": snapshot.get("feature_flags"),
                "kill_switch": snapshot.get("kill_switch"),
                **_capability_payload(ctx.participant_identity, ctx.room),
            },
            error="auto remediation cooldown",
        )

    rollback = await _ops_rollback_scenario_action(
        {
            "scenario": scenario,
            "dry_run": dry_run,
            "domain": resolved_domain,
            "containment_strategy": (
                "domain_autonomy"
                if scenario == "reliability_breach"
                and bool(signal.get("autonomy_notice_delivery_breach"))
                and bool(resolved_domain)
                else "default"
            ),
            "reason": "auto remediation",
        },
        ctx,
    )
    if not rollback.success:
        return rollback

    if not dry_run:
        AUTO_REMEDIATION_LAST_EXECUTION[room_key] = now_ts

    rollback_data = rollback.data if isinstance(rollback.data, dict) else {}
    return ActionResult(
        success=True,
        message=f"Auto-remediacao {'simulada' if dry_run else 'aplicada'} via `{scenario}`.",
        data={
            **rollback_data,
            "ops_auto_remediation": {
                "executed": True,
                "dry_run": dry_run,
                "scenario": scenario,
                "signal": signal,
                "cooldown_remaining_seconds": 0 if not dry_run else remaining_cooldown,
                "generated_at": _now_iso(),
            },
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


def _ops_canary_gate_report(
    *,
    snapshot: JsonObject,
    min_samples: int,
    success_rate_min: float,
    max_regression_vs_stable: float,
    require_no_alerts: bool,
) -> JsonObject:
    canary_state = snapshot.get("canary_state") if isinstance(snapshot.get("canary_state"), dict) else {}
    canary_metrics = snapshot.get("canary_metrics") if isinstance(snapshot.get("canary_metrics"), dict) else {}
    alerts = snapshot.get("alerts") if isinstance(snapshot.get("alerts"), list) else []
    signal = _ops_slo_signal(snapshot)

    canary_row = canary_metrics.get("canary") if isinstance(canary_metrics.get("canary"), dict) else {}
    stable_row = canary_metrics.get("stable") if isinstance(canary_metrics.get("stable"), dict) else {}
    canary_total = int(canary_row.get("total") or 0)
    canary_success_rate = float(canary_row.get("success_rate") or 0.0)
    stable_total = int(stable_row.get("total") or 0)
    stable_success_rate = float(stable_row.get("success_rate") or 0.0)
    current_rollout = int(canary_state.get("rollout_percent") or 0)

    passed = True
    reasons: list[str] = []
    if current_rollout >= 100:
        passed = False
        reasons.append("rollout ja esta em 100%.")
    if canary_total < int(min_samples):
        passed = False
        reasons.append(f"amostragem canario insuficiente ({canary_total} < {int(min_samples)}).")
    if canary_success_rate < float(success_rate_min):
        passed = False
        reasons.append(
            f"taxa de sucesso canario abaixo do minimo ({round(canary_success_rate, 4)} < {round(float(success_rate_min), 4)})."
        )
    if stable_total >= int(min_samples):
        threshold = stable_success_rate - float(max_regression_vs_stable)
        if canary_success_rate < threshold:
            passed = False
            reasons.append(
                "canario regrediu acima do permitido vs stable "
                f"({round(canary_success_rate, 4)} < {round(threshold, 4)})."
            )
    if require_no_alerts and alerts:
        passed = False
        reasons.append(f"snapshot possui {len(alerts)} alerta(s).")
    if require_no_alerts and signal.get("recommended_scenario"):
        passed = False
        reasons.append(f"sinal operacional pede `{str(signal.get('recommended_scenario'))}`.")

    return {
        "passed": passed,
        "reasons": reasons,
        "signal": signal,
        "current_rollout_percent": current_rollout,
        "next_rollout_percent": _rollout_step_percent(current_rollout, direction="up"),
        "canary": {
            "total": canary_total,
            "success_rate": round(canary_success_rate, 4),
        },
        "stable": {
            "total": stable_total,
            "success_rate": round(stable_success_rate, 4),
        },
    }


async def _ops_canary_promote_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    dry_run = bool(params.get("dry_run", True))
    force = bool(params.get("force", False))
    step_if_passed = bool(params.get("step_if_passed", True))
    rollback_on_fail = bool(params.get("rollback_on_fail", False))
    min_samples = int(params.get("min_samples", 20))
    min_samples = max(5, min(min_samples, 200))
    success_rate_min = float(params.get("success_rate_min", 0.95))
    success_rate_min = max(0.5, min(success_rate_min, 1.0))
    max_regression_vs_stable = float(params.get("max_regression_vs_stable", 0.03))
    max_regression_vs_stable = max(0.0, min(max_regression_vs_stable, 0.4))
    require_no_alerts = bool(params.get("require_no_alerts", True))
    metrics_limit = int(params.get("metrics_limit", 400))
    cooldown_seconds = int(
        params.get("cooldown_seconds", int(str(os.getenv("JARVEZ_CANARY_PROMOTION_COOLDOWN_SECONDS", "600"))))
    )
    cooldown_seconds = max(30, min(cooldown_seconds, 7200))

    snapshot = _build_ops_incident_snapshot(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        include_ping=False,
        ping_prompt="Responda apenas: ok",
        metrics_limit=metrics_limit,
    )
    gate = _ops_canary_gate_report(
        snapshot=snapshot,
        min_samples=min_samples,
        success_rate_min=success_rate_min,
        max_regression_vs_stable=max_regression_vs_stable,
        require_no_alerts=require_no_alerts,
    )

    now_ts = time.time()
    room_key = _canary_key(ctx.participant_identity, ctx.room)
    last_run = float(CANARY_PROMOTION_LAST_EXECUTION.get(room_key, 0.0))
    remaining_cooldown = max(0, int(cooldown_seconds - (now_ts - last_run)))
    if not dry_run and remaining_cooldown > 0 and not force:
        return ActionResult(
            success=False,
            message=f"Cooldown ativo para promocao de canario ({remaining_cooldown}s).",
            data={
                "ops_canary_promotion": {
                    "executed": False,
                    "promoted": False,
                    "dry_run": dry_run,
                    "reason": "cooldown",
                    "gate": gate,
                    "cooldown_remaining_seconds": remaining_cooldown,
                    "generated_at": _now_iso(),
                },
                "ops_incident_snapshot": snapshot,
                "canary_state": snapshot.get("canary_state"),
                "feature_flags": snapshot.get("feature_flags"),
                "slo_report": snapshot.get("slo_report"),
                **_capability_payload(ctx.participant_identity, ctx.room),
            },
            error="canary promotion cooldown",
        )

    gate_passed = bool(gate.get("passed"))
    if force:
        gate_passed = True

    rollback_result: ActionResult | None = None
    promoted = False
    rollout_result: ActionResult | None = None
    if gate_passed and step_if_passed:
        rollout_result = await _ops_canary_rollout_set_action(
            {"operation": "step_up", "dry_run": dry_run},
            ctx,
        )
        promoted = bool(rollout_result.success)
        if rollout_result.success and not dry_run:
            CANARY_PROMOTION_LAST_EXECUTION[room_key] = now_ts
        if rollout_result.success and isinstance(rollout_result.data, dict):
            maybe_snapshot = rollout_result.data.get("ops_incident_snapshot")
            if isinstance(maybe_snapshot, dict):
                snapshot = maybe_snapshot
    elif (not gate_passed) and rollback_on_fail:
        rollback_result = await _ops_rollback_scenario_action(
            {
                "scenario": "reliability_breach",
                "dry_run": dry_run,
                "reason": "canary promotion gate failed",
            },
            ctx,
        )
        if rollback_result.success and isinstance(rollback_result.data, dict):
            maybe_snapshot = rollback_result.data.get("ops_incident_snapshot")
            if isinstance(maybe_snapshot, dict):
                snapshot = maybe_snapshot

    report: JsonObject = {
        "executed": True,
        "promoted": promoted,
        "dry_run": dry_run,
        "force": force,
        "step_if_passed": step_if_passed,
        "rollback_on_fail": rollback_on_fail,
        "gate": gate,
        "cooldown_remaining_seconds": 0 if not dry_run else remaining_cooldown,
        "generated_at": _now_iso(),
    }
    if rollout_result is not None:
        report["rollout_status"] = {"success": rollout_result.success, "message": rollout_result.message}
    if rollback_result is not None:
        report["rollback_status"] = {"success": rollback_result.success, "message": rollback_result.message}

    return ActionResult(
        success=True,
        message=(
            "Promocao de canario aplicada."
            if promoted and not dry_run
            else "Promocao de canario simulada."
            if promoted and dry_run
            else "Gate de promocao nao aprovado."
        ),
        data={
            "ops_canary_promotion": report,
            "ops_playbook_report": (
                rollout_result.data.get("ops_playbook_report") if rollout_result and isinstance(rollout_result.data, dict) else None
            ) or (
                rollback_result.data.get("ops_playbook_report") if rollback_result and isinstance(rollback_result.data, dict) else None
            ),
            "ops_incident_snapshot": snapshot,
            "canary_state": snapshot.get("canary_state"),
            "feature_flags": snapshot.get("feature_flags"),
            "kill_switch": snapshot.get("kill_switch"),
            "slo_report": snapshot.get("slo_report"),
            "eval_metrics_summary": snapshot.get("metrics_summary"),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _ops_control_loop_tick_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    dry_run = bool(params.get("dry_run", True))
    auto_remediate = bool(params.get("auto_remediate", True))
    auto_promote_canary = bool(params.get("auto_promote_canary", True))
    force_remediation = bool(params.get("force_remediation", False))
    force_promotion = bool(params.get("force_promotion", False))
    metrics_limit = int(params.get("metrics_limit", 400))
    domain = str(params.get("domain", "")).strip().lower()
    freeze_threshold = int(
        params.get("freeze_threshold", int(str(os.getenv("JARVEZ_CONTROL_LOOP_FREEZE_THRESHOLD", "3"))))
    )
    freeze_window_seconds = int(
        params.get("freeze_window_seconds", int(str(os.getenv("JARVEZ_CONTROL_LOOP_FREEZE_WINDOW_SECONDS", "900"))))
    )
    freeze_cooldown_seconds = int(
        params.get("freeze_cooldown_seconds", int(str(os.getenv("JARVEZ_CONTROL_LOOP_FREEZE_COOLDOWN_SECONDS", "1800"))))
    )
    freeze_threshold = max(1, min(freeze_threshold, 20))
    freeze_window_seconds = max(60, min(freeze_window_seconds, 86400))
    freeze_cooldown_seconds = max(60, min(freeze_cooldown_seconds, 86400))

    initial_snapshot = _build_ops_incident_snapshot(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        include_ping=False,
        ping_prompt="Responda apenas: ok",
        metrics_limit=metrics_limit,
    )
    remediation_result: ActionResult | None = None
    promotion_result: ActionResult | None = None

    if auto_remediate:
        remediation_result = await _ops_auto_remediate_action(
            {
                "dry_run": dry_run,
                "force": force_remediation,
                "domain": domain,
                "metrics_limit": metrics_limit,
                },
                ctx,
            )

    room_key = _canary_key(ctx.participant_identity, ctx.room)
    now_ts = time.time()
    initial_signal = _ops_slo_signal(initial_snapshot)
    current_breach = str(initial_signal.get("recommended_scenario") or "").strip()
    history = [
        stamp
        for stamp in CONTROL_LOOP_BREACH_HISTORY.get(room_key, [])
        if (now_ts - float(stamp)) <= float(freeze_window_seconds)
    ]
    if current_breach:
        history.append(now_ts)
    CONTROL_LOOP_BREACH_HISTORY[room_key] = history

    last_freeze = float(CONTROL_LOOP_FREEZE_LAST_TRIGGER.get(room_key, 0.0))
    freeze_cooldown_remaining = max(0, int(freeze_cooldown_seconds - (now_ts - last_freeze)))
    freeze_should_apply = bool(
        len(history) >= freeze_threshold and (freeze_cooldown_remaining == 0)
    )

    remediation_data = remediation_result.data if remediation_result and isinstance(remediation_result.data, dict) else {}
    auto_remediation_payload = remediation_data.get("ops_auto_remediation")
    remediation_triggered = bool(isinstance(auto_remediation_payload, dict) and auto_remediation_payload.get("executed"))
    remediation_scenario = (
        str(auto_remediation_payload.get("scenario") or "")
        if isinstance(auto_remediation_payload, dict)
        else ""
    ).strip()

    skip_promotion_reason = ""
    if auto_promote_canary:
        if remediation_triggered and remediation_scenario in {"provider_outage", "reliability_breach", "latency_spike", "trust_drift_breach"}:
            skip_promotion_reason = f"remediacao ativa em cenario `{remediation_scenario}`."
        else:
            promotion_result = await _ops_canary_promote_action(
                {
                    "dry_run": dry_run,
                    "force": force_promotion,
                    "step_if_passed": True,
                    "rollback_on_fail": False,
                    "metrics_limit": metrics_limit,
                },
                ctx,
            )

    final_snapshot = initial_snapshot
    for result in [remediation_result, promotion_result]:
        if result and isinstance(result.data, dict):
            maybe_snapshot = result.data.get("ops_incident_snapshot")
            if isinstance(maybe_snapshot, dict):
                final_snapshot = maybe_snapshot

    freeze_applied = False
    freeze_reason = ""
    if freeze_should_apply:
        freeze_reason = (
            "control_loop_freeze: "
            f"{len(history)} breach(es) em {freeze_window_seconds}s "
            f"(threshold={freeze_threshold})."
        )
        if dry_run:
            freeze_reason = f"{freeze_reason} [dry-run]"
        else:
            set_killswitch_global(True, reason=freeze_reason)
            _set_runtime_feature_override("canary_v1", False)
            _set_canary_rollout_percent(0)
            CONTROL_LOOP_FREEZE_LAST_TRIGGER[room_key] = now_ts
            freeze_applied = True
            final_snapshot = _build_ops_incident_snapshot(
                participant_identity=ctx.participant_identity,
                room=ctx.room,
                include_ping=False,
                ping_prompt="Responda apenas: ok",
                metrics_limit=metrics_limit,
            )

    control_report: JsonObject = {
        "executed": True,
        "dry_run": dry_run,
        "auto_remediate": auto_remediate,
        "auto_promote_canary": auto_promote_canary,
        "remediation_triggered": remediation_triggered,
        "remediation_scenario": remediation_scenario or None,
        "promotion_skipped_reason": skip_promotion_reason or None,
        "initial_signal": initial_signal,
        "breach_window": {
            "count": len(history),
            "threshold": freeze_threshold,
            "window_seconds": freeze_window_seconds,
        },
        "freeze": {
            "should_apply": freeze_should_apply,
            "applied": freeze_applied,
            "reason": freeze_reason or None,
            "cooldown_remaining_seconds": max(0, freeze_cooldown_remaining),
            "cooldown_seconds": freeze_cooldown_seconds,
        },
        "generated_at": _now_iso(),
    }
    if remediation_result is not None:
        control_report["remediation_status"] = {
            "success": remediation_result.success,
            "message": remediation_result.message,
        }
    if promotion_result is not None:
        control_report["promotion_status"] = {
            "success": promotion_result.success,
            "message": promotion_result.message,
        }

    return ActionResult(
        success=True,
        message="Tick operacional concluido.",
        data={
            "ops_control_tick": control_report,
            "ops_auto_remediation": remediation_data.get("ops_auto_remediation"),
            "ops_canary_promotion": (
                promotion_result.data.get("ops_canary_promotion")
                if promotion_result and isinstance(promotion_result.data, dict)
                else None
            ),
            "ops_playbook_report": (
                promotion_result.data.get("ops_playbook_report")
                if promotion_result and isinstance(promotion_result.data, dict)
                else remediation_data.get("ops_playbook_report")
            ),
            "ops_incident_snapshot": final_snapshot,
            "canary_state": final_snapshot.get("canary_state"),
            "feature_flags": final_snapshot.get("feature_flags"),
            "kill_switch": final_snapshot.get("kill_switch"),
            "slo_report": final_snapshot.get("slo_report"),
            "eval_metrics_summary": final_snapshot.get("metrics_summary"),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _ops_feature_flags_status_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    return ActionResult(
        success=True,
        message="Status das feature flags coletado.",
        data={
            "feature_flags": _feature_flags_snapshot(),
            "canary_state": _canary_state_payload(ctx.participant_identity, ctx.room),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _ops_feature_flags_set_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    feature_name = str(params.get("feature", "")).strip().lower()
    if not feature_name:
        return ActionResult(success=False, message="Informe `feature`.", error="missing feature")
    enabled = bool(params.get("enabled", True))
    FEATURE_FLAG_OVERRIDES[feature_name] = enabled
    return ActionResult(
        success=True,
        message=f"Feature `{feature_name}` ajustada para {'on' if enabled else 'off'} (runtime).",
        data={
            "feature_flags": _feature_flags_snapshot(),
            "canary_state": _canary_state_payload(ctx.participant_identity, ctx.room),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


def _set_runtime_feature_override(flag: str, enabled: bool) -> bool:
    normalized = flag.strip().lower()
    previous = FEATURE_FLAG_OVERRIDES.get(normalized)
    FEATURE_FLAG_OVERRIDES[normalized] = enabled
    return previous != enabled


def _predict_feature_values_from_overrides(overrides: dict[str, bool]) -> JsonObject:
    values: JsonObject = {}
    for flag in _known_feature_flags():
        if flag in overrides:
            values[flag] = bool(overrides[flag])
        else:
            values[flag] = _feature_value_from_env(flag, default=False if flag == "canary_v1" else True)
    return values


async def _ops_apply_playbook_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    playbook = str(params.get("playbook", "")).strip().lower()
    dry_run = bool(params.get("dry_run", False))
    domain = str(params.get("domain", "")).strip().lower()
    reason = str(params.get("reason", "")).strip()
    allowed = {
        "provider_degradation",
        "strict_guardrails",
        "degrade_domain_autonomy",
        "restore_domain_autonomy",
        "block_domain",
        "unblock_domain",
        "restore_runtime_overrides",
    }
    if playbook not in allowed:
        return ActionResult(
            success=False,
            message=f"Playbook invalido. Opcoes: {', '.join(sorted(allowed))}.",
            error="invalid playbook",
        )
    if playbook in {"degrade_domain_autonomy", "restore_domain_autonomy", "block_domain", "unblock_domain"} and not domain:
        return ActionResult(success=False, message="Informe `domain` para este playbook.", error="missing domain")

    before_flags = _feature_flags_snapshot()
    before_killswitch = get_killswitch_status().to_payload()
    before_mode = get_autonomy_mode(ctx.participant_identity, ctx.room)
    before_domain_mode = get_domain_autonomy_mode(ctx.participant_identity, ctx.room, domain) if domain else None
    predicted_domain_modes: dict[str, str] = {
        str(item.get("domain") or ""): str(item.get("mode") or "")
        for item in list_domain_autonomy_modes(ctx.participant_identity, ctx.room)
        if isinstance(item, dict) and str(item.get("domain") or "")
    }

    predicted_overrides: dict[str, bool] = {
        str(key).strip().lower(): bool(value)
        for key, value in dict(before_flags.get("overrides", {})).items()
    }
    predicted_killswitch = {
        "global_enabled": bool(before_killswitch.get("global_enabled", False)),
        "global_reason": before_killswitch.get("global_reason"),
        "domains": dict(before_killswitch.get("domains", {})),
    }
    predicted_mode = before_mode
    predicted_domain_mode = before_domain_mode
    changes: list[JsonObject] = []

    def _track_override(flag_name: str, enabled: bool, note: str) -> None:
        normalized = flag_name.strip().lower()
        previous_override = predicted_overrides.get(normalized)
        previous_effective = (
            bool(previous_override) if previous_override is not None else _feature_value_from_env(normalized)
        )
        changes.append(
            {
                "type": "feature_flag_override",
                "target": normalized,
                "from": previous_effective,
                "to": enabled,
                "note": note,
            }
        )
        predicted_overrides[normalized] = enabled
        if not dry_run:
            _set_runtime_feature_override(normalized, enabled)

    if playbook == "provider_degradation":
        _track_override("multi_model_router_v1", False, "Desliga roteador multi-model para reduzir variacao.")
        _track_override("subagents_v1", False, "Desliga subagentes para simplificar execucao.")
        _track_override("policy_v1", True, "Mantem politica ativa durante degradacao.")
        _track_override("skills_v1", True, "Mantem skills disponiveis para operacao manual assistida.")
    elif playbook == "strict_guardrails":
        changes.append(
            {
                "type": "autonomy_mode",
                "target": f"{ctx.participant_identity}:{ctx.room}",
                "from": before_mode,
                "to": "safe",
                "note": "Forca guardrails mais conservadores durante incidente.",
            }
        )
        predicted_mode = "safe"
        if not dry_run:
            set_autonomy_mode(ctx.participant_identity, ctx.room, "safe")
        _track_override("policy_v1", True, "Garante engine de politica habilitada.")
    elif playbook == "degrade_domain_autonomy":
        changes.append(
            {
                "type": "domain_autonomy_mode",
                "target": domain,
                "from": before_domain_mode,
                "to": "safe",
                "note": "Reduz autonomia apenas no dominio afetado.",
            }
        )
        predicted_domain_mode = "safe"
        predicted_domain_modes[domain] = "safe"
        if not dry_run:
            set_domain_autonomy_mode(
                ctx.participant_identity,
                ctx.room,
                domain,
                "safe",
                reason=reason or "ops_playbook_degrade_domain_autonomy",
                source="ops_playbook",
            )
    elif playbook == "restore_domain_autonomy":
        changes.append(
            {
                "type": "domain_autonomy_mode",
                "target": domain,
                "from": before_domain_mode,
                "to": None,
                "note": "Remove floor de autonomia por dominio apos estabilizacao.",
            }
        )
        predicted_domain_mode = None
        predicted_domain_modes.pop(domain, None)
        if not dry_run:
            clear_domain_autonomy_mode(ctx.participant_identity, ctx.room, domain)
    elif playbook == "block_domain":
        previous_reason = str(predicted_killswitch["domains"].get(domain, "")) or None
        applied_reason = reason or "blocked by ops playbook"
        changes.append(
            {
                "type": "domain_killswitch",
                "target": domain,
                "from": previous_reason,
                "to": applied_reason,
                "note": "Bloqueia dominio para conter erro em acao real.",
            }
        )
        predicted_killswitch["domains"][domain] = applied_reason
        if not dry_run:
            set_killswitch_domain(domain, True, applied_reason)
    elif playbook == "unblock_domain":
        previous_reason = str(predicted_killswitch["domains"].get(domain, "")) or None
        changes.append(
            {
                "type": "domain_killswitch",
                "target": domain,
                "from": previous_reason,
                "to": None,
                "note": "Reabre dominio bloqueado apos estabilizacao.",
            }
        )
        predicted_killswitch["domains"].pop(domain, None)
        if not dry_run:
            set_killswitch_domain(domain, False, None)
    elif playbook == "restore_runtime_overrides":
        existing = dict(FEATURE_FLAG_OVERRIDES)
        changes.append(
            {
                "type": "feature_flag_override",
                "target": "*",
                "from": len(existing),
                "to": 0,
                "note": "Limpa overrides runtime e volta para estado de env.",
            }
        )
        predicted_overrides = {}
        if not dry_run:
            FEATURE_FLAG_OVERRIDES.clear()

    if dry_run:
        after_flags = {
            "values": _predict_feature_values_from_overrides(predicted_overrides),
            "overrides": dict(predicted_overrides),
        }
        after_killswitch = {
            "global_enabled": predicted_killswitch["global_enabled"],
            "global_reason": predicted_killswitch["global_reason"],
            "domains": dict(predicted_killswitch["domains"]),
            "updated_at": _now_iso(),
        }
        after_mode = predicted_mode
        after_domain_mode = predicted_domain_mode
        after_domain_modes = [
            {
                "domain": item_domain,
                "mode": item_mode,
                "reason": reason if item_domain == domain and playbook == "degrade_domain_autonomy" else "",
                "source": "ops_playbook" if item_domain == domain and playbook == "degrade_domain_autonomy" else "",
                "updated_at": _now_iso() if item_domain == domain and playbook == "degrade_domain_autonomy" else "",
            }
            for item_domain, item_mode in sorted(predicted_domain_modes.items(), key=lambda item: item[0])
        ]
    else:
        after_flags = _feature_flags_snapshot()
        after_killswitch = get_killswitch_status().to_payload()
        after_mode = get_autonomy_mode(ctx.participant_identity, ctx.room)
        after_domain_mode = get_domain_autonomy_mode(ctx.participant_identity, ctx.room, domain) if domain else None
        after_domain_modes = list_domain_autonomy_modes(ctx.participant_identity, ctx.room)

    report = {
        "playbook": playbook,
        "dry_run": dry_run,
        "applied": not dry_run,
        "changes": changes,
        "before": {
            "feature_flags": before_flags,
            "kill_switch": before_killswitch,
            "autonomy_mode": before_mode,
            "domain_autonomy_mode": before_domain_mode,
            "domain_autonomy_modes": list_domain_autonomy_modes(ctx.participant_identity, ctx.room),
        },
        "after": {
            "feature_flags": after_flags,
            "kill_switch": after_killswitch,
            "autonomy_mode": after_mode,
            "domain_autonomy_mode": after_domain_mode,
            "domain_autonomy_modes": after_domain_modes,
        },
        "generated_at": _now_iso(),
    }

    snapshot = _build_ops_incident_snapshot(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        include_ping=False,
        ping_prompt="Responda apenas: ok",
        metrics_limit=300,
    )
    snapshot["autonomy_mode"] = after_mode
    snapshot["domain_autonomy_modes"] = after_domain_modes
    snapshot["domain_autonomy_status"] = _build_domain_autonomy_audit_rows(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        metrics_summary=snapshot.get("metrics_summary") if isinstance(snapshot.get("metrics_summary"), dict) else None,
        domain_mode_rows_override=after_domain_modes,
        autonomy_mode_override=after_mode,
    )
    snapshot["feature_flags"] = after_flags
    snapshot["kill_switch"] = after_killswitch

    return ActionResult(
        success=True,
        message=f"Playbook `{playbook}` {'simulado' if dry_run else 'aplicado'} com {len(changes)} ajuste(s).",
        data={
            "ops_playbook_report": report,
            "ops_incident_snapshot": snapshot,
            "canary_state": snapshot.get("canary_state"),
            "autonomy_mode": after_mode,
            "domain_autonomy_mode": after_domain_mode,
            "feature_flags": after_flags,
            "kill_switch": after_killswitch,
            "providers_health": snapshot.get("providers_health"),
            "eval_metrics_summary": snapshot.get("metrics_summary"),
            "slo_report": snapshot.get("slo_report"),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _ops_rollback_scenario_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    scenario = str(params.get("scenario", "")).strip().lower()
    dry_run = bool(params.get("dry_run", False))
    domain = str(params.get("domain", "")).strip().lower()
    containment_strategy = str(params.get("containment_strategy", "default")).strip().lower() or "default"
    reason = str(params.get("reason", "")).strip()
    allowed = {"provider_outage", "latency_spike", "reliability_breach", "trust_drift_breach", "recover_to_stable"}
    if scenario not in allowed:
        return ActionResult(
            success=False,
            message=f"Cenario invalido. Opcoes: {', '.join(sorted(allowed))}.",
            error="invalid scenario",
        )

    steps: list[JsonObject] = []
    if scenario == "provider_outage":
        steps = [{"playbook": "provider_degradation"}, {"playbook": "strict_guardrails"}]
        if domain:
            steps.append({"playbook": "block_domain", "domain": domain, "reason": reason or "provider outage containment"})
    elif scenario == "latency_spike":
        steps = [{"playbook": "provider_degradation"}]
    elif scenario == "reliability_breach":
        steps = [{"playbook": "strict_guardrails"}]
        if domain:
            if containment_strategy == "domain_autonomy":
                steps.append(
                    {
                        "playbook": "degrade_domain_autonomy",
                        "domain": domain,
                        "reason": reason or "reliability containment via domain autonomy",
                    }
                )
            else:
                steps.append({"playbook": "block_domain", "domain": domain, "reason": reason or "reliability containment"})
    elif scenario == "trust_drift_breach":
        steps = [{"playbook": "strict_guardrails"}]
        if domain:
            steps.append({"playbook": "block_domain", "domain": domain, "reason": reason or "trust drift containment"})
    elif scenario == "recover_to_stable":
        steps = [{"playbook": "restore_runtime_overrides"}]
        if domain:
            steps.append({"playbook": "unblock_domain", "domain": domain})
            steps.append({"playbook": "restore_domain_autonomy", "domain": domain})

    before_flags = _feature_flags_snapshot()
    before_killswitch = get_killswitch_status().to_payload()
    before_mode = get_autonomy_mode(ctx.participant_identity, ctx.room)
    before_rollout = _get_canary_rollout_percent()
    before_canary_enabled = _is_feature_enabled("canary_v1", default=False)
    step_reports: list[JsonObject] = []

    for step in steps:
        playbook_params: JsonObject = {"playbook": step.get("playbook"), "dry_run": dry_run}
        if isinstance(step.get("domain"), str) and step.get("domain"):
            playbook_params["domain"] = step.get("domain")
        if isinstance(step.get("reason"), str) and step.get("reason"):
            playbook_params["reason"] = step.get("reason")
        step_result = await _ops_apply_playbook_action(playbook_params, ctx)
        if not step_result.success:
            return step_result
        if isinstance(step_result.data, dict) and isinstance(step_result.data.get("ops_playbook_report"), dict):
            step_reports.append(dict(step_result.data["ops_playbook_report"]))

    mode_change: JsonObject | None = None
    if scenario == "recover_to_stable":
        if dry_run:
            mode_change = {
                "type": "autonomy_mode",
                "target": f"{ctx.participant_identity}:{ctx.room}",
                "from": before_mode,
                "to": "aggressive",
                "note": "Dry-run: retornaria autonomia para agressivo apos recuperacao.",
            }
        else:
            after_set = set_autonomy_mode(ctx.participant_identity, ctx.room, "aggressive")
            mode_change = {
                "type": "autonomy_mode",
                "target": f"{ctx.participant_identity}:{ctx.room}",
                "from": before_mode,
                "to": after_set,
                "note": "Retorno para perfil padrao apos rollback.",
            }
    if mode_change is not None:
        step_reports.append({"playbook": "autonomy_mode_adjustment", "changes": [mode_change], "dry_run": dry_run})

    canary_changes: list[JsonObject] = []
    if scenario in {"provider_outage", "latency_spike", "reliability_breach", "trust_drift_breach"}:
        canary_changes.append(
            {
                "type": "feature_flag_override",
                "target": "canary_v1",
                "from": before_canary_enabled,
                "to": False,
                "note": "Congela canario durante rollback de incidente.",
            }
        )
        canary_changes.append(
            {
                "type": "canary_rollout",
                "target": "rollout_percent",
                "from": before_rollout,
                "to": 0,
                "note": "Zera rollout para evitar expandir regressao.",
            }
        )
        if not dry_run:
            _set_runtime_feature_override("canary_v1", False)
            _set_canary_rollout_percent(0)
    elif scenario == "recover_to_stable":
        canary_changes.append(
            {
                "type": "feature_flag_override",
                "target": "canary_v1",
                "from": before_canary_enabled,
                "to": None,
                "note": "Remove override manual de canario e volta para o default configurado.",
            }
        )
        canary_changes.append(
            {
                "type": "canary_rollout",
                "target": "rollout_percent",
                "from": before_rollout,
                "to": 10,
                "note": "Retoma rollout em 10% apos recuperacao.",
            }
        )
        if not dry_run:
            FEATURE_FLAG_OVERRIDES.pop("canary_v1", None)
            _set_canary_rollout_percent(10)
    if canary_changes:
        step_reports.append({"playbook": "canary_control", "changes": canary_changes, "dry_run": dry_run})

    after_flags = _feature_flags_snapshot()
    after_killswitch = get_killswitch_status().to_payload()
    after_mode = get_autonomy_mode(ctx.participant_identity, ctx.room)
    after_domain_modes = list_domain_autonomy_modes(ctx.participant_identity, ctx.room)
    if dry_run:
        mode_rank = {"aggressive": 0, "safe": 1, "manual": 2}
        for step_report in step_reports:
            after_payload = step_report.get("after") if isinstance(step_report, dict) else None
            if not isinstance(after_payload, dict):
                continue
            if isinstance(after_payload.get("autonomy_mode"), str) and after_payload.get("autonomy_mode"):
                candidate_mode = str(after_payload.get("autonomy_mode"))
                if mode_rank.get(candidate_mode, 0) >= mode_rank.get(after_mode, 0):
                    after_mode = candidate_mode
            if isinstance(after_payload.get("domain_autonomy_modes"), list):
                after_domain_modes = [
                    item
                    for item in after_payload.get("domain_autonomy_modes", [])
                    if isinstance(item, dict)
                ]

    scenario_report: JsonObject = {
        "playbook": f"rollback_scenario:{scenario}",
        "dry_run": dry_run,
        "applied": not dry_run,
        "steps_executed": [str(step.get("playbook") or "") for step in steps],
        "step_reports": step_reports,
        "before": {
            "feature_flags": before_flags,
            "kill_switch": before_killswitch,
            "autonomy_mode": before_mode,
        },
        "after": {
            "feature_flags": after_flags,
            "kill_switch": after_killswitch,
            "autonomy_mode": after_mode,
            "domain_autonomy_modes": after_domain_modes,
        },
        "notes": (
            ["Dry-run em multiplos passos e nao transacional; revisar `step_reports` antes de aplicar."]
            if dry_run and len(steps) > 1
            else []
        ),
        "generated_at": _now_iso(),
    }

    snapshot = _build_ops_incident_snapshot(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        include_ping=False,
        ping_prompt="Responda apenas: ok",
        metrics_limit=300,
    )
    snapshot["autonomy_mode"] = after_mode
    snapshot["domain_autonomy_modes"] = after_domain_modes
    snapshot["domain_autonomy_status"] = _build_domain_autonomy_audit_rows(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        metrics_summary=snapshot.get("metrics_summary") if isinstance(snapshot.get("metrics_summary"), dict) else None,
        domain_mode_rows_override=after_domain_modes,
        autonomy_mode_override=after_mode,
    )

    return ActionResult(
        success=True,
        message=f"Rollback de cenario `{scenario}` {'simulado' if dry_run else 'aplicado'} com {len(steps)} passo(s).",
        data={
            "ops_playbook_report": scenario_report,
            "ops_incident_snapshot": snapshot,
            "canary_state": snapshot.get("canary_state"),
            "feature_flags": snapshot.get("feature_flags"),
            "kill_switch": snapshot.get("kill_switch"),
            "autonomy_mode": snapshot.get("autonomy_mode"),
            "domain_autonomy_modes": snapshot.get("domain_autonomy_modes"),
            "providers_health": snapshot.get("providers_health"),
            "eval_metrics_summary": snapshot.get("metrics_summary"),
            "slo_report": snapshot.get("slo_report"),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _code_worker_status_action(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    response, worker_error = _code_worker_request("/health")
    if worker_error is not None:
        return ActionResult(
            success=False,
            message=worker_error.message,
            data={
                "worker_status": {"success": False, "message": worker_error.message},
                **_active_project_payload(ctx.participant_identity, ctx.room),
            },
            error=worker_error.error,
        )
    return ActionResult(
        success=True,
        message="Code worker online.",
        data={
            "worker_status": {"success": True, "message": str(response.get("message", "Code worker online."))},
            "worker_info": response.get("data"),
            **_active_project_payload(ctx.participant_identity, ctx.room),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _code_read_file_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    path = str(params.get("path", "")).strip()
    if not path:
        return ActionResult(success=False, message="Informe o arquivo que devo ler.", error="missing path")
    record, error = _resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None
    worker_payload: JsonObject = {
        "project_id": record.project_id,
        "path": path,
    }
    if isinstance(params.get("start_line"), int):
        worker_payload["start_line"] = params.get("start_line")
    if isinstance(params.get("end_line"), int):
        worker_payload["end_line"] = params.get("end_line")
    response, worker_error = _code_worker_request("/read-file", worker_payload)
    if worker_error is not None:
        return worker_error
    return ActionResult(
        success=True,
        message=f"Arquivo lido em {record.name}.",
        data={
            "project": _project_record_to_payload(record),
            "file": response.get("data"),
            **_active_project_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _code_search_in_active_project_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    query = str(params.get("query", "")).strip()
    if not query:
        return ActionResult(success=False, message="Informe a busca de codigo.", error="missing query")
    limit = int(params.get("limit", 5))
    record, error = _resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None
    indexed = _get_code_index().search(query, limit=limit, project_id=record.project_id)
    worker_response, worker_error = _code_worker_request(
        "/search-files",
        {"project_id": record.project_id, "query": query, "limit": limit},
    )
    file_hits = [] if worker_error is not None else list((worker_response or {}).get("data", {}).get("results", []))
    return ActionResult(
        success=True,
        message=f"Busca de codigo concluida em {record.name}.",
        data={
            "project": _project_record_to_payload(record),
            "query": query,
            "results": indexed,
            "file_hits": file_hits,
            **_active_project_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _code_git_status_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    record, error = _resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None
    response, worker_error = _code_worker_request("/git-status", {"project_id": record.project_id})
    if worker_error is not None:
        return worker_error
    return ActionResult(
        success=True,
        message=f"Git status coletado para {record.name}.",
        data={
            "project": _project_record_to_payload(record),
            "git_status": response.get("data"),
            **_active_project_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _code_git_diff_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    record, error = _resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None
    paths = params.get("paths", [])
    worker_payload: JsonObject = {"project_id": record.project_id}
    if isinstance(paths, list):
        worker_payload["paths"] = [item for item in paths if isinstance(item, str) and item.strip()]
    response, worker_error = _code_worker_request("/git-diff", worker_payload)
    if worker_error is not None:
        return worker_error
    diff_data = response.get("data") if isinstance(response.get("data"), dict) else {}
    diff_text = str(diff_data.get("stdout", "") or diff_data.get("stderr", "")).strip()
    diff_summary = summarize_diff(project=_project_record_to_payload(record), diff_text=diff_text) if diff_text else None
    return ActionResult(
        success=True,
        message=f"Git diff coletado para {record.name}.",
        data={
            "project": _project_record_to_payload(record),
            "git_diff": diff_data,
            "git_diff_summary": diff_summary,
            **_active_project_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _code_explain_project_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    request_text = str(params.get("request", "")).strip() or str(params.get("query", "")).strip()
    if not request_text:
        return ActionResult(success=False, message="Descreva o que devo analisar no projeto.", error="missing request")
    limit = int(params.get("limit", 4))
    record, error = _resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None

    snippets = _get_code_index().search(request_text, limit=limit, project_id=record.project_id)
    extra_files: list[JsonObject] = []
    read_paths = params.get("read_paths", [])
    if isinstance(read_paths, list):
        for item in read_paths[:2]:
            if not isinstance(item, str) or not item.strip():
                continue
            response, worker_error = _code_worker_request(
                "/read-file",
                {"project_id": record.project_id, "path": item},
            )
            if worker_error is None and isinstance(response.get("data"), dict):
                file_payload = response.get("data") or {}
                extra_files.append(
                    {
                        "path": file_payload.get("relative_path") or file_payload.get("path"),
                        "content": file_payload.get("content", ""),
                    }
                )

    explanation = explain_project_state(
        user_request=request_text,
        project=_project_record_to_payload(record),
        snippets=snippets,
        extra_files=extra_files,
    )
    return ActionResult(
        success=True,
        message=f"Analise preparada para {record.name}.",
        data={
            "project": _project_record_to_payload(record),
            "project_analysis": explanation,
            "context_results": snippets,
            "context_files": extra_files,
            **_active_project_payload(ctx.participant_identity, ctx.room),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _code_propose_change_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    request_text = str(params.get("request", "")).strip() or str(params.get("query", "")).strip()
    if not request_text:
        return ActionResult(success=False, message="Descreva a mudanca ou pergunta de engenharia.", error="missing request")
    limit = int(params.get("limit", 4))
    record, error = _resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None

    snippets = _get_code_index().search(request_text, limit=limit, project_id=record.project_id)
    extra_files: list[JsonObject] = []
    read_paths = params.get("read_paths", [])
    if isinstance(read_paths, list):
        for item in read_paths[:2]:
            if not isinstance(item, str) or not item.strip():
                continue
            response, worker_error = _code_worker_request(
                "/read-file",
                {"project_id": record.project_id, "path": item},
            )
            if worker_error is None and isinstance(response.get("data"), dict):
                file_payload = response.get("data") or {}
                extra_files.append(
                    {
                        "path": file_payload.get("relative_path") or file_payload.get("path"),
                        "content": file_payload.get("content", ""),
                    }
                )

    proposal = propose_patch_plan(
        user_request=request_text,
        project=_project_record_to_payload(record),
        snippets=snippets,
        extra_files=extra_files,
    )
    return ActionResult(
        success=True,
        message=f"Proposta de mudanca preparada para {record.name}.",
        data={
            "project": _project_record_to_payload(record),
            "proposed_code_change": proposal,
            "context_results": snippets,
            "context_files": extra_files,
            **_active_project_payload(ctx.participant_identity, ctx.room),
            **_capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _code_apply_patch_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    changes = params.get("changes", [])
    if not isinstance(changes, list) or not changes:
        return ActionResult(success=False, message="Envie ao menos uma mudanca para aplicar.", error="missing changes")
    record, error = _resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None
    response, worker_error = _code_worker_request(
        "/apply-patch",
        {"project_id": record.project_id, "changes": changes},
    )
    if worker_error is not None:
        return worker_error
    return ActionResult(
        success=True,
        message=f"Patch aplicado em {record.name}.",
        data={
            "project": _project_record_to_payload(record),
            "patch_result": response.get("data"),
            **_active_project_payload(ctx.participant_identity, ctx.room),
        },
    )


async def _code_run_command_action(params: JsonObject, ctx: ActionContext) -> ActionResult:
    command = str(params.get("command", "")).strip()
    arguments = params.get("arguments", [])
    if not command:
        return ActionResult(success=False, message="Informe o comando para validacao.", error="missing command")
    if not isinstance(arguments, list) or any(not isinstance(item, str) for item in arguments):
        return ActionResult(success=False, message="`arguments` precisa ser uma lista de textos.", error="invalid arguments")
    record, error = _resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None
    response, worker_error = _code_worker_request(
        "/run-command",
        {
            "project_id": record.project_id,
            "command": command,
            "arguments": arguments,
            "timeout_seconds": int(params.get("timeout_seconds", 60) or 60),
        },
    )
    if worker_error is not None:
        return worker_error
    return ActionResult(
        success=True,
        message=f"Comando executado em {record.name}.",
        data={
            "project": _project_record_to_payload(record),
            "command_execution": response.get("data"),
            **_active_project_payload(ctx.participant_identity, ctx.room),
        },
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
    if not name:
        return ActionResult(success=False, message="Informe o nome do personagem.", error="missing name")

    world = str(params.get("world", "tormenta20")).strip() or "tormenta20"
    class_name = (
        str(params.get("class_name", "")).strip()
        or str(params.get("class", "")).strip()
        or str(params.get("character_class", "")).strip()
        or "A definir"
    )
    safe_world = _safe_file_part(world)
    safe_name = _safe_file_part(name)
    target_dir = _rpg_characters_dir() / safe_world
    target_dir.mkdir(parents=True, exist_ok=True)
    md_path = target_dir / f"{safe_name}.md"
    json_path = target_dir / f"{safe_name}.json"
    pdf_dir = _rpg_character_pdfs_dir() / safe_world
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / f"{safe_name}.pdf"

    try:
        generation = generate_character_sheet(params)
    except InvalidCharacterBuildError as error:
        return ActionResult(success=False, message=str(error), error=str(error))

    sheet_data = generation.normalized_sheet
    sheet_md = generation.markdown
    builder_source = generation.source
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
            skill_summary = []
        artifact_summary = (
            f"Arquivos locais: JSON {json_path.resolve()} | MD {md_path.resolve()} | "
            f"PDF {pdf_path.resolve() if pdf_exported else 'indisponivel'}."
        )
        append_text = (
            f"Ficha Tormenta20 atualizada. Classe: {class_name}. Nivel: {sheet_data.get('level', 1)}. "
            f"Builder: {builder_source}. Status: {generation.status}. "
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
                "generation_status": generation.status,
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
            "sheet_builder_error": "; ".join(generation.errors) if generation.errors else None,
            "sheet_generation_status": generation.status,
            "sheet_generation_warnings": generation.warnings,
            "sheet_applied_choices": generation.applied_choices,
            "sheet_unsupported_fields": generation.unsupported_fields,
            "template_references": existing_templates,
            "one_note_character_page_sync": one_note_sync_status,
            "one_note_character_page_error": one_note_sync_error,
        },
    )


async def _rpg_create_threat_sheet(params: JsonObject, ctx: ActionContext) -> ActionResult:  # noqa: ARG001
    name = str(params.get("name", "")).strip()
    if not name:
        return ActionResult(success=False, message="Informe o nome da ameaça.", error="missing name")

    try:
        generation = generate_threat_sheet(params)
    except InvalidThreatDefinitionError as error:
        return ActionResult(success=False, message=str(error), error=str(error))

    threat_data = generation.normalized_threat
    world = str(threat_data.get("world", "tormenta20")).strip() or "tormenta20"
    safe_world = _safe_file_part(world)
    safe_name = _safe_file_part(name)
    target_dir = _rpg_threats_dir() / safe_world
    target_dir.mkdir(parents=True, exist_ok=True)
    md_path = target_dir / f"{safe_name}.md"
    json_path = target_dir / f"{safe_name}.json"
    pdf_dir = _rpg_threat_pdfs_dir() / safe_world
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / f"{safe_name}.pdf"

    md_path.write_text(generation.markdown, encoding="utf-8")
    json_path.write_text(json.dumps(threat_data, ensure_ascii=False, indent=2), encoding="utf-8")
    pdf_exported, pdf_error = _export_tormenta20_threat_pdf(threat_data, pdf_path)
    pdf_status = "created" if pdf_exported else "failed"

    logger.info(
        "rpg_threat_pipeline %s",
        json.dumps(
            {
                "threat_name": name,
                "world": world,
                "challenge_level": threat_data.get("challenge_level"),
                "role": threat_data.get("role"),
                "builder_source": threat_data.get("builder"),
                "generation_status": generation.status,
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
            "threat_generation_status": generation.status,
            "threat_generation_warnings": generation.warnings,
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
            name="code_reindex_repo",
            description="Reindexa o codigo local do repositorio para busca semantica/FTS.",
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
            handler=_code_reindex_repo,
            expose_to_model=False,
        )
    )

    register_action(
        ActionSpec(
            name="code_search_repo",
            description="Busca trechos no codigo local do repositorio por termos, arquivos, funcoes e implementacoes.",
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
            handler=_code_search_repo,
            expose_to_model=False,
        )
    )

    register_action(
        ActionSpec(
            name="project_list",
            description="Lista os projetos conhecidos no catalogo multi-repo do Jarvez.",
            params_schema={
                "type": "object",
                "properties": {
                    "include_inactive": {"type": "boolean"},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_project_list_action,
        )
    )

    register_action(
        ActionSpec(
            name="project_scan",
            description="Faz um scan nas pastas configuradas e atualiza o catalogo de projetos.",
            params_schema={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_project_scan_action,
        )
    )

    register_action(
        ActionSpec(
            name="github_list_repos",
            description="Lista repositorios acessiveis no GitHub conectado. Pode filtrar por busca.",
            params_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "minLength": 1, "maxLength": 200},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                    "visibility": {"type": "string", "enum": ["all", "public", "private"]},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_github_list_repos_action,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="github_find_repo",
            description="Encontra um repositorio do GitHub por nome curto ou nome completo.",
            params_schema={
                "type": "object",
                "properties": {
                    "repository": {"type": "string", "minLength": 1, "maxLength": 200},
                    "full_name": {"type": "string", "minLength": 1, "maxLength": 200},
                    "name": {"type": "string", "minLength": 1, "maxLength": 200},
                    "query": {"type": "string", "minLength": 1, "maxLength": 200},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_github_find_repo_action,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="github_clone_and_register",
            description="Resolve um repositorio no GitHub, faz git clone localmente e registra o projeto no catalogo.",
            params_schema={
                "type": "object",
                "properties": {
                    "repository": {"type": "string", "minLength": 1, "maxLength": 200},
                    "full_name": {"type": "string", "minLength": 1, "maxLength": 200},
                    "name": {"type": "string", "minLength": 1, "maxLength": 200},
                    "query": {"type": "string", "minLength": 1, "maxLength": 200},
                    "destination": {"type": "string", "minLength": 1, "maxLength": 500},
                    "destination_root": {"type": "string", "minLength": 1, "maxLength": 500},
                    "branch": {"type": "string", "minLength": 1, "maxLength": 120},
                    "depth": {"type": "integer", "minimum": 1, "maximum": 1000},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_github_clone_and_register_action,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="project_update",
            description="Atualiza metadados de um projeto do catalogo (nome, aliases, prioridade e estado ativo).",
            params_schema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "minLength": 4, "maxLength": 80},
                    "name": {"type": "string", "minLength": 1, "maxLength": 200},
                    "aliases": {"type": "array"},
                    "priority_score": {"type": "integer", "minimum": -100, "maximum": 100},
                    "is_active": {"type": "boolean"},
                },
                "required": ["project_id"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_project_update_action,
        )
    )

    register_action(
        ActionSpec(
            name="project_remove",
            description="Remove um projeto do catalogo sem apagar arquivos do disco.",
            params_schema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "minLength": 4, "maxLength": 80},
                },
                "required": ["project_id"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_project_remove_action,
        )
    )

    register_action(
        ActionSpec(
            name="project_select",
            description="Seleciona um projeto por project_id, nome, alias ou consulta aproximada e ativa ele na sessao.",
            params_schema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "minLength": 4, "maxLength": 80},
                    "query": {"type": "string", "minLength": 1, "maxLength": 300},
                    "project_query": {"type": "string", "minLength": 1, "maxLength": 300},
                    "fuzzy_query": {"type": "string", "minLength": 1, "maxLength": 300},
                    "project": {"type": "string", "minLength": 1, "maxLength": 300},
                    "project_name": {"type": "string", "minLength": 1, "maxLength": 300},
                    "name": {"type": "string", "minLength": 1, "maxLength": 300},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_project_select_action,
        )
    )

    register_action(
        ActionSpec(
            name="project_get_active",
            description="Retorna o projeto ativo no contexto atual.",
            params_schema={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_project_get_active_action,
        )
    )

    register_action(
        ActionSpec(
            name="project_clear_active",
            description="Limpa o projeto ativo da sessao atual.",
            params_schema={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_project_clear_active_action,
        )
    )

    register_action(
        ActionSpec(
            name="project_refresh_index",
            description="Reindexa explicitamente um projeto do catalogo.",
            params_schema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "minLength": 4, "maxLength": 80},
                    "query": {"type": "string", "minLength": 1, "maxLength": 300},
                    "project": {"type": "string", "minLength": 1, "maxLength": 300},
                    "project_name": {"type": "string", "minLength": 1, "maxLength": 300},
                    "name": {"type": "string", "minLength": 1, "maxLength": 300},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_project_refresh_index_action,
        )
    )

    register_action(
        ActionSpec(
            name="project_search",
            description="Busca trechos no indice do projeto ativo ou de um projeto informado.",
            params_schema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "minLength": 4, "maxLength": 80},
                    "query": {"type": "string", "minLength": 2, "maxLength": 300},
                    "project": {"type": "string", "minLength": 1, "maxLength": 300},
                    "project_name": {"type": "string", "minLength": 1, "maxLength": 300},
                    "name": {"type": "string", "minLength": 1, "maxLength": 300},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_project_search_action,
        )
    )

    register_action(
        ActionSpec(
            name="coding_mode_get",
            description="Retorna o modo funcional atual (default/coding).",
            params_schema={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_coding_mode_get_action,
        )
    )

    register_action(
        ActionSpec(
            name="coding_mode_set",
            description="Ativa ou desativa o modo funcional de engenharia (coding/codex).",
            params_schema={
                "type": "object",
                "properties": {
                    "mode": {"type": "string", "enum": ["default", "coding", "codex"]},
                },
                "required": ["mode"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_coding_mode_set_action,
        )
    )

    register_action(
        ActionSpec(
            name="code_worker_status",
            description="Verifica se o code worker local esta online e acessivel.",
            params_schema={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_code_worker_status_action,
            expose_to_model=False,
        )
    )

    register_action(
        ActionSpec(
            name="codex_exec_task",
            description="Executa uma tarefa de analise, explicacao ou planejamento via Codex CLI no projeto ativo (ou informado).",
            params_schema={
                "type": "object",
                "properties": {
                    "request": {"type": "string", "minLength": 2, "maxLength": 4000},
                    "query": {"type": "string", "minLength": 2, "maxLength": 4000},
                    "prompt": {"type": "string", "minLength": 2, "maxLength": 4000},
                    "project_id": {"type": "string", "minLength": 4, "maxLength": 80},
                    "project": {"type": "string", "minLength": 1, "maxLength": 300},
                    "project_name": {"type": "string", "minLength": 1, "maxLength": 300},
                    "name": {"type": "string", "minLength": 1, "maxLength": 300},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_codex_exec_task_action,
        )
    )

    register_action(
        ActionSpec(
            name="codex_exec_review",
            description="Executa um review tecnico read-only via Codex CLI no projeto ativo (ou informado).",
            params_schema={
                "type": "object",
                "properties": {
                    "request": {"type": "string", "minLength": 2, "maxLength": 4000},
                    "query": {"type": "string", "minLength": 2, "maxLength": 4000},
                    "project_id": {"type": "string", "minLength": 4, "maxLength": 80},
                    "project": {"type": "string", "minLength": 1, "maxLength": 300},
                    "project_name": {"type": "string", "minLength": 1, "maxLength": 300},
                    "name": {"type": "string", "minLength": 1, "maxLength": 300},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_codex_exec_review_action,
        )
    )

    register_action(
        ActionSpec(
            name="codex_exec_status",
            description="Retorna o estado da tarefa atual ou da ultima tarefa executada via Codex CLI.",
            params_schema={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_codex_exec_status_action,
        )
    )

    register_action(
        ActionSpec(
            name="codex_cancel_task",
            description="Cancela a tarefa atual do Codex CLI nesta sessao.",
            params_schema={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_codex_cancel_task_action,
        )
    )

    register_action(
        ActionSpec(
            name="skills_list",
            description="Lista skills disponiveis no workspace para carregar instrucoes sob demanda.",
            params_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "minLength": 1, "maxLength": 200},
                    "refresh": {"type": "boolean"},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_skills_list_action,
        )
    )

    register_action(
        ActionSpec(
            name="skills_read",
            description="Le o SKILL.md de uma skill por id ou nome.",
            params_schema={
                "type": "object",
                "properties": {
                    "skill_id": {"type": "string", "minLength": 1, "maxLength": 200},
                    "skill_name": {"type": "string", "minLength": 1, "maxLength": 200},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_skills_read_action,
        )
    )

    register_action(
        ActionSpec(
            name="orchestrate_task",
            description="Planeja uma tarefa, escolhe provider com fallback e retorna um resumo de execucao orquestrada.",
            params_schema={
                "type": "object",
                "properties": {
                    "request": {"type": "string", "minLength": 2, "maxLength": 4000},
                    "query": {"type": "string", "minLength": 2, "maxLength": 4000},
                    "prompt": {"type": "string", "minLength": 2, "maxLength": 4000},
                    "action_hint": {"type": "string", "minLength": 2, "maxLength": 120},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_orchestrate_task_action,
        )
    )

    register_action(
        ActionSpec(
            name="subagent_spawn",
            description="Dispara um subagente para tarefas longas e retorna o estado do run.",
            params_schema={
                "type": "object",
                "properties": {
                    "request": {"type": "string", "minLength": 2, "maxLength": 4000},
                    "action_hint": {"type": "string", "minLength": 2, "maxLength": 120},
                    "auto_complete": {"type": "boolean"},
                    "wait_for_completion": {"type": "boolean"},
                },
                "required": ["request"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_subagent_spawn_action,
        )
    )

    register_action(
        ActionSpec(
            name="subagent_status",
            description="Retorna o estado de um subagente especifico ou de todos os subagentes da sessao.",
            params_schema={
                "type": "object",
                "properties": {
                    "subagent_id": {"type": "string", "minLength": 5, "maxLength": 120},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_subagent_status_action,
        )
    )

    register_action(
        ActionSpec(
            name="subagent_cancel",
            description="Cancela um subagente em execucao.",
            params_schema={
                "type": "object",
                "properties": {
                    "subagent_id": {"type": "string", "minLength": 5, "maxLength": 120},
                },
                "required": ["subagent_id"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_subagent_cancel_action,
        )
    )

    register_action(
        ActionSpec(
            name="policy_explain_decision",
            description="Explica risco e decisao de politica para uma action especifica.",
            params_schema={
                "type": "object",
                "properties": {
                    "action_name": {"type": "string", "minLength": 2, "maxLength": 180},
                },
                "required": ["action_name"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_policy_explain_decision_action,
        )
    )

    register_action(
        ActionSpec(
            name="autonomy_set_mode",
            description="Ajusta o modo de autonomia da sessao (safe/aggressive/manual).",
            params_schema={
                "type": "object",
                "properties": {
                    "mode": {"type": "string", "enum": ["safe", "aggressive", "manual"]},
                },
                "required": ["mode"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_autonomy_set_mode_action,
        )
    )

    register_action(
        ActionSpec(
            name="autonomy_killswitch",
            description="Liga/desliga kill switch global ou por dominio para bloquear automacoes.",
            params_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["status", "enable", "disable", "enable_domain", "disable_domain"],
                    },
                    "domain": {"type": "string", "minLength": 2, "maxLength": 60},
                    "reason": {"type": "string", "minLength": 2, "maxLength": 240},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_autonomy_killswitch_action,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="policy_action_risk_matrix",
            description="Lista as actions com risco/classificacao para governanca e auditoria.",
            params_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "minLength": 1, "maxLength": 120},
                    "include_internal": {"type": "boolean"},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_policy_action_risk_matrix_action,
        )
    )

    register_action(
        ActionSpec(
            name="policy_domain_trust_status",
            description="Retorna trust score por dominio usado pela politica dinamica de autonomia.",
            params_schema={
                "type": "object",
                "properties": {
                    "domain": {"type": "string", "minLength": 2, "maxLength": 80},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_policy_domain_trust_status_action,
        )
    )

    register_action(
        ActionSpec(
            name="policy_trust_drift_report",
            description="Sincroniza com o backend o drift de trust detectado no Trust Center do cliente.",
            params_schema={
                "type": "object",
                "properties": {
                    "signature": {"type": "string", "minLength": 1, "maxLength": 512},
                    "rows": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "domain": {"type": "string", "minLength": 2, "maxLength": 80},
                                "active": {"type": "boolean"},
                                "state": {"type": "string", "minLength": 2, "maxLength": 40},
                                "score_delta": {"type": "number"},
                                "recommendation_delta_ms": {"type": "integer"},
                                "retry_delta": {"type": "integer"},
                            },
                            "required": ["domain"],
                            "additionalProperties": True,
                        },
                        "maxItems": 32,
                    },
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_policy_trust_drift_report_action,
        )
    )

    register_action(
        ActionSpec(
            name="evals_list_scenarios",
            description="Lista cenarios de baseline para validacao de confiabilidade do Jarvez.",
            params_schema={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_evals_list_scenarios_action,
            expose_to_model=False,
        )
    )

    register_action(
        ActionSpec(
            name="evals_run_baseline",
            description="Executa a suite baseline de cenarios e salva o resultado nas metricas locais.",
            params_schema={
                "type": "object",
                "properties": {
                    "task_type": {"type": "string", "enum": ["chat", "code", "review", "research", "automation", "unknown"]},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_evals_run_baseline_action,
            expose_to_model=False,
        )
    )

    register_action(
        ActionSpec(
            name="evals_get_metrics",
            description="Retorna metricas e resultados das execucoes de baseline/observabilidade.",
            params_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 200},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_evals_get_metrics_action,
            expose_to_model=False,
        )
    )

    register_action(
        ActionSpec(
            name="evals_metrics_summary",
            description="Resume metricas por provider e risco para acompanhar confiabilidade operacional.",
            params_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 10, "maximum": 1000},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_evals_metrics_summary_action,
            expose_to_model=False,
        )
    )

    register_action(
        ActionSpec(
            name="evals_slo_report",
            description="Calcula SLOs operacionais (p95, taxa de sucesso baixo risco e proxy de false-success).",
            params_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 20, "maximum": 1200},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_evals_slo_report_action,
            expose_to_model=False,
        )
    )

    register_action(
        ActionSpec(
            name="providers_health_check",
            description="Checa configuracao e estado dos providers multi-model; opcionalmente executa ping curto.",
            params_schema={
                "type": "object",
                "properties": {
                    "include_ping": {"type": "boolean"},
                    "ping_prompt": {"type": "string", "minLength": 2, "maxLength": 300},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_providers_health_check_action,
            expose_to_model=False,
        )
    )

    register_action(
        ActionSpec(
            name="ops_incident_snapshot",
            description="Gera snapshot operacional com saude de providers, flags, kill switch, autonomia, metrics e SLO.",
            params_schema={
                "type": "object",
                "properties": {
                    "include_ping": {"type": "boolean"},
                    "ping_prompt": {"type": "string", "minLength": 2, "maxLength": 300},
                    "metrics_limit": {"type": "integer", "minimum": 20, "maximum": 1200},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_ops_incident_snapshot_action,
            expose_to_model=False,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="ops_canary_status",
            description="Retorna o estado do canario para a sessao e um resumo por coorte (canary/stable).",
            params_schema={
                "type": "object",
                "properties": {
                    "metrics_limit": {"type": "integer", "minimum": 20, "maximum": 1200},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_ops_canary_status_action,
            expose_to_model=False,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="ops_canary_set",
            description="Controla canario por sessao (enroll/unenroll) e flag global canary_v1.",
            params_schema={
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": ["enroll", "unenroll", "enable_global", "disable_global"]},
                },
                "required": ["operation"],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_ops_canary_set_action,
            expose_to_model=False,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="ops_canary_rollout_set",
            description="Ajusta rollout progressivo do canario (set_percent/step_up/step_down/pause/resume).",
            params_schema={
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": ["set_percent", "step_up", "step_down", "pause", "resume"]},
                    "percent": {"type": "integer", "minimum": 0, "maximum": 100},
                    "dry_run": {"type": "boolean"},
                },
                "required": ["operation"],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_ops_canary_rollout_set_action,
            expose_to_model=False,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="ops_canary_promote",
            description="Avalia gates de canario e promove rollout para o proximo estagio quando aprovado.",
            params_schema={
                "type": "object",
                "properties": {
                    "dry_run": {"type": "boolean"},
                    "force": {"type": "boolean"},
                    "step_if_passed": {"type": "boolean"},
                    "rollback_on_fail": {"type": "boolean"},
                    "min_samples": {"type": "integer", "minimum": 5, "maximum": 200},
                    "success_rate_min": {"type": "number", "minimum": 0.5, "maximum": 1.0},
                    "max_regression_vs_stable": {"type": "number", "minimum": 0.0, "maximum": 0.4},
                    "require_no_alerts": {"type": "boolean"},
                    "metrics_limit": {"type": "integer", "minimum": 20, "maximum": 1200},
                    "cooldown_seconds": {"type": "integer", "minimum": 30, "maximum": 7200},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_ops_canary_promote_action,
            expose_to_model=False,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="ops_apply_playbook",
            description="Aplica playbook operacional para degradacao controlada, guardrails estritos ou bloqueio de dominio.",
            params_schema={
                "type": "object",
                "properties": {
                    "playbook": {
                        "type": "string",
                        "enum": [
                            "provider_degradation",
                            "strict_guardrails",
                            "block_domain",
                            "unblock_domain",
                            "restore_runtime_overrides",
                        ],
                    },
                    "domain": {"type": "string", "minLength": 2, "maxLength": 80},
                    "reason": {"type": "string", "minLength": 2, "maxLength": 240},
                    "dry_run": {"type": "boolean"},
                },
                "required": ["playbook"],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_ops_apply_playbook_action,
            expose_to_model=False,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="ops_control_loop_tick",
            description="Executa um tick de operacao: diagnostico, auto-remediacao e promocao de canario.",
            params_schema={
                "type": "object",
                "properties": {
                    "dry_run": {"type": "boolean"},
                    "auto_remediate": {"type": "boolean"},
                    "auto_promote_canary": {"type": "boolean"},
                    "force_remediation": {"type": "boolean"},
                    "force_promotion": {"type": "boolean"},
                    "domain": {"type": "string", "minLength": 2, "maxLength": 80},
                    "metrics_limit": {"type": "integer", "minimum": 20, "maximum": 1200},
                    "freeze_threshold": {"type": "integer", "minimum": 1, "maximum": 20},
                    "freeze_window_seconds": {"type": "integer", "minimum": 60, "maximum": 86400},
                    "freeze_cooldown_seconds": {"type": "integer", "minimum": 60, "maximum": 86400},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_ops_control_loop_tick_action,
            expose_to_model=False,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="ops_auto_remediate",
            description="Avalia sinais de SLO e dispara rollback automatico por cenario com cooldown.",
            params_schema={
                "type": "object",
                "properties": {
                    "dry_run": {"type": "boolean"},
                    "force": {"type": "boolean"},
                    "domain": {"type": "string", "minLength": 2, "maxLength": 80},
                    "metrics_limit": {"type": "integer", "minimum": 20, "maximum": 1200},
                    "cooldown_seconds": {"type": "integer", "minimum": 30, "maximum": 3600},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_ops_auto_remediate_action,
            expose_to_model=False,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="ops_rollback_scenario",
            description="Executa rollback one-click por cenario operacional (provider_outage, latency_spike, reliability_breach, trust_drift_breach, recover_to_stable).",
            params_schema={
                "type": "object",
                "properties": {
                    "scenario": {
                        "type": "string",
                        "enum": ["provider_outage", "latency_spike", "reliability_breach", "trust_drift_breach", "recover_to_stable"],
                    },
                    "domain": {"type": "string", "minLength": 2, "maxLength": 80},
                    "reason": {"type": "string", "minLength": 2, "maxLength": 240},
                    "dry_run": {"type": "boolean"},
                },
                "required": ["scenario"],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_ops_rollback_scenario_action,
            expose_to_model=False,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="ops_feature_flags_status",
            description="Retorna o estado atual das feature flags (env + overrides runtime).",
            params_schema={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_ops_feature_flags_status_action,
            expose_to_model=False,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="ops_feature_flags_set",
            description="Liga/desliga feature flag em runtime para fallback ou rollback imediato sem deploy.",
            params_schema={
                "type": "object",
                "properties": {
                    "feature": {"type": "string", "minLength": 2, "maxLength": 80},
                    "enabled": {"type": "boolean"},
                },
                "required": ["feature", "enabled"],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_ops_feature_flags_set_action,
            expose_to_model=False,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="code_read_file",
            description="Le um arquivo do projeto ativo ou de um projeto informado usando o code worker.",
            params_schema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "minLength": 4, "maxLength": 80},
                    "query": {"type": "string", "minLength": 1, "maxLength": 300},
                    "project": {"type": "string", "minLength": 1, "maxLength": 300},
                    "project_name": {"type": "string", "minLength": 1, "maxLength": 300},
                    "name": {"type": "string", "minLength": 1, "maxLength": 300},
                    "path": {"type": "string", "minLength": 1, "maxLength": 500},
                    "start_line": {"type": "integer", "minimum": 1, "maximum": 50000},
                    "end_line": {"type": "integer", "minimum": 1, "maximum": 50000},
                },
                "required": ["path"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_code_read_file_action,
            expose_to_model=False,
        )
    )

    register_action(
        ActionSpec(
            name="code_search_in_active_project",
            description="Busca no indice e nos arquivos do projeto ativo (ou informado).",
            params_schema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "minLength": 4, "maxLength": 80},
                    "query": {"type": "string", "minLength": 2, "maxLength": 300},
                    "project": {"type": "string", "minLength": 1, "maxLength": 300},
                    "project_name": {"type": "string", "minLength": 1, "maxLength": 300},
                    "name": {"type": "string", "minLength": 1, "maxLength": 300},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_code_search_in_active_project_action,
            expose_to_model=False,
        )
    )

    register_action(
        ActionSpec(
            name="code_explain_project",
            description="Explica o estado de um projeto com base no indice, arquivos lidos e adaptador OpenAI.",
            params_schema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "minLength": 4, "maxLength": 80},
                    "request": {"type": "string", "minLength": 2, "maxLength": 4000},
                    "query": {"type": "string", "minLength": 2, "maxLength": 4000},
                    "project": {"type": "string", "minLength": 1, "maxLength": 300},
                    "project_name": {"type": "string", "minLength": 1, "maxLength": 300},
                    "name": {"type": "string", "minLength": 1, "maxLength": 300},
                    "read_paths": {"type": "array"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 8},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_code_explain_project_action,
            expose_to_model=False,
        )
    )

    register_action(
        ActionSpec(
            name="code_git_status",
            description="Consulta o git status do projeto ativo (ou informado).",
            params_schema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "minLength": 4, "maxLength": 80},
                    "query": {"type": "string", "minLength": 1, "maxLength": 300},
                    "project": {"type": "string", "minLength": 1, "maxLength": 300},
                    "project_name": {"type": "string", "minLength": 1, "maxLength": 300},
                    "name": {"type": "string", "minLength": 1, "maxLength": 300},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_code_git_status_action,
            expose_to_model=False,
        )
    )

    register_action(
        ActionSpec(
            name="code_git_diff",
            description="Consulta o git diff do projeto ativo (ou informado).",
            params_schema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "minLength": 4, "maxLength": 80},
                    "query": {"type": "string", "minLength": 1, "maxLength": 300},
                    "project": {"type": "string", "minLength": 1, "maxLength": 300},
                    "project_name": {"type": "string", "minLength": 1, "maxLength": 300},
                    "name": {"type": "string", "minLength": 1, "maxLength": 300},
                    "paths": {"type": "array"},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_code_git_diff_action,
            expose_to_model=False,
        )
    )

    register_action(
        ActionSpec(
            name="code_propose_change",
            description="Monta uma proposta de mudanca usando contexto real do projeto e o adaptador OpenAI.",
            params_schema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "minLength": 4, "maxLength": 80},
                    "request": {"type": "string", "minLength": 2, "maxLength": 4000},
                    "query": {"type": "string", "minLength": 2, "maxLength": 4000},
                    "project": {"type": "string", "minLength": 1, "maxLength": 300},
                    "project_name": {"type": "string", "minLength": 1, "maxLength": 300},
                    "name": {"type": "string", "minLength": 1, "maxLength": 300},
                    "read_paths": {"type": "array"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 8},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_code_propose_change_action,
            expose_to_model=False,
        )
    )

    register_action(
        ActionSpec(
            name="code_apply_patch",
            description="Aplica um patch controlado em um ou mais arquivos do projeto ativo (ou informado).",
            params_schema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "minLength": 4, "maxLength": 80},
                    "query": {"type": "string", "minLength": 1, "maxLength": 300},
                    "project": {"type": "string", "minLength": 1, "maxLength": 300},
                    "project_name": {"type": "string", "minLength": 1, "maxLength": 300},
                    "name": {"type": "string", "minLength": 1, "maxLength": 300},
                    "changes": {"type": "array"},
                    "confirmation_summary": {"type": "string", "minLength": 8, "maxLength": 500},
                },
                "required": ["changes"],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_code_apply_patch_action,
            requires_auth=True,
            expose_to_model=False,
        )
    )

    register_action(
        ActionSpec(
            name="code_run_command",
            description="Executa um comando allowlisted no projeto ativo (ou informado) via code worker.",
            params_schema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "minLength": 4, "maxLength": 80},
                    "query": {"type": "string", "minLength": 1, "maxLength": 300},
                    "project": {"type": "string", "minLength": 1, "maxLength": 300},
                    "project_name": {"type": "string", "minLength": 1, "maxLength": 300},
                    "name": {"type": "string", "minLength": 1, "maxLength": 300},
                    "command": {"type": "string", "minLength": 1, "maxLength": 120},
                    "arguments": {"type": "array"},
                    "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 600},
                    "confirmation_summary": {"type": "string", "minLength": 8, "maxLength": 500},
                },
                "required": ["command"],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_code_run_command_action,
            requires_auth=True,
            expose_to_model=False,
        )
    )

    register_action(
        ActionSpec(
            name="web_search_dashboard",
            description=(
                "Pesquisa na web, coleta os principais links publicos e devolve um dashboard estruturado "
                "com resumo, sites e imagens de referencia."
            ),
            params_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "minLength": 2, "maxLength": 300},
                    "max_results": {"type": "integer", "minimum": 3, "maximum": 8},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_web_search_dashboard,
        )
    )

    register_action(
        ActionSpec(
            name="save_web_briefing_schedule",
            description=(
                "Salva uma rotina de briefing diario para o frontend disparar uma pesquisa web automatica "
                "em horario fixo durante a sessao."
            ),
            params_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "minLength": 2, "maxLength": 300},
                    "time_of_day": {"type": "string", "minLength": 5, "maxLength": 5},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_save_web_briefing_schedule,
        )
    )

    register_action(
        ActionSpec(
            name="open_desktop_resource",
            description=(
                "Abre um site, pasta, arquivo ou aplicativo local no computador. "
                "Aceita URL, caminho, alias de pasta (desktop, downloads, documents, repo) "
                "ou alias de app (chrome, edge, firefox, explorer, vscode, terminal, cmd)."
            ),
            params_schema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "minLength": 1, "maxLength": 512},
                    "target_kind": {"type": "string", "enum": ["auto", "url", "path", "app"]},
                },
                "required": ["target"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_open_desktop_resource,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="run_local_command",
            description=(
                "Executa um comando local permitido por allowlist (ex.: git, python, node, pnpm, code). "
                "Use para tarefas tecnicas no PC quando houver confirmacao explicita."
            ),
            params_schema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "minLength": 1, "maxLength": 260},
                    "arguments": {"type": "array"},
                    "working_directory": {"type": "string", "minLength": 1, "maxLength": 512},
                    "wait_for_exit": {"type": "boolean"},
                    "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 600},
                },
                "required": ["command"],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_run_local_command,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="git_clone_repository",
            description="Executa `git clone` para clonar um repositorio em uma pasta local opcional.",
            params_schema={
                "type": "object",
                "properties": {
                    "repository_url": {"type": "string", "minLength": 8, "maxLength": 500},
                    "destination": {"type": "string", "minLength": 1, "maxLength": 512},
                    "branch": {"type": "string", "minLength": 1, "maxLength": 120},
                    "depth": {"type": "integer", "minimum": 1, "maximum": 1000},
                },
                "required": ["repository_url"],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_git_clone_repository,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="git_commit_and_push_project",
            description="Faz git add, cria um commit e executa git push no projeto ativo (ou informado).",
            params_schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "minLength": 3, "maxLength": 240},
                    "commit_message": {"type": "string", "minLength": 3, "maxLength": 240},
                    "summary": {"type": "string", "minLength": 3, "maxLength": 240},
                    "project_id": {"type": "string", "minLength": 4, "maxLength": 80},
                    "query": {"type": "string", "minLength": 1, "maxLength": 300},
                    "project_query": {"type": "string", "minLength": 1, "maxLength": 300},
                    "fuzzy_query": {"type": "string", "minLength": 1, "maxLength": 300},
                    "project": {"type": "string", "minLength": 1, "maxLength": 300},
                    "project_name": {"type": "string", "minLength": 1, "maxLength": 300},
                    "name": {"type": "string", "minLength": 1, "maxLength": 300},
                    "confirmation_summary": {"type": "string", "minLength": 8, "maxLength": 500},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_git_commit_and_push_project_action,
            requires_auth=True,
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
                    "class": {"type": "string", "minLength": 1, "maxLength": 120},
                    "character_class": {"type": "string", "minLength": 1, "maxLength": 120},
                    "origin": {"type": "string", "minLength": 1, "maxLength": 120},
                    "level": {"type": "integer", "minimum": 1, "maximum": 20},
                    "concept": {"type": "string", "minLength": 1, "maxLength": 400},
                    "attributes": {"type": "object"},
                    "build_choices": {"type": "object"},
                    "generation_mode": {"type": "string", "enum": ["auto", "strict"]},
                    "prefer_engine": {"type": "string", "enum": ["t20", "fallback", "auto"]},
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
                    "attacks_override": {"type": "array"},
                    "abilities_override": {"type": "array"},
                    "spells_override": {"type": "array"},
                    "special_qualities": {"type": "string", "minLength": 1, "maxLength": 1200},
                    "equipment": {"type": "string", "minLength": 1, "maxLength": 1200},
                    "treasure_level": {"type": "string", "minLength": 1, "maxLength": 80},
                    "generation_mode": {"type": "string", "enum": ["suggested", "structured"]},
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
            name="thinq_status",
            description="Verifica configuracao da API LG ThinQ e testa acesso basico a dispositivos.",
            params_schema={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_thinq_status,
        )
    )

    register_action(
        ActionSpec(
            name="thinq_list_devices",
            description="Lista dispositivos cadastrados na sua conta LG ThinQ.",
            params_schema={
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_thinq_list_devices,
        )
    )

    register_action(
        ActionSpec(
            name="thinq_get_device_profile",
            description="Busca o perfil de um dispositivo ThinQ. Use primeiro para descobrir quais comandos o aparelho aceita.",
            params_schema={
                "type": "object",
                "properties": {
                    "device_name": {"type": "string", "minLength": 2, "maxLength": 128},
                    "device_id": {"type": "string", "minLength": 8, "maxLength": 256},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_thinq_get_device_profile,
        )
    )

    register_action(
        ActionSpec(
            name="thinq_get_device_state",
            description="Consulta o estado atual de um dispositivo ThinQ.",
            params_schema={
                "type": "object",
                "properties": {
                    "device_name": {"type": "string", "minLength": 2, "maxLength": 128},
                    "device_id": {"type": "string", "minLength": 8, "maxLength": 256},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_thinq_get_device_state,
        )
    )

    register_action(
        ActionSpec(
            name="thinq_control_device",
            description="Envia um comando bruto para um dispositivo ThinQ. Use apenas com payload derivado do perfil do dispositivo.",
            params_schema={
                "type": "object",
                "properties": {
                    "device_name": {"type": "string", "minLength": 2, "maxLength": 128},
                    "device_id": {"type": "string", "minLength": 8, "maxLength": 256},
                    "conditional": {"type": "boolean"},
                    "command": {"type": "object"},
                },
                "required": ["command"],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_thinq_control_device,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="ac_get_status",
            description="Consulta o estado do seu ar-condicionado LG ThinQ. Se houver um unico ar visivel, resolve automaticamente.",
            params_schema={
                "type": "object",
                "properties": {
                    "device_name": {"type": "string", "minLength": 2, "maxLength": 128},
                    "device_id": {"type": "string", "minLength": 8, "maxLength": 256},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_ac_get_status,
        )
    )

    register_action(
        ActionSpec(
            name="ac_send_command",
            description="Envia um comando bruto para o ar-condicionado LG ThinQ usando o payload exato do perfil do aparelho.",
            params_schema={
                "type": "object",
                "properties": {
                    "device_name": {"type": "string", "minLength": 2, "maxLength": 128},
                    "device_id": {"type": "string", "minLength": 8, "maxLength": 256},
                    "conditional": {"type": "boolean"},
                    "command": {"type": "object"},
                },
                "required": ["command"],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_ac_send_command,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="ac_turn_on",
            description="Liga o ar-condicionado LG ThinQ.",
            params_schema={
                "type": "object",
                "properties": {
                    "device_name": {"type": "string", "minLength": 2, "maxLength": 128},
                    "device_id": {"type": "string", "minLength": 8, "maxLength": 256},
                    "conditional": {"type": "boolean"},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_ac_turn_on,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="ac_turn_off",
            description="Desliga o ar-condicionado LG ThinQ.",
            params_schema={
                "type": "object",
                "properties": {
                    "device_name": {"type": "string", "minLength": 2, "maxLength": 128},
                    "device_id": {"type": "string", "minLength": 8, "maxLength": 256},
                    "conditional": {"type": "boolean"},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_ac_turn_off,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="ac_set_temperature",
            description="Ajusta a temperatura alvo do ar-condicionado LG ThinQ.",
            params_schema={
                "type": "object",
                "properties": {
                    "device_name": {"type": "string", "minLength": 2, "maxLength": 128},
                    "device_id": {"type": "string", "minLength": 8, "maxLength": 256},
                    "temperature": {"type": "number", "minimum": 16, "maximum": 30},
                    "unit": {"type": "string", "minLength": 1, "maxLength": 2},
                    "conditional": {"type": "boolean"},
                },
                "required": ["temperature"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_ac_set_temperature,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="ac_set_mode",
            description="Ajusta o modo do ar-condicionado LG ThinQ (AUTO, AIR_DRY, HEAT, FAN, COOL).",
            params_schema={
                "type": "object",
                "properties": {
                    "device_name": {"type": "string", "minLength": 2, "maxLength": 128},
                    "device_id": {"type": "string", "minLength": 8, "maxLength": 256},
                    "mode": {"type": "string", "minLength": 2, "maxLength": 32},
                    "conditional": {"type": "boolean"},
                },
                "required": ["mode"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_ac_set_mode,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="ac_set_fan_speed",
            description="Ajusta a ventilacao do ar-condicionado LG ThinQ (AUTO, LOW, MID, HIGH e variantes).",
            params_schema={
                "type": "object",
                "properties": {
                    "device_name": {"type": "string", "minLength": 2, "maxLength": 128},
                    "device_id": {"type": "string", "minLength": 8, "maxLength": 256},
                    "fan_speed": {"type": "string", "minLength": 2, "maxLength": 32},
                    "detail": {"type": "boolean"},
                    "conditional": {"type": "boolean"},
                },
                "required": ["fan_speed"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_ac_set_fan_speed,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="ac_set_swing",
            description="Liga ou desliga a oscilacao vertical do ar-condicionado LG ThinQ.",
            params_schema={
                "type": "object",
                "properties": {
                    "device_name": {"type": "string", "minLength": 2, "maxLength": 128},
                    "device_id": {"type": "string", "minLength": 8, "maxLength": 256},
                    "enabled": {"type": "boolean"},
                    "conditional": {"type": "boolean"},
                },
                "required": ["enabled"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_ac_set_swing,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="ac_set_sleep_timer",
            description="Programa o desligamento do ar em X horas e minutos. Use 0 para remover o timer.",
            params_schema={
                "type": "object",
                "properties": {
                    "device_name": {"type": "string", "minLength": 2, "maxLength": 128},
                    "device_id": {"type": "string", "minLength": 8, "maxLength": 256},
                    "hours": {"type": "integer", "minimum": 0, "maximum": 23},
                    "minutes": {"type": "integer", "minimum": 0, "maximum": 59},
                    "conditional": {"type": "boolean"},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_ac_set_sleep_timer,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="ac_set_start_timer",
            description="Programa o ligamento do ar em X horas e minutos. Use 0 para remover o timer de inicio.",
            params_schema={
                "type": "object",
                "properties": {
                    "device_name": {"type": "string", "minLength": 2, "maxLength": 128},
                    "device_id": {"type": "string", "minLength": 8, "maxLength": 256},
                    "hours": {"type": "integer", "minimum": 0, "maximum": 23},
                    "minutes": {"type": "integer", "minimum": 0, "maximum": 59},
                    "conditional": {"type": "boolean"},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_ac_set_start_timer,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="ac_set_power_save",
            description="Liga ou desliga o modo economia de energia do ar-condicionado LG ThinQ.",
            params_schema={
                "type": "object",
                "properties": {
                    "device_name": {"type": "string", "minLength": 2, "maxLength": 128},
                    "device_id": {"type": "string", "minLength": 8, "maxLength": 256},
                    "enabled": {"type": "boolean"},
                    "conditional": {"type": "boolean"},
                },
                "required": ["enabled"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_ac_set_power_save,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="ac_apply_preset",
            description="Aplica um preset do ar. Presets atuais: 'modo dormir', 'gelar sala', 'modo visita', 'economia' e 'ventilar leve'.",
            params_schema={
                "type": "object",
                "properties": {
                    "device_name": {"type": "string", "minLength": 2, "maxLength": 128},
                    "device_id": {"type": "string", "minLength": 8, "maxLength": 256},
                    "preset": {"type": "string", "minLength": 2, "maxLength": 64},
                    "conditional": {"type": "boolean"},
                },
                "required": ["preset"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_ac_apply_preset,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="ac_configure_arrival_prefs",
            description="Salva preferencias de chegada em casa para o ar: temperatura desejada, limites de calor e se deve oscilar.",
            params_schema={
                "type": "object",
                "properties": {
                    "device_name": {"type": "string", "minLength": 2, "maxLength": 128},
                    "desired_temperature": {"type": "number", "minimum": 16, "maximum": 30},
                    "hot_threshold": {"type": "number", "minimum": 18, "maximum": 40},
                    "vent_only_threshold": {"type": "number", "minimum": 16, "maximum": 40},
                    "eta_minutes": {"type": "integer", "minimum": 0, "maximum": 240},
                    "enable_swing": {"type": "boolean"},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_ac_configure_arrival_prefs,
        )
    )

    register_action(
        ActionSpec(
            name="ac_prepare_arrival",
            description="Lê a temperatura atual do ambiente e decide se deve resfriar, só ventilar ou não mexer no ar quando voce estiver chegando em casa.",
            params_schema={
                "type": "object",
                "properties": {
                    "device_name": {"type": "string", "minLength": 2, "maxLength": 128},
                    "device_id": {"type": "string", "minLength": 8, "maxLength": 256},
                    "desired_temperature": {"type": "number", "minimum": 16, "maximum": 30},
                    "hot_threshold": {"type": "number", "minimum": 18, "maximum": 40},
                    "vent_only_threshold": {"type": "number", "minimum": 16, "maximum": 40},
                    "eta_minutes": {"type": "integer", "minimum": 0, "maximum": 240},
                    "enable_swing": {"type": "boolean"},
                    "dry_run": {"type": "boolean"},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_ac_prepare_arrival,
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
            description="Troca o speaker ativo do Spotify para um device especifico. Use apenas quando o usuario quiser so mudar o device, sem pedir musica/artista/playlist.",
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
            requires_auth=False,
        )
    )

    register_action(
        ActionSpec(
            name="spotify_play",
            description="Toca musica no Spotify por busca textual (query) ou URI; pode escolher speaker. Se o usuario citou musica, artista, album ou playlist, inclua query ou uri junto com device_name/device_id.",
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
            requires_auth=False,
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
            requires_auth=False,
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
            requires_auth=False,
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
            requires_auth=False,
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
            requires_auth=False,
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
            name="whatsapp_channel_status",
            description="Mostra o status do canal WhatsApp (MCP bidirecional e fallback legado).",
            params_schema={"type": "object", "properties": {}, "additionalProperties": False},
            requires_confirmation=False,
            handler=_whatsapp_channel_status,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="browser_agent_run",
            description="Executa uma tarefa de browser automation com allowed_domains e modo read_only definidos.",
            params_schema={
                "type": "object",
                "properties": {
                    "request": {"type": "string", "minLength": 3, "maxLength": 2000},
                    "allowed_domains": {
                        "type": "array",
                        "items": {"type": "string", "minLength": 3, "maxLength": 255},
                        "minItems": 1,
                        "maxItems": 20,
                    },
                    "read_only": {"type": "boolean"},
                },
                "required": ["request", "allowed_domains"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_browser_agent_run,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="browser_agent_status",
            description="Retorna o status mais recente do browser agent.",
            params_schema={"type": "object", "properties": {}, "additionalProperties": False},
            requires_confirmation=False,
            handler=_browser_agent_status,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="browser_agent_cancel",
            description="Cancela a tarefa ativa do browser agent.",
            params_schema={"type": "object", "properties": {}, "additionalProperties": False},
            requires_confirmation=True,
            handler=_browser_agent_cancel,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="workflow_run",
            description="Cria um workflow ideia para codigo com checkpoint antes de aplicar mudancas.",
            params_schema={
                "type": "object",
                "properties": {
                    "request": {"type": "string", "minLength": 3, "maxLength": 4000},
                },
                "required": ["request"],
                "additionalProperties": False,
            },
            requires_confirmation=False,
            handler=_workflow_run,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="workflow_status",
            description="Retorna o status do workflow atual.",
            params_schema={"type": "object", "properties": {}, "additionalProperties": False},
            requires_confirmation=False,
            handler=_workflow_status,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="workflow_cancel",
            description="Cancela o workflow atual.",
            params_schema={"type": "object", "properties": {}, "additionalProperties": False},
            requires_confirmation=True,
            handler=_workflow_cancel,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="automation_status",
            description="Retorna o estado resumido das automacoes persistidas.",
            params_schema={"type": "object", "properties": {}, "additionalProperties": False},
            requires_confirmation=False,
            handler=_automation_status,
            requires_auth=True,
        )
    )

    register_action(
        ActionSpec(
            name="automation_run_now",
            description="Dispara uma automacao de forma manual e controlada.",
            params_schema={
                "type": "object",
                "properties": {
                    "automation_type": {"type": "string", "minLength": 2, "maxLength": 120},
                    "dry_run": {"type": "boolean"},
                },
                "required": [],
                "additionalProperties": False,
            },
            requires_confirmation=True,
            handler=_automation_run_now,
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
