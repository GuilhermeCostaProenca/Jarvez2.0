from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from actions_core.store import JarvezStateStore, get_state_store
from memory import MemoryManager

PROACTIVITY_NAMESPACE = "proactivity_state"
PROACTIVITY_EVENT_TYPE = "proactivity_state"
PROACTIVITY_INTENSITIES = {"silent", "moderate", "active"}
DEFAULT_INTENSITY = str(os.getenv("JARVEZ_PROACTIVITY_INTENSITY", "moderate")).strip().lower() or "moderate"
DEFAULT_COOLDOWN_SECONDS = max(60, int(os.getenv("JARVEZ_PROACTIVITY_COOLDOWN_SECONDS", "1800")))

LOW_RISK_PARALLEL_ACTIONS = {
    "automation_run_now",
}
LIGHT_ACTIONS = {"turn_light_on", "turn_light_off", "set_light_brightness", "call_service"}
AC_ACTIONS = {"ac_get_status", "ac_turn_on", "ac_turn_off", "ac_set_mode", "ac_set_temperature"}
SPOTIFY_DEVICE_ACTIONS = {"spotify_transfer_playback"}
WHATSAPP_ACTIONS = {"whatsapp_send_text"}


class _NoOpMem0:
    async def get_all(self, **_kwargs: Any) -> list[dict[str, Any]]:
        return []

    async def search(self, *_args: Any, **_kwargs: Any) -> list[dict[str, Any]]:
        return []

    async def add(self, *_args: Any, **_kwargs: Any) -> None:
        return None


class SuggestionEngine:
    def __init__(
        self,
        *,
        state_store: JarvezStateStore | None = None,
        memory_manager: MemoryManager | None = None,
        default_cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS,
    ) -> None:
        self.state_store = state_store or get_state_store()
        self.memory_manager = memory_manager or MemoryManager(mem0=_NoOpMem0(), state_store=self.state_store)
        self.default_cooldown_seconds = max(60, int(default_cooldown_seconds))

    def set_intensity(self, *, participant_identity: str, intensity: str) -> str:
        normalized = self._normalize_intensity(intensity)
        self.memory_manager.set_preference(
            participant_identity=participant_identity,
            key="proactivity_intensity",
            value=normalized,
        )
        return normalized

    def set_silent_until(self, *, participant_identity: str, until: datetime | None) -> str | None:
        value = self._to_iso(until) if until is not None else None
        self.memory_manager.set_preference(
            participant_identity=participant_identity,
            key="proactivity_silent_until",
            value=value,
        )
        return value

    def load_controls(self, *, participant_identity: str, now: datetime | None = None) -> dict[str, Any]:
        current = self._utc_now(now)
        intensity = self._normalize_intensity(
            self.memory_manager.get_preference(participant_identity=participant_identity, key="proactivity_intensity")
        )
        silent_until_raw = self.memory_manager.get_preference(
            participant_identity=participant_identity,
            key="proactivity_silent_until",
        )
        silent_until = self._parse_iso(silent_until_raw)
        cooldown_seconds = self._normalize_cooldown(
            self.memory_manager.get_preference(participant_identity=participant_identity, key="proactivity_cooldown_seconds")
        )
        return {
            "intensity": intensity,
            "silent_until": self._to_iso(silent_until) if silent_until is not None else None,
            "silent_active": bool(silent_until and silent_until > current) or intensity == "silent",
            "cooldown_seconds": cooldown_seconds,
            "reason_visible": True,
        }

    def evaluate(
        self,
        *,
        participant_identity: str,
        room: str,
        now: datetime | None = None,
        frontend_state: dict[str, Any] | None = None,
        automation_state: dict[str, Any] | None = None,
        persist: bool = True,
    ) -> dict[str, Any]:
        current = self._utc_now(now)
        controls = self.load_controls(participant_identity=participant_identity, now=current)
        state = self._load_state(participant_identity=participant_identity, room=room)
        if automation_state is None:
            loaded = self.state_store.get_event_state(
                participant_identity=participant_identity,
                room=room,
                namespace="automation_state",
            )
            automation_state = loaded if isinstance(loaded, dict) else None
        research_schedules = self.state_store.get_event_state(
            participant_identity=participant_identity,
            room=room,
            namespace="research_schedules",
        )
        recent_turns = self.memory_manager.get_recent_turns(
            participant_identity=participant_identity,
            room=room,
            limit=4,
        )
        preferences = self.memory_manager.list_preferences(participant_identity=participant_identity)
        status = "idle"
        suggestions: list[dict[str, Any]] = []

        if controls["silent_active"]:
            status = "silent"
        else:
            candidates = self._build_candidates(
                participant_identity=participant_identity,
                room=room,
                now=current,
                frontend_state=frontend_state or {},
                automation_state=automation_state,
                research_schedules=research_schedules,
                preferences=preferences,
                recent_turns=recent_turns,
                controls=controls,
            )
            recent_map = dict(state.get("last_suggestion_by_kind") or {})
            blocked = 0
            for candidate in candidates:
                cooldown_key = str(candidate.get("cooldown_key") or candidate.get("kind") or "").strip()
                if not cooldown_key:
                    continue
                last_at = self._parse_iso(recent_map.get(cooldown_key))
                if last_at is not None and (current - last_at).total_seconds() < controls["cooldown_seconds"]:
                    blocked += 1
                    continue
                candidate["id"] = f"pro_{uuid.uuid4().hex[:10]}"
                candidate["created_at"] = self._to_iso(current)
                suggestions.append(candidate)
                recent_map[cooldown_key] = self._to_iso(current)
            if suggestions:
                status = "suggested"
            elif blocked:
                status = "cooldown"
            state["last_suggestion_by_kind"] = recent_map

        payload = {
            "status": status,
            "updated_at": self._to_iso(current),
            "controls": controls,
            "suggestions": suggestions[:3],
            "recent_context": {
                "recent_turns_count": len(recent_turns),
                "frontend_context": frontend_state if isinstance(frontend_state, dict) else None,
                "automation_status": str((automation_state or {}).get("status") or "").strip() or None,
            },
            "last_suggestion_by_kind": dict(state.get("last_suggestion_by_kind") or {}),
        }
        if persist:
            self.state_store.upsert_event_state(
                participant_identity=participant_identity,
                room=room,
                namespace=PROACTIVITY_NAMESPACE,
                payload=payload,
            )
        return payload

    def build_clarification(
        self,
        *,
        participant_identity: str,
        room: str,
        action_name: str,
        params: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        normalized_action = str(action_name or "").strip().lower()
        payload = dict(params or {})
        preferences = self.memory_manager.list_preferences(participant_identity=participant_identity)
        preferred_devices = preferences.get("preferred_devices")
        candidates = self._candidate_names_for_action(normalized_action, preferred_devices)
        if len(candidates) < 2:
            return None

        if normalized_action in LIGHT_ACTIONS and str(payload.get("entity_id") or "").strip():
            return None
        if normalized_action in AC_ACTIONS and str(payload.get("device_name") or "").strip():
            return None
        if normalized_action in SPOTIFY_DEVICE_ACTIONS and str(payload.get("device_id") or "").strip():
            return None
        if normalized_action in WHATSAPP_ACTIONS and str(payload.get("phone_number") or payload.get("to") or "").strip():
            return None

        if normalized_action in LIGHT_ACTIONS:
            target_label = "luz"
        elif normalized_action in AC_ACTIONS:
            target_label = "ar-condicionado"
        elif normalized_action in SPOTIFY_DEVICE_ACTIONS:
            target_label = "device do Spotify"
        elif normalized_action in WHATSAPP_ACTIONS:
            target_label = "contato do WhatsApp"
        else:
            target_label = "alvo"

        question = f"Encontrei mais de um {target_label} plausivel. Qual deles voce quer usar?"
        clarification = {
            "status": "clarifying",
            "action_name": normalized_action,
            "question": question,
            "options": candidates[:4],
            "reason": f"Existem multiplos alvos plausiveis para {normalized_action}.",
            "updated_at": self._to_iso(),
        }
        self.state_store.upsert_event_state(
            participant_identity=participant_identity,
            room=room,
            namespace=PROACTIVITY_NAMESPACE,
            payload={
                "status": "clarifying",
                "updated_at": clarification["updated_at"],
                "controls": self.load_controls(participant_identity=participant_identity),
                "suggestions": [],
                "clarification": clarification,
                "last_suggestion_by_kind": (self._load_state(participant_identity=participant_identity, room=room)).get(
                    "last_suggestion_by_kind",
                    {},
                ),
            },
        )
        return clarification

    def mark_parallel_execution(
        self,
        *,
        participant_identity: str,
        room: str,
        suggestion_kind: str,
        message: str,
    ) -> dict[str, Any]:
        state = self._load_state(participant_identity=participant_identity, room=room)
        payload = {
            "status": "background",
            "updated_at": self._to_iso(),
            "controls": self.load_controls(participant_identity=participant_identity),
            "suggestions": [],
            "background_execution": {
                "kind": suggestion_kind,
                "message": message,
                "updated_at": self._to_iso(),
            },
            "last_suggestion_by_kind": dict(state.get("last_suggestion_by_kind") or {}),
        }
        self.state_store.upsert_event_state(
            participant_identity=participant_identity,
            room=room,
            namespace=PROACTIVITY_NAMESPACE,
            payload=payload,
        )
        return payload

    def _build_candidates(
        self,
        *,
        participant_identity: str,
        room: str,
        now: datetime,
        frontend_state: dict[str, Any],
        automation_state: dict[str, Any] | None,
        research_schedules: Any,
        preferences: dict[str, Any],
        recent_turns: list[dict[str, Any]],
        controls: dict[str, Any],
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        hour = now.astimezone(timezone.utc).hour
        context = str(frontend_state.get("context") or "").strip().lower()
        favorite_apps = self._normalize_text_list(preferences.get("favorite_apps"))
        recurring = self._normalize_text_list(preferences.get("routine_recurring"))
        preferred_devices = preferences.get("preferred_devices")

        has_briefing_schedule = isinstance(research_schedules, list) and len(research_schedules) > 0
        wants_briefing = has_briefing_schedule or any("brief" in item for item in recurring)
        if 6 <= hour <= 11 and wants_briefing:
            auto_execute = controls["intensity"] == "active"
            candidates.append(
                {
                    "kind": "daily_briefing",
                    "title": "Briefing matinal",
                    "message": (
                        "Posso preparar seu briefing matinal; ja deixei a execucao em paralelo."
                        if auto_execute
                        else "Posso preparar seu briefing matinal agora."
                    ),
                    "reason": "Ja e de manha e existe rotina/schedule de briefing configurado.",
                    "cooldown_key": "daily_briefing",
                    "parallel_safe": True,
                    "auto_execute": auto_execute,
                    "action_name": "automation_run_now",
                    "action_params": {"automation_type": "daily_briefing", "dry_run": True},
                    "spoken_message": "Posso preparar seu briefing matinal.",
                }
            )

        if context == "coding" or any("coding" in str(turn.get("content") or "").lower() for turn in recent_turns):
            candidates.append(
                {
                    "kind": "coding_focus",
                    "title": "Foco em codigo",
                    "message": "Posso montar um plano curto de foco para a sessao atual.",
                    "reason": "Seu contexto recente indica sessao de codigo.",
                    "cooldown_key": "coding_focus",
                    "parallel_safe": False,
                    "auto_execute": False,
                    "spoken_message": "Posso montar um plano curto para o que voce esta codando.",
                }
            )

        if any("spotify" in item for item in favorite_apps) and 18 <= hour <= 23:
            candidates.append(
                {
                    "kind": "spotify_resume",
                    "title": "Retomar Spotify",
                    "message": "Quer que eu confira o Spotify e retome sua rotina de audio?",
                    "reason": "Spotify aparece nas suas preferencias e este e um horario recorrente de uso.",
                    "cooldown_key": "spotify_resume",
                    "parallel_safe": False,
                    "auto_execute": False,
                    "spoken_message": "Quer que eu confira o Spotify?",
                }
            )

        if self._has_preferred_device_type(preferred_devices, "ac") and 11 <= hour <= 17:
            candidates.append(
                {
                    "kind": "ac_check",
                    "title": "Checar ar-condicionado",
                    "message": "Posso verificar o estado do ar-condicionado preferido.",
                    "reason": "Voce tem um ar-condicionado preferido salvo e este e um horario sensivel para conforto.",
                    "cooldown_key": "ac_check",
                    "parallel_safe": False,
                    "auto_execute": False,
                    "spoken_message": "Posso verificar o ar-condicionado preferido.",
                }
            )

        if isinstance(automation_state, dict) and str(automation_state.get("status") or "").strip().lower() == "scheduled":
            candidates.append(
                {
                    "kind": "automation_followup",
                    "title": "Acompanhamento de automacao",
                    "message": "Ha uma automacao agendada. Quer que eu acompanhe o resultado com voce?",
                    "reason": "O estado atual de automacao indica execucao agendada em andamento.",
                    "cooldown_key": "automation_followup",
                    "parallel_safe": False,
                    "auto_execute": False,
                    "spoken_message": "Ha uma automacao agendada; posso acompanhar com voce.",
                }
            )

        return candidates

    def _candidate_names_for_action(self, action_name: str, preferred_devices: Any) -> list[str]:
        rows = preferred_devices if isinstance(preferred_devices, list) else []
        if action_name in LIGHT_ACTIONS:
            return self._filter_device_names(rows, allowed_types={"light"})
        if action_name in AC_ACTIONS:
            return self._filter_device_names(rows, allowed_types={"ac", "air_conditioner"})
        if action_name in SPOTIFY_DEVICE_ACTIONS:
            return self._filter_device_names(rows, allowed_types={"spotify_device"})
        if action_name in WHATSAPP_ACTIONS:
            return self._filter_device_names(rows, allowed_types={"contact", "whatsapp_contact"})
        return []

    def _filter_device_names(self, rows: list[Any], *, allowed_types: set[str]) -> list[str]:
        names: list[str] = []
        for item in rows:
            if not isinstance(item, dict):
                continue
            item_type = str(item.get("type") or "").strip().lower()
            if item_type not in allowed_types:
                continue
            name = str(item.get("name") or item.get("alias") or "").strip()
            if name:
                names.append(name)
        return names

    def _has_preferred_device_type(self, preferred_devices: Any, device_type: str) -> bool:
        rows = preferred_devices if isinstance(preferred_devices, list) else []
        for item in rows:
            if isinstance(item, dict) and str(item.get("type") or "").strip().lower() == device_type:
                return True
        return False

    def _load_state(self, *, participant_identity: str, room: str) -> dict[str, Any]:
        payload = self.state_store.get_event_state(
            participant_identity=participant_identity,
            room=room,
            namespace=PROACTIVITY_NAMESPACE,
        )
        if isinstance(payload, dict):
            return dict(payload)
        return {
            "status": "idle",
            "updated_at": self._to_iso(),
            "controls": {},
            "suggestions": [],
            "last_suggestion_by_kind": {},
        }

    def _normalize_intensity(self, value: Any) -> str:
        text = str(value or DEFAULT_INTENSITY).strip().lower()
        if text in PROACTIVITY_INTENSITIES:
            return text
        return "moderate"

    def _normalize_cooldown(self, value: Any) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = self.default_cooldown_seconds
        return max(60, min(parsed, 86_400))

    def _normalize_text_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip().lower() for item in value if str(item).strip()]

    def _utc_now(self, value: datetime | None = None) -> datetime:
        current = value or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        return current.astimezone(timezone.utc)

    def _parse_iso(self, value: Any) -> datetime | None:
        if not isinstance(value, str):
            return None
        text = value.strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _to_iso(self, value: datetime | None = None) -> str:
        return self._utc_now(value).isoformat()
