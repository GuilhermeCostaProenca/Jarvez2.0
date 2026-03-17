from __future__ import annotations

from policy.risk_engine import RiskTier
from providers import AnthropicProvider, GoogleProvider, LocalMockProvider, OpenAIProvider, route_request
from providers.provider_router import ModelRouteDecision, TaskType, choose_provider_order
from runtime.model_gateway import resolve_runtime


def build_provider_registry() -> dict[str, object]:
    return {
        "openai": OpenAIProvider(),
        "anthropic": AnthropicProvider(),
        "google": GoogleProvider(),
        "local_mock": LocalMockProvider(),
    }


def _provider_order_from_runtime(*, task_type: TaskType, risk: RiskTier, primary: str, fallback: str | None) -> list[str]:
    order: list[str] = []
    for provider_name in [primary, fallback, *choose_provider_order(task_type, risk), "local_mock"]:
        normalized = str(provider_name or "").strip()
        if not normalized:
            continue
        if normalized in order:
            continue
        order.append(normalized)
    return order


def route_orchestration(*, request: str, task_type: TaskType, risk: RiskTier) -> tuple[str, ModelRouteDecision]:
    runtime_decision = resolve_runtime(
        intent=f"orchestration:{task_type}",
        task_type=task_type,
        risk=risk,
        required_capabilities=["tools"],
    )
    provider_order = _provider_order_from_runtime(
        task_type=task_type,
        risk=risk,
        primary=runtime_decision.primary_provider,
        fallback=runtime_decision.fallback_provider,
    )
    providers = build_provider_registry()
    output, decision = route_request(
        request=request,
        task_type=task_type,
        risk=risk,
        providers=providers,
        provider_order=provider_order,
    )
    decision.primary_provider = runtime_decision.primary_provider
    decision.fallback_provider = runtime_decision.fallback_provider
    decision.reason = f"{runtime_decision.reason} {decision.reason}".strip()
    return output, decision
