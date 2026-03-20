from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from identity.face_id import identify_face, unlock_with_face
from identity.identity_store import IdentityStore


class _FakeFace:
    def __init__(self, embedding: list[float]) -> None:
        self.embedding = np.asarray(embedding, dtype=np.float32)
        self.bbox = [0.0, 0.0, 10.0, 10.0]


class _FakeFaceEngine:
    def __init__(self, embeddings: list[list[float]]) -> None:
        self._embeddings = embeddings

    def get(self, frame):  # noqa: ARG002
        return [_FakeFace(embedding) for embedding in self._embeddings]


class FaceIdentificationTests(unittest.TestCase):
    def test_identify_face_returns_registered_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = IdentityStore(Path(tmp) / "profiles.json")
            store.upsert_profile(
                name="Joao",
                role="guest",
                confidence_level="medium",
                face_embeddings=[[1.0, 0.0, 0.0]],
            )
            result = identify_face(
                store,
                frame=np.zeros((16, 16, 3), dtype=np.uint8),
                engine=_FakeFaceEngine([[1.0, 0.0, 0.0]]),
                threshold=0.5,
            )

        self.assertTrue(result.matched)
        self.assertEqual(result.name, "Joao")
        self.assertTrue(result.face_detected)

    def test_identify_face_returns_unknown_when_no_face_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = IdentityStore(Path(tmp) / "profiles.json")
            result = identify_face(
                store,
                frame=np.zeros((16, 16, 3), dtype=np.uint8),
                engine=_FakeFaceEngine([]),
                threshold=0.5,
            )

        self.assertFalse(result.matched)
        self.assertEqual(result.name, "unknown")
        self.assertFalse(result.face_detected)

    def test_unlock_with_face_uses_owner_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = IdentityStore(Path(tmp) / "profiles.json")
            store.upsert_profile(
                name="Guilherme",
                role="owner",
                confidence_level="high",
                face_embeddings=[[1.0, 0.0, 0.0]],
                face_unlock_threshold=0.9,
            )
            result = unlock_with_face(
                store,
                frame=np.zeros((16, 16, 3), dtype=np.uint8),
                engine=_FakeFaceEngine([[1.0, 0.0, 0.0]]),
            )

        self.assertTrue(result.matched)
        self.assertEqual(result.name, "Guilherme")
        self.assertEqual(result.threshold_used, 0.9)

    def test_unlock_with_face_rejects_ambiguous_owner_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = IdentityStore(Path(tmp) / "profiles.json")
            store.upsert_profile(
                name="Owner A",
                role="owner",
                confidence_level="high",
                face_embeddings=[[1.0, 0.0, 0.0]],
                face_unlock_threshold=0.8,
            )
            store.upsert_profile(
                name="Owner B",
                role="owner",
                confidence_level="high",
                face_embeddings=[[0.98, 0.02, 0.0]],
                face_unlock_threshold=0.8,
            )
            result = unlock_with_face(
                store,
                frame=np.zeros((16, 16, 3), dtype=np.uint8),
                engine=_FakeFaceEngine([[0.99, 0.01, 0.0]]),
            )

        self.assertFalse(result.matched)
        self.assertEqual(result.failure_reason, "ambiguous_match")


if __name__ == "__main__":
    unittest.main()
