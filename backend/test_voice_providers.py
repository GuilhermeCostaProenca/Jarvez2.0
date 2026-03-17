from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from runtime.voice_providers import (
    ElevenLabsProvider,
    GoogleRealtimeProvider,
    KokoroProvider,
    OpenAIVoiceProvider,
    VoiceProviderError,
    build_voice_provider_from_env,
)


class VoiceProviderFactoryTests(unittest.TestCase):
    def test_factory_google_provider(self) -> None:
        with patch.dict(os.environ, {"JARVEZ_VOICE_PROVIDER": "google", "JARVEZ_VOICE_NAME": "Charon"}, clear=False):
            provider = build_voice_provider_from_env()
        self.assertIsInstance(provider, GoogleRealtimeProvider)
        self.assertEqual(provider.voice_name, "Charon")

    def test_factory_openai_provider(self) -> None:
        with patch.dict(os.environ, {"JARVEZ_VOICE_PROVIDER": "openai", "JARVEZ_VOICE_NAME": "nova"}, clear=False):
            provider = build_voice_provider_from_env()
        self.assertIsInstance(provider, OpenAIVoiceProvider)
        self.assertEqual(provider.voice_name, "nova")

    def test_invalid_provider_falls_back_to_google(self) -> None:
        with patch.dict(os.environ, {"JARVEZ_VOICE_PROVIDER": "invalid-provider"}, clear=False):
            with self.assertLogs("runtime.voice_providers", level="WARNING") as captured:
                provider = build_voice_provider_from_env()
        self.assertIsInstance(provider, GoogleRealtimeProvider)
        self.assertTrue(any("falling back" in line.lower() or "usando google" in line.lower() for line in captured.output))

    def test_lazy_import_errors_are_clear(self) -> None:
        with patch.dict(os.environ, {"JARVEZ_VOICE_PROVIDER": "elevenlabs"}, clear=False):
            provider = build_voice_provider_from_env()
        self.assertIsInstance(provider, ElevenLabsProvider)
        with patch("runtime.voice_providers.importlib.import_module", side_effect=ImportError("missing elevenlabs")):
            with self.assertRaisesRegex(VoiceProviderError, "pip install elevenlabs"):
                self._run_async(provider.synthesize("teste"))

        with patch.dict(os.environ, {"JARVEZ_VOICE_PROVIDER": "kokoro"}, clear=False):
            provider = build_voice_provider_from_env()
        self.assertIsInstance(provider, KokoroProvider)
        with patch("runtime.voice_providers.importlib.import_module", side_effect=ImportError("missing kokoro_onnx")):
            with self.assertRaisesRegex(VoiceProviderError, "pip install kokoro-onnx soundfile"):
                self._run_async(provider.synthesize("teste"))

    def _run_async(self, awaitable):
        import asyncio

        return asyncio.run(awaitable)


if __name__ == "__main__":
    unittest.main()
