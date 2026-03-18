from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

_DEBOUNCE_MS = 500  # milliseconds

# GES1 — Default gesture map (user-configurable via user_preferences key "gesture_map")
DEFAULT_GESTURE_MAP: dict[str, dict[str, Any]] = {
    "wave": {
        "action": "toggle_light",
        "params": {"area": "bedroom"},
        "description": "Aceno = ligar/desligar luz",
        "min_confidence": 0.7,
    },
    "open_hand": {
        "action": "media_pause",
        "params": {},
        "description": "Mão aberta = pausar música",
        "min_confidence": 0.75,
    },
    "fist": {
        # GES4 — fist is the global cancel primitive
        "action": "__cancel__",
        "params": {},
        "description": "Punho = cancelar ação em andamento",
        "min_confidence": 0.8,
    },
}


def _import_mediapipe() -> Any:
    try:
        import mediapipe as mp  # type: ignore[import-untyped]
        return mp
    except ImportError as exc:
        raise ImportError(
            "mediapipe is required for gesture detection. "
            "Install it with: pip install mediapipe"
        ) from exc


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class GestureResult:
    gesture_name: str
    confidence: float
    timestamp: str = field(default_factory=_now_iso)
    action: str = ""
    action_params: dict[str, Any] = field(default_factory=dict)


class GestureEngine:
    """
    GES1+GES2 — Detects hand gestures using MediaPipe Hands landmarks.
    GES3 — Receives frames from CameraPipeline (no new camera opened).
    GES4 — fist gesture emits __cancel__ primitive.
    GES5 — Gesture map loaded from user_preferences if available, else uses DEFAULT_GESTURE_MAP.
    """

    def __init__(self, user_preferences: dict[str, Any] | None = None) -> None:
        # GES5 — load from user preferences if available
        prefs = user_preferences or {}
        user_gesture_map = prefs.get("gesture_map")
        if isinstance(user_gesture_map, dict) and user_gesture_map:
            self._gesture_map = user_gesture_map
        else:
            self._gesture_map = dict(DEFAULT_GESTURE_MAP)

        self._hands: Any = None
        self._mp: Any = None
        self._last_detection_ms: dict[str, float] = {}
        # For wave detection: track previous wrist x position
        self._prev_wrist_x: float | None = None
        self._wave_positions: list[float] = []

    def _ensure_hands(self) -> None:
        if self._hands is None:
            mp = _import_mediapipe()
            self._mp = mp
            self._hands = mp.solutions.hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.6,
                min_tracking_confidence=0.5,
            )

    def detect(self, frame: Any) -> GestureResult | None:
        """
        GES3 — Detect gesture in frame captured by CameraPipeline.
        Returns GestureResult or None if no gesture detected or debounce active.
        """
        if frame is None:
            return None

        self._ensure_hands()

        try:
            import cv2  # type: ignore[import-untyped]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self._hands.process(rgb)
        except Exception as exc:
            logger.warning("GestureEngine: error processing frame: %s", exc)
            return None

        if results is None or not results.multi_hand_landmarks:
            self._prev_wrist_x = None
            return None

        hand_landmarks = results.multi_hand_landmarks[0]
        gesture_name, confidence = self._classify_gesture(hand_landmarks)

        if gesture_name is None:
            return None

        # Check gesture map
        gesture_config = self._gesture_map.get(gesture_name)
        if gesture_config is None:
            return None

        min_conf = float(gesture_config.get("min_confidence", 0.0))
        if confidence < min_conf:
            return None

        # Debounce check
        now_ms = time.monotonic() * 1000
        last_ms = self._last_detection_ms.get(gesture_name, 0.0)
        if now_ms - last_ms < _DEBOUNCE_MS:
            logger.debug(
                "GestureEngine: debouncing %s (%.0fms elapsed, need %dms)",
                gesture_name,
                now_ms - last_ms,
                _DEBOUNCE_MS,
            )
            return None

        self._last_detection_ms[gesture_name] = now_ms
        action = str(gesture_config.get("action", ""))
        action_params = dict(gesture_config.get("params") or {})

        logger.info(
            "gesture_detected | name=%s confidence=%.3f action=%s",
            gesture_name,
            confidence,
            action,
        )

        # GES4 — emit cancel primitive if action is __cancel__
        if action == "__cancel__":
            return GestureResult(
                gesture_name="fist",
                confidence=round(confidence, 3),
                timestamp=_now_iso(),
                action="__cancel__",
                action_params={},
            )

        return GestureResult(
            gesture_name=gesture_name,
            confidence=round(confidence, 3),
            timestamp=_now_iso(),
            action=action,
            action_params=action_params,
        )

    def _classify_gesture(self, hand_landmarks: Any) -> tuple[str | None, float]:
        """
        Classify gesture using simple landmark heuristics.
        Finger indices in MediaPipe Hands:
          Thumb: 1-4, Index: 5-8, Middle: 9-12, Ring: 13-16, Pinky: 17-20
          Wrist: 0
        tip indices: thumb=4, index=8, middle=12, ring=16, pinky=20
        mcp indices: thumb=2, index=5, middle=9, ring=13, pinky=17
        """
        try:
            lm = hand_landmarks.landmark

            # Extract fingertip and MCP y-coordinates
            tips = [lm[4], lm[8], lm[12], lm[16], lm[20]]
            mcps = [lm[2], lm[5], lm[9], lm[13], lm[17]]

            # Finger is extended if tip.y < mcp.y (MediaPipe: y decreases upward in image)
            extended = [tips[i].y < mcps[i].y for i in range(5)]
            n_extended = sum(extended)

            wrist_x = lm[0].x

            # Wave detection: horizontal wrist movement
            self._wave_positions.append(wrist_x)
            if len(self._wave_positions) > 15:
                self._wave_positions.pop(0)

            if len(self._wave_positions) >= 10:
                x_range = max(self._wave_positions) - min(self._wave_positions)
                direction_changes = sum(
                    1
                    for i in range(2, len(self._wave_positions))
                    if (self._wave_positions[i] - self._wave_positions[i - 1]) *
                       (self._wave_positions[i - 1] - self._wave_positions[i - 2]) < 0
                )
                if x_range > 0.15 and direction_changes >= 2:
                    self._wave_positions.clear()
                    return "wave", 0.75

            # Fist: all fingers closed (0 extended)
            if n_extended == 0:
                return "fist", 0.90

            # Open hand: all 5 fingers extended
            if n_extended == 5:
                return "open_hand", 0.85

            return None, 0.0

        except Exception as exc:
            logger.debug("GestureEngine: landmark classification error: %s", exc)
            return None, 0.0
