from __future__ import annotations

from datetime import datetime, timezone

from actions_core.store import get_state_store

from .types import WorkflowState

WORKFLOW_STATE_NAMESPACE = "workflow_engine_v1"
WORKFLOW_COMPAT_NAMESPACE = "workflow_state"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkflowStateRepository:
    def __init__(
        self,
        *,
        store: object | None = None,
        namespace: str = WORKFLOW_STATE_NAMESPACE,
        compat_namespace: str = WORKFLOW_COMPAT_NAMESPACE,
        max_workflows: int = 12,
    ):
        self._store = store or get_state_store()
        self._namespace = namespace
        self._compat_namespace = compat_namespace
        self._max_workflows = max(1, int(max_workflows))

    def _load_blob(self, *, participant_identity: str, room: str) -> dict[str, object]:
        raw = getattr(self._store, "get_session_state")(
            participant_identity=participant_identity,
            room=room,
            namespace=self._namespace,
        )
        if not isinstance(raw, dict):
            return {"active_workflow_id": None, "workflows": {}}
        workflows = raw.get("workflows")
        if not isinstance(workflows, dict):
            workflows = {}
        active_workflow_id = str(raw.get("active_workflow_id", "")).strip() or None
        return {
            "active_workflow_id": active_workflow_id,
            "workflows": workflows,
        }

    def _save_blob(self, *, participant_identity: str, room: str, blob: dict[str, object]) -> None:
        getattr(self._store, "upsert_session_state")(
            participant_identity=participant_identity,
            room=room,
            namespace=self._namespace,
            payload=blob,
        )

    def _save_compat_snapshot(self, *, participant_identity: str, room: str, state: WorkflowState | None) -> None:
        payload = state.to_payload() if state is not None else {}
        getattr(self._store, "upsert_event_state")(
            participant_identity=participant_identity,
            room=room,
            namespace=self._compat_namespace,
            payload=payload,
        )

    def save_workflow(
        self,
        *,
        participant_identity: str,
        room: str,
        state: WorkflowState,
        make_active: bool = True,
    ) -> WorkflowState:
        blob = self._load_blob(participant_identity=participant_identity, room=room)
        workflows = blob.get("workflows")
        if not isinstance(workflows, dict):
            workflows = {}
        workflows[state.workflow_id] = state.to_payload()

        if len(workflows) > self._max_workflows:
            sorted_items = sorted(
                workflows.items(),
                key=lambda item: str((item[1] or {}).get("updated_at", "")),
                reverse=True,
            )
            workflows = {key: value for key, value in sorted_items[: self._max_workflows]}

        blob["workflows"] = workflows
        if make_active or not blob.get("active_workflow_id"):
            blob["active_workflow_id"] = state.workflow_id
        self._save_blob(participant_identity=participant_identity, room=room, blob=blob)
        self._save_compat_snapshot(participant_identity=participant_identity, room=room, state=state)
        return state

    def list_workflows(self, *, participant_identity: str, room: str) -> list[WorkflowState]:
        blob = self._load_blob(participant_identity=participant_identity, room=room)
        workflows = blob.get("workflows")
        if not isinstance(workflows, dict):
            return []
        states: list[WorkflowState] = []
        for item in workflows.values():
            if isinstance(item, dict):
                states.append(WorkflowState.from_payload(item))
        states.sort(key=lambda state: state.updated_at or state.started_at or "", reverse=True)
        return states

    def get_workflow(
        self,
        *,
        participant_identity: str,
        room: str,
        workflow_id: str | None = None,
    ) -> WorkflowState | None:
        blob = self._load_blob(participant_identity=participant_identity, room=room)
        workflows = blob.get("workflows")
        if not isinstance(workflows, dict):
            workflows = {}

        candidate_id = str(workflow_id or "").strip() or str(blob.get("active_workflow_id", "")).strip()
        if candidate_id and isinstance(workflows.get(candidate_id), dict):
            return WorkflowState.from_payload(workflows[candidate_id])

        if candidate_id:
            return None

        states = self.list_workflows(participant_identity=participant_identity, room=room)
        if states:
            return states[0]
        legacy = getattr(self._store, "get_event_state")(
            participant_identity=participant_identity,
            room=room,
            namespace=self._compat_namespace,
        )
        if isinstance(legacy, dict) and legacy:
            return WorkflowState.from_payload(legacy)
        return None

    def delete_workflow(self, *, participant_identity: str, room: str, workflow_id: str) -> bool:
        target = workflow_id.strip()
        if not target:
            return False
        blob = self._load_blob(participant_identity=participant_identity, room=room)
        workflows = blob.get("workflows")
        if not isinstance(workflows, dict):
            return False
        if target not in workflows:
            return False
        workflows.pop(target, None)
        blob["workflows"] = workflows
        active_workflow_id = str(blob.get("active_workflow_id", "")).strip()
        if active_workflow_id == target:
            next_id = next(iter(workflows), None)
            blob["active_workflow_id"] = next_id
            snapshot = WorkflowState.from_payload(workflows[next_id]) if next_id and isinstance(workflows.get(next_id), dict) else None
            self._save_compat_snapshot(participant_identity=participant_identity, room=room, state=snapshot)
        self._save_blob(participant_identity=participant_identity, room=room, blob=blob)
        return True


def cancel_workflow_state(current: dict[str, object]) -> dict[str, object]:
    if not isinstance(current, dict):
        return {
            "workflow_id": "",
            "workflow_type": "idea_to_code",
            "status": "cancelled",
            "summary": "Workflow cancelado.",
            "finished_at": _now_iso(),
        }
    state = WorkflowState.from_payload(current)
    now = _now_iso()
    state.status = "cancelled"
    state.finished_at = now
    state.updated_at = now
    state.error = None
    state.summary = "Workflow cancelado pelo usuario."
    for step in state.steps:
        if step.status in {"pending", "running", "blocked"}:
            step.status = "cancelled"
            step.finished_at = now
            step.summary = step.summary or "Step cancelado."
    return state.to_payload()
