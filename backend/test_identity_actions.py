from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import actions as actions_module
from actions import AUTHENTICATED_SESSIONS, ActionContext, dispatch_action
from identity.face_id import FaceIdentificationResult
from identity.identity_store import IdentityStore
from identity.speaker_id import SpeakerIdentificationResult


class IdentityActionsTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        actions_module.PENDING_CONFIRMATIONS.clear()
        actions_module.PARTICIPANT_PENDING_TOKENS.clear()
        AUTHENTICATED_SESSIONS.clear()
        actions_module.VOICE_STEP_UP_PENDING.clear()
        actions_module.STATE_STORE.clear_all()

    async def test_register_identity_guest_requires_explicit_capture_only(self) -> None:
        ctx = ActionContext(job_id="job-1", room="room-a", participant_identity="user-a")
        with tempfile.TemporaryDirectory() as tmp:
            store = IdentityStore(Path(tmp) / "profiles.json")
            with patch("actions.IDENTITY_STORE", store), patch(
                "actions.extract_current_speaker_embedding",
                return_value=([0.1, 0.2, 0.3], "resemblyzer"),
            ), patch("actions.capture_face_embedding", return_value=None):
                result = await dispatch_action(
                    "register_identity",
                    {"name": "Joao", "role": "guest", "capture_voice": True, "capture_face": False},
                    ctx,
                )

            saved = store.get_profile("Joao")

        self.assertTrue(result.success)
        self.assertIsNotNone(saved)
        assert saved is not None
        self.assertEqual(saved.role, "guest")
        self.assertEqual(result.data["recognized_identity"]["name"], "Joao")
        self.assertEqual(AUTHENTICATED_SESSIONS, {})

    async def test_identify_contextual_identity_updates_snapshot_without_authenticating(self) -> None:
        ctx = ActionContext(job_id="job-2", room="room-a", participant_identity="user-a")
        with tempfile.TemporaryDirectory() as tmp:
            store = IdentityStore(Path(tmp) / "profiles.json")
            with patch("actions.IDENTITY_STORE", store), patch(
                "actions.identify_speaker",
                return_value=SpeakerIdentificationResult(
                    name="Guilherme",
                    confidence=0.93,
                    matched=True,
                    source="voice",
                    compared_profiles=1,
                    method="resemblyzer",
                ),
            ), patch(
                "actions.identify_face",
                return_value=FaceIdentificationResult(
                    name="unknown",
                    confidence=0.0,
                    matched=False,
                    face_detected=False,
                    source="face",
                    compared_profiles=0,
                    method="face_context",
                ),
            ):
                result = await dispatch_action("identify_contextual_identity", {"mode": "voice"}, ctx)

        self.assertTrue(result.success)
        self.assertEqual(result.data["recognized_identity"]["name"], "Guilherme")
        self.assertEqual(AUTHENTICATED_SESSIONS, {})
        self.assertFalse(result.data["authentication_bypass"])


if __name__ == "__main__":
    unittest.main()
