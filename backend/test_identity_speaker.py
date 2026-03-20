from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from identity.identity_store import IdentityStore
from identity import speaker_id


class SpeakerIdentificationTests(unittest.TestCase):
    def test_identify_speaker_returns_owner_with_high_confidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = IdentityStore(Path(tmp) / "profiles.json")
            store.upsert_profile(
                name="Guilherme",
                role="owner",
                confidence_level="high",
                voice_embeddings=[[0.9, 0.1, 0.0]],
            )

            result = speaker_id.identify_speaker(
                "user-a",
                store,
                embedding=[0.9, 0.1, 0.0],
                threshold=0.8,
            )

        self.assertTrue(result.matched)
        self.assertEqual(result.name, "Guilherme")
        self.assertGreaterEqual(result.confidence, 0.99)

    def test_identify_speaker_returns_unknown_for_unregistered_voice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = IdentityStore(Path(tmp) / "profiles.json")
            store.upsert_profile(
                name="Guilherme",
                role="owner",
                confidence_level="high",
                voice_embeddings=[[1.0, 0.0, 0.0]],
            )

            result = speaker_id.identify_speaker(
                "user-a",
                store,
                embedding=[0.0, 1.0, 0.0],
                threshold=0.8,
            )

        self.assertFalse(result.matched)
        self.assertEqual(result.name, "unknown")
        self.assertLess(result.confidence, 0.8)

    def test_identify_speaker_does_not_call_verify_voice_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = IdentityStore(Path(tmp) / "profiles.json")
            store.upsert_profile(
                name="Guilherme",
                role="owner",
                confidence_level="high",
                voice_embeddings=[[0.8, 0.2]],
            )
            forbidden = Mock(side_effect=AssertionError("identify_speaker must not call verify_voice_identity"))
            with patch.object(speaker_id, "verify_voice_identity", forbidden, create=True):
                result = speaker_id.identify_speaker(
                    "user-a",
                    store,
                    embedding=[0.8, 0.2],
                    threshold=0.7,
                )

        self.assertTrue(result.matched)
        forbidden.assert_not_called()

    def test_unlock_with_voice_uses_owner_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = IdentityStore(Path(tmp) / "profiles.json")
            store.upsert_profile(
                name="Guilherme",
                role="owner",
                confidence_level="high",
                voice_embeddings=[[0.95, 0.05]],
                voice_unlock_threshold=0.9,
            )

            result = speaker_id.unlock_with_voice(
                "user-a",
                store,
                embedding=[0.95, 0.05],
            )

        self.assertTrue(result.matched)
        self.assertEqual(result.name, "Guilherme")
        self.assertEqual(result.threshold_used, 0.9)

    def test_unlock_with_voice_rejects_ambiguous_owner_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = IdentityStore(Path(tmp) / "profiles.json")
            store.upsert_profile(
                name="Guilherme",
                role="owner",
                confidence_level="high",
                voice_embeddings=[[0.95, 0.05]],
                voice_unlock_threshold=0.8,
            )
            store.upsert_profile(
                name="Outro Owner",
                role="owner",
                confidence_level="high",
                voice_embeddings=[[0.93, 0.07]],
                voice_unlock_threshold=0.8,
            )

            result = speaker_id.unlock_with_voice(
                "user-a",
                store,
                embedding=[0.94, 0.06],
            )

        self.assertFalse(result.matched)
        self.assertEqual(result.failure_reason, "ambiguous_match")


if __name__ == "__main__":
    unittest.main()
