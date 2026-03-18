from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

logger = logging.getLogger(__name__)

_SAMPLE_EVERY_N_FRAMES = 5
_POSTURE_STANDING = "standing"
_POSTURE_SITTING = "sitting"
_POSTURE_LYING = "lying"
_POSTURE_OUT_OF_FRAME = "out_of_frame"
_POSTURE_UNKNOWN = "unknown"

PostureType = Literal["standing", "sitting", "lying", "out_of_frame", "unknown"]


def _import_mediapipe() -> Any:
    try:
        import mediapipe as mp  # type: ignore[import-untyped]
        return mp
    except ImportError as exc:
        raise ImportError(
            "mediapipe is required for pose classification. "
            "Install it with: pip install mediapipe"
        ) from exc


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class PoseResult:
    posture: PostureType
    confidence: float
    landmarks_detected: bool
    timestamp: str = field(default_factory=_now_iso)


class PoseClassifier:
    """
    CAM3 — Classify body posture using MediaPipe Pose landmarks.
    Uses simple heuristics on shoulder/hip/ankle landmarks.
    Samples every N frames (default 5) to reduce GPU load.
    """

    def __init__(self, sample_every: int = _SAMPLE_EVERY_N_FRAMES) -> None:
        self._sample_every = max(1, sample_every)
        self._frame_count: int = 0
        self._last_result: PoseResult | None = None
        self._pose: Any = None
        self._mp: Any = None

    def _ensure_pose(self) -> None:
        if self._pose is None:
            mp = _import_mediapipe()
            self._mp = mp
            self._pose = mp.solutions.pose.Pose(
                static_image_mode=False,
                model_complexity=0,  # lightest model
                enable_segmentation=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )

    def classify(self, frame: Any) -> PoseResult:
        """
        Classify posture. Only runs inference every N frames.
        Returns last valid result on skipped frames.
        """
        self._frame_count += 1

        if frame is None:
            return PoseResult(
                posture=_POSTURE_OUT_OF_FRAME,
                confidence=0.0,
                landmarks_detected=False,
            )

        if self._frame_count % self._sample_every != 0:
            if self._last_result is not None:
                return self._last_result
            return PoseResult(posture=_POSTURE_UNKNOWN, confidence=0.0, landmarks_detected=False)

        self._ensure_pose()

        try:
            import cv2  # type: ignore[import-untyped]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self._pose.process(rgb)
        except Exception as exc:
            logger.warning("PoseClassifier: error processing frame: %s", exc)
            result = PoseResult(posture=_POSTURE_UNKNOWN, confidence=0.0, landmarks_detected=False)
            self._last_result = result
            return result

        if results is None or not results.pose_landmarks:
            result = PoseResult(
                posture=_POSTURE_OUT_OF_FRAME,
                confidence=0.0,
                landmarks_detected=False,
            )
            self._last_result = result
            return result

        posture, confidence = self._classify_landmarks(results.pose_landmarks)
        result = PoseResult(
            posture=posture,
            confidence=round(confidence, 3),
            landmarks_detected=True,
        )
        self._last_result = result
        return result

    def _classify_landmarks(self, landmarks: Any) -> tuple[PostureType, float]:
        """
        Simple heuristic classification based on y-coordinates (normalized 0-1).
        In MediaPipe, y increases downward in image space.
        Landmark indices:
          11 = left shoulder, 12 = right shoulder
          23 = left hip, 24 = right hip
          27 = left ankle, 28 = right ankle
        """
        try:
            mp_pose = self._mp.solutions.pose.PoseLandmark
            lm = landmarks.landmark

            left_shoulder_y = lm[mp_pose.LEFT_SHOULDER].y
            right_shoulder_y = lm[mp_pose.RIGHT_SHOULDER].y
            left_hip_y = lm[mp_pose.LEFT_HIP].y
            right_hip_y = lm[mp_pose.RIGHT_HIP].y
            left_ankle_y = lm[mp_pose.LEFT_ANKLE].y
            right_ankle_y = lm[mp_pose.RIGHT_ANKLE].y

            shoulder_y = (left_shoulder_y + right_shoulder_y) / 2.0
            hip_y = (left_hip_y + right_hip_y) / 2.0
            ankle_y = (left_ankle_y + right_ankle_y) / 2.0

            torso_len = abs(hip_y - shoulder_y)
            leg_len = abs(ankle_y - hip_y)

            # Heuristic: if ankles and hips are at similar height (horizontal body)
            if abs(ankle_y - shoulder_y) < 0.25 and torso_len < 0.15:
                return _POSTURE_LYING, 0.75

            # Standing: legs are clearly below hips which are below shoulders
            if leg_len > 0.3 and leg_len > torso_len * 0.8:
                return _POSTURE_STANDING, 0.80

            # Sitting: torso present but legs shorter/folded
            if torso_len > 0.1:
                return _POSTURE_SITTING, 0.70

            return _POSTURE_UNKNOWN, 0.3

        except Exception as exc:
            logger.debug("PoseClassifier: landmark classification error: %s", exc)
            return _POSTURE_UNKNOWN, 0.0
