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
        self.assertEqual(result.data["auth_state"]["status"], "locked")
        self.assertEqual(result.data["voice_samples_collected"], 1)
        self.assertEqual(result.data["recommended_voice_samples_remaining"], 4)
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
        self.assertEqual(result.data["auth_state"]["status"], "locked")
        self.assertEqual(AUTHENTICATED_SESSIONS, {})
        self.assertFalse(result.data["authentication_bypass"])

    async def test_unlock_with_voice_unlocks_owner_without_password(self) -> None:
        ctx = ActionContext(job_id="job-3", room="room-a", participant_identity="user-a")
        with tempfile.TemporaryDirectory() as tmp:
            store = IdentityStore(Path(tmp) / "profiles.json")
            store.upsert_profile(
                name="Guilherme",
                role="owner",
                confidence_level="high",
                voice_embeddings=[[0.9, 0.1]],
                voice_unlock_threshold=0.9,
            )
            with patch(
                "actions.unlock_with_voice",
                return_value=SpeakerIdentificationResult(
                    name="Guilherme",
                    confidence=0.96,
                    matched=True,
                    source="voice",
                    compared_profiles=1,
                    method="resemblyzer",
                    threshold_used=0.9,
                    margin_to_second=0.25,
                ),
            ), patch("actions.IDENTITY_STORE", store):
                result = await dispatch_action("unlock_with_voice", {}, ctx)

        self.assertTrue(result.success)
        self.assertEqual(result.data["auth_state"]["status"], "unlocked_by_voice")
        self.assertEqual(result.data["recognized_identity"]["name"], "Guilherme")
        self.assertTrue(result.data["private_access_granted"])

    async def test_unlock_with_voice_rejects_guest_profile(self) -> None:
        ctx = ActionContext(job_id="job-4", room="room-a", participant_identity="user-a")
        with tempfile.TemporaryDirectory() as tmp:
            store = IdentityStore(Path(tmp) / "profiles.json")
            store.upsert_profile(
                name="Joao",
                role="guest",
                confidence_level="medium",
                voice_embeddings=[[0.9, 0.1]],
                voice_unlock_threshold=0.9,
            )
            with patch(
                "actions.unlock_with_voice",
                return_value=SpeakerIdentificationResult(
                    name="Joao",
                    confidence=0.95,
                    matched=True,
                    source="voice",
                    compared_profiles=1,
                    method="resemblyzer",
                    threshold_used=0.9,
                    margin_to_second=0.20,
                ),
            ), patch("actions.IDENTITY_STORE", store):
                result = await dispatch_action("unlock_with_voice", {}, ctx)

        self.assertFalse(result.success)
        self.assertEqual(result.error, "voice_unlock_not_owner")
        self.assertEqual(result.data["auth_state"]["status"], "locked")

    async def test_unlock_with_face_unlocks_owner_without_password(self) -> None:
        ctx = ActionContext(job_id="job-5", room="room-a", participant_identity="user-a")
        with tempfile.TemporaryDirectory() as tmp:
            store = IdentityStore(Path(tmp) / "profiles.json")
            store.upsert_profile(
                name="Guilherme",
                role="owner",
                confidence_level="high",
                face_embeddings=[[1.0, 0.0, 0.0]],
                face_unlock_threshold=0.9,
            )
            with patch(
                "actions.unlock_with_face",
                return_value=FaceIdentificationResult(
                    name="Guilherme",
                    confidence=0.95,
                    matched=True,
                    face_detected=True,
                    source="face",
                    compared_profiles=1,
                    method="insightface",
                    threshold_used=0.9,
                    margin_to_second=0.20,
                ),
            ), patch("actions.IDENTITY_STORE", store):
                result = await dispatch_action("unlock_with_face", {}, ctx)

        self.assertTrue(result.success)
        self.assertEqual(result.data["auth_state"]["status"], "unlocked_by_face")
        self.assertEqual(result.data["recognized_identity"]["name"], "Guilherme")
        self.assertTrue(result.data["private_access_granted"])

    async def test_unlock_with_face_rejects_guest_profile(self) -> None:
        ctx = ActionContext(job_id="job-6", room="room-a", participant_identity="user-a")
        with tempfile.TemporaryDirectory() as tmp:
            store = IdentityStore(Path(tmp) / "profiles.json")
            store.upsert_profile(
                name="Joao",
                role="guest",
                confidence_level="medium",
                face_embeddings=[[1.0, 0.0, 0.0]],
                face_unlock_threshold=0.9,
            )
            with patch(
                "actions.unlock_with_face",
                return_value=FaceIdentificationResult(
                    name="Joao",
                    confidence=0.96,
                    matched=True,
                    face_detected=True,
                    source="face",
                    compared_profiles=1,
                    method="insightface",
                    threshold_used=0.9,
                    margin_to_second=0.22,
                ),
            ), patch("actions.IDENTITY_STORE", store):
                result = await dispatch_action("unlock_with_face", {}, ctx)

        self.assertFalse(result.success)
        self.assertEqual(result.error, "face_unlock_not_owner")
        self.assertEqual(result.data["auth_state"]["status"], "locked")

    async def test_unlock_with_face_sets_presence_lost_when_no_face_detected(self) -> None:
        ctx = ActionContext(job_id="job-7", room="room-a", participant_identity="user-a")
        with tempfile.TemporaryDirectory() as tmp:
            store = IdentityStore(Path(tmp) / "profiles.json")
            with patch(
                "actions.unlock_with_face",
                return_value=FaceIdentificationResult(
                    name="unknown",
                    confidence=0.0,
                    matched=False,
                    face_detected=False,
                    source="face",
                    compared_profiles=0,
                    method="face_context",
                    threshold_used=0.9,
                    failure_reason="face_not_detected",
                ),
            ), patch("actions.IDENTITY_STORE", store):
                result = await dispatch_action("unlock_with_face", {}, ctx)

        self.assertFalse(result.success)
        self.assertEqual(result.error, "face_unlock_failed")
        self.assertEqual(result.data["auth_state"]["relock_reason"], "presence_lost")


if __name__ == "__main__":
    unittest.main()
