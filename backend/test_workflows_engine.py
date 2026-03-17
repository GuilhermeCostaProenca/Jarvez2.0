from __future__ import annotations

import unittest

from workflows.engine import WorkflowEngine
from workflows.state import WorkflowStateRepository, cancel_workflow_state


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
            "project": {"project_id": "proj_1", "name": "Jarvez2.0"},
            "summary": "Projeto resolvido.",
        },
        "build_plan": lambda _state, _step: {
            "task_plan": {"steps": ["a", "b"]},
            "summary": "Plano gerado.",
        },
        "codex_review": lambda _state, _step: {
            "codex_review": {"mode": "read-only", "result": "ok"},
            "summary": "Review concluida.",
        },
        "apply_changes": lambda _state, _step: {
            "apply_result": {"mode": "workspace-write", "files_changed": 2},
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


class WorkflowsEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = _MemoryStore()
        self.clock = _Clock()
        self.repository = WorkflowStateRepository(store=self.store)
        self.engine = WorkflowEngine(
            repository=self.repository,
            step_executors=_build_executors(),
            now_iso=self.clock.now_iso,
            workflow_id_factory=lambda: "wf_test_001",
        )

    def test_start_persists_and_stops_at_first_gate(self) -> None:
        state = self.engine.start_idea_to_code(
            participant_identity="user-1",
            room="room-1",
            request="Implementar F2.4",
        )
        payload = state.to_payload()
        self.assertEqual(state.status, "awaiting_approval")
        self.assertEqual(state.current_step_index, 3)
        self.assertEqual(payload["pending_gate"]["gate_id"], "apply_changes")
        self.assertEqual(payload["steps"][0]["status"], "completed")
        self.assertEqual(payload["steps"][1]["status"], "completed")
        self.assertEqual(payload["steps"][2]["status"], "completed")

        persisted = self.repository.get_workflow(participant_identity="user-1", room="room-1")
        self.assertIsNotNone(persisted)
        assert persisted is not None
        self.assertEqual(persisted.workflow_id, "wf_test_001")
        self.assertEqual(persisted.status, "awaiting_approval")

    def test_approve_resume_and_finish(self) -> None:
        self.engine.start_idea_to_code(
            participant_identity="user-1",
            room="room-1",
            request="Implementar F2.4",
        )
        after_apply = self.engine.approve_gate(
            participant_identity="user-1",
            room="room-1",
            gate_id="apply_changes",
            approved=True,
        )
        self.assertEqual(after_apply.status, "awaiting_approval")
        self.assertEqual(after_apply.current_step_index, 5)
        self.assertEqual(after_apply.pending_gate["gate_id"], "commit_and_push")

        resumed = self.engine.resume_workflow(participant_identity="user-1", room="room-1")
        assert resumed is not None
        self.assertEqual(resumed.status, "awaiting_approval")

        completed = self.engine.approve_gate(
            participant_identity="user-1",
            room="room-1",
            gate_id="commit_and_push",
            approved=True,
        )
        self.assertEqual(completed.status, "completed")
        self.assertIsNotNone(completed.finished_at)

    def test_reject_gate_cancels_workflow(self) -> None:
        self.engine.start_idea_to_code(
            participant_identity="user-1",
            room="room-1",
            request="Implementar F2.4",
        )
        cancelled = self.engine.approve_gate(
            participant_identity="user-1",
            room="room-1",
            gate_id="apply_changes",
            approved=False,
            note="nao seguir",
        )
        self.assertEqual(cancelled.status, "cancelled")
        self.assertIn("rejeicao", cancelled.summary)
        self.assertIsNotNone(cancelled.finished_at)

    def test_cancel_workflow_state_compatibility(self) -> None:
        state = self.engine.start_idea_to_code(
            participant_identity="user-1",
            room="room-1",
            request="Implementar F2.4",
        )
        cancelled_payload = cancel_workflow_state(state.to_payload())
        self.assertEqual(cancelled_payload["status"], "cancelled")
        self.assertIn("cancelado", str(cancelled_payload["summary"]).lower())
        self.assertIsNotNone(cancelled_payload.get("finished_at"))


if __name__ == "__main__":
    unittest.main()
