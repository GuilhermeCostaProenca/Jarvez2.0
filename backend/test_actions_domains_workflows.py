from __future__ import annotations

from types import SimpleNamespace
import unittest

from actions_core import ActionContext, ActionResult
from actions_domains.workflows import (
    workflow_approve_action,
    workflow_cancel_action,
    workflow_resume_action,
    workflow_run_action,
    workflow_status_action,
)
from workflows.engine import WorkflowEngine
from workflows.state import WorkflowStateRepository


class _MemoryStore:
    def __init__(self):
        self.session_state: dict[tuple[str, str, str], object] = {}
        self.event_state: dict[tuple[str, str, str], object] = {}

    def upsert_session_state(self, *, participant_identity: str, room: str, namespace: str, payload: object) -> None:
        self.session_state[(participant_identity, room, namespace)] = payload

    def get_session_state(self, *, participant_identity: str, room: str, namespace: str):
        return self.session_state.get((participant_identity, room, namespace))

    def upsert_event_state(self, *, participant_identity: str, room: str, namespace: str, payload: object) -> None:
        self.event_state[(participant_identity, room, namespace)] = payload

    def get_event_state(self, *, participant_identity: str, room: str, namespace: str):
        return self.event_state.get((participant_identity, room, namespace))


class _Clock:
    def __init__(self):
        self._value = 0

    def now_iso(self) -> str:
        self._value += 1
        return f"2026-03-09T00:00:{self._value:02d}+00:00"


def _build_executors() -> dict[str, object]:
    return {
        "resolve_project": lambda _state, _step: {
            "project": {"project_id": "proj_1", "name": "Jarvez2.0", "root_path": "C:/repo/jarvez"},
            "summary": "Projeto resolvido.",
        },
        "build_plan": lambda _state, _step: {
            "task_plan": {"task_type": "code", "steps": ["s1", "s2"]},
            "summary": "Plano gerado.",
        },
        "codex_review": lambda _state, _step: {
            "codex_review": {"mode": "read-only"},
            "summary": "Review concluida.",
        },
        "apply_changes": lambda _state, _step: {
            "apply_result": {"mode": "workspace-write"},
            "summary": "Mudancas aplicadas.",
        },
        "validate_changes": lambda _state, _step: {
            "validation_result": {"ok": True},
            "summary": "Validacao concluida.",
        },
        "commit_and_push": lambda _state, _step: {
            "commit_result": {"sha": "abc123"},
            "summary": "Commit e push concluidos.",
        },
    }


def _project_payload(record: object) -> dict[str, object]:
    return {
        "project_id": str(getattr(record, "project_id")),
        "name": str(getattr(record, "name")),
        "root_path": str(getattr(record, "root_path")),
    }


def _workflow_resolve_project_target(
    *,
    project_query: str | None,
    active_project: object | None,
    catalog_resolve,
) -> tuple[dict[str, object] | None, ActionResult | None]:
    query = str(project_query or "").strip()
    if not query and active_project is not None:
        return _project_payload(active_project), None
    if not query:
        return None, ActionResult(success=False, message="missing project", error="missing project")
    active_project_id = str(getattr(active_project, "project_id", "") or "").strip() or None
    match, confidence, candidates = catalog_resolve(query, active_project_id)
    if match is None:
        return None, ActionResult(
            success=False,
            message="not found",
            data={"project_resolution_required": True, "confidence": confidence, "candidates": [_project_payload(item) for item in candidates]},
            error="project resolution failed",
        )
    if confidence == "medium":
        return None, ActionResult(
            success=False,
            message="ambiguous",
            data={"project_resolution_required": True, "confidence": confidence, "candidates": [_project_payload(item) for item in candidates]},
            error="ambiguous project",
        )
    return _project_payload(match), None


def _workflow_build_task_plan_payload(request: str) -> dict[str, object]:
    return {"task_type": "code", "steps": ["planejar", request], "generated_at": "2026-03-09T00:00:00+00:00"}


def _workflow_build_codex_review_preview(*, request: str, project_name: str | None, working_directory: str | None) -> dict[str, object]:
    target_name = str(project_name or "").strip() or "projeto ativo"
    command = "codex exec --json --skip-git-repo-check --sandbox read-only --ephemeral"
    if isinstance(working_directory, str) and working_directory.strip():
        command = f'{command} -C "{working_directory.strip()}"'
    return {
        "mode": "read-only",
        "project_name": target_name,
        "prompt": request,
        "command_preview": f'{command} "<prompt>"',
        "summary": f"Preview para {target_name}.",
    }


def _workflow_default_validation_plan(project_name: str | None) -> list[dict[str, object]]:
    target_name = str(project_name or "").strip() or "project"
    return [
        {
            "step": "py_compile",
            "command": "python",
            "arguments": ["-m", "compileall", "backend/workflows"],
            "summary": f"Validar workflow em {target_name}.",
        }
    ]


class WorkflowActionsDomainTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        store = _MemoryStore()
        clock = _Clock()
        repository = WorkflowStateRepository(store=store)
        self.engine = WorkflowEngine(
            repository=repository,
            step_executors=_build_executors(),
            now_iso=clock.now_iso,
            workflow_id_factory=lambda: "wf_actions_001",
        )
        self.ctx = ActionContext(job_id="job", room="room-1", participant_identity="user-1")
        self.active = SimpleNamespace(project_id="proj_1", name="Jarvez2.0", root_path="C:/repo/jarvez")

    async def test_workflow_run_and_approval_flow(self) -> None:
        async_result = await workflow_run_action(
            {"request": "Adicionar retomada com approval gate"},
            self.ctx,
            workflow_engine=self.engine,
            get_active_project=lambda _pid, _room: self.active,
            resolve_project_target=lambda project_query, active_project: _workflow_resolve_project_target(
                project_query=project_query,
                active_project=active_project,
                catalog_resolve=lambda _query, _active_id: (self.active, "high", [self.active]),
            ),
            build_task_plan_payload=_workflow_build_task_plan_payload,
            build_codex_review_preview=_workflow_build_codex_review_preview,
            build_validation_plan=_workflow_default_validation_plan,
            active_project_payload=lambda _pid, _room: {"active_project": {"name": "Jarvez2.0"}},
            capability_payload=lambda _pid, _room: {"capability_mode": "coding"},
        )
        self.assertTrue(async_result.success)
        workflow_state = async_result.data["workflow_state"]
        self.assertEqual(workflow_state["status"], "awaiting_approval")
        self.assertEqual(workflow_state["pending_gate"]["gate_id"], "apply_changes")

        approved_apply = await workflow_approve_action(
            {"gate_id": "apply_changes", "approved": True},
            self.ctx,
            workflow_engine=self.engine,
            active_project_payload=lambda _pid, _room: {},
            capability_payload=lambda _pid, _room: {},
        )
        self.assertTrue(approved_apply.success)
        self.assertEqual(approved_apply.data["workflow_state"]["pending_gate"]["gate_id"], "commit_and_push")

        resumed = await workflow_resume_action(
            {},
            self.ctx,
            workflow_engine=self.engine,
            active_project_payload=lambda _pid, _room: {},
            capability_payload=lambda _pid, _room: {},
        )
        self.assertTrue(resumed.success)
        self.assertEqual(resumed.data["workflow_state"]["status"], "awaiting_approval")

        approved_commit = await workflow_approve_action(
            {"gate_id": "commit_and_push", "approved": True},
            self.ctx,
            workflow_engine=self.engine,
            active_project_payload=lambda _pid, _room: {},
            capability_payload=lambda _pid, _room: {},
        )
        self.assertTrue(approved_commit.success)
        self.assertEqual(approved_commit.data["workflow_state"]["status"], "completed")

        status = await workflow_status_action(
            {},
            self.ctx,
            workflow_engine=self.engine,
            active_project_payload=lambda _pid, _room: {},
            capability_payload=lambda _pid, _room: {},
        )
        self.assertTrue(status.success)
        self.assertEqual(status.data["workflow_state"]["status"], "completed")

    async def test_workflow_run_returns_ambiguous_project(self) -> None:
        candidate_a = SimpleNamespace(project_id="p1", name="Jarvez", root_path="C:/a")
        candidate_b = SimpleNamespace(project_id="p2", name="Jarvez2", root_path="C:/b")
        result = await workflow_run_action(
            {"request": "Mudar modulo", "project_query": "jar"},
            self.ctx,
            workflow_engine=self.engine,
            get_active_project=lambda _pid, _room: None,
            resolve_project_target=lambda project_query, active_project: _workflow_resolve_project_target(
                project_query=project_query,
                active_project=active_project,
                catalog_resolve=lambda _query, _active_id: (candidate_a, "medium", [candidate_a, candidate_b]),
            ),
            build_task_plan_payload=_workflow_build_task_plan_payload,
            build_codex_review_preview=_workflow_build_codex_review_preview,
            build_validation_plan=_workflow_default_validation_plan,
            active_project_payload=lambda _pid, _room: {},
            capability_payload=lambda _pid, _room: {},
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "ambiguous project")
        self.assertTrue(result.data["project_resolution_required"])

    async def test_cancel_returns_error_when_missing(self) -> None:
        result = await workflow_cancel_action(
            {"workflow_id": "wf_unknown"},
            self.ctx,
            workflow_engine=self.engine,
            active_project_payload=lambda _pid, _room: {},
            capability_payload=lambda _pid, _room: {},
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "workflow missing")


if __name__ == "__main__":
    unittest.main()
