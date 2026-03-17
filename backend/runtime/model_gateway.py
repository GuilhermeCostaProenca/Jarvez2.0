from __future__ import annotations

from dataclasses import dataclass, field

from providers.provider_router import TaskType, preview_route


@dataclass(slots=True)
class RuntimeDecision:
    intent: str
    task_type: TaskType
    risk: str
    required_capabilities: list[str] = field(default_factory=list)
    primary_provider: str = "google"
    fallback_provider: str | None = None
    reason: str = ""

    def to_payload(self) -> dict[str, object]:
        return {
            "intent": self.intent,
            "task_type": self.task_type,
            "risk": self.risk,
            "required_capabilities": list(self.required_capabilities),
            "primary_provider": self.primary_provider,
            "fallback_provider": self.fallback_provider,
            "reason": self.reason,
        }


def resolve_runtime(
    *,
    intent: str,
    task_type: TaskType,
    risk: str,
    required_capabilities: list[str] | None = None,
) -> RuntimeDecision:
    capabilities = required_capabilities or []
    primary_provider, fallback_provider = preview_route(task_type, risk)
    if "realtime" in capabilities:
        # Google remains the only realtime adapter today, but the decision is now centralized.
        primary_provider = "google"
        if fallback_provider == "google":
            fallback_provider = "openai"
    return RuntimeDecision(
        intent=intent,
        task_type=task_type,
        risk=risk,
        required_capabilities=capabilities,
        primary_provider=primary_provider,
        fallback_provider=fallback_provider,
        reason="Runtime gateway selected provider from task type, risk, and required capabilities.",
    )
