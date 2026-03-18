from __future__ import annotations

# Privacy: no raw frames or embeddings leave the device
# This pipeline captures frames locally and discards them after processing.

import logging
import os
import threading
import time
from typing import Any

logger = logging.getLogger(__name__)

_CONSECUTIVE_ERROR_LIMIT = int(os.getenv("JARVEZ_CAMERA_ERROR_LIMIT", "10"))
_CAMERA_INDEX = int(os.getenv("JARVEZ_CAMERA_INDEX", "0"))

_STATE_ACTIVE = "active"
_STATE_PAUSED = "paused"
_STATE_STOPPED = "stopped"
_STATE_ERROR = "error"


def _import_cv2() -> Any:
    try:
        import cv2  # type: ignore[import-untyped]
        return cv2
    except ImportError as exc:
        raise ImportError(
            "cv2 (opencv-python) is required for the camera pipeline. "
            "Install it with: pip install opencv-python"
        ) from exc


class CameraPipeline:
    """
    Passive singleton camera capture pipeline.
    CAM1 — starts once and runs in a daemon thread, pausing/resuming without restart.
    Privacy: no raw frames are persisted; only structured events leave this module.
    """

    def __init__(self, camera_index: int = _CAMERA_INDEX) -> None:
        self._camera_index = camera_index
        self._state: str = _STATE_STOPPED
        self._frame: Any = None  # numpy array or None
        self._frame_lock = threading.Lock()
        self._pause_event = threading.Event()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._consecutive_errors: int = 0
        self._fps_real: float = 0.0
        self._frames_captured: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def is_active(self) -> bool:
        return self._state == _STATE_ACTIVE

    def get_state(self) -> str:
        return self._state

    def get_telemetry(self) -> dict[str, Any]:
        return {
            "state": self._state,
            "fps_real": round(self._fps_real, 2),
            "consecutive_errors": self._consecutive_errors,
            "frames_captured": self._frames_captured,
        }

    def get_frame(self) -> Any:
        """Return the latest captured frame (numpy array) or None."""
        # Privacy: caller must never persist this frame
        with self._frame_lock:
            return self._frame

    def start(self) -> None:
        """Start capture thread. Idempotent — safe to call multiple times."""
        if self._state in (_STATE_ACTIVE, _STATE_PAUSED):
            return
        self._stop_event.clear()
        self._pause_event.set()  # not paused initially
        self._state = _STATE_ACTIVE
        self._thread = threading.Thread(
            target=self._capture_loop,
            daemon=True,
            name="jarvez-camera-capture",
        )
        self._thread.start()
        logger.info("CameraPipeline started (index=%d)", self._camera_index)

    def stop(self) -> None:
        """Stop capture thread cleanly."""
        self._stop_event.set()
        self._pause_event.set()  # unblock if paused so thread can exit
        self._state = _STATE_STOPPED
        with self._frame_lock:
            self._frame = None
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None
        logger.info("CameraPipeline stopped")

    def pause(self) -> None:
        """
        Pause frame processing. No new frames are captured or made available.
        Privacy: ensures no frame updates while paused.
        """
        if self._state == _STATE_ACTIVE:
            self._pause_event.clear()
            self._state = _STATE_PAUSED
            logger.info("CameraPipeline paused")

    def resume(self) -> None:
        """Resume frame processing after pause."""
        if self._state == _STATE_PAUSED:
            self._pause_event.set()
            self._state = _STATE_ACTIVE
            logger.info("CameraPipeline resumed")

    # ------------------------------------------------------------------
    # Internal capture loop
    # ------------------------------------------------------------------

    def _capture_loop(self) -> None:
        cv2 = _import_cv2()
        cap: Any = None
        try:
            cap = cv2.VideoCapture(self._camera_index)
            if not cap.isOpened():
                logger.error("CameraPipeline: failed to open camera index %d", self._camera_index)
                self._state = _STATE_ERROR
                return

            t_prev = time.monotonic()
            while not self._stop_event.is_set():
                # Block if paused
                self._pause_event.wait(timeout=1.0)
                if self._stop_event.is_set():
                    break
                if not self._pause_event.is_set():
                    continue

                ok, frame = cap.read()
                if not ok or frame is None:
                    self._consecutive_errors += 1
                    logger.warning(
                        "CameraPipeline: frame read failed (%d/%d)",
                        self._consecutive_errors,
                        _CONSECUTIVE_ERROR_LIMIT,
                    )
                    if self._consecutive_errors >= _CONSECUTIVE_ERROR_LIMIT:
                        logger.error("CameraPipeline: too many consecutive errors → error state")
                        self._state = _STATE_ERROR
                        break
                    time.sleep(0.1)
                    continue

                self._consecutive_errors = 0
                with self._frame_lock:
                    self._frame = frame

                self._frames_captured += 1
                t_now = time.monotonic()
                elapsed = t_now - t_prev
                if elapsed > 0:
                    self._fps_real = 1.0 / elapsed
                t_prev = t_now

        except Exception as exc:
            logger.exception("CameraPipeline: unexpected error in capture loop: %s", exc)
            self._state = _STATE_ERROR
        finally:
            if cap is not None:
                cap.release()
            logger.info("CameraPipeline capture loop exited")


# ------------------------------------------------------------------
# Singleton
# ------------------------------------------------------------------

_pipeline_instance: CameraPipeline | None = None
_pipeline_lock = threading.Lock()


def get_camera_pipeline() -> CameraPipeline:
    """Return (creating if needed) the global singleton CameraPipeline."""
    global _pipeline_instance
    with _pipeline_lock:
        if _pipeline_instance is None:
            _pipeline_instance = CameraPipeline()
        return _pipeline_instance
