from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

WorkflowStatus = Literal[
    "running",
    "awaiting_approval",
    "blocked",
    "completed",
    "failed",
    "cancelled",
]
StepStatus = Literal["pending", "running", "blocked", "completed", "failed", "cancelled"]
GateStatus = Literal["pending", "approved", "rejected"]


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return {str(key): item for key, item in value.items()}
    return {}


@dataclass(slots=True)
class WorkflowApprovalGate:
    gate_id: str
    title: str
    prompt: str
    status: GateStatus = "pending"
    decision_note: str | None = None
    decided_at: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "gate_id": self.gate_id,
            "title": self.title,
            "prompt": self.prompt,
            "status": self.status,
        }
        if self.decision_note is not None:
            payload["decision_note"] = self.decision_note
        if self.decided_at is not None:
            payload["decided_at"] = self.decided_at
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "WorkflowApprovalGate":
        gate_id = str(payload.get("gate_id", "")).strip()
        title = str(payload.get("title", "")).strip()
        prompt = str(payload.get("prompt", "")).strip()
        status = str(payload.get("status", "pending")).strip() or "pending"
        return cls(
            gate_id=gate_id,
            title=title or gate_id or "approval_gate",
            prompt=prompt or "Confirme para continuar.",
            status=status if status in {"pending", "approved", "rejected"} else "pending",
            decision_note=str(payload.get("decision_note", "")).strip() or None,
            decided_at=str(payload.get("decided_at", "")).strip() or None,
        )


@dataclass(slots=True)
class WorkflowStepDefinition:
    step_id: str
    title: str
    action_name: str
    gate: WorkflowApprovalGate | None = None


@dataclass(slots=True)
class WorkflowStepState:
    step_id: str
    title: str
    action_name: str
    status: StepStatus = "pending"
    summary: str | None = None
    output: dict[str, Any] | None = None
    error: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    gate: WorkflowApprovalGate | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "step_id": self.step_id,
            "title": self.title,
            "action_name": self.action_name,
            "status": self.status,
        }
        if self.summary is not None:
            payload["summary"] = self.summary
        if self.output is not None:
            payload["output"] = self.output
        if self.error is not None:
            payload["error"] = self.error
        if self.started_at is not None:
            payload["started_at"] = self.started_at
        if self.finished_at is not None:
            payload["finished_at"] = self.finished_at
        if self.gate is not None:
            payload["gate"] = self.gate.to_payload()
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "WorkflowStepState":
        raw_status = str(payload.get("status", "pending")).strip() or "pending"
        gate_payload = payload.get("gate")
        return cls(
            step_id=str(payload.get("step_id", "")).strip(),
            title=str(payload.get("title", "")).strip(),
            action_name=str(payload.get("action_name", "")).strip(),
            status=raw_status if raw_status in {"pending", "running", "blocked", "completed", "failed", "cancelled"} else "pending",
            summary=str(payload.get("summary", "")).strip() or None,
            output=_as_dict(payload.get("output")) or None,
            error=str(payload.get("error", "")).strip() or None,
            started_at=str(payload.get("started_at", "")).strip() or None,
            finished_at=str(payload.get("finished_at", "")).strip() or None,
            gate=WorkflowApprovalGate.from_payload(gate_payload) if isinstance(gate_payload, dict) else None,
        )


@dataclass(slots=True)
class WorkflowState:
    workflow_id: str
    workflow_type: str
    status: WorkflowStatus
    summary: str
    request: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    current_step_index: int = 0
    steps: list[WorkflowStepState] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    started_at: str | None = None
    updated_at: str | None = None
    finished_at: str | None = None
    error: str | None = None

    @property
    def current_step(self) -> WorkflowStepState | None:
        if not self.steps:
            return None
        if self.current_step_index < 0:
            return self.steps[0]
        if self.current_step_index >= len(self.steps):
            return self.steps[-1]
        return self.steps[self.current_step_index]

    @property
    def pending_gate(self) -> dict[str, Any] | None:
        for step in self.steps:
            if step.gate is None:
                continue
            if step.gate.status != "pending":
                continue
            if step.status not in {"pending", "blocked", "running"}:
                continue
            payload = step.gate.to_payload()
            payload["step_id"] = step.step_id
            payload["step_title"] = step.title
            return payload
        return None

    def to_payload(self) -> dict[str, Any]:
        current_step = self.current_step
        payload: dict[str, Any] = {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type,
            "status": self.status,
            "summary": self.summary,
            "current_step_index": self.current_step_index,
            "steps": [step.to_payload() for step in self.steps],
            "context": self.context,
        }
        if self.request is not None:
            payload["request"] = self.request
        if self.project_id is not None:
            payload["project_id"] = self.project_id
        if self.project_name is not None:
            payload["project_name"] = self.project_name
        if current_step is not None:
            payload["current_step"] = current_step.title
        if self.started_at is not None:
            payload["started_at"] = self.started_at
        if self.updated_at is not None:
            payload["updated_at"] = self.updated_at
        if self.finished_at is not None:
            payload["finished_at"] = self.finished_at
        if self.error is not None:
            payload["error"] = self.error
        gate = self.pending_gate
        if gate is not None:
            payload["pending_gate"] = gate
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "WorkflowState":
        raw_status = str(payload.get("status", "running")).strip() or "running"
        steps_payload = payload.get("steps")
        steps: list[WorkflowStepState] = []
        if isinstance(steps_payload, list):
            for item in steps_payload:
                if isinstance(item, dict):
                    steps.append(WorkflowStepState.from_payload(item))
        current_step_index = payload.get("current_step_index", 0)
        if not isinstance(current_step_index, int):
            current_step_index = 0
        return cls(
            workflow_id=str(payload.get("workflow_id", "")).strip(),
            workflow_type=str(payload.get("workflow_type", "")).strip() or "idea_to_code",
            status=raw_status
            if raw_status in {"running", "awaiting_approval", "blocked", "completed", "failed", "cancelled"}
            else "running",
            summary=str(payload.get("summary", "")).strip(),
            request=str(payload.get("request", "")).strip() or None,
            project_id=str(payload.get("project_id", "")).strip() or None,
            project_name=str(payload.get("project_name", "")).strip() or None,
            current_step_index=current_step_index,
            steps=steps,
            context=_as_dict(payload.get("context")),
            started_at=str(payload.get("started_at", "")).strip() or None,
            updated_at=str(payload.get("updated_at", "")).strip() or None,
            finished_at=str(payload.get("finished_at", "")).strip() or None,
            error=str(payload.get("error", "")).strip() or None,
        )
