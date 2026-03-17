from __future__ import annotations

import asyncio

from .store import get_state_store
from .types import ActiveCharacterMode, ActiveCodexTask, ActiveProjectMode, AuthenticatedSession, PendingConfirmation, RPGSessionRecordingState

PENDING_CONFIRMATIONS: dict[str, PendingConfirmation] = {}
PARTICIPANT_PENDING_TOKENS: dict[str, str] = {}
AUTHENTICATED_SESSIONS: dict[str, AuthenticatedSession] = {}
VOICE_STEP_UP_PENDING: dict[str, float] = {}
MEMORY_SCOPE_OVERRIDES: dict[str, str] = {}
PERSONA_MODE_BY_PARTICIPANT: dict[str, str] = {}
ACTIVE_PROJECT_BY_PARTICIPANT: dict[str, ActiveProjectMode] = {}
CAPABILITY_MODE_BY_PARTICIPANT: dict[str, str] = {}
ACTIVE_CODEX_TASK_BY_PARTICIPANT: dict[str, ActiveCodexTask] = {}
CODEX_TASK_HISTORY_BY_PARTICIPANT: dict[str, list[dict[str, object]]] = {}
CODEX_RUNNING_PROCESSES: dict[str, asyncio.subprocess.Process] = {}
FEATURE_FLAG_OVERRIDES: dict[str, bool] = {}
CANARY_SESSION_OVERRIDES: dict[str, bool] = {}
CANARY_ROLLOUT_PERCENT_OVERRIDE: int | None = None
AUTO_REMEDIATION_LAST_EXECUTION: dict[str, float] = {}
CANARY_PROMOTION_LAST_EXECUTION: dict[str, float] = {}
CONTROL_LOOP_BREACH_HISTORY: dict[str, list[float]] = {}
CONTROL_LOOP_FREEZE_LAST_TRIGGER: dict[str, float] = {}
RPG_ACTIVE_RECORDINGS: dict[str, RPGSessionRecordingState] = {}
RPG_LAST_SESSION_FILES: dict[str, str] = {}
ACTIVE_CHARACTER_BY_PARTICIPANT: dict[str, ActiveCharacterMode] = {}

# Instantiate early so the DB is created during backend import, not lazily mid-request.
STATE_STORE = get_state_store()
