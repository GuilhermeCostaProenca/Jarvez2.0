from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

JsonObject = dict[str, Any]
ActionHandler = Callable[[JsonObject, "ActionContext"], Awaitable["ActionResult"]]


@dataclass(slots=True)
class ActionResult:
    success: bool
    message: str
    data: JsonObject | None = None
    error: str | None = None
    trace_id: str | None = None
    risk: str | None = None
    policy_decision: str | None = None
    evidence: JsonObject | None = None
    fallback_used: bool | None = None

    def to_json(self) -> str:
        payload: JsonObject = {
            "success": self.success,
            "message": self.message,
        }
        if self.data is not None:
            payload["data"] = self.data
        if self.error is not None:
            payload["error"] = self.error
        if self.trace_id:
            payload["trace_id"] = self.trace_id
        if self.risk:
            payload["risk"] = self.risk
        if self.policy_decision:
            payload["policy_decision"] = self.policy_decision
        if self.evidence is not None:
            payload["evidence"] = self.evidence
        if self.fallback_used is not None:
            payload["fallback_used"] = self.fallback_used
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
    expires_at: Any


@dataclass(slots=True)
class AuthenticatedSession:
    participant_identity: str
    room: str
    expires_at: Any
    auth_method: str
    last_activity_at: Any


@dataclass(slots=True)
class RPGSessionRecordingState:
    participant_identity: str
    room: str
    title: str
    world: str
    started_at: Any
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


@dataclass(slots=True)
class ActiveProjectMode:
    project_id: str
    name: str
    root_path: str
    aliases: list[str]
    selected_at: str
    selection_reason: str
    index_status: str


@dataclass(slots=True)
class ActiveCodexTask:
    task_id: str
    status: str
    project_id: str
    project_name: str
    working_directory: str
    request: str
    started_at: str
    finished_at: str | None = None
    current_phase: str | None = None
    summary: str | None = None
    exit_code: int | None = None
    raw_last_event: JsonObject | None = None
    command_preview: str | None = None
    error: str | None = None
