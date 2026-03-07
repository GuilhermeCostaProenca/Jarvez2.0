from __future__ import annotations

from datetime import datetime, timezone

from orchestration import build_task_plan

from .types import WorkflowState


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_idea_to_code_workflow(
    *,
    workflow_id: str,
    request: str,
    project_id: str | None = None,
    project_name: str | None = None,
) -> tuple[WorkflowState, dict[str, object]]:
    task_plan = build_task_plan(request).to_payload()
    first_step = ""
    steps = task_plan.get("steps")
    if isinstance(steps, list) and steps:
        first_step = str(steps[0] or "").strip()
    state = WorkflowState(
        workflow_id=workflow_id,
        workflow_type="idea_to_code",
        status="awaiting_confirmation",
        summary="Plano inicial gerado. Aguardando confirmacao para executar mudancas.",
        project_id=project_id,
        project_name=project_name,
        current_step=first_step or "Classificar objetivo, risco e contexto.",
        started_at=_now_iso(),
    )
    return state, task_plan
