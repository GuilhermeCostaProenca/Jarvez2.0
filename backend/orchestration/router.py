from __future__ import annotations

from policy.risk_engine import RiskTier
from providers import AnthropicProvider, GoogleProvider, LocalMockProvider, OpenAIProvider, route_request
from providers.provider_router import ModelRouteDecision, TaskType


def build_provider_registry() -> dict[str, object]:
    return {
        "openai": OpenAIProvider(),
        "anthropic": AnthropicProvider(),
        "google": GoogleProvider(),
        "local_mock": LocalMockProvider(),
    }


def route_orchestration(*, request: str, task_type: TaskType, risk: RiskTier) -> tuple[str, ModelRouteDecision]:
    providers = build_provider_registry()
    output, decision = route_request(request=request, task_type=task_type, risk=risk, providers=providers)
    return output, decision
