from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal, Protocol

from policy.risk_engine import RiskTier

TaskType = Literal["chat", "code", "review", "research", "automation", "unknown"]


class ProviderClient(Protocol):
    provider_name: str

    def supports_tools(self) -> bool: ...

    def supports_realtime(self) -> bool: ...

    def generate_text(self, request: str) -> tuple[str | None, str | None]: ...

    def stream_text(self, request: str) -> tuple[str | None, str | None]: ...

    def realtime_turn(self, request: str) -> tuple[str | None, str | None]: ...


@dataclass(slots=True)
class ModelRouteDecision:
    task_type: TaskType
    risk: RiskTier
    primary_provider: str
    fallback_provider: str | None
    used_provider: str
    fallback_used: bool
    reason: str
    generated_at: str

    def to_payload(self) -> dict[str, object]:
        return {
            "task_type": self.task_type,
            "risk": self.risk,
            "primary_provider": self.primary_provider,
            "fallback_provider": self.fallback_provider,
            "used_provider": self.used_provider,
            "fallback_used": self.fallback_used,
            "reason": self.reason,
            "generated_at": self.generated_at,
        }


class LocalMockProvider:
    provider_name = "local_mock"

    def supports_tools(self) -> bool:
        return True

    def supports_realtime(self) -> bool:
        return True

    def generate_text(self, request: str) -> tuple[str | None, str | None]:
        return f"[local-mock] {request}".strip(), None

    def stream_text(self, request: str) -> tuple[str | None, str | None]:
        return self.generate_text(request)

    def realtime_turn(self, request: str) -> tuple[str | None, str | None]:
        return self.generate_text(request)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def choose_provider_order(task_type: TaskType, risk: RiskTier) -> list[str]:
    if task_type in ("code", "review"):
        return ["anthropic", "openai", "google", "local_mock"]
    if task_type == "research":
        return ["google", "openai", "anthropic", "local_mock"]
    if risk == "R3":
        return ["openai", "anthropic", "google", "local_mock"]
    return ["openai", "anthropic", "google", "local_mock"]


def preview_route(task_type: TaskType, risk: RiskTier) -> tuple[str, str | None]:
    order = choose_provider_order(task_type, risk)
    primary = order[0] if order else "local_mock"
    fallback = order[1] if len(order) > 1 else None
    return primary, fallback


def route_request(
    *,
    request: str,
    task_type: TaskType,
    risk: RiskTier,
    providers: dict[str, ProviderClient],
) -> tuple[str, ModelRouteDecision]:
    order = choose_provider_order(task_type, risk)
    primary = order[0]
    fallback = order[1] if len(order) > 1 else None

    used = "local_mock"
    fallback_used = False
    reason = "Nenhum provider configurado; fallback local."
    text = ""
    last_error = ""

    for index, provider_name in enumerate(order):
        provider = providers.get(provider_name)
        if provider is None:
            continue
        candidate_text, error = provider.generate_text(request)
        if candidate_text:
            text = candidate_text
            used = provider_name
            fallback_used = index > 0
            reason = "Provider selecionado por task_type/risk."
            break
        if error:
            last_error = error

    if not text:
        local = providers.get("local_mock")
        if local is not None:
            local_text, _ = local.generate_text(request)
            text = local_text or request
            used = "local_mock"
            fallback_used = True
            reason = f"Fallback local acionado ({last_error or 'provider unavailable'})."
        else:
            text = request

    decision = ModelRouteDecision(
        task_type=task_type,
        risk=risk,
        primary_provider=primary,
        fallback_provider=fallback,
        used_provider=used,
        fallback_used=fallback_used,
        reason=reason,
        generated_at=_now_iso(),
    )
    return text, decision
