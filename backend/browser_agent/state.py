from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BrowserTaskState:
    task_id: str
    status: str
    request: str
    allowed_domains: list[str]
    read_only: bool
    summary: str | None = None
    error: str | None = None
    started_at: str | None = None
    finished_at: str | None = None

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "task_id": self.task_id,
            "status": self.status,
            "request": self.request,
            "allowed_domains": list(self.allowed_domains),
            "read_only": self.read_only,
        }
        if self.summary is not None:
            payload["summary"] = self.summary
        if self.error is not None:
            payload["error"] = self.error
        if self.started_at is not None:
            payload["started_at"] = self.started_at
        if self.finished_at is not None:
            payload["finished_at"] = self.finished_at
        return payload
