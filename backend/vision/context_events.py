from __future__ import annotations

# CTX6: Visual context triggers only R1 (low-risk) actions automatically.
# R2+ actions (messages, data, code) always require explicit confirmation
# regardless of recognized identity or visual context.

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class VisualEvent:
    """
    CTX1 — Structured contract for visual events consumed by the automation loop.
    Converts camera/pose/gesture signals into the format expected by
    evaluate_arrival_presence_trigger and execute_automation_cycle.
    """

    event_type: str        # "presence_detected", "presence_lost", "got_up", "lay_down", etc.
    source: str            # "camera_pipeline"
    confidence: float
    timestamp: str = field(default_factory=_now_iso)
    identity: str | None = None   # recognized identity name if available, else None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_presence_event(self, entity_id: str) -> dict[str, Any]:
        """
        Convert to format expected by evaluate_arrival_presence_trigger.
        Maps visual event types to presence states.
        """
        # Map visual events to presence states
        _presence_new_state = {
            "presence_detected": "home",
            "got_up": "present",
            "approached_pc": "present",
            "lay_down": "present",
            "left_room": "not_home",
            "presence_lost": "not_home",
        }
        _presence_old_state = {
            "presence_detected": "not_home",
            "got_up": "present",
            "approached_pc": "present",
            "lay_down": "present",
            "left_room": "home",
            "presence_lost": "home",
        }
        new_state = _presence_new_state.get(self.event_type, "present")
        old_state = _presence_old_state.get(self.event_type, "present")

        return {
            "entity_id": entity_id,
            "old_state": old_state,
            "new_state": new_state,
            "source": self.source,
            "changed_at": self.timestamp,
        }

    def to_automation_params(self) -> dict[str, Any]:
        """
        Return params dict consumable by execute_automation_cycle.
        Embeds the presence_event and extra visual context.
        """
        return {
            "presence_event": {
                "entity_id": "camera_pipeline",
                "old_state": "not_home" if self.event_type == "presence_detected" else "present",
                "new_state": "home" if self.event_type == "presence_detected" else "present",
                "source": self.source,
                "changed_at": self.timestamp,
            },
            "visual_event_type": self.event_type,
            "visual_confidence": self.confidence,
            "visual_identity": self.identity,
            "visual_metadata": self.metadata,
            "visual_timestamp": self.timestamp,
        }
