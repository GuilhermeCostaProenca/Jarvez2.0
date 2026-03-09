from __future__ import annotations

from collections.abc import Callable
from typing import Any

from actions_core import ActionContext, ActionResult
from workflows.engine import WorkflowEngine

JsonObject = dict[str, Any]


def _coerce_approval(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().casefold()
    if text in {"true", "1", "yes", "sim", "confirmo", "aprovar", "aprovado"}:
        return True
    if text in {"false", "0", "no", "nao", "reject", "rejeitar", "reprovado"}:
        return False
    return None


def _project_name(payload: JsonObject | None) -> str | None:
    if not isinstance(payload, dict):
        return None
    return str(payload.get("name", "")).strip() or str(payload.get("project_name", "")).strip() or None


def _project_id(payload: JsonObject | None) -> str | None:
    if not isinstance(payload, dict):
        return None
    return str(payload.get("project_id", "")).strip() or None


async def workflow_run_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    workflow_engine: WorkflowEngine,
    get_active_project: Callable[[str, str], Any | None],
    resolve_project_target: Callable[..., tuple[JsonObject | None, ActionResult | None]],
    build_task_plan_payload: Callable[[str], JsonObject],
    build_codex_review_preview: Callable[..., JsonObject],
    build_validation_plan: Callable[[str | None], list[JsonObject]],
    active_project_payload: Callable[[str, str], JsonObject],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    request = (
        str(params.get("request", "")).strip()
        or str(params.get("query", "")).strip()
        or str(params.get("prompt", "")).strip()
    )
    if not request:
        return ActionResult(success=False, message="Descreva a ideia para iniciar o workflow.", error="missing request")

    active_project = get_active_project(ctx.participant_identity, ctx.room)
    project_query = (
        str(params.get("project_query", "")).strip()
        or str(params.get("project", "")).strip()
        or str(params.get("project_name", "")).strip()
    )
    project_payload, resolution_error = resolve_project_target(
        project_query=project_query or None,
        active_project=active_project,
    )
    if resolution_error is not None:
        return resolution_error

    project_payload = project_payload if isinstance(project_payload, dict) else {}
    plan_payload = build_task_plan_payload(request)
    codex_preview = build_codex_review_preview(
        request=request,
        project_name=_project_name(project_payload),
        working_directory=str(project_payload.get("root_path", "")).strip() or None,
    )
    validation_plan = build_validation_plan(_project_name(project_payload))

    initial_context = {
        "project": project_payload,
        "task_plan": plan_payload,
        "codex_review": codex_preview,
        "validation_plan": validation_plan,
    }
    state = workflow_engine.start_idea_to_code(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        request=request,
        project_id=_project_id(project_payload),
        project_name=_project_name(project_payload),
        initial_context=initial_context,
    )
    state_payload = state.to_payload()
    pending_gate = state_payload.get("pending_gate")
    if isinstance(pending_gate, dict):
        gate_label = str(pending_gate.get("title", "")).strip() or str(pending_gate.get("gate_id", "")).strip()
        message = f"Workflow iniciado e pausado em gate: {gate_label}."
    else:
        message = "Workflow iniciado com sucesso."

    return ActionResult(
        success=True,
        message=message,
        data={
            "workflow_state": state_payload,
            "orchestration": {"request": request, "task_plan": plan_payload},
            "workflow_context": initial_context,
            **active_project_payload(ctx.participant_identity, ctx.room),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def workflow_status_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    workflow_engine: WorkflowEngine,
    active_project_payload: Callable[[str, str], JsonObject],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    workflow_id = str(params.get("workflow_id", "")).strip() or None
    state = workflow_engine.get_workflow(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        workflow_id=workflow_id,
    )
    if state is None:
        return ActionResult(success=False, message="Nenhum workflow ativo nesta sessao.", error="workflow missing")
    payload = state.to_payload()
    return ActionResult(
        success=True,
        message=f"Workflow em estado {state.status}.",
        data={
            "workflow_state": payload,
            **active_project_payload(ctx.participant_identity, ctx.room),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def workflow_cancel_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    workflow_engine: WorkflowEngine,
    active_project_payload: Callable[[str, str], JsonObject],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    workflow_id = str(params.get("workflow_id", "")).strip() or None
    state = workflow_engine.cancel_workflow(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        workflow_id=workflow_id,
    )
    if state is None:
        return ActionResult(success=False, message="Nenhum workflow ativo para cancelar.", error="workflow missing")
    return ActionResult(
        success=True,
        message="Workflow cancelado.",
        data={
            "workflow_state": state.to_payload(),
            **active_project_payload(ctx.participant_identity, ctx.room),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def workflow_approve_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    workflow_engine: WorkflowEngine,
    active_project_payload: Callable[[str, str], JsonObject],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    workflow_id = str(params.get("workflow_id", "")).strip() or None
    decision = _coerce_approval(params.get("approved", True))
    if decision is None:
        return ActionResult(success=False, message="Informe approved=true ou approved=false.", error="invalid approval")

    current = workflow_engine.get_workflow(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        workflow_id=workflow_id,
    )
    if current is None:
        return ActionResult(success=False, message="Workflow nao encontrado.", error="workflow missing")

    gate_id = str(params.get("gate_id", "")).strip()
    if not gate_id:
        pending_gate = current.pending_gate
        if isinstance(pending_gate, dict):
            gate_id = str(pending_gate.get("gate_id", "")).strip()
    if not gate_id:
        return ActionResult(success=False, message="Nao existe gate pendente para aprovar.", error="missing gate")

    try:
        state = workflow_engine.approve_gate(
            participant_identity=ctx.participant_identity,
            room=ctx.room,
            workflow_id=workflow_id,
            gate_id=gate_id,
            approved=decision,
            note=str(params.get("note", "")).strip() or None,
        )
    except KeyError:
        return ActionResult(success=False, message="Workflow nao encontrado.", error="workflow missing")
    except ValueError as error:
        return ActionResult(success=False, message=f"Nao foi possivel decidir o gate: {error}", error=str(error))

    message = "Gate aprovado e workflow retomado." if decision else "Gate rejeitado e workflow encerrado."
    return ActionResult(
        success=True,
        message=message,
        data={
            "workflow_state": state.to_payload(),
            **active_project_payload(ctx.participant_identity, ctx.room),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def workflow_resume_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    workflow_engine: WorkflowEngine,
    active_project_payload: Callable[[str, str], JsonObject],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    workflow_id = str(params.get("workflow_id", "")).strip() or None
    state = workflow_engine.resume_workflow(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        workflow_id=workflow_id,
    )
    if state is None:
        return ActionResult(success=False, message="Workflow nao encontrado.", error="workflow missing")
    payload = state.to_payload()
    pending_gate = payload.get("pending_gate")
    if isinstance(pending_gate, dict):
        label = str(pending_gate.get("title", "")).strip() or "gate pendente"
        message = f"Workflow ainda aguardando aprovacao: {label}."
    else:
        message = f"Workflow retomado em estado {state.status}."
    return ActionResult(
        success=True,
        message=message,
        data={
            "workflow_state": payload,
            **active_project_payload(ctx.participant_identity, ctx.room),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )
