from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _derive_key(raw_key: str) -> bytes:
    # Accept user-provided text key and deterministically derive a 32-byte key for AES-GCM.
    return hashlib.sha256(raw_key.encode("utf-8")).digest()


def _participant_hash(participant_identity: str) -> str:
    salt = os.getenv("JARVEZ_VOICE_PROFILE_SALT", "jarvez-local-salt")
    digest = hashlib.sha256(f"{salt}:{participant_identity}".encode("utf-8")).hexdigest()
    return digest


def _l2_normalize(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm <= 1e-8:
        return vector
    return vector / norm


def _resample_linear(samples: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
    if from_rate == to_rate:
        return samples
    if samples.size == 0:
        return samples

    duration = samples.size / float(from_rate)
    if duration <= 0.0:
        return np.array([], dtype=np.float32)

    out_size = max(1, int(duration * to_rate))
    x_old = np.linspace(0.0, duration, num=samples.size, endpoint=False)
    x_new = np.linspace(0.0, duration, num=out_size, endpoint=False)
    return np.interp(x_new, x_old, samples).astype(np.float32)


def _compute_voice_embedding(samples: np.ndarray, sample_rate: int) -> np.ndarray | None:
    if samples.size < max(1600, int(sample_rate * 0.8)):
        return None

    # Focus on voiced chunks and ignore near-silence to reduce noise.
    voiced = samples[np.abs(samples) > 0.01]
    if voiced.size >= int(sample_rate * 0.5):
        samples = voiced

    frame_size = int(sample_rate * 0.025)
    hop_size = int(sample_rate * 0.010)
    fft_size = 512
    if samples.size < frame_size or hop_size <= 0:
        return None

    window = np.hanning(frame_size).astype(np.float32)
    spectra: list[np.ndarray] = []
    zcr_values: list[float] = []
    energy_values: list[float] = []

    for start in range(0, samples.size - frame_size + 1, hop_size):
        frame = samples[start : start + frame_size]
        windowed = frame * window
        energy_values.append(float(np.sqrt(np.mean(windowed**2))))
        zcr_values.append(float(np.mean(np.abs(np.diff(np.signbit(windowed).astype(np.int8))))))

        spectrum = np.abs(np.fft.rfft(windowed, n=fft_size)).astype(np.float32)
        power = np.maximum(1e-9, spectrum**2)
        spectra.append(power)

    if not spectra:
        return None

    spectrogram = np.vstack(spectra)
    n_freq_bins = spectrogram.shape[1]
    band_edges = np.unique(np.linspace(1, n_freq_bins, num=25, dtype=np.int32))
    if band_edges.size < 3:
        return None

    band_features: list[float] = []
    band_energies = []
    for idx in range(len(band_edges) - 1):
        start_bin = int(band_edges[idx])
        end_bin = int(band_edges[idx + 1])
        if end_bin <= start_bin:
            continue
        band = spectrogram[:, start_bin:end_bin]
        mean_band = np.mean(band, axis=1)
        band_energies.append(mean_band)
        band_features.append(float(np.mean(np.log1p(mean_band))))
        band_features.append(float(np.std(np.log1p(mean_band))))

    if not band_features:
        return None

    band_energy_matrix = np.vstack(band_energies).T if band_energies else np.empty((0, 0))
    centroid = 0.0
    centroid_std = 0.0
    if band_energy_matrix.size > 0:
        positions = np.arange(1, band_energy_matrix.shape[1] + 1, dtype=np.float32)
        denom = np.sum(band_energy_matrix, axis=1) + 1e-9
        centroids = np.sum(band_energy_matrix * positions, axis=1) / denom
        centroid = float(np.mean(centroids))
        centroid_std = float(np.std(centroids))

    summary_features = [
        float(np.mean(energy_values)),
        float(np.std(energy_values)),
        float(np.mean(zcr_values)),
        float(np.std(zcr_values)),
        centroid,
        centroid_std,
    ]
    embedding = np.array(band_features + summary_features, dtype=np.float32)
    return _l2_normalize(embedding)


class RecentVoiceBuffer:
    def __init__(self, max_seconds: float = 20.0):
        self._max_seconds = max_seconds
        self._lock = threading.Lock()
        self._buffers: dict[str, deque[tuple[np.ndarray, int, float]]] = {}

    def clear(self, participant_identity: str | None = None) -> None:
        with self._lock:
            if participant_identity is None:
                self._buffers.clear()
                return
            self._buffers.pop(participant_identity, None)

    def add_frame(self, participant_identity: str, frame: Any) -> None:
        if not participant_identity:
            return
        try:
            raw = np.asarray(frame.data, dtype=np.int16)
            if raw.size == 0:
                return

            channels = int(getattr(frame, "num_channels", 1))
            sample_rate = int(getattr(frame, "sample_rate", 16000))
            if channels > 1:
                raw = raw.reshape(-1, channels).mean(axis=1).astype(np.int16)

            samples = (raw.astype(np.float32) / 32768.0).clip(-1.0, 1.0)
            duration = float(samples.size) / float(sample_rate)
            if duration <= 0:
                return
        except Exception:
            return

        with self._lock:
            queue = self._buffers.setdefault(participant_identity, deque())
            queue.append((samples, sample_rate, time.time()))
            cutoff = time.time() - self._max_seconds
            while queue and queue[0][2] < cutoff:
                queue.popleft()

    def get_recent_audio(
        self,
        participant_identity: str,
        *,
        seconds: float,
        min_seconds: float,
        target_sample_rate: int = 16000,
    ) -> tuple[np.ndarray, int] | None:
        with self._lock:
            queue = list(self._buffers.get(participant_identity, ()))

        if not queue:
            return None

        now = time.time()
        cutoff = now - seconds
        selected = [(samples, sr) for samples, sr, ts in queue if ts >= cutoff]
        if not selected:
            selected = [(samples, sr) for samples, sr, _ in queue]

        normalized: list[np.ndarray] = []
        total_duration = 0.0
        for samples, sr in selected:
            if sr <= 0:
                continue
            resampled = _resample_linear(samples, sr, target_sample_rate)
            normalized.append(resampled)
            total_duration += float(resampled.size) / float(target_sample_rate)

        if total_duration < min_seconds or not normalized:
            return None

        return np.concatenate(normalized).astype(np.float32), target_sample_rate


@dataclass(slots=True)
class VoiceVerifyResult:
    matched: bool
    score: float
    profile_name: str | None = None
    compared_profiles: int = 0
    method: str = "audio_embedding"


VOICE_AUDIO_BUFFER = RecentVoiceBuffer()


def capture_voice_frame(participant_identity: str, frame: Any) -> None:
    VOICE_AUDIO_BUFFER.add_frame(participant_identity, frame)


def clear_voice_buffer(participant_identity: str | None = None) -> None:
    VOICE_AUDIO_BUFFER.clear(participant_identity)


def get_recent_voice_embedding(
    participant_identity: str,
    *,
    seconds: float = 4.0,
    min_seconds: float = 1.2,
) -> list[float] | None:
    payload = VOICE_AUDIO_BUFFER.get_recent_audio(
        participant_identity,
        seconds=seconds,
        min_seconds=min_seconds,
        target_sample_rate=16000,
    )
    if payload is None:
        return None
    samples, sample_rate = payload
    embedding = _compute_voice_embedding(samples, sample_rate)
    if embedding is None:
        return None
    return [float(x) for x in embedding]


class VoiceProfileStore:
    def __init__(self, file_path: Path, key: bytes):
        self._file_path = file_path
        self._key = key

    @classmethod
    def from_env(cls) -> VoiceProfileStore | None:
        enabled = os.getenv("JARVEZ_VOICE_BIOMETRY_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}
        if not enabled:
            return None

        raw_key = os.getenv("JARVEZ_VOICE_PROFILE_KEY", "").strip()
        if not raw_key:
            return None

        data_path = Path(os.getenv("JARVEZ_VOICE_PROFILES_PATH", "data/voice_profiles.enc"))
        if not data_path.is_absolute():
            data_path = Path(__file__).resolve().parent / data_path
        data_path.parent.mkdir(parents=True, exist_ok=True)

        return cls(file_path=data_path, key=_derive_key(raw_key))

    def _read_profiles(self) -> list[dict[str, Any]]:
        if not self._file_path.exists():
            return []

        payload = self._file_path.read_bytes()
        if not payload:
            return []

        nonce = payload[:12]
        ciphertext = payload[12:]
        data = AESGCM(self._key).decrypt(nonce, ciphertext, None)
        parsed = json.loads(data.decode("utf-8"))
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
        return []

    def _write_profiles(self, profiles: list[dict[str, Any]]) -> None:
        serialized = json.dumps(profiles, ensure_ascii=False).encode("utf-8")
        nonce = secrets.token_bytes(12)
        ciphertext = AESGCM(self._key).encrypt(nonce, serialized, None)
        self._file_path.write_bytes(nonce + ciphertext)

    def list_profiles(self) -> list[dict[str, str]]:
        profiles = self._read_profiles()
        return [
            {
                "name": str(profile.get("name", "")),
                "created_at": str(profile.get("created_at", "")),
            }
            for profile in profiles
            if profile.get("name")
        ]

    def enroll_profile(self, *, name: str, participant_identity: str, embedding: list[float] | None = None) -> None:
        normalized_name = name.strip().lower()
        profiles = self._read_profiles()
        participant_digest = _participant_hash(participant_identity)

        filtered = [profile for profile in profiles if str(profile.get("name", "")).strip().lower() != normalized_name]
        profile_payload: dict[str, Any] = {
            "name": name.strip(),
            "participant_hash": participant_digest,
            "created_at": _now_iso(),
        }
        if embedding:
            profile_payload["embedding"] = [float(value) for value in embedding]
        filtered.append(
            profile_payload
        )
        self._write_profiles(filtered)

    def delete_profile(self, *, name: str) -> bool:
        normalized_name = name.strip().lower()
        profiles = self._read_profiles()
        filtered = [profile for profile in profiles if str(profile.get("name", "")).strip().lower() != normalized_name]
        changed = len(filtered) != len(profiles)
        if changed:
            self._write_profiles(filtered)
        return changed

    def verify_identity(self, *, participant_identity: str, embedding: list[float] | None = None) -> VoiceVerifyResult:
        profiles = self._read_profiles()
        if not profiles:
            return VoiceVerifyResult(matched=False, score=0.0, profile_name=None, compared_profiles=0)

        if embedding:
            probe = np.array(embedding, dtype=np.float32)
            probe = _l2_normalize(probe)
            best_name: str | None = None
            best_score = 0.0
            compared_profiles = 0
            for profile in profiles:
                stored = profile.get("embedding")
                if not isinstance(stored, list) or not stored:
                    continue
                try:
                    candidate = np.array([float(value) for value in stored], dtype=np.float32)
                    candidate = _l2_normalize(candidate)
                except Exception:
                    continue
                if candidate.size != probe.size:
                    continue
                compared_profiles += 1
                score = float(np.clip((np.dot(probe, candidate) + 1.0) / 2.0, 0.0, 1.0))
                if score > best_score:
                    best_score = score
                    best_name = str(profile.get("name", "")) or None

            if compared_profiles > 0:
                return VoiceVerifyResult(
                    matched=best_name is not None,
                    score=best_score,
                    profile_name=best_name,
                    compared_profiles=compared_profiles,
                    method="audio_embedding",
                )

        # Fallback for legacy profiles that only have participant hash.
        participant_digest = _participant_hash(participant_identity)
        for profile in profiles:
            if profile.get("participant_hash") == participant_digest:
                return VoiceVerifyResult(
                    matched=True,
                    score=1.0,
                    profile_name=str(profile.get("name", "")),
                    compared_profiles=1,
                    method="legacy_identity_hash",
                )

        return VoiceVerifyResult(matched=False, score=0.15, profile_name=None, compared_profiles=len(profiles))


def obfuscate_profile_key(raw_key: str) -> str:
    digest = hashlib.sha256(raw_key.encode("utf-8")).digest()[:8]
    return base64.urlsafe_b64encode(digest).decode("utf-8")
