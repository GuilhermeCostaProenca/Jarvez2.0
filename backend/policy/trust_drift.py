from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _session_key(participant_identity: str, room: str) -> str:
    return f"{participant_identity}:{room}"


def _normalize_domain(domain: str | None) -> str:
    normalized = (domain or "").strip().lower()
    return normalized or "general"


@dataclass(slots=True)
class TrustDriftState:
    domain: str
    active: bool
    score_delta: float
    recommendation_delta_ms: int
    retry_delta: int
    updated_at: str
    source: str = "frontend"
    signature: str | None = None
    reason: str | None = None

    def to_payload(self) -> dict[str, object]:
        return {
            "domain": self.domain,
            "active": self.active,
            "score_delta": round(self.score_delta, 4),
            "recommendation_delta_ms": self.recommendation_delta_ms,
            "retry_delta": self.retry_delta,
            "updated_at": self.updated_at,
            "source": self.source,
            "signature": self.signature,
            "reason": self.reason,
        }


_TRUST_DRIFT_BY_SESSION: dict[str, dict[str, TrustDriftState]] = {}


def get_trust_drift(participant_identity: str, room: str, domain: str | None) -> TrustDriftState | None:
    session = _TRUST_DRIFT_BY_SESSION.get(_session_key(participant_identity, room), {})
    return session.get(_normalize_domain(domain))


def list_trust_drift(participant_identity: str, room: str) -> list[TrustDriftState]:
    session = _TRUST_DRIFT_BY_SESSION.get(_session_key(participant_identity, room), {})
    return sorted(session.values(), key=lambda item: item.domain)


def replace_trust_drift(
    participant_identity: str,
    room: str,
    rows: list[dict[str, object]] | None,
    *,
    source: str = "frontend",
    signature: str | None = None,
) -> list[TrustDriftState]:
    session_key = _session_key(participant_identity, room)
    next_rows: dict[str, TrustDriftState] = {}
    for row in rows or []:
        domain = _normalize_domain(str(row.get("domain", "")).strip().lower())
        active = bool(row.get("active")) or str(row.get("state", "")).strip().lower() == "drift"
        if not active:
            continue
        try:
            score_delta = abs(float(row.get("score_delta", 0.0)))
        except (TypeError, ValueError):
            score_delta = 0.0
        try:
            recommendation_delta_ms = abs(int(row.get("recommendation_delta_ms", 0)))
        except (TypeError, ValueError):
            recommendation_delta_ms = 0
        try:
            retry_delta = abs(int(row.get("retry_delta", 0)))
        except (TypeError, ValueError):
            retry_delta = 0
        next_rows[domain] = TrustDriftState(
            domain=domain,
            active=True,
            score_delta=score_delta,
            recommendation_delta_ms=recommendation_delta_ms,
            retry_delta=retry_delta,
            updated_at=_now_iso(),
            source=source,
            signature=signature,
            reason=f"Trust drift reportado pelo cliente para dominio {domain}.",
        )
    _TRUST_DRIFT_BY_SESSION[session_key] = next_rows
    return list_trust_drift(participant_identity, room)


def clear_trust_drift(participant_identity: str | None = None, room: str | None = None) -> None:
    if participant_identity is None or room is None:
        _TRUST_DRIFT_BY_SESSION.clear()
        return
    _TRUST_DRIFT_BY_SESSION.pop(_session_key(participant_identity, room), None)
