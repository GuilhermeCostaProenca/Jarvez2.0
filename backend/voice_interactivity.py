from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


VOICE_INTERACTIVITY_NAMESPACE = "voice_interactivity"
VOICE_INTERACTIVITY_EVENT_TYPE = "voice_interactivity_state"
VOICE_INTERACTIVITY_STATES = {
    "idle",
    "listening",
    "transcribing",
    "thinking",
    "confirming",
    "executing",
    "background",
    "speaking",
    "error",
}
VOICE_ACTIVATION_MODES = {
    "button",
    "wake_word",
    "voice",
    "system",
    "unknown",
}

_LATENT_ACTION_PREFIXES = (
    "spotify_",
    "onenote_",
    "whatsapp_",
    "thinq_",
    "ac_",
    "rpg_",
    "workflow_",
    "codex_",
    "browser_agent_",
    "research_",
)
_LATENT_ACTION_NAMES = {
    "open_desktop_resource",
    "run_local_command",
    "git_clone_repository",
    "call_service",
    "turn_light_on",
    "turn_light_off",
    "set_light_brightness",
    "web_search_dashboard",
    "project_scan",
    "project_refresh_index",
    "github_clone_and_register",
}
_BACKGROUND_ACTION_PREFIXES = ("workflow_", "codex_", "browser_agent_", "research_")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_voice_state(value: Any, *, default: str = "idle") -> str:
    text = str(value or "").strip().lower()
    if text in VOICE_INTERACTIVITY_STATES:
        return text
    return default


def normalize_activation_mode(value: Any, *, default: str = "unknown") -> str:
    text = str(value or "").strip().lower()
    if text in VOICE_ACTIVATION_MODES:
        return text
    return default


def build_voice_interactivity_payload(
    *,
    state: str,
    source: str,
    activation_mode: str | None = None,
    raw_client_state: str | None = None,
    display_message: str | None = None,
    spoken_message: str | None = None,
    action_name: str | None = None,
    trace_id: str | None = None,
    error_code: str | None = None,
    can_retry: bool | None = None,
    extra: dict[str, Any] | None = None,
    updated_at: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "state": normalize_voice_state(state),
        "source": str(source or "backend").strip().lower() or "backend",
        "updated_at": updated_at or _now_iso(),
    }
    normalized_activation_mode = normalize_activation_mode(activation_mode) if activation_mode else None
    if normalized_activation_mode is not None:
        payload["activation_mode"] = normalized_activation_mode
    if raw_client_state:
        payload["raw_client_state"] = str(raw_client_state).strip()
    if display_message:
        payload["display_message"] = str(display_message).strip()
    if spoken_message:
        payload["spoken_message"] = str(spoken_message).strip()
    if action_name:
        payload["action_name"] = str(action_name).strip()
    if trace_id:
        payload["trace_id"] = str(trace_id).strip()
    if error_code:
        payload["error_code"] = str(error_code).strip()
    if can_retry is not None:
        payload["can_retry"] = bool(can_retry)
    if extra:
        payload.update(extra)
    return payload


def is_latency_sensitive_action(action_name: str) -> bool:
    normalized = str(action_name or "").strip().lower()
    if not normalized:
        return False
    if normalized in _LATENT_ACTION_NAMES:
        return True
    if normalized.startswith(_LATENT_ACTION_PREFIXES):
        return True
    if "search" in normalized or "scan" in normalized or "clone" in normalized:
        return True
    return False


def build_action_preamble(action_name: str, params: dict[str, Any] | None = None) -> str | None:
    normalized = str(action_name or "").strip().lower()
    if not is_latency_sensitive_action(normalized):
        return None

    if normalized in {"open_desktop_resource", "github_clone_and_register", "git_clone_repository"}:
        return "Abrindo."
    if "search" in normalized or normalized.startswith(("web_search_", "research_", "rpg_search_")):
        return "Procurando."
    if normalized.startswith(("project_scan", "browser_agent_", "workflow_", "codex_")):
        return "Deixa comigo."
    if normalized.startswith(("spotify_", "onenote_", "whatsapp_", "thinq_", "ac_")):
        return "Deixa comigo."
    return "Processando."


def is_background_candidate(action_name: str, result_data: dict[str, Any] | None) -> bool:
    normalized = str(action_name or "").strip().lower()
    if normalized.startswith(_BACKGROUND_ACTION_PREFIXES):
        return True
    if not isinstance(result_data, dict):
        return False
    workflow_state = result_data.get("workflow_state")
    if isinstance(workflow_state, dict) and str(workflow_state.get("status") or "").strip().lower() in {
        "planning",
        "awaiting_confirmation",
        "running",
    }:
        return True
    browser_task = result_data.get("browser_task")
    if isinstance(browser_task, dict) and str(browser_task.get("status") or "").strip().lower() in {
        "running",
    }:
        return True
    codex_task = result_data.get("codex_task")
    if isinstance(codex_task, dict) and str(codex_task.get("status") or "").strip().lower() in {
        "running",
    }:
        return True
    return False


def build_voice_error_message(action_name: str, message: str | None, error: str | None) -> str:
    normalized = str(action_name or "").strip().lower()
    message_text = str(message or "").strip()
    error_text = str(error or "").strip().lower()

    if "auth" in error_text or "autentic" in message_text.lower():
        return "Nao consegui agora porque ainda falta autenticacao. Quer tentar de novo depois de conectar?"
    if "missing" in error_text or "not configured" in error_text or "nao configurado" in message_text.lower():
        return "Nao consegui concluir porque essa integracao ainda nao esta configurada. Quer que eu tente de novo depois?"
    if normalized.startswith(("open_desktop_resource", "run_local_command", "git_clone_repository")):
        return "Nao consegui abrir ou executar isso agora. Quer que eu tente de novo?"
    if normalized.startswith(("spotify_", "onenote_", "whatsapp_", "thinq_", "ac_")):
        return "Nao consegui concluir essa acao agora. Quer que eu tente de novo?"
    return "Nao consegui concluir isso agora. Quer tentar de novo ou prefere outra abordagem?"
