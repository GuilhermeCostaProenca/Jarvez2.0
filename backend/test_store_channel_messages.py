from __future__ import annotations

import gc
import shutil
import tempfile
from pathlib import Path
import unittest
import uuid

from actions_core.store import JarvezStateStore


class StoreChannelMessagesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.gettempdir()) / f"jarvez_store_test_{uuid.uuid4().hex[:10]}"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.temp_dir / "state.db"
        self.store = JarvezStateStore(self.db_path)

    def tearDown(self) -> None:
        self.store = None
        gc.collect()
        for suffix in ("", "-wal", "-shm"):
            try:
                (self.db_path.parent / f"{self.db_path.name}{suffix}").unlink(missing_ok=True)
            except Exception:
                pass
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_append_channel_message_deduplicates_by_external_id(self) -> None:
        inserted_first = self.store.append_channel_message(
            channel="whatsapp",
            direction="inbound",
            participant_identity="5511999999999",
            room="whatsapp_legacy_v1",
            address="5511999999999",
            text="oi",
            payload={"id": "wamid.1", "text": "oi"},
            external_message_id="wamid.1",
            created_at="2026-03-09T00:00:00+00:00",
        )
        inserted_second = self.store.append_channel_message(
            channel="whatsapp",
            direction="inbound",
            participant_identity="5511999999999",
            room="whatsapp_legacy_v1",
            address="5511999999999",
            text="oi duplicado",
            payload={"id": "wamid.1", "text": "oi duplicado"},
            external_message_id="wamid.1",
            created_at="2026-03-09T00:00:05+00:00",
        )
        self.assertTrue(inserted_first)
        self.assertFalse(inserted_second)
        self.assertEqual(self.store.count_channel_messages(channel="whatsapp", direction="inbound"), 1)

    def test_list_and_latest_channel_messages(self) -> None:
        self.store.append_channel_message(
            channel="whatsapp",
            direction="inbound",
            participant_identity="5511000000001",
            room="whatsapp_legacy_v1",
            address="5511000000001",
            text="primeira",
            payload={"id": "wamid.2", "text": "primeira"},
            external_message_id="wamid.2",
            created_at="2026-03-09T00:01:00+00:00",
        )
        self.store.append_channel_message(
            channel="whatsapp",
            direction="outbound",
            participant_identity="user-a",
            room="room-a",
            address="5511000000001",
            text="resposta",
            payload={"type": "text", "text": "resposta"},
            external_message_id="wamid.out.1",
            created_at="2026-03-09T00:02:00+00:00",
        )
        inbound_rows = self.store.list_channel_messages(channel="whatsapp", direction="inbound", limit=10)
        self.assertEqual(len(inbound_rows), 1)
        self.assertEqual(inbound_rows[0]["text"], "primeira")

        latest_outbound = self.store.latest_channel_message(channel="whatsapp", direction="outbound")
        self.assertIsInstance(latest_outbound, dict)
        assert isinstance(latest_outbound, dict)
        self.assertEqual(latest_outbound["external_message_id"], "wamid.out.1")
        self.assertEqual(self.store.count_channel_messages(channel="whatsapp"), 2)


if __name__ == "__main__":
    unittest.main()
