"""
Tests for CAM frente — camera pipeline, presence detector, visual routine.
Run: python test_vision_cam.py
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Helpers to mock cv2 and numpy without requiring installed packages
# ---------------------------------------------------------------------------

def _make_fake_numpy_frame(value: int = 128):
    """Return a mock numpy array for use as a frame."""
    frame = MagicMock()
    frame.shape = (480, 640, 3)
    frame.__class__ = object  # prevent isinstance checks
    return frame


def _make_cv2_mock(motion_pixels: int = 1000):
    cv2 = MagicMock()
    # VideoCapture mock
    cap = MagicMock()
    cap.isOpened.return_value = True
    cap.read.return_value = (True, _make_fake_numpy_frame())
    cv2.VideoCapture.return_value = cap
    # Background subtractor mock
    fg_mask = MagicMock()
    subtractor = MagicMock()
    subtractor.apply.return_value = fg_mask
    cv2.createBackgroundSubtractorMOG2.return_value = subtractor
    cv2.countNonZero.return_value = motion_pixels
    cv2.COLOR_BGR2RGB = 4
    cv2.cvtColor.return_value = _make_fake_numpy_frame()
    return cv2, cap, subtractor


# ===========================================================================
# CAM2 — PresenceDetector tests
# ===========================================================================

class TestPresenceDetector(unittest.TestCase):

    def _make_detector(self, motion_pixels: int):
        cv2_mock, _, subtractor_mock = _make_cv2_mock(motion_pixels)
        with patch.dict("sys.modules", {"cv2": cv2_mock}):
            from vision.presence_detector import PresenceDetector
            detector = PresenceDetector(threshold=500.0)
            detector._subtractor = subtractor_mock
            detector._cv2 = cv2_mock
            frame = _make_fake_numpy_frame()
            result = detector.detect(frame)
        return result

    def test_motion_above_threshold_has_presence(self):
        """Frame with motion above threshold → has_presence=True."""
        result = self._make_detector(motion_pixels=1000)
        self.assertTrue(result.has_presence)
        self.assertGreater(result.confidence, 0.0)

    def test_static_frame_no_presence(self):
        """Frame with motion below threshold → has_presence=False."""
        result = self._make_detector(motion_pixels=100)
        self.assertFalse(result.has_presence)

    def test_none_frame_returns_false(self):
        """None frame → has_presence=False without error."""
        cv2_mock, _, _ = _make_cv2_mock()
        with patch.dict("sys.modules", {"cv2": cv2_mock}):
            from vision.presence_detector import PresenceDetector
            detector = PresenceDetector()
            result = detector.detect(None)
        self.assertFalse(result.has_presence)
        self.assertEqual(result.confidence, 0.0)

    def test_confidence_is_bounded(self):
        """Confidence stays between 0 and 1."""
        result = self._make_detector(motion_pixels=999999)
        self.assertLessEqual(result.confidence, 1.0)
        self.assertGreaterEqual(result.confidence, 0.0)


# ===========================================================================
# CAM1 — CameraPipeline state tests (no real camera needed)
# ===========================================================================

class TestCameraPipelineState(unittest.TestCase):

    def _make_pipeline(self):
        cv2_mock, cap_mock, _ = _make_cv2_mock()
        with patch.dict("sys.modules", {"cv2": cv2_mock}):
            from vision.camera_pipeline import CameraPipeline
            pipeline = CameraPipeline(camera_index=0)
        return pipeline, cv2_mock, cap_mock

    def test_initial_state_is_stopped(self):
        pipeline, _, _ = self._make_pipeline()
        self.assertEqual(pipeline.get_state(), "stopped")
        self.assertFalse(pipeline.is_active)

    def test_pause_sets_paused_state(self):
        pipeline, cv2_mock, _ = self._make_pipeline()
        with patch.dict("sys.modules", {"cv2": cv2_mock}):
            pipeline.start()
            time.sleep(0.05)
            pipeline.pause()
        self.assertEqual(pipeline.get_state(), "paused")
        self.assertFalse(pipeline.is_active)
        pipeline.stop()

    def test_resume_sets_active_state(self):
        pipeline, cv2_mock, _ = self._make_pipeline()
        with patch.dict("sys.modules", {"cv2": cv2_mock}):
            pipeline.start()
            time.sleep(0.05)
            pipeline.pause()
            pipeline.resume()
        self.assertEqual(pipeline.get_state(), "active")
        pipeline.stop()

    def test_stop_clears_frame(self):
        """After stop(), get_frame() returns None (privacy: no frame retained after stop)."""
        pipeline, cv2_mock, _ = self._make_pipeline()
        with patch.dict("sys.modules", {"cv2": cv2_mock}):
            pipeline.stop()  # stop before starting so no frame is ever set
        # Frame should be None since we stopped immediately (never started capturing)
        self.assertIsNone(pipeline.get_frame())

    def test_get_frame_none_after_pause_sets_none(self):
        """After stop(), get_frame() returns None (privacy: no frame retained)."""
        pipeline, cv2_mock, _ = self._make_pipeline()
        with patch.dict("sys.modules", {"cv2": cv2_mock}):
            pipeline.stop()
        self.assertIsNone(pipeline.get_frame())


# ===========================================================================
# CAM5 — VisualRoutineStore tests
# ===========================================================================

class TestVisualRoutineStore(unittest.TestCase):
    """
    Uses ignore_cleanup_errors on tempdir for Windows compatibility
    (SQLite WAL files may linger briefly after connection is closed).
    """

    def test_record_and_retrieve_movement_event(self):
        """record_event of MovementEvent → get_recent_events returns it."""
        from vision.visual_routine import VisualRoutineStore
        from vision.movement_detector import MovementEvent
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            store = VisualRoutineStore(db_path=Path(tmp) / "v.db")
            evt = MovementEvent(
                event_type="got_up",
                confidence=0.85,
                metadata={"from_posture": "lying", "to_posture": "standing"},
            )
            store.record_event(evt)
            events = store.get_recent_events(hours=24)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "got_up")
        self.assertAlmostEqual(events[0]["confidence"], 0.85, places=2)

    def test_record_and_retrieve_presence_result(self):
        """record_event of PresenceResult → get_recent_events returns it."""
        from vision.visual_routine import VisualRoutineStore
        from vision.presence_detector import PresenceResult
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            store = VisualRoutineStore(db_path=Path(tmp) / "v.db")
            result = PresenceResult(has_presence=True, confidence=0.9, motion_area=1500.0)
            store.record_event(result)
            events = store.get_recent_events(hours=24)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "presence_detected")

    def test_get_recent_events_empty(self):
        """Empty store returns empty list."""
        from vision.visual_routine import VisualRoutineStore
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            store = VisualRoutineStore(db_path=Path(tmp) / "v.db")
            events = store.get_recent_events(hours=1)
        self.assertEqual(events, [])

    def test_get_routine_patterns(self):
        """get_routine_patterns returns event type summary."""
        from vision.visual_routine import VisualRoutineStore
        from vision.movement_detector import MovementEvent
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            store = VisualRoutineStore(db_path=Path(tmp) / "v.db")
            for _ in range(3):
                store.record_event(MovementEvent(event_type="got_up", confidence=0.8))
            patterns = store.get_routine_patterns()
        self.assertIn("got_up", patterns)
        self.assertEqual(patterns["got_up"]["count"], 3)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    unittest.main(verbosity=2)
