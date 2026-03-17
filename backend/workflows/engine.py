from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import Any, Callable

from orchestration import build_task_plan

from .definitions.idea_to_code import build_idea_to_code_definition
from .state import WorkflowStateRepository
from .types import WorkflowState, WorkflowStepDefinition, WorkflowStepState


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


StepExecutor = Callable[[WorkflowState, WorkflowStepState], dict[str, Any] | None]


class WorkflowEngine:
    def __init__(
        self,
        *,
        repository: WorkflowStateRepository | None = None,
        step_executors: dict[str, StepExecutor] | None = None,
        now_iso: Callable[[], str] = _now_iso,
        workflow_id_factory: Callable[[], str] | None = None,
    ):
        self._repository = repository or WorkflowStateRepository()
        self._step_executors = dict(step_executors or {})
        self._now_iso = now_iso
        self._workflow_id_factory = workflow_id_factory or (lambda: f"wf_{uuid.uuid4().hex[:10]}")

    def start_idea_to_code(
        self,
        *,
        participant_identity: str,
        room: str,
        request: str,
        project_id: str | None = None,
        project_name: str | None = None,
        workflow_id: str | None = None,
        initial_context: dict[str, Any] | None = None,
    ) -> WorkflowState:
        workflow_steps = build_idea_to_code_definition(request=request)
        now = self._now_iso()
        state = WorkflowState(
            workflow_id=str(workflow_id or self._workflow_id_factory()),
            workflow_type="idea_to_code",
            status="running",
            summary="Workflow iniciado. Preparando plano inicial.",
            request=request,
            project_id=project_id,
            project_name=project_name,
            current_step_index=0,
            steps=[self._new_step_state(item) for item in workflow_steps],
            context=dict(initial_context or {}),
            started_at=now,
            updated_at=now,
        )
        state = self._advance(state)
        return self._repository.save_workflow(
            participant_identity=participant_identity,
            room=room,
            state=state,
            make_active=True,
        )

    def get_workflow(
        self,
        *,
        participant_identity: str,
        room: str,
        workflow_id: str | None = None,
    ) -> WorkflowState | None:
        return self._repository.get_workflow(
            participant_identity=participant_identity,
            room=room,
            workflow_id=workflow_id,
        )

    def cancel_workflow(
        self,
        *,
        participant_identity: str,
        room: str,
        workflow_id: str | None = None,
    ) -> WorkflowState | None:
        state = self.get_workflow(participant_identity=participant_identity, room=room, workflow_id=workflow_id)
        if state is None:
            return None
        now = self._now_iso()
        state.status = "cancelled"
        state.summary = "Workflow cancelado pelo usuario."
        state.finished_at = now
        state.updated_at = now
        for step in state.steps:
            if step.status in {"pending", "running", "blocked"}:
                step.status = "cancelled"
                step.finished_at = now
                step.summary = step.summary or "Step cancelado."
        return self._repository.save_workflow(
            participant_identity=participant_identity,
            room=room,
            state=state,
            make_active=True,
        )

    def approve_gate(
        self,
        *,
        participant_identity: str,
        room: str,
        gate_id: str,
        approved: bool,
        workflow_id: str | None = None,
        note: str | None = None,
    ) -> WorkflowState:
        state = self.get_workflow(participant_identity=participant_identity, room=room, workflow_id=workflow_id)
        if state is None:
            raise KeyError("workflow not found")
        normalized_gate_id = gate_id.strip()
        if not normalized_gate_id:
            raise ValueError("missing gate_id")

        step = self._find_step_by_gate(state=state, gate_id=normalized_gate_id)
        if step is None or step.gate is None:
            raise ValueError("unknown gate")
        if step.gate.status != "pending":
            raise ValueError("gate already decided")

        now = self._now_iso()
        step.gate.decision_note = note.strip() if isinstance(note, str) and note.strip() else None
        step.gate.decided_at = now

        if approved:
            step.gate.status = "approved"
            step.status = "pending"
            step.error = None
            step.summary = "Gate aprovado. Retomando workflow."
            state.status = "running"
            state.summary = step.summary
            state.updated_at = now
            state = self._advance(state)
        else:
            step.gate.status = "rejected"
            step.status = "cancelled"
            step.finished_at = now
            step.summary = "Gate rejeitado pelo usuario."
            state.status = "cancelled"
            state.summary = "Workflow interrompido por rejeicao de gate."
            state.finished_at = now
            state.updated_at = now

        return self._repository.save_workflow(
            participant_identity=participant_identity,
            room=room,
            state=state,
            make_active=True,
        )

    def resume_workflow(
        self,
        *,
        participant_identity: str,
        room: str,
        workflow_id: str | None = None,
    ) -> WorkflowState | None:
        state = self.get_workflow(participant_identity=participant_identity, room=room, workflow_id=workflow_id)
        if state is None:
            return None
        if state.status in {"completed", "failed", "cancelled"}:
            return state
        pending_gate = state.pending_gate
        if isinstance(pending_gate, dict):
            state.status = "awaiting_approval"
            state.summary = f"Aguardando aprovacao: {pending_gate.get('title', 'approval gate')}."
            state.updated_at = self._now_iso()
            return self._repository.save_workflow(
                participant_identity=participant_identity,
                room=room,
                state=state,
                make_active=True,
            )
        state.status = "running"
        state.updated_at = self._now_iso()
        state = self._advance(state)
        return self._repository.save_workflow(
            participant_identity=participant_identity,
            room=room,
            state=state,
            make_active=True,
        )

    def _new_step_state(self, definition: WorkflowStepDefinition) -> WorkflowStepState:
        return WorkflowStepState(
            step_id=definition.step_id,
            title=definition.title,
            action_name=definition.action_name,
            gate=definition.gate,
        )

    def _find_step_by_gate(self, *, state: WorkflowState, gate_id: str) -> WorkflowStepState | None:
        for step in state.steps:
            if step.gate is None:
                continue
            if step.gate.gate_id == gate_id:
                return step
        return None

    def _advance(self, state: WorkflowState) -> WorkflowState:
        while state.current_step_index < len(state.steps):
            step = state.steps[state.current_step_index]
            if step.status == "completed":
                state.current_step_index += 1
                continue
            if step.gate is not None and step.gate.status == "pending":
                step.status = "blocked"
                step.summary = step.summary or "Aguardando aprovacao para executar este step."
                state.status = "awaiting_approval"
                state.summary = f"Aguardando aprovacao: {step.gate.title}."
                state.updated_at = self._now_iso()
                return state
            if step.gate is not None and step.gate.status == "rejected":
                step.status = "cancelled"
                step.summary = step.summary or "Gate rejeitado."
                step.finished_at = step.finished_at or self._now_iso()
                state.status = "cancelled"
                state.summary = "Workflow interrompido por rejeicao de gate."
                state.finished_at = self._now_iso()
                state.updated_at = self._now_iso()
                return state

            now = self._now_iso()
            step.status = "running"
            step.started_at = step.started_at or now
            executor = self._step_executors.get(step.step_id) or self._step_executors.get(step.action_name)

            try:
                output = executor(state, step) if executor is not None else {}
            except Exception as error:  # noqa: BLE001
                step.status = "failed"
                step.error = str(error)
                step.summary = f"Falha no step {step.title}."
                step.finished_at = self._now_iso()
                state.status = "failed"
                state.error = step.error
                state.summary = step.summary
                state.finished_at = self._now_iso()
                state.updated_at = self._now_iso()
                return state

            payload = output if isinstance(output, dict) else {"result": output}
            step.output = payload or None
            step.summary = str(payload.get("summary", "")).strip() or f"Step concluido: {step.title}."
            step.status = "completed"
            step.error = None
            step.finished_at = self._now_iso()
            self._merge_context(state=state, payload=payload)
            state.summary = step.summary
            state.updated_at = self._now_iso()
            state.current_step_index += 1

        state.status = "completed"
        state.summary = "Workflow concluido."
        now = self._now_iso()
        state.finished_at = now
        state.updated_at = now
        return state

    def _merge_context(self, *, state: WorkflowState, payload: dict[str, Any]) -> None:
        for key, value in payload.items():
            if key == "summary":
                continue
            state.context[key] = value
        project_payload = state.context.get("project")
        if isinstance(project_payload, dict):
            project_id = str(project_payload.get("project_id", "")).strip()
            project_name = str(project_payload.get("name", "")).strip() or str(project_payload.get("project_name", "")).strip()
            if project_id:
                state.project_id = project_id
            if project_name:
                state.project_name = project_name


def build_idea_to_code_workflow(
    *,
    workflow_id: str,
    request: str,
    project_id: str | None = None,
    project_name: str | None = None,
) -> tuple[WorkflowState, dict[str, object]]:
    task_plan = build_task_plan(request).to_payload()
    steps = build_idea_to_code_definition(request=request)
    runtime_steps = [WorkflowStepState(step_id=item.step_id, title=item.title, action_name=item.action_name, gate=item.gate) for item in steps]
    now = _now_iso()

    initial_project = {
        "project_id": project_id,
        "name": project_name,
    }
    context: dict[str, Any] = {
        "task_plan": task_plan,
        "project": initial_project,
        "codex_review": {
            "mode": "read-only",
            "summary": "Revisao inicial preparada. Aguardando aprovacao para aplicar mudancas.",
        },
    }

    if len(runtime_steps) >= 3:
        runtime_steps[0].status = "completed"
        runtime_steps[0].summary = "Projeto resolvido para execucao."
        runtime_steps[0].started_at = now
        runtime_steps[0].finished_at = now
        runtime_steps[0].output = {"project": initial_project}

        runtime_steps[1].status = "completed"
        runtime_steps[1].summary = "Plano de execucao gerado."
        runtime_steps[1].started_at = now
        runtime_steps[1].finished_at = now
        runtime_steps[1].output = {"task_plan": task_plan}

        runtime_steps[2].status = "completed"
        runtime_steps[2].summary = "Revisao read-only concluida."
        runtime_steps[2].started_at = now
        runtime_steps[2].finished_at = now
        runtime_steps[2].output = {"codex_review": context["codex_review"]}

    current_step_index = 3 if len(runtime_steps) > 3 else len(runtime_steps)
    if current_step_index < len(runtime_steps):
        runtime_steps[current_step_index].status = "blocked"

    state = WorkflowState(
        workflow_id=workflow_id,
        workflow_type="idea_to_code",
        status="awaiting_approval",
        summary="Plano inicial gerado. Aguardando aprovacao para aplicar mudancas.",
        request=request,
        project_id=project_id,
        project_name=project_name,
        current_step_index=current_step_index,
        steps=runtime_steps,
        context=context,
        started_at=now,
        updated_at=now,
    )
    return state, task_plan
