from __future__ import annotations

import sys
from types import SimpleNamespace
import unittest

import session_snapshot


class SessionSnapshotTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self._previous_actions = sys.modules.get("actions")

    def tearDown(self) -> None:
        if self._previous_actions is None:
            sys.modules.pop("actions", None)
        else:
            sys.modules["actions"] = self._previous_actions

    def _install_actions_stub(self) -> None:
        def _load_event_namespace(participant_identity: str, room: str, namespace: str):
            _ = participant_identity
            _ = room
            return {"namespace": namespace}

        stub = SimpleNamespace(
            _security_status_payload=lambda participant_identity, room: {
                "security_status": {
                    "authenticated": True,
                    "identity_bound": bool(participant_identity),
                },
                "room": room,
            },
            _load_event_namespace=_load_event_namespace,
            _codex_task_to_payload=lambda task: {"task_id": getattr(task, "task_id", "")},
            get_active_codex_task=lambda participant_identity, room: SimpleNamespace(task_id=f"{participant_identity}:{room}"),
            _codex_history_payload=lambda participant_identity, room: [
                {"task_id": f"{participant_identity}:{room}:history"}
            ],
        )
        sys.modules["actions"] = stub

    def test_build_session_snapshot_includes_core_namespaces(self) -> None:
        self._install_actions_stub()
        payload = session_snapshot.build_session_snapshot("user-a", "room-1")
        self.assertEqual(payload.get("type"), "session_snapshot")
        snapshot = payload.get("snapshot")
        self.assertIsInstance(snapshot, dict)
        assert isinstance(snapshot, dict)
        for key in (
            "security_session",
            "research_schedules",
            "model_route",
            "subagent_states",
            "policy_events",
            "execution_traces",
            "eval_metrics_summary",
            "slo_report",
            "providers_health",
            "feature_flags",
            "canary_state",
            "incident_snapshot",
            "playbook_report",
            "auto_remediation",
            "canary_promotion",
            "control_tick",
            "active_codex_task",
            "codex_history",
            "browser_tasks",
            "workflow_state",
            "automation_state",
            "whatsapp_channel",
        ):
            self.assertIn(key, snapshot)

    async def test_publish_session_snapshot_forwards_payload(self) -> None:
        self._install_actions_stub()
        captured: dict[str, object] = {}

        async def _publish(session, payload):
            captured["session"] = session
            captured["payload"] = payload

        original_publish = session_snapshot.publish_session_event
        session_snapshot.publish_session_event = _publish
        try:
            fake_session = object()
            await session_snapshot.publish_session_snapshot(
                fake_session,
                participant_identity="user-b",
                room="room-2",
            )
        finally:
            session_snapshot.publish_session_event = original_publish

        self.assertIs(captured.get("session"), fake_session)
        payload = captured.get("payload")
        self.assertIsInstance(payload, dict)
        assert isinstance(payload, dict)
        self.assertEqual(payload.get("type"), "session_snapshot")


if __name__ == "__main__":
    unittest.main()
