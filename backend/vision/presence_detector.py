from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

_PRESENCE_THRESHOLD = float(os.getenv("JARVEZ_PRESENCE_THRESHOLD", "500"))


def _import_cv2() -> Any:
    try:
        import cv2  # type: ignore[import-untyped]
        return cv2
    except ImportError as exc:
        raise ImportError(
            "cv2 (opencv-python) is required for presence detection. "
            "Install it with: pip install opencv-python"
        ) from exc


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class PresenceResult:
    has_presence: bool
    confidence: float
    motion_area: float
    timestamp: str = field(default_factory=_now_iso)


class PresenceDetector:
    """
    CAM2 — Detects presence/absence using OpenCV background subtraction.
    Uses MOG2 with conservative parameters to reduce false positives.
    """

    def __init__(self, threshold: float = _PRESENCE_THRESHOLD) -> None:
        self._threshold = threshold
        self._subtractor: Any = None
        self._last_has_presence: bool | None = None
        self._presence_since: str | None = None
        self._cv2: Any = None

    def _ensure_subtractor(self) -> None:
        if self._subtractor is None:
            cv2 = _import_cv2()
            self._cv2 = cv2
            # Conservative MOG2: high history, high varThreshold to avoid noise
            self._subtractor = cv2.createBackgroundSubtractorMOG2(
                history=500,
                varThreshold=50,
                detectShadows=False,
            )

    def detect(self, frame: Any) -> PresenceResult:
        """
        Detect presence in the given frame.
        Returns PresenceResult with has_presence, confidence and motion_area.
        """
        if frame is None:
            return PresenceResult(has_presence=False, confidence=0.0, motion_area=0.0)

        self._ensure_subtractor()
        now = _now_iso()

        try:
            fg_mask = self._subtractor.apply(frame)
            # Count non-zero pixels (motion area in pixels)
            motion_area = float(self._cv2.countNonZero(fg_mask))
        except Exception as exc:
            logger.warning("PresenceDetector: error processing frame: %s", exc)
            return PresenceResult(has_presence=False, confidence=0.0, motion_area=0.0)

        has_presence = motion_area >= self._threshold

        # Confidence scaled from 0 to 1 relative to threshold * 3 (cap at 1.0)
        raw_confidence = min(1.0, motion_area / (self._threshold * 3.0)) if self._threshold > 0 else 0.0

        result = PresenceResult(
            has_presence=has_presence,
            confidence=round(raw_confidence, 3),
            motion_area=round(motion_area, 1),
            timestamp=now,
        )

        self._emit_event(result)
        return result

    def _emit_event(self, result: PresenceResult) -> None:
        """Log structured presence/absence transition events."""
        prev = self._last_has_presence
        curr = result.has_presence

        if prev is None:
            self._last_has_presence = curr
            if curr:
                self._presence_since = result.timestamp
            return

        if not prev and curr:
            self._presence_since = result.timestamp
            logger.info(
                "presence_detected | confidence=%.3f motion_area=%.1f timestamp=%s",
                result.confidence,
                result.motion_area,
                result.timestamp,
            )
        elif prev and not curr:
            duration = self._calc_duration(self._presence_since, result.timestamp)
            self._presence_since = None
            logger.info(
                "presence_lost | confidence=%.3f motion_area=%.1f timestamp=%s duration_s=%.1f",
                result.confidence,
                result.motion_area,
                result.timestamp,
                duration,
            )

        self._last_has_presence = curr

    @staticmethod
    def _calc_duration(since_iso: str | None, now_iso: str) -> float:
        if since_iso is None:
            return 0.0
        try:
            from datetime import datetime
            fmt = "%Y-%m-%dT%H:%M:%S.%f+00:00"
            t0 = datetime.fromisoformat(since_iso)
            t1 = datetime.fromisoformat(now_iso)
            return max(0.0, (t1 - t0).total_seconds())
        except Exception:
            return 0.0
