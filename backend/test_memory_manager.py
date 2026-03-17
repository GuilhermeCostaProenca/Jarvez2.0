from __future__ import annotations

import gc
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest
import uuid

from actions_core.store import JarvezStateStore
from memory.memory_manager import MemoryManager


class FakeMem0:
    def __init__(self) -> None:
        self.scope_data: dict[str, list[dict[str, str]]] = {}

    async def get_all(self, *, user_id: str) -> list[dict[str, str]]:
        return list(self.scope_data.get(user_id, []))

    async def search(self, *_args, **_kwargs) -> list[dict[str, str]]:
        return []

    async def add(self, batch: list[dict[str, str]], *, user_id: str) -> None:
        current = list(self.scope_data.get(user_id, []))
        for item in batch:
            current.append({"memory": str(item.get("content") or ""), "updated_at": "2026-03-17T00:00:00+00:00"})
        self.scope_data[user_id] = current


class MemoryManagerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.gettempdir()) / f"jarvez_memory_test_{uuid.uuid4().hex[:10]}"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.temp_dir / "state.db"
        self.store = JarvezStateStore(self.db_path)
        self.mem0 = FakeMem0()

    def tearDown(self) -> None:
        self.store = None
        gc.collect()
        for suffix in ("", "-wal", "-shm"):
            try:
                (self.db_path.parent / f"{self.db_path.name}{suffix}").unlink(missing_ok=True)
            except Exception:
                pass
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    async def test_persist_turns_and_load_recent_n(self) -> None:
        manager = MemoryManager(mem0=self.mem0, state_store=self.store, recent_turn_limit=2)
        base = datetime(2026, 3, 17, 12, 0, tzinfo=timezone.utc)
        manager.record_turn(
            session_id="session-a",
            participant_identity="user-a",
            room="room-1",
            role="user",
            content="primeiro turno",
            timestamp=base.isoformat(),
        )
        manager.record_turn(
            session_id="session-a",
            participant_identity="user-a",
            room="room-1",
            role="assistant",
            content="segundo turno",
            timestamp=(base + timedelta(minutes=1)).isoformat(),
        )
        manager.record_turn(
            session_id="session-a",
            participant_identity="user-a",
            room="room-1",
            role="user",
            content="terceiro turno relevante",
            timestamp=(base + timedelta(minutes=2)).isoformat(),
        )

        bootstrap = await manager.load_bootstrap_context(
            participant_identity="user-a",
            room="room-1",
            user_name="Usuario",
            authenticated=False,
        )

        self.assertEqual(len(bootstrap.recent_turns), 2)
        self.assertEqual(bootstrap.recent_turns[0]["content"], "segundo turno")
        self.assertEqual(bootstrap.recent_turns[1]["content"], "terceiro turno relevante")
        self.assertTrue(any("recent_turns" in message for message in bootstrap.prompt_messages))

    async def test_preferences_persist_between_instances(self) -> None:
        manager = MemoryManager(mem0=self.mem0, state_store=self.store)
        manager.set_preference(
            participant_identity="user-a",
            key="response_tone",
            value={"value": "natural"},
        )

        reloaded_store = JarvezStateStore(self.db_path)
        reloaded_manager = MemoryManager(mem0=self.mem0, state_store=reloaded_store)
        preference = reloaded_manager.get_preference(participant_identity="user-a", key="response_tone")

        self.assertEqual(preference, {"value": "natural"})

    async def test_old_turns_become_summary_instead_of_disappearing(self) -> None:
        manager = MemoryManager(mem0=self.mem0, state_store=self.store, summary_after_days=1)
        old_timestamp = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        manager.record_turn(
            session_id="session-old",
            participant_identity="user-a",
            room="room-1",
            role="user",
            content="Prefiro abrir o Spotify de manha.",
            timestamp=old_timestamp,
        )
        manager.record_turn(
            session_id="session-old",
            participant_identity="user-a",
            room="room-1",
            role="assistant",
            content="Entendido, vou lembrar disso.",
            timestamp=old_timestamp,
        )

        manager.summarize_and_prune_old_turns(participant_identity="user-a", room="room-1")

        summary = self.store.get_latest_session_summary(participant_identity="user-a", room="room-1")
        remaining_turns = self.store.list_conversation_turns(
            participant_identity="user-a",
            room="room-1",
            limit=10,
        )

        self.assertIsNotNone(summary)
        assert isinstance(summary, dict)
        self.assertIn("Spotify", summary["summary"])
        self.assertEqual(remaining_turns, [])


if __name__ == "__main__":
    unittest.main()
