from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from providers.provider_router import TaskType


@dataclass(slots=True)
class TaskPlan:
    task_type: TaskType
    steps: list[str]
    assumptions: list[str]
    generated_at: str

    def to_payload(self) -> dict[str, object]:
        return {
            "task_type": self.task_type,
            "steps": self.steps,
            "assumptions": self.assumptions,
            "generated_at": self.generated_at,
        }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def infer_task_type(request: str) -> TaskType:
    lowered = request.lower()
    if any(word in lowered for word in ("refator", "codigo", "code", "bug", "teste", "lint", "build", "review")):
        if "review" in lowered or "revis" in lowered:
            return "review"
        return "code"
    if any(word in lowered for word in ("pesquisa", "research", "buscar", "web", "internet")):
        return "research"
    if any(word in lowered for word in ("liga", "desliga", "whatsapp", "spotify", "thinq", "automacao")):
        return "automation"
    if any(word in lowered for word in ("chat", "conversa", "resuma", "explica")):
        return "chat"
    return "unknown"


def build_task_plan(request: str) -> TaskPlan:
    task_type = infer_task_type(request)
    steps = [
        "Classificar objetivo, risco e contexto.",
        "Selecionar provider e ferramentas com fallback.",
        "Executar em blocos curtos com evidencias de resultado.",
        "Retornar resumo + proximos passos objetivos.",
    ]
    assumptions = [
        "Nao executar acao sensivel sem guardrails/politica.",
        "Preferir output estruturado para consumo da UI.",
    ]
    if task_type in ("code", "review"):
        steps.insert(1, "Resolver projeto ativo e dependencias relevantes.")
    if task_type == "research":
        steps.insert(1, "Consolidar fontes com resumo e links verificaveis.")

    return TaskPlan(task_type=task_type, steps=steps, assumptions=assumptions, generated_at=_now_iso())
