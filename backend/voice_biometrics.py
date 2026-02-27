from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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


@dataclass(slots=True)
class VoiceVerifyResult:
    matched: bool
    score: float
    profile_name: str | None = None


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

    def enroll_profile(self, *, name: str, participant_identity: str) -> None:
        normalized_name = name.strip().lower()
        profiles = self._read_profiles()
        participant_digest = _participant_hash(participant_identity)

        filtered = [profile for profile in profiles if str(profile.get("name", "")).strip().lower() != normalized_name]
        filtered.append(
            {
                "name": name.strip(),
                "participant_hash": participant_digest,
                "created_at": _now_iso(),
            }
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

    def verify_identity(self, *, participant_identity: str) -> VoiceVerifyResult:
        profiles = self._read_profiles()
        participant_digest = _participant_hash(participant_identity)

        for profile in profiles:
            if profile.get("participant_hash") == participant_digest:
                return VoiceVerifyResult(matched=True, score=1.0, profile_name=str(profile.get("name", "")))

        if profiles:
            return VoiceVerifyResult(matched=False, score=0.2, profile_name=None)
        return VoiceVerifyResult(matched=False, score=0.0, profile_name=None)


def obfuscate_profile_key(raw_key: str) -> str:
    digest = hashlib.sha256(raw_key.encode("utf-8")).digest()[:8]
    return base64.urlsafe_b64encode(digest).decode("utf-8")
