from __future__ import annotations

from workflows.types import WorkflowApprovalGate, WorkflowStepDefinition


def build_idea_to_code_definition(*, request: str) -> list[WorkflowStepDefinition]:
    _ = request
    return [
        WorkflowStepDefinition(
            step_id="resolve_project",
            title="Resolver projeto alvo",
            action_name="project_resolve",
        ),
        WorkflowStepDefinition(
            step_id="build_plan",
            title="Gerar plano de execucao",
            action_name="build_task_plan",
        ),
        WorkflowStepDefinition(
            step_id="codex_review",
            title="Revisao read-only com Codex",
            action_name="codex_exec_review",
        ),
        WorkflowStepDefinition(
            step_id="apply_changes",
            title="Aplicar mudancas no codigo",
            action_name="codex_exec_apply",
            gate=WorkflowApprovalGate(
                gate_id="apply_changes",
                title="Aprovar aplicacao de mudancas",
                prompt="Confirme para executar codex em workspace-write.",
            ),
        ),
        WorkflowStepDefinition(
            step_id="validate_changes",
            title="Validar mudancas",
            action_name="code_run_command",
        ),
        WorkflowStepDefinition(
            step_id="commit_and_push",
            title="Commit e push",
            action_name="git_commit_and_push_project",
            gate=WorkflowApprovalGate(
                gate_id="commit_and_push",
                title="Aprovar commit e push",
                prompt="Confirme para criar commit e subir no remoto.",
            ),
        ),
    ]
