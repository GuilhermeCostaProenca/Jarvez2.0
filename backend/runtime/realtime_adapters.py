from __future__ import annotations

import logging
from dataclasses import dataclass

from runtime.model_gateway import RuntimeDecision
from runtime.voice_providers import (
    GoogleRealtimeProvider,
    VoiceProvider,
    build_voice_provider_from_env,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class VoiceRuntime:
    model: object
    tts: object | None
    provider: VoiceProvider


def _build_google_realtime_model(*, voice_name: str, audio_output: bool) -> object:
    from livekit.plugins import google  # must be imported at top-level in agent.py first

    modalities = ["AUDIO"] if audio_output else ["TEXT"]
    return google.beta.realtime.RealtimeModel(
        voice=voice_name,
        temperature=0.72,
        modalities=modalities,
    )


def build_realtime_runtime(decision: RuntimeDecision) -> VoiceRuntime:  # noqa: ARG001
    provider = build_voice_provider_from_env()
    if provider.provider_name == "google":
        return VoiceRuntime(
            model=_build_google_realtime_model(voice_name=provider.voice_name, audio_output=True),
            tts=None,
            provider=provider,
        )

    fallback_google_voice = GoogleRealtimeProvider.default_voice_name
    logger.info(
        "voice_provider=%s selected with voice=%s; keeping Google Realtime in text mode and using provider TTS.",
        provider.provider_name,
        provider.voice_name,
    )
    return VoiceRuntime(
        model=_build_google_realtime_model(voice_name=fallback_google_voice, audio_output=False),
        tts=provider.build_livekit_tts(),
        provider=provider,
    )


def build_realtime_model(decision: RuntimeDecision):
    return build_realtime_runtime(decision).model
