from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

DomainTrustOutcome = Literal["success", "failure", "no_evidence"]

DEFAULT_TRUST_SCORE = 0.7
TRUST_DELTA_BY_OUTCOME: dict[DomainTrustOutcome, float] = {
    "success": 0.06,
    "failure": -0.12,
    "no_evidence": -0.18,
}

_DOMAIN_TRUST: dict[str, "DomainTrustState"] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clamp_score(value: float) -> float:
    if value < 0:
        return 0.0
    if value > 1:
        return 1.0
    return value


def _normalize_domain(domain: str | None) -> str:
    normalized = (domain or "").strip().lower()
    return normalized or "general"


def _recommendation(score: float) -> dict[str, int]:
    if score >= 0.85:
        return {"timeout_ms": 30_000, "max_auto_retries": 2}
    if score >= 0.65:
        return {"timeout_ms": 45_000, "max_auto_retries": 1}
    if score >= 0.45:
        return {"timeout_ms": 60_000, "max_auto_retries": 0}
    return {"timeout_ms": 90_000, "max_auto_retries": 0}


@dataclass(slots=True)
class DomainTrustState:
    domain: str
    score: float
    samples: int
    success_count: int
    failure_count: int
    no_evidence_count: int
    updated_at: str

    def to_payload(self) -> dict[str, object]:
        return {
            "domain": self.domain,
            "score": round(self.score, 4),
            "samples": self.samples,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "no_evidence_count": self.no_evidence_count,
            "updated_at": self.updated_at,
            "recommendation": _recommendation(self.score),
        }


def infer_action_domain(action_name: str) -> str:
    normalized = action_name.strip().lower()
    if not normalized:
        return "general"
    if normalized.startswith("whatsapp_"):
        return "whatsapp"
    if normalized.startswith("spotify_"):
        return "spotify"
    if normalized.startswith("thinq_") or normalized.startswith("ac_"):
        return "home"
    if normalized in {"turn_light_on", "turn_light_off", "set_light_brightness", "call_service"}:
        return "home"
    if (
        normalized.startswith("project_")
        or normalized.startswith("code_")
        or normalized.startswith("codex_")
        or normalized.startswith("github_")
        or normalized in {"run_local_command", "git_clone_repository", "git_commit_and_push_project"}
    ):
        return "shell"
    if normalized.startswith("onenote_"):
        return "notes"
    if normalized.startswith("web_search_") or normalized == "save_web_briefing_schedule":
        return "research"
    if (
        normalized.startswith("ops_")
        or normalized.startswith("autonomy_")
        or normalized.startswith("policy_")
        or normalized.startswith("evals_")
        or normalized.startswith("providers_")
    ):
        return "ops"
    return "general"


def get_domain_trust(domain: str | None) -> DomainTrustState:
    normalized = _normalize_domain(domain)
    existing = _DOMAIN_TRUST.get(normalized)
    if existing is not None:
        return existing
    return DomainTrustState(
        domain=normalized,
        score=DEFAULT_TRUST_SCORE,
        samples=0,
        success_count=0,
        failure_count=0,
        no_evidence_count=0,
        updated_at=_now_iso(),
    )


def list_domain_trust() -> list[DomainTrustState]:
    return sorted(_DOMAIN_TRUST.values(), key=lambda item: item.domain)


def record_domain_outcome(domain: str | None, outcome: DomainTrustOutcome) -> DomainTrustState:
    normalized = _normalize_domain(domain)
    current = get_domain_trust(normalized)
    delta = TRUST_DELTA_BY_OUTCOME[outcome]
    updated = DomainTrustState(
        domain=normalized,
        score=_clamp_score(current.score + delta),
        samples=current.samples + 1,
        success_count=current.success_count + (1 if outcome == "success" else 0),
        failure_count=current.failure_count + (1 if outcome == "failure" else 0),
        no_evidence_count=current.no_evidence_count + (1 if outcome == "no_evidence" else 0),
        updated_at=_now_iso(),
    )
    _DOMAIN_TRUST[normalized] = updated
    return updated


def clear_domain_trust(domain: str | None = None) -> None:
    if domain is None:
        _DOMAIN_TRUST.clear()
        return
    _DOMAIN_TRUST.pop(_normalize_domain(domain), None)
