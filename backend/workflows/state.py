from __future__ import annotations

from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def cancel_workflow_state(current: dict[str, object]) -> dict[str, object]:
    next_state = dict(current)
    next_state["status"] = "cancelled"
    next_state["finished_at"] = _now_iso()
    next_state["summary"] = "Workflow cancelado antes da execucao."
    return next_state
