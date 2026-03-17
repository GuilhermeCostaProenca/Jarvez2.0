from __future__ import annotations

from livekit.plugins import google

from runtime.model_gateway import RuntimeDecision


def build_realtime_model(decision: RuntimeDecision):
    # The adapter surface is now explicit even though only Google Realtime is wired today.
    return google.beta.realtime.RealtimeModel(
        voice="Charon",
        temperature=0.6,
    )
