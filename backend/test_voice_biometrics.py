import tempfile
import unittest
from pathlib import Path

import numpy as np

from voice_biometrics import VoiceProfileStore, VoiceVerifyResult, _compute_voice_embedding


class VoiceBiometricsTests(unittest.TestCase):
    def test_compute_voice_embedding_from_signal(self):
        sample_rate = 16000
        t = np.linspace(0.0, 2.0, num=sample_rate * 2, endpoint=False)
        signal = (0.25 * np.sin(2 * np.pi * 180 * t) + 0.15 * np.sin(2 * np.pi * 350 * t)).astype(np.float32)
        embedding = _compute_voice_embedding(signal, sample_rate)
        self.assertIsNotNone(embedding)
        self.assertGreater(embedding.size, 16)

    def test_profile_enroll_and_verify_by_embedding(self):
        with tempfile.TemporaryDirectory() as tmp:
            file_path = Path(tmp) / "voice_profiles.enc"
            store = VoiceProfileStore(file_path=file_path, key=b"x" * 32)

            sample_embedding = [0.02] * 54
            store.enroll_profile(name="Guil", participant_identity="user-a", embedding=sample_embedding)

            result: VoiceVerifyResult = store.verify_identity(participant_identity="user-z", embedding=sample_embedding)
            self.assertTrue(result.matched)
            self.assertGreaterEqual(result.score, 0.99)
            self.assertEqual(result.profile_name, "Guil")
            self.assertEqual(result.method, "audio_embedding")


if __name__ == "__main__":
    unittest.main()
