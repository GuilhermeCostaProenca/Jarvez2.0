from __future__ import annotations

import gc
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
import types
import unittest
import uuid
from unittest.mock import AsyncMock, patch

if "numpy" not in sys.modules:
    numpy_stub = types.ModuleType("numpy")
    numpy_stub.ndarray = object
    sys.modules["numpy"] = numpy_stub

import actions as actions_module
from actions import ActionContext, dispatch_action
from actions_core.store import JarvezStateStore
from memory import MemoryManager
from proactivity.suggestion_engine import PROACTIVITY_NAMESPACE, SuggestionEngine


class FakeMem0:
    async def get_all(self, **_kwargs):  # noqa: ANN003
        return []

    async def search(self, *_args, **_kwargs):  # noqa: ANN003
        return []

    async def add(self, *_args, **_kwargs):  # noqa: ANN003
        return None


class ProactivityEngineTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.gettempdir()) / f"jarvez_proactivity_test_{uuid.uuid4().hex[:10]}"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.temp_dir / "state.db"
        self.store = JarvezStateStore(self.db_path)
        self.memory_manager = MemoryManager(mem0=FakeMem0(), state_store=self.store)
        actions_module.STATE_STORE.clear_all()

    def tearDown(self) -> None:
        self.store = None
        gc.collect()
        for suffix in ("", "-wal", "-shm"):
            try:
                (self.db_path.parent / f"{self.db_path.name}{suffix}").unlink(missing_ok=True)
            except Exception:
                pass
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_morning_briefing_suggestion_uses_real_context(self) -> None:
        engine = SuggestionEngine(state_store=self.store, memory_manager=self.memory_manager)
        self.memory_manager.set_preference(
            participant_identity="user-pro",
            key="routine_recurring",
            value=["daily_briefing"],
        )
        self.memory_manager.set_preference(
            participant_identity="user-pro",
            key="proactivity_intensity",
            value="active",
        )
        payload = engine.evaluate(
            participant_identity="user-pro",
            room="room-pro",
            now=datetime(2026, 3, 17, 8, 0, tzinfo=timezone.utc),
            persist=False,
        )

        self.assertEqual(payload["status"], "suggested")
        self.assertEqual(payload["controls"]["intensity"], "active")
        self.assertTrue(payload["suggestions"])
        suggestion = payload["suggestions"][0]
        self.assertEqual(suggestion["kind"], "daily_briefing")
        self.assertTrue(suggestion["auto_execute"])
        self.assertEqual(suggestion["action_name"], "automation_run_now")
        self.assertIn("manha", suggestion["reason"])

    def test_cooldown_blocks_repeated_suggestion(self) -> None:
        engine = SuggestionEngine(state_store=self.store, memory_manager=self.memory_manager, default_cooldown_seconds=1800)
        self.memory_manager.set_preference(
            participant_identity="user-pro",
            key="routine_recurring",
            value=["daily_briefing"],
        )
        first = engine.evaluate(
            participant_identity="user-pro",
            room="room-pro",
            now=datetime(2026, 3, 17, 8, 0, tzinfo=timezone.utc),
            persist=True,
        )
        second = engine.evaluate(
            participant_identity="user-pro",
            room="room-pro",
            now=datetime(2026, 3, 17, 8, 10, tzinfo=timezone.utc),
            persist=False,
        )

        self.assertEqual(first["status"], "suggested")
        self.assertEqual(second["status"], "cooldown")
        self.assertEqual(second["suggestions"], [])

    async def test_ambiguous_action_emits_confirming_before_execution(self) -> None:
        global_memory = MemoryManager(mem0=FakeMem0(), state_store=actions_module.STATE_STORE)
        global_memory.set_preference(
            participant_identity="user-pro",
            key="preferred_devices",
            value=[
                {"type": "ac", "name": "Ar da Sala"},
                {"type": "ac", "name": "Ar do Quarto"},
            ],
        )
        ctx = ActionContext(
            job_id="job-pro-1",
            room="room-pro",
            participant_identity="user-pro",
            session=object(),
        )
        published_payloads: list[dict[str, object]] = []

        async def _fake_publish(_session, payload):  # noqa: ANN001
            if isinstance(payload, dict):
                published_payloads.append(dict(payload))

        with patch("actions.publish_session_event", side_effect=_fake_publish):
            with patch("actions._publish_session_snapshot_for_context", AsyncMock()):
                result = await dispatch_action(
                    "ac_turn_on",
                    {},
                    ctx,
                    skip_confirmation=True,
                    bypass_auth=True,
                )

        self.assertTrue(result.success)
        self.assertTrue(result.data.get("clarification_required"))
        self.assertIn("Qual deles", result.message)
        voice_payload = actions_module.STATE_STORE.get_event_state(
            participant_identity="user-pro",
            room="room-pro",
            namespace="voice_interactivity",
        )
        proactive_payload = actions_module.STATE_STORE.get_event_state(
            participant_identity="user-pro",
            room="room-pro",
            namespace=PROACTIVITY_NAMESPACE,
        )
        self.assertEqual(voice_payload["state"], "confirming")
        self.assertTrue(voice_payload["clarification_required"])
        self.assertEqual(proactive_payload["status"], "clarifying")
        self.assertEqual(proactive_payload["clarification"]["options"], ["Ar da Sala", "Ar do Quarto"])
        event_types = [payload.get("type") for payload in published_payloads]
        self.assertIn("voice_interactivity_state", event_types)
        self.assertIn("proactivity_state", event_types)


if __name__ == "__main__":
    unittest.main()
