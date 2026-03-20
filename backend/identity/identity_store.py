from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]
IDENTITY_ROLES = {"owner", "guest"}
IDENTITY_CONFIDENCE_LEVELS = {"low", "medium", "high"}
IDENTITY_UNLOCK_MODES = {"voice", "face", "voice+face"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_identity_path() -> Path:
    raw = os.getenv("JARVEZ_IDENTITY_PROFILES_PATH", "data/identity/profiles.json").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _normalize_name(value: str) -> str:
    return value.strip().casefold()


def _normalize_embedding_rows(rows: Any) -> list[list[float]]:
    normalized: list[list[float]] = []
    if not isinstance(rows, list):
        return normalized
    for item in rows:
        if not isinstance(item, list):
            continue
        values: list[float] = []
        for value in item:
            try:
                values.append(float(value))
            except (TypeError, ValueError):
                values = []
                break
        if values:
            normalized.append(values)
    return normalized


def _normalize_optional_threshold(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return max(0.0, min(float(value), 1.0))
    except (TypeError, ValueError):
        return None


def _normalize_unlock_modes(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    for item in value:
        mode = str(item or "").strip().lower()
        if mode in IDENTITY_UNLOCK_MODES and mode not in normalized:
            normalized.append(mode)
    return normalized


@dataclass(slots=True)
class IdentityProfile:
    name: str
    voice_embeddings: list[list[float]]
    face_embeddings: list[list[float]]
    confidence_level: str
    role: str
    registered_at: str
    last_calibrated_at: str | None = None
    preferred_unlock_modes: list[str] | None = None
    voice_unlock_threshold: float | None = None
    face_unlock_threshold: float | None = None

    @classmethod
    def from_payload(cls, payload: JsonObject) -> "IdentityProfile":
        role = str(payload.get("role") or "guest").strip().lower()
        confidence_level = str(payload.get("confidence_level") or "medium").strip().lower()
        return cls(
            name=str(payload.get("name") or "").strip(),
            voice_embeddings=_normalize_embedding_rows(payload.get("voice_embeddings")),
            face_embeddings=_normalize_embedding_rows(payload.get("face_embeddings")),
            confidence_level=confidence_level if confidence_level in IDENTITY_CONFIDENCE_LEVELS else "medium",
            role=role if role in IDENTITY_ROLES else "guest",
            registered_at=str(payload.get("registered_at") or _now_iso()),
            last_calibrated_at=str(payload.get("last_calibrated_at")).strip() if payload.get("last_calibrated_at") else None,
            preferred_unlock_modes=_normalize_unlock_modes(payload.get("preferred_unlock_modes")) or None,
            voice_unlock_threshold=_normalize_optional_threshold(payload.get("voice_unlock_threshold")),
            face_unlock_threshold=_normalize_optional_threshold(payload.get("face_unlock_threshold")),
        )

    def to_payload(self) -> JsonObject:
        return asdict(self)


class IdentityStore:
    def __init__(self, file_path: Path | None = None) -> None:
        self.file_path = file_path or _default_identity_path()
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    @classmethod
    def from_env(cls) -> "IdentityStore":
        return cls(file_path=_default_identity_path())

    def _read_profiles(self) -> list[IdentityProfile]:
        if not self.file_path.exists():
            return []
        try:
            raw = json.loads(self.file_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        if not isinstance(raw, list):
            return []
        return [IdentityProfile.from_payload(item) for item in raw if isinstance(item, dict)]

    def _write_profiles(self, profiles: list[IdentityProfile]) -> None:
        payload = [profile.to_payload() for profile in profiles]
        self.file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def list_profiles(self) -> list[IdentityProfile]:
        with self._lock:
            return list(self._read_profiles())

    def get_profile(self, name: str) -> IdentityProfile | None:
        normalized = _normalize_name(name)
        with self._lock:
            for profile in self._read_profiles():
                if _normalize_name(profile.name) == normalized:
                    return profile
        return None

    def upsert_profile(
        self,
        *,
        name: str,
        role: str = "guest",
        confidence_level: str = "medium",
        voice_embeddings: list[list[float]] | None = None,
        face_embeddings: list[list[float]] | None = None,
        registered_at: str | None = None,
        last_calibrated_at: str | None = None,
        preferred_unlock_modes: list[str] | None = None,
        voice_unlock_threshold: float | None = None,
        face_unlock_threshold: float | None = None,
    ) -> IdentityProfile:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("name is required")
        resolved_role = role.strip().lower()
        if resolved_role not in IDENTITY_ROLES:
            raise ValueError("role must be owner or guest")
        resolved_confidence = confidence_level.strip().lower()
        if resolved_confidence not in IDENTITY_CONFIDENCE_LEVELS:
            resolved_confidence = "medium"

        with self._lock:
            profiles = self._read_profiles()
            existing = next(
                (profile for profile in profiles if _normalize_name(profile.name) == _normalize_name(normalized_name)),
                None,
            )
            base_registered_at = existing.registered_at if existing is not None else (registered_at or _now_iso())
            next_profile = IdentityProfile(
                name=normalized_name,
                voice_embeddings=_normalize_embedding_rows(
                    voice_embeddings if voice_embeddings is not None else (existing.voice_embeddings if existing else [])
                ),
                face_embeddings=_normalize_embedding_rows(
                    face_embeddings if face_embeddings is not None else (existing.face_embeddings if existing else [])
                ),
                confidence_level=resolved_confidence,
                role=resolved_role,
                registered_at=base_registered_at,
                last_calibrated_at=(
                    str(last_calibrated_at).strip()
                    if last_calibrated_at
                    else (existing.last_calibrated_at if existing is not None else None)
                ),
                preferred_unlock_modes=(
                    _normalize_unlock_modes(preferred_unlock_modes)
                    if preferred_unlock_modes is not None
                    else (list(existing.preferred_unlock_modes or []) if existing is not None else [])
                )
                or None,
                voice_unlock_threshold=(
                    _normalize_optional_threshold(voice_unlock_threshold)
                    if voice_unlock_threshold is not None
                    else (existing.voice_unlock_threshold if existing is not None else None)
                ),
                face_unlock_threshold=(
                    _normalize_optional_threshold(face_unlock_threshold)
                    if face_unlock_threshold is not None
                    else (existing.face_unlock_threshold if existing is not None else None)
                ),
            )
            filtered = [
                profile for profile in profiles if _normalize_name(profile.name) != _normalize_name(normalized_name)
            ]
            filtered.append(next_profile)
            self._write_profiles(filtered)
            return next_profile

    def delete_profile(self, name: str) -> bool:
        normalized = _normalize_name(name)
        with self._lock:
            profiles = self._read_profiles()
            filtered = [profile for profile in profiles if _normalize_name(profile.name) != normalized]
            changed = len(filtered) != len(profiles)
            if changed:
                self._write_profiles(filtered)
            return changed

    def append_voice_embedding(
        self,
        *,
        name: str,
        embedding: list[float],
        role: str = "guest",
        confidence_level: str = "medium",
        voice_unlock_threshold: float | None = None,
    ) -> IdentityProfile:
        existing = self.get_profile(name)
        next_rows = list(existing.voice_embeddings) if existing is not None else []
        next_rows.append([float(value) for value in embedding])
        return self.upsert_profile(
            name=name,
            role=existing.role if existing is not None else role,
            confidence_level=existing.confidence_level if existing is not None else confidence_level,
            voice_embeddings=next_rows,
            face_embeddings=existing.face_embeddings if existing is not None else [],
            last_calibrated_at=_now_iso(),
            voice_unlock_threshold=(
                voice_unlock_threshold if voice_unlock_threshold is not None else (existing.voice_unlock_threshold if existing is not None else None)
            ),
        )

    def append_face_embedding(
        self,
        *,
        name: str,
        embedding: list[float],
        role: str = "guest",
        confidence_level: str = "medium",
        face_unlock_threshold: float | None = None,
    ) -> IdentityProfile:
        existing = self.get_profile(name)
        next_rows = list(existing.face_embeddings) if existing is not None else []
        next_rows.append([float(value) for value in embedding])
        return self.upsert_profile(
            name=name,
            role=existing.role if existing is not None else role,
            confidence_level=existing.confidence_level if existing is not None else confidence_level,
            voice_embeddings=existing.voice_embeddings if existing is not None else [],
            face_embeddings=next_rows,
            last_calibrated_at=_now_iso(),
            face_unlock_threshold=(
                face_unlock_threshold if face_unlock_threshold is not None else (existing.face_unlock_threshold if existing is not None else None)
            ),
        )
