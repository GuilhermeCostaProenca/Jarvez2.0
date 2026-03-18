from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np

from voice_biometrics import get_recent_voice_audio, get_recent_voice_embedding

from .identity_store import IdentityStore

try:
    from resemblyzer import VoiceEncoder, preprocess_wav
except Exception:  # pragma: no cover - optional runtime dependency
    VoiceEncoder = None
    preprocess_wav = None


_VOICE_ENCODER: Any | None = None
_VOICE_ENCODER_FAILED = False


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    lhs = np.asarray(left, dtype=np.float32)
    rhs = np.asarray(right, dtype=np.float32)
    if lhs.size == 0 or rhs.size == 0:
        return 0.0
    lhs_norm = float(np.linalg.norm(lhs))
    rhs_norm = float(np.linalg.norm(rhs))
    if lhs_norm <= 1e-8 or rhs_norm <= 1e-8:
        return 0.0
    score = float(np.dot(lhs / lhs_norm, rhs / rhs_norm))
    return max(0.0, min(score, 1.0))


def _speaker_threshold() -> float:
    raw = os.getenv("JARVEZ_SPEAKER_ID_THRESHOLD", "0.82").strip()
    try:
        return max(0.0, min(float(raw), 1.0))
    except ValueError:
        return 0.82


def _load_voice_encoder() -> Any | None:
    global _VOICE_ENCODER
    global _VOICE_ENCODER_FAILED
    if _VOICE_ENCODER is not None:
        return _VOICE_ENCODER
    if _VOICE_ENCODER_FAILED or VoiceEncoder is None:
        return None
    try:
        _VOICE_ENCODER = VoiceEncoder()
    except Exception:
        _VOICE_ENCODER_FAILED = True
        return None
    return _VOICE_ENCODER


@dataclass(slots=True)
class SpeakerIdentificationResult:
    name: str
    confidence: float
    matched: bool
    source: str = "voice"
    compared_profiles: int = 0
    method: str = "voice_context"


def extract_current_speaker_embedding(
    participant_identity: str,
    *,
    seconds: float = 4.0,
    min_seconds: float = 1.2,
    encoder: Any | None = None,
    get_recent_voice_audio_fn: Callable[..., tuple[np.ndarray, int] | None] = get_recent_voice_audio,
    get_recent_voice_embedding_fn: Callable[..., list[float] | None] = get_recent_voice_embedding,
) -> tuple[list[float] | None, str]:
    payload = get_recent_voice_audio_fn(participant_identity, seconds=seconds, min_seconds=min_seconds)
    if payload is not None and preprocess_wav is not None:
        samples, sample_rate = payload
        resolved_encoder = encoder or _load_voice_encoder()
        if resolved_encoder is not None:
            try:
                wav = preprocess_wav(np.asarray(samples, dtype=np.float32), source_sr=sample_rate)
                embedding = resolved_encoder.embed_utterance(wav)
                return [float(value) for value in np.asarray(embedding, dtype=np.float32)], "resemblyzer"
            except Exception:
                pass
    fallback = get_recent_voice_embedding_fn(participant_identity, seconds=seconds, min_seconds=min_seconds)
    if fallback is not None:
        return [float(value) for value in fallback], "voice_biometrics"
    return None, "unavailable"


def identify_speaker(
    participant_identity: str,
    store: IdentityStore,
    *,
    embedding: list[float] | None = None,
    threshold: float | None = None,
    encoder: Any | None = None,
    get_recent_voice_audio_fn: Callable[..., tuple[np.ndarray, int] | None] = get_recent_voice_audio,
    get_recent_voice_embedding_fn: Callable[..., list[float] | None] = get_recent_voice_embedding,
) -> SpeakerIdentificationResult:
    probe = [float(value) for value in embedding] if embedding is not None else None
    method = "provided_embedding" if probe is not None else "voice_context"
    if probe is None:
        probe, method = extract_current_speaker_embedding(
            participant_identity,
            encoder=encoder,
            get_recent_voice_audio_fn=get_recent_voice_audio_fn,
            get_recent_voice_embedding_fn=get_recent_voice_embedding_fn,
        )
    if probe is None:
        return SpeakerIdentificationResult(name="unknown", confidence=0.0, matched=False, method=method)

    resolved_threshold = _speaker_threshold() if threshold is None else max(0.0, min(float(threshold), 1.0))
    best_name = "unknown"
    best_score = 0.0
    compared_profiles = 0
    for profile in store.list_profiles():
        for candidate in profile.voice_embeddings:
            compared_profiles += 1
            score = _cosine_similarity(probe, candidate)
            if score > best_score:
                best_score = score
                best_name = profile.name

    if best_score < resolved_threshold:
        return SpeakerIdentificationResult(
            name="unknown",
            confidence=best_score,
            matched=False,
            compared_profiles=compared_profiles,
            method=method,
        )
    return SpeakerIdentificationResult(
        name=best_name,
        confidence=best_score,
        matched=True,
        compared_profiles=compared_profiles,
        method=method,
    )
