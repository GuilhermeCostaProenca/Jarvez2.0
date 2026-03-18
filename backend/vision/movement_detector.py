from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .presence_detector import PresenceResult
from .pose_classifier import PoseResult

logger = logging.getLogger(__name__)

_DEBOUNCE_SECONDS = 10.0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(ts: str) -> datetime | None:
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None


@dataclass(slots=True)
class MovementEvent:
    event_type: str
    confidence: float
    timestamp: str = field(default_factory=_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)


class MovementDetector:
    """
    CAM4 — State machine that derives movement events from presence + pose transitions.
    Supported events: got_up, lay_down, approached_pc, left_room
    Debounce: same event is not emitted within DEBOUNCE_SECONDS.
    """

    def __init__(self, debounce_seconds: float = _DEBOUNCE_SECONDS) -> None:
        self._debounce_seconds = debounce_seconds
        self._last_posture: str | None = None
        self._last_presence: bool | None = None
        self._presence_start: datetime | None = None
        self._last_event_at: dict[str, datetime] = {}
        # Track motion area trend for approached_pc heuristic
        self._motion_history: list[float] = []
        self._max_motion_history = 10

    def update(
        self,
        presence_result: PresenceResult,
        pose_result: PoseResult,
        timestamp: str,
    ) -> list[MovementEvent]:
        """
        Process new frame signals and return any triggered MovementEvents.
        """
        events: list[MovementEvent] = []
        now = _parse_iso(timestamp) or datetime.now(timezone.utc)

        curr_presence = presence_result.has_presence
        curr_posture = pose_result.posture

        # Track motion area trend
        self._motion_history.append(presence_result.motion_area)
        if len(self._motion_history) > self._max_motion_history:
            self._motion_history.pop(0)

        # --- Presence transitions ---
        if self._last_presence is not None:
            if self._last_presence and not curr_presence:
                # Presence lost — check if it was long enough to be "left_room"
                if self._presence_start is not None:
                    duration = (now - self._presence_start).total_seconds()
                    if duration >= 60.0:  # Was present for at least 60s
                        evt = self._make_event(
                            "left_room",
                            confidence=min(1.0, duration / 300.0),
                            now=now,
                            metadata={"presence_duration_s": round(duration, 1)},
                        )
                        if evt is not None:
                            events.append(evt)
                self._presence_start = None
            elif not self._last_presence and curr_presence:
                self._presence_start = now

        if curr_presence and self._presence_start is None:
            self._presence_start = now

        # --- Posture transitions ---
        if self._last_posture is not None and curr_posture not in ("unknown", "out_of_frame"):
            prev = self._last_posture
            curr = curr_posture

            if prev == "lying" and curr in ("standing", "sitting"):
                evt = self._make_event(
                    "got_up",
                    confidence=pose_result.confidence,
                    now=now,
                    metadata={"from_posture": prev, "to_posture": curr},
                )
                if evt is not None:
                    events.append(evt)

            elif prev in ("standing", "sitting") and curr == "lying":
                evt = self._make_event(
                    "lay_down",
                    confidence=pose_result.confidence,
                    now=now,
                    metadata={"from_posture": prev, "to_posture": curr},
                )
                if evt is not None:
                    events.append(evt)

        # --- approached_pc: increasing motion area trend while presence is active ---
        if curr_presence and len(self._motion_history) >= self._max_motion_history:
            first_half = sum(self._motion_history[: self._max_motion_history // 2])
            second_half = sum(self._motion_history[self._max_motion_history // 2 :])
            if second_half > first_half * 1.5:  # area grew 50%+ in last N frames
                evt = self._make_event(
                    "approached_pc",
                    confidence=min(1.0, second_half / (first_half + 1) / 3.0),
                    now=now,
                    metadata={"motion_trend": round(second_half / (first_half + 1), 2)},
                )
                if evt is not None:
                    events.append(evt)

        # Update state
        self._last_presence = curr_presence
        if curr_posture not in ("unknown", "out_of_frame"):
            self._last_posture = curr_posture

        return events

    def _make_event(
        self,
        event_type: str,
        confidence: float,
        now: datetime,
        metadata: dict[str, Any] | None = None,
    ) -> MovementEvent | None:
        """Create a MovementEvent if not within debounce window."""
        last = self._last_event_at.get(event_type)
        if last is not None:
            elapsed = (now - last).total_seconds()
            if elapsed < self._debounce_seconds:
                logger.debug(
                    "MovementDetector: debouncing %s (%.1fs elapsed, need %.1fs)",
                    event_type,
                    elapsed,
                    self._debounce_seconds,
                )
                return None

        self._last_event_at[event_type] = now
        logger.info(
            "movement_event | type=%s confidence=%.3f",
            event_type,
            confidence,
        )
        return MovementEvent(
            event_type=event_type,
            confidence=round(confidence, 3),
            timestamp=now.isoformat(),
            metadata=metadata or {},
        )
