from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Callable

from actions_core.store import JarvezStateStore, get_state_store

if TYPE_CHECKING:
    from livekit.agents import ChatContext
    from mem0 import AsyncMemoryClient
else:
    AsyncMemoryClient = Any

logger = logging.getLogger(__name__)

PUBLIC_SCOPE = "public"
PRIVATE_SCOPE = "private"
SENSITIVE_MEMORY_RE = re.compile(
    r"\b(senha|pin|cpf|cart[aÃ£]o|banco|conta|endere[cÃ§]o|telefone|email|segredo|doen[cÃ§]a|sa[uÃº]de|trauma|intim[oa])\b",
    re.IGNORECASE,
)
EXPLICIT_PRIVATE_RE = re.compile(
    r"\b(segredo|privad[oa]|n[aÃ£]o conta|nao conta|entre n[oÃ³]s|isso e segredo)\b",
    re.IGNORECASE,
)
EXPLICIT_PUBLIC_RE = re.compile(
    r"\b(n[aÃ£]o e segredo|nao e segredo|pode compartilhar|isso e publico|isso e p[uÃº]blico)\b",
    re.IGNORECASE,
)
DEFAULT_RECENT_TURNS = max(3, int(os.getenv("JARVEZ_MEMORY_RECENT_TURNS", "8")))
DEFAULT_SUMMARY_AFTER_DAYS = max(1, int(os.getenv("JARVEZ_MEMORY_SUMMARY_AFTER_DAYS", "7")))
DEFAULT_TURN_MAX_CHARS = max(120, int(os.getenv("JARVEZ_MEMORY_TURN_MAX_CHARS", "280")))
IDENTITY_CONTEXT_NAMESPACE = "recognized_identity"


@dataclass(slots=True)
class MemoryBootstrapContext:
    prompt_messages: list[str]
    loaded_memory_markers: set[str]
    recent_turns: list[dict[str, Any]]
    preferences: dict[str, Any]
    latest_summary: dict[str, Any] | None
    public_memories: list[dict[str, Any]]
    private_memories: list[dict[str, Any]]


class MemoryManager:
    """
    Hybrid memory ownership for Jarvez:
    - SQLite stores structured and recent conversational context, preferences and session summaries.
    - Mem0 stores long-term semantic memories across sessions, split into public/private scopes.
    """

    def __init__(
        self,
        *,
        mem0: AsyncMemoryClient,
        state_store: JarvezStateStore | None = None,
        recent_turn_limit: int = DEFAULT_RECENT_TURNS,
        summary_after_days: int = DEFAULT_SUMMARY_AFTER_DAYS,
        turn_max_chars: int = DEFAULT_TURN_MAX_CHARS,
    ) -> None:
        self.mem0 = mem0
        self.state_store = state_store or get_state_store()
        self.recent_turn_limit = max(1, recent_turn_limit)
        self.summary_after_days = max(1, summary_after_days)
        self.turn_max_chars = max(80, turn_max_chars)

    async def load_bootstrap_context(
        self,
        *,
        participant_identity: str,
        room: str,
        user_name: str,
        authenticated: bool,
    ) -> MemoryBootstrapContext:
        self.summarize_and_prune_old_turns(participant_identity=participant_identity, room=room)
        recent_turns = self.get_recent_turns(
            participant_identity=participant_identity,
            room=room,
            limit=self.recent_turn_limit,
        )
        preferences = self.list_preferences(participant_identity=participant_identity)
        latest_summary = self.state_store.get_latest_session_summary(
            participant_identity=participant_identity,
            room=room,
        )
        public_bundle = await self.load_scope_memories(
            participant_identity=participant_identity,
            scope=PUBLIC_SCOPE,
        )
        recognized_identity = self.get_identity_context(participant_identity=participant_identity, room=room)
        private_bundle = (
            await self.load_scope_memories(participant_identity=participant_identity, scope=PRIVATE_SCOPE)
            if authenticated
            else {"memories": [], "blob": "", "count": 0}
        )

        messages: list[str] = []
        markers: set[str] = set()
        structured_payload: dict[str, Any] = {"user_name": user_name}
        if preferences:
            structured_payload["preferences"] = preferences
        if recognized_identity:
            structured_payload["recognized_identity"] = recognized_identity
        if latest_summary and latest_summary.get("summary"):
            structured_payload["previous_session_summary"] = latest_summary["summary"]
        if recent_turns:
            structured_payload["recent_turns"] = [
                {
                    "role": item["role"],
                    "content": item["content"],
                    "timestamp": item["timestamp"],
                }
                for item in recent_turns
            ]
        if len(structured_payload) > 1:
            structured_message = (
                "Contexto persistido da conversa para esta sessao: "
                + json.dumps(structured_payload, ensure_ascii=False)
                + "."
            )
            messages.append(structured_message)
            markers.add(structured_message)

        public_blob = str(public_bundle.get("blob") or "").strip()
        if public_blob:
            semantic_public = f"Memorias semanticas publicas conhecidas: {public_blob}."
            messages.append(semantic_public)
            markers.add(semantic_public)

        private_blob = str(private_bundle.get("blob") or "").strip()
        if private_blob:
            semantic_private = f"Memorias privadas liberadas para esta sessao: {private_blob}."
            messages.append(semantic_private)
            markers.add(semantic_private)
            logger.info(
                "private_memory_access %s",
                json.dumps(
                    {
                        "participant_identity": participant_identity,
                        "room": room,
                        "source": "session_start",
                        "count": int(private_bundle.get("count") or 0),
                    },
                    ensure_ascii=False,
                ),
            )

        return MemoryBootstrapContext(
            prompt_messages=messages,
            loaded_memory_markers=markers,
            recent_turns=recent_turns,
            preferences=preferences,
            latest_summary=latest_summary,
            public_memories=list(public_bundle.get("memories") or []),
            private_memories=list(private_bundle.get("memories") or []),
        )

    async def load_scope_memories(
        self,
        *,
        participant_identity: str,
        scope: str,
    ) -> dict[str, Any]:
        results: list[dict[str, Any]] = []
        scoped_user_id = self._scoped_user_id(participant_identity, scope)
        try:
            raw_results = await self.mem0.get_all(user_id=scoped_user_id)
            if isinstance(raw_results, list):
                results = [item for item in raw_results if isinstance(item, dict)]
            logger.info("Retrieved %s memories for %s using get_all", len(results), scoped_user_id)
        except Exception as error:
            logger.warning("get_all failed for %s: %s", scoped_user_id, error)
            try:
                response = await self.mem0.search(
                    "informacoes preferencias contexto",
                    filters={"user_id": scoped_user_id},
                )
                candidate = response["results"] if isinstance(response, dict) and "results" in response else response
                if isinstance(candidate, list):
                    results = [item for item in candidate if isinstance(item, dict)]
                logger.info("Retrieved %s memories for %s using search", len(results), scoped_user_id)
            except Exception as search_error:
                logger.warning("search failed for %s: %s", scoped_user_id, search_error)
                results = []
        return {
            "memories": results,
            "blob": self._memory_json_blob(results),
            "count": len(results),
        }

    def record_turn(
        self,
        *,
        session_id: str,
        participant_identity: str,
        room: str,
        role: str,
        content: str,
        timestamp: str | None = None,
        relevance_score: float | None = None,
    ) -> int:
        normalized_content = str(content or "").strip()
        if not normalized_content:
            return 0
        return self.state_store.append_conversation_turn(
            session_id=session_id,
            participant_identity=participant_identity,
            room=room,
            role=role,
            content=normalized_content,
            timestamp=timestamp,
            relevance_score=relevance_score if relevance_score is not None else self._score_turn(role, normalized_content),
        )

    def get_recent_turns(
        self,
        *,
        participant_identity: str,
        room: str,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        rows = self.state_store.list_conversation_turns(
            participant_identity=participant_identity,
            room=room,
            limit=limit or self.recent_turn_limit,
        )
        return [
            {
                **item,
                "content": self._truncate_text(str(item.get("content") or "")),
            }
            for item in rows
        ]

    def set_preference(self, *, participant_identity: str, key: str, value: Any) -> None:
        self.state_store.set_user_preference(
            participant_identity=participant_identity,
            key=key,
            value=value,
        )

    def get_preference(self, *, participant_identity: str, key: str) -> Any | None:
        return self.state_store.get_user_preference(participant_identity=participant_identity, key=key)

    def list_preferences(self, *, participant_identity: str) -> dict[str, Any]:
        return self.state_store.list_user_preferences(participant_identity=participant_identity)

    def set_identity_context(self, *, participant_identity: str, room: str, payload: dict[str, Any]) -> None:
        self.state_store.upsert_session_state(
            participant_identity=participant_identity,
            room=room,
            namespace=IDENTITY_CONTEXT_NAMESPACE,
            payload=payload,
        )

    def get_identity_context(self, *, participant_identity: str, room: str) -> dict[str, Any] | None:
        current = self.state_store.get_session_state(
            participant_identity=participant_identity,
            room=room,
            namespace=IDENTITY_CONTEXT_NAMESPACE,
        )
        return current if isinstance(current, dict) else None

    def summarize_and_prune_old_turns(self, *, participant_identity: str, room: str) -> None:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=self.summary_after_days)).isoformat()
        old_turns = self.state_store.list_conversation_turns(
            participant_identity=participant_identity,
            room=room,
            limit=500,
            older_than=cutoff,
        )
        if not old_turns:
            return
        turns_by_session: dict[str, list[dict[str, Any]]] = {}
        for item in old_turns:
            turns_by_session.setdefault(str(item["session_id"]), []).append(item)
        for session_id, turns in turns_by_session.items():
            summary_text = self._build_summary(turns, mode="historical")
            if not summary_text:
                continue
            existing = self.state_store.get_session_summary(session_id=session_id)
            merged_summary = self._merge_summaries(existing.get("summary") if existing else None, summary_text)
            self.state_store.save_session_summary(
                session_id=session_id,
                participant_identity=participant_identity,
                room=room,
                summary=merged_summary,
                started_at=str(turns[0]["timestamp"]),
                ended_at=str(turns[-1]["timestamp"]),
                turns_count=(existing.get("turns_count", 0) if existing else 0) + len(turns),
            )
            self.state_store.delete_conversation_turns([int(item["id"]) for item in turns])

    async def finalize_session(
        self,
        *,
        chat_ctx: "ChatContext",
        participant_identity: str,
        room: str,
        session_id: str,
        loaded_memory_markers: set[str],
        scope_override_getter: Callable[[str, str], str | None] | None = None,
    ) -> None:
        structured_turns = self._extract_turns_from_chat_ctx(
            chat_ctx,
            loaded_memory_markers,
            participant_identity=participant_identity,
            room=room,
            scope_override_getter=scope_override_getter,
        )
        public_batch: list[dict[str, str]] = []
        private_batch: list[dict[str, str]] = []
        for item in structured_turns:
            self.record_turn(
                session_id=session_id,
                participant_identity=participant_identity,
                room=room,
                role=str(item["role"]),
                content=str(item["content"]),
                timestamp=str(item["timestamp"]),
                relevance_score=float(item["relevance_score"]),
            )
            target = private_batch if item["scope"] == PRIVATE_SCOPE else public_batch
            target.append({"role": str(item["role"]), "content": str(item["content"])})

        if public_batch:
            await self.mem0.add(public_batch, user_id=self._scoped_user_id(participant_identity, PUBLIC_SCOPE))
            logger.info("Saved %s public messages to memory.", len(public_batch))
        if private_batch:
            await self.mem0.add(private_batch, user_id=self._scoped_user_id(participant_identity, PRIVATE_SCOPE))
            logger.info("Saved %s private messages to memory.", len(private_batch))
        if structured_turns:
            self.state_store.save_session_summary(
                session_id=session_id,
                participant_identity=participant_identity,
                room=room,
                summary=self._build_summary(structured_turns, mode="session"),
                started_at=str(structured_turns[0]["timestamp"]),
                ended_at=str(structured_turns[-1]["timestamp"]),
                turns_count=len(structured_turns),
            )
        else:
            logger.info("No new structured turns to persist.")
        if not public_batch and not private_batch:
            logger.info("No new messages to persist in Mem0.")
        self.summarize_and_prune_old_turns(participant_identity=participant_identity, room=room)

    def _extract_turns_from_chat_ctx(
        self,
        chat_ctx: "ChatContext",
        loaded_memory_markers: set[str],
        *,
        participant_identity: str,
        room: str,
        scope_override_getter: Callable[[str, str], str | None] | None = None,
    ) -> list[dict[str, Any]]:
        turns: list[dict[str, Any]] = []
        current_scope = PUBLIC_SCOPE
        for item in chat_ctx.items:
            role = getattr(item, "role", None)
            if role not in {"user", "assistant"}:
                continue
            text = self._extract_item_text(item)
            if not text:
                continue
            if any(marker and marker in text for marker in loaded_memory_markers):
                continue
            if role == "user":
                override_scope = (
                    scope_override_getter(participant_identity, room) if scope_override_getter is not None else None
                )
                if override_scope in {PUBLIC_SCOPE, PRIVATE_SCOPE}:
                    current_scope = str(override_scope)
                else:
                    current_scope = self._detect_scope_for_text(text, current_scope)
            turns.append(
                {
                    "role": role,
                    "content": text,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "relevance_score": self._score_turn(role, text),
                    "scope": current_scope,
                }
            )
            if role == "assistant":
                current_scope = PUBLIC_SCOPE
        return turns

    def _memory_json_blob(self, memories: list[dict[str, Any]]) -> str:
        filtered: list[dict[str, str]] = []
        for result in memories:
            memory_text = result.get("memory")
            if not memory_text:
                continue
            filtered.append(
                {
                    "memory": str(memory_text),
                    "updated_at": str(result.get("updated_at") or ""),
                }
            )
        return json.dumps(filtered, ensure_ascii=False) if filtered else ""

    def _extract_item_text(self, item: Any) -> str:
        content = getattr(item, "content", None)
        if content is None:
            return ""
        if isinstance(content, list):
            return "".join(part for part in content if isinstance(part, str)).strip()
        return str(content).strip()

    def _detect_scope_for_text(self, text: str, fallback_scope: str) -> str:
        if EXPLICIT_PUBLIC_RE.search(text):
            return PUBLIC_SCOPE
        if EXPLICIT_PRIVATE_RE.search(text):
            return PRIVATE_SCOPE
        if SENSITIVE_MEMORY_RE.search(text):
            return PRIVATE_SCOPE
        return fallback_scope

    def _build_summary(self, turns: list[dict[str, Any]], *, mode: str) -> str:
        if not turns:
            return ""
        trimmed = turns[-6:]
        lines: list[str] = []
        for item in trimmed:
            role = "usuario" if str(item.get("role")) == "user" else "jarvez"
            content = self._truncate_text(str(item.get("content") or ""), maximum=160)
            if content:
                lines.append(f"{role}: {content}")
        if not lines:
            return ""
        prefix = (
            "Resumo consolidado de contexto recente"
            if mode == "session"
            else "Resumo preservado de turnos antigos"
        )
        return f"{prefix}: " + " | ".join(lines)

    def _merge_summaries(self, previous: str | None, new_summary: str) -> str:
        previous_text = str(previous or "").strip()
        if not previous_text:
            return new_summary
        if new_summary in previous_text:
            return previous_text
        return f"{previous_text}\n{new_summary}"

    def _score_turn(self, role: str, content: str) -> float:
        normalized = str(content).strip()
        score = 1.0
        if role == "user":
            score += 0.25
        if len(normalized) > 80:
            score += 0.25
        if any(keyword in normalized.lower() for keyword in ("prefiro", "sempre", "gosto", "favorito", "rotina")):
            score += 0.5
        return round(score, 2)

    def _truncate_text(self, value: str, *, maximum: int | None = None) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            return ""
        limit = maximum or self.turn_max_chars
        if len(normalized) <= limit:
            return normalized
        return normalized[: limit - 3].rstrip() + "..."

    def _scoped_user_id(self, participant_identity: str, scope: str) -> str:
        return f"{participant_identity}::{scope}"
