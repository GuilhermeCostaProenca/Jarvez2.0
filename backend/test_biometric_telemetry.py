from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import actions as actions_module
from actions import AUTHENTICATED_SESSIONS, ActionContext, dispatch_action
from identity.biometric_telemetry import BiometricTelemetryStore
from identity.speaker_id import SpeakerIdentificationResult


class BiometricTelemetryStoreTests(unittest.TestCase):
    def test_append_event_drops_raw_biometric_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = BiometricTelemetryStore(Path(tmp) / "biometric_telemetry.jsonl")
            store.append_event(
                {
                    "event_type": "unlock_failure",
                    "participant_identity": "user-a",
                    "room": "room-a",
                    "method": "voice",
                    "failure_reason": "threshold_low",
                    "raw_audio": "should-not-persist",
                    "face_frame_path": "frame.png",
                    "embedding": [0.1, 0.2, 0.3],
                }
            )

            rows = store.file_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(rows), 1)
            payload = json.loads(rows[0])

        self.assertEqual(payload["event_type"], "unlock_failure")
        self.assertEqual(payload["failure_reason"], "threshold_low")
        self.assertNotIn("raw_audio", payload)
        self.assertNotIn("face_frame_path", payload)
        self.assertNotIn("embedding", payload)

    def test_recent_failure_reasons_filters_and_orders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = BiometricTelemetryStore(Path(tmp) / "biometric_telemetry.jsonl")
            store.append_event(
                {
                    "timestamp": "2026-03-20T10:00:00+00:00",
                    "event_type": "unlock_failure",
                    "participant_identity": "user-a",
                    "room": "room-a",
                    "method": "voice",
                    "failure_reason": "threshold_low",
                }
            )
            store.append_event(
                {
                    "timestamp": "2026-03-20T10:01:00+00:00",
                    "event_type": "relock",
                    "participant_identity": "user-a",
                    "room": "room-a",
                    "method": "face",
                    "relock_reason": "timeout",
                }
            )
            store.append_event(
                {
                    "timestamp": "2026-03-20T10:02:00+00:00",
                    "event_type": "unlock_success",
                    "participant_identity": "user-a",
                    "room": "room-a",
                    "method": "voice",
                }
            )

            failures = store.recent_failure_reasons(participant_identity="user-a", room="room-a", limit=2)

        self.assertEqual(
            failures,
            [
                {
                    "timestamp": "2026-03-20T10:01:00+00:00",
                    "method": "face",
                    "reason": "timeout",
                    "event_type": "relock",
                },
                {
                    "timestamp": "2026-03-20T10:00:00+00:00",
                    "method": "voice",
                    "reason": "threshold_low",
                    "event_type": "unlock_failure",
                },
            ],
        )


class BiometricTelemetryIntegrationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        AUTHENTICATED_SESSIONS.clear()
        actions_module.PENDING_CONFIRMATIONS.clear()
        actions_module.PARTICIPANT_PENDING_TOKENS.clear()
        actions_module.VOICE_STEP_UP_PENDING.clear()
        actions_module.STATE_STORE.clear_all()

    async def test_unlock_with_voice_failure_records_telemetry(self) -> None:
        ctx = ActionContext(job_id="job-1", room="room-a", participant_identity="user-a")
        with tempfile.TemporaryDirectory() as tmp:
            store = BiometricTelemetryStore(Path(tmp) / "biometric_telemetry.jsonl")
            with patch("actions.BIOMETRIC_TELEMETRY_STORE", store), patch(
                "actions.unlock_with_voice",
                return_value=SpeakerIdentificationResult(
                    name="unknown",
                    confidence=0.42,
                    matched=False,
                    source="voice",
                    compared_profiles=1,
                    method="resemblyzer",
                    threshold_used=0.9,
                    margin_to_second=0.1,
                    failure_reason="threshold_low",
                ),
            ):
                result = await dispatch_action("unlock_with_voice", {}, ctx)

            events = store.list_events(participant_identity="user-a", room="room-a", limit=10)

        self.assertFalse(result.success)
        self.assertEqual(result.data["recent_biometric_failures"][0]["reason"], "threshold_low")
        self.assertEqual([event["event_type"] for event in events], ["unlock_failure", "unlock_attempt"])

    async def test_authenticate_identity_includes_recent_biometric_failures(self) -> None:
        ctx = ActionContext(job_id="job-2", room="room-a", participant_identity="user-a")
        with tempfile.TemporaryDirectory() as tmp:
            store = BiometricTelemetryStore(Path(tmp) / "biometric_telemetry.jsonl")
            store.append_event(
                {
                    "event_type": "unlock_failure",
                    "participant_identity": "user-a",
                    "room": "room-a",
                    "method": "voice",
                    "failure_reason": "ambiguous_match",
                }
            )
            with patch("actions.BIOMETRIC_TELEMETRY_STORE", store), patch("actions.os.getenv") as getenv:
                getenv.side_effect = lambda key, default="": "1234" if key == "JARVEZ_SECURITY_PIN" else default
                result = await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)

        self.assertTrue(result.success)
        self.assertEqual(result.data["recent_biometric_failures"][0]["reason"], "ambiguous_match")


if __name__ == "__main__":
    unittest.main()
