from __future__ import annotations

import unittest
from types import SimpleNamespace

from actions_core.events import publish_session_event


class _LocalParticipant:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []
        self.identity = "agent-local"

    async def publish_data(self, text: str, *, topic: str | None = None) -> None:
        self.calls.append((text, topic))


class ActionsCoreEventsTests(unittest.IsolatedAsyncioTestCase):
    async def test_publish_session_event_uses_livekit_topic(self) -> None:
        participant = _LocalParticipant()
        room = SimpleNamespace(name="room-1", local_participant=participant)
        session = SimpleNamespace(room_io=SimpleNamespace(room=room))
        await publish_session_event(session, {"type": "session_snapshot", "ok": True})
        self.assertEqual(len(participant.calls), 1)
        text, topic = participant.calls[0]
        self.assertEqual(topic, "lk.agent.events")
        self.assertIn('"type": "session_snapshot"', text)

    async def test_publish_session_event_ignores_none_session(self) -> None:
        await publish_session_event(None, {"type": "noop"})


if __name__ == "__main__":
    unittest.main()
