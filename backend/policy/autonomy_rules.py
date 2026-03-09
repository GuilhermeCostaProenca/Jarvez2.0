from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .risk_engine import PolicyDecision, RiskTier

AutonomyMode = str

DEFAULT_MODE: AutonomyMode = "aggressive"
ALLOWED_AUTONOMY_MODES = {"safe", "aggressive", "manual"}
_AUTONOMY_MODE_BY_IDENTITY: dict[str, AutonomyMode] = {}
_DOMAIN_AUTONOMY_MODE_BY_IDENTITY: dict[str, dict[str, dict[str, str]]] = {}


def _identity_key(participant_identity: str, room: str) -> str:
    return f"{participant_identity}:{room}"


def get_autonomy_mode(participant_identity: str, room: str) -> AutonomyMode:
    mode = _AUTONOMY_MODE_BY_IDENTITY.get(_identity_key(participant_identity, room), DEFAULT_MODE)
    if mode not in ALLOWED_AUTONOMY_MODES:
        return DEFAULT_MODE
    return mode


def _normalize_domain(domain: str | None) -> str:
    normalized = (domain or "").strip().lower()
    return normalized or "general"


def set_autonomy_mode(participant_identity: str, room: str, mode: str) -> AutonomyMode:
    normalized = mode.strip().lower()
    if normalized not in ALLOWED_AUTONOMY_MODES:
        normalized = DEFAULT_MODE
    _AUTONOMY_MODE_BY_IDENTITY[_identity_key(participant_identity, room)] = normalized
    return normalized


def get_domain_autonomy_mode(participant_identity: str, room: str, domain: str | None) -> AutonomyMode | None:
    details = get_domain_autonomy_details(participant_identity, room, domain)
    mode = details.get("mode") if details else None
    if mode not in ALLOWED_AUTONOMY_MODES:
        return None
    return mode


def get_domain_autonomy_details(
    participant_identity: str,
    room: str,
    domain: str | None,
) -> dict[str, str] | None:
    session = _DOMAIN_AUTONOMY_MODE_BY_IDENTITY.get(_identity_key(participant_identity, room), {})
    details = session.get(_normalize_domain(domain))
    if not isinstance(details, dict):
        return None
    mode = str(details.get("mode") or "").strip().lower()
    if mode not in ALLOWED_AUTONOMY_MODES:
        return None
    return {
        "domain": _normalize_domain(domain),
        "mode": mode,
        "reason": str(details.get("reason") or "").strip(),
        "source": str(details.get("source") or "").strip() or "manual",
        "updated_at": str(details.get("updated_at") or "").strip(),
    }


def set_domain_autonomy_mode(
    participant_identity: str,
    room: str,
    domain: str | None,
    mode: str | None,
    *,
    reason: str | None = None,
    source: str | None = None,
) -> AutonomyMode | None:
    key = _identity_key(participant_identity, room)
    normalized_domain = _normalize_domain(domain)
    if mode is None or not str(mode).strip():
        session = _DOMAIN_AUTONOMY_MODE_BY_IDENTITY.get(key, {})
        session.pop(normalized_domain, None)
        if not session:
            _DOMAIN_AUTONOMY_MODE_BY_IDENTITY.pop(key, None)
        return None

    normalized_mode = str(mode).strip().lower()
    if normalized_mode not in ALLOWED_AUTONOMY_MODES:
        normalized_mode = DEFAULT_MODE
    session = _DOMAIN_AUTONOMY_MODE_BY_IDENTITY.setdefault(key, {})
    session[normalized_domain] = {
        "mode": normalized_mode,
        "reason": str(reason or "").strip(),
        "source": str(source or "").strip() or "manual",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    return normalized_mode


def list_domain_autonomy_modes(participant_identity: str, room: str) -> list[dict[str, str]]:
    session = _DOMAIN_AUTONOMY_MODE_BY_IDENTITY.get(_identity_key(participant_identity, room), {})
    rows: list[dict[str, str]] = []
    for domain, details in sorted(session.items(), key=lambda item: item[0]):
        if not isinstance(details, dict):
            continue
        mode = str(details.get("mode") or "").strip().lower()
        if mode not in ALLOWED_AUTONOMY_MODES:
            continue
        rows.append(
            {
                "domain": domain,
                "mode": mode,
                "reason": str(details.get("reason") or "").strip(),
                "source": str(details.get("source") or "").strip() or "manual",
                "updated_at": str(details.get("updated_at") or "").strip(),
            }
        )
    return rows


def clear_domain_autonomy_mode(
    participant_identity: str | None = None,
    room: str | None = None,
    domain: str | None = None,
) -> None:
    if participant_identity is None or room is None:
        _DOMAIN_AUTONOMY_MODE_BY_IDENTITY.clear()
        return
    key = _identity_key(participant_identity, room)
    if domain is None:
        _DOMAIN_AUTONOMY_MODE_BY_IDENTITY.pop(key, None)
        return
    session = _DOMAIN_AUTONOMY_MODE_BY_IDENTITY.get(key, {})
    session.pop(_normalize_domain(domain), None)
    if not session:
        _DOMAIN_AUTONOMY_MODE_BY_IDENTITY.pop(key, None)


def get_effective_autonomy_mode(
    participant_identity: str,
    room: str,
    *,
    domain: str | None = None,
) -> AutonomyMode:
    base_mode = get_autonomy_mode(participant_identity, room)
    domain_mode = get_domain_autonomy_mode(participant_identity, room, domain)
    if domain_mode is None:
        return base_mode
    if base_mode == "manual":
        return "manual"
    if domain_mode == "manual":
        return "manual"
    if domain_mode == "safe":
        return "safe"
    return base_mode


@dataclass(slots=True)
class PolicyEvaluation:
    decision: PolicyDecision
    reason: str


def _normalize_trust_score(value: float | None) -> float | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric < 0:
        return 0.0
    if numeric > 1:
        return 1.0
    return numeric


def evaluate_policy(
    *,
    risk: RiskTier,
    mode: AutonomyMode,
    requires_confirmation: bool,
    kill_switch_active: bool,
    kill_switch_reason: str | None = None,
    domain: str | None = None,
    domain_trust_score: float | None = None,
    trust_drift_active: bool = False,
    trust_drift_reason: str | None = None,
) -> PolicyEvaluation:
    if kill_switch_active:
        return PolicyEvaluation(decision="deny", reason=kill_switch_reason or "Bloqueado por kill switch.")

    if requires_confirmation:
        return PolicyEvaluation(decision="require_confirmation", reason="Action exige confirmacao por especificacao.")

    trust_score = _normalize_trust_score(domain_trust_score)
    trust_label = f" (dominio={domain or 'general'} trust={trust_score:.2f})" if trust_score is not None else ""
    drift_label = f" (dominio={domain or 'general'} drift=ativo)" if trust_drift_active else ""

    if mode == "manual":
        if risk == "R0":
            return PolicyEvaluation(decision="allow_with_log", reason="Modo manual com risco baixo.")
        return PolicyEvaluation(
            decision="require_confirmation",
            reason="Modo manual exige confirmacao para risco moderado/alto.",
        )

    if mode == "safe":
        if risk == "R0":
            return PolicyEvaluation(decision="allow_with_log", reason="Modo seguro e risco baixo.")
        if risk == "R1":
            if trust_drift_active:
                return PolicyEvaluation(
                    decision="require_confirmation",
                    reason=f"Trust drift exige confirmacao em risco R1 no modo seguro.{drift_label}",
                )
            if trust_score is not None and trust_score < 0.35:
                return PolicyEvaluation(
                    decision="require_confirmation",
                    reason=f"Trust baixo exige confirmacao em risco R1 no modo seguro.{trust_label}",
                )
            return PolicyEvaluation(decision="allow_with_log", reason="Modo seguro com logging reforcado.")
        if risk == "R2":
            if trust_drift_active:
                return PolicyEvaluation(
                    decision="deny",
                    reason=f"Trust drift bloqueia risco R2 no modo seguro ate nova sincronizacao.{drift_label}",
                )
            if trust_score is not None and trust_score < 0.40:
                return PolicyEvaluation(
                    decision="deny",
                    reason=f"Trust muito baixo bloqueia risco R2 no modo seguro.{trust_label}",
                )
            return PolicyEvaluation(decision="require_confirmation", reason="Modo seguro exige confirmacao para risco R2.")
        return PolicyEvaluation(decision="deny", reason="Modo seguro bloqueia risco R3 sem step-up explicito.")

    # aggressive (default)
    if risk in ("R0", "R1"):
        if trust_drift_active:
            return PolicyEvaluation(
                decision="allow_with_log",
                reason=f"Trust drift ativo aplica logging reforcado para risco baixo.{drift_label}",
            )
        if risk == "R1" and trust_score is not None and trust_score < 0.30:
            return PolicyEvaluation(
                decision="allow_with_log",
                reason=f"Trust baixo aplica logging reforcado em R1 no modo agressivo.{trust_label}",
            )
        return PolicyEvaluation(decision="allow", reason="Modo agressivo em risco baixo.")
    if risk == "R2":
        if trust_drift_active:
            return PolicyEvaluation(
                decision="require_confirmation",
                reason=f"Trust drift exige confirmacao em risco R2 no modo agressivo.{drift_label}",
            )
        if trust_score is not None and trust_score < 0.55:
            return PolicyEvaluation(
                decision="require_confirmation",
                reason=f"Trust baixo exige confirmacao em risco R2 no modo agressivo.{trust_label}",
            )
        return PolicyEvaluation(decision="allow_with_guardrail", reason="Modo agressivo com guardrails para risco R2.")
    if trust_score is not None and trust_score < 0.25:
        return PolicyEvaluation(
            decision="deny",
            reason=f"Trust critico bloqueia risco R3 ate recuperacao de confiabilidade.{trust_label}",
        )
    if trust_drift_active and trust_drift_reason:
        return PolicyEvaluation(
            decision="require_confirmation",
            reason=f"Trust drift exige confirmacao antes de risco critico R3. {trust_drift_reason}",
        )
    return PolicyEvaluation(
        decision="require_confirmation",
        reason="Modo agressivo requer confirmacao em risco critico R3.",
    )
