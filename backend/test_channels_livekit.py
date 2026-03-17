from __future__ import annotations

import unittest
from types import SimpleNamespace

from channels.livekit_adapter import (
    build_livekit_event_envelope,
    normalize_livekit_data_packet,
)


class ChannelsLivekitTests(unittest.TestCase):
    def test_normalize_livekit_data_packet_decodes_json_payload(self) -> None:
        packet = SimpleNamespace(
            topic="jarvez.client.telemetry",
            data=b'{"type":"autonomy_notice_delivery","channel":"browser_tts"}',
            participant=SimpleNamespace(identity="user-1"),
        )
        envelope = normalize_livekit_data_packet(packet, room="room-a")
        self.assertIsNotNone(envelope)
        assert envelope is not None
        self.assertEqual(envelope.topic, "jarvez.client.telemetry")
        self.assertEqual(envelope.identity.channel, "livekit")
        self.assertEqual(envelope.identity.participant_identity, "user-1")
        self.assertEqual(envelope.identity.room, "room-a")
        self.assertEqual(envelope.raw_payload["payload"]["channel"], "browser_tts")

    def test_normalize_livekit_data_packet_rejects_non_bytes(self) -> None:
        packet = SimpleNamespace(
            topic="jarvez.client.telemetry",
            data="not-bytes",
            participant=SimpleNamespace(identity="user-1"),
        )
        envelope = normalize_livekit_data_packet(packet, room="room-a")
        self.assertIsNone(envelope)

    def test_build_livekit_event_envelope_serializes_payload(self) -> None:
        envelope = build_livekit_event_envelope(
            participant_identity="agent",
            room="room-a",
            payload={"type": "session_snapshot", "ok": True},
        )
        self.assertEqual(envelope.topic, "lk.agent.events")
        self.assertIn('"type": "session_snapshot"', envelope.text)
        self.assertEqual(envelope.identity.participant_identity, "agent")


if __name__ == "__main__":
    unittest.main()
