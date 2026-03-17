from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class EvalScenario:
    scenario_id: str
    name: str
    prompt: str
    expected: list[str]

    def to_payload(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "prompt": self.prompt,
            "expected": self.expected,
        }


def baseline_scenarios() -> list[EvalScenario]:
    return [
        EvalScenario(
            scenario_id="action-evidence-001",
            name="Acao real com evidencia",
            prompt="Envie uma mensagem no WhatsApp para +551199999999 dizendo que cheguei.",
            expected=["confirmation_required", "evidence", "policy_decision"],
        ),
        EvalScenario(
            scenario_id="research-dashboard-001",
            name="Pesquisa web com dashboard",
            prompt="Pesquise novidades de IA agentes e me traga dashboard com links.",
            expected=["web_dashboard", "results", "summary"],
        ),
        EvalScenario(
            scenario_id="codex-fallback-001",
            name="Fallback de provider",
            prompt="Revise o projeto e diga riscos de deploy.",
            expected=["model_route", "fallback_used"],
        ),
    ]
