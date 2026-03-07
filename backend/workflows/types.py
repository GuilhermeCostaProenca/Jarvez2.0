from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class WorkflowState:
    workflow_id: str
    workflow_type: str
    status: str
    summary: str
    project_id: str | None = None
    project_name: str | None = None
    current_step: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type,
            "status": self.status,
            "summary": self.summary,
        }
        if self.project_id is not None:
            payload["project_id"] = self.project_id
        if self.project_name is not None:
            payload["project_name"] = self.project_name
        if self.current_step is not None:
            payload["current_step"] = self.current_step
        if self.started_at is not None:
            payload["started_at"] = self.started_at
        if self.finished_at is not None:
            payload["finished_at"] = self.finished_at
        if self.error is not None:
            payload["error"] = self.error
        return payload
