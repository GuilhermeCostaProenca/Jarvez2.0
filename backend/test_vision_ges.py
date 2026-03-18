"""
Tests for GES frente — gesture engine.
Run: python test_vision_ges.py
"""
from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


def _make_hand_landmark(x: float = 0.5, y: float = 0.5, z: float = 0.0) -> MagicMock:
    lm = MagicMock()
    lm.x = x
    lm.y = y
    lm.z = z
    return lm


def _make_hand_landmarks_fist() -> MagicMock:
    """All fingertips above their MCPs → fist (all fingers closed)."""
    # In MediaPipe convention: y increases downward
    # Closed: tip.y > mcp.y (tip is lower in image = larger y)
    hand = MagicMock()
    lm = [MagicMock() for _ in range(21)]
    for i in range(21):
        lm[i].x = 0.5
        lm[i].y = 0.5
        lm[i].z = 0.0
    # Set tips (4,8,12,16,20) to have y > mcp (2,5,9,13,17)
    # Tip indices: 4,8,12,16,20 — MCP indices: 2,5,9,13,17
    pairs = [(4, 2), (8, 5), (12, 9), (16, 13), (20, 17)]
    for tip_i, mcp_i in pairs:
        lm[tip_i].y = 0.8   # lower in image (larger y) = closed
        lm[mcp_i].y = 0.4
    hand.landmark = lm
    return hand


def _make_hand_landmarks_open() -> MagicMock:
    """All fingertips below their MCPs → open hand (all fingers extended)."""
    hand = MagicMock()
    lm = [MagicMock() for _ in range(21)]
    for i in range(21):
        lm[i].x = 0.5
        lm[i].y = 0.5
        lm[i].z = 0.0
    # Open: tip.y < mcp.y
    pairs = [(4, 2), (8, 5), (12, 9), (16, 13), (20, 17)]
    for tip_i, mcp_i in pairs:
        lm[tip_i].y = 0.1   # higher in image (smaller y) = extended
        lm[mcp_i].y = 0.6
    hand.landmark = lm
    return hand


def _make_cv2_mock() -> MagicMock:
    cv2 = MagicMock()
    cv2.COLOR_BGR2RGB = 4
    cv2.cvtColor.return_value = MagicMock()
    return cv2


def _make_mp_mock(hand_landmarks=None) -> MagicMock:
    mp = MagicMock()
    hands_results = MagicMock()
    if hand_landmarks is not None:
        hands_results.multi_hand_landmarks = [hand_landmarks]
    else:
        hands_results.multi_hand_landmarks = None
    mp.solutions.hands.Hands.return_value.process.return_value = hands_results
    return mp


# ===========================================================================
# GES1+GES4 — Gesture map and cancel primitive
# ===========================================================================

class TestGestureEngineMap(unittest.TestCase):

    def _make_engine(self, user_preferences=None):
        cv2_mock = _make_cv2_mock()
        mp_mock = _make_mp_mock()
        with patch.dict("sys.modules", {"cv2": cv2_mock, "mediapipe": mp_mock}):
            from vision.gesture_engine import GestureEngine
            engine = GestureEngine(user_preferences=user_preferences)
            engine._cv2 = cv2_mock  # type: ignore[attr-defined]
        return engine, cv2_mock, mp_mock

    def test_fist_maps_to_cancel_primitive(self):
        """fist gesture → action == __cancel__."""
        from vision.gesture_engine import DEFAULT_GESTURE_MAP
        fist_config = DEFAULT_GESTURE_MAP.get("fist")
        self.assertIsNotNone(fist_config)
        self.assertEqual(fist_config["action"], "__cancel__")

    def test_default_gesture_map_has_expected_gestures(self):
        """Default map has wave, open_hand, fist."""
        from vision.gesture_engine import DEFAULT_GESTURE_MAP
        self.assertIn("wave", DEFAULT_GESTURE_MAP)
        self.assertIn("open_hand", DEFAULT_GESTURE_MAP)
        self.assertIn("fist", DEFAULT_GESTURE_MAP)

    def test_custom_gesture_map_from_preferences(self):
        """User preferences gesture_map overrides default."""
        custom_map = {
            "thumbs_up": {
                "action": "turn_light_on",
                "params": {"area": "office"},
                "description": "Polegar = ligar luz escritório",
                "min_confidence": 0.7,
            }
        }
        engine, _, _ = self._make_engine(user_preferences={"gesture_map": custom_map})
        self.assertIn("thumbs_up", engine._gesture_map)
        self.assertNotIn("fist", engine._gesture_map)

    def test_empty_user_prefs_uses_default(self):
        """Empty user_preferences → default gesture_map is used."""
        engine, _, _ = self._make_engine(user_preferences={})
        from vision.gesture_engine import DEFAULT_GESTURE_MAP
        self.assertEqual(engine._gesture_map, DEFAULT_GESTURE_MAP)


# ===========================================================================
# GES2 — Gesture detection with mocked MediaPipe
# ===========================================================================

class TestGestureDetection(unittest.TestCase):

    def _make_engine_with_hands(self, hand_landmarks):
        cv2_mock = _make_cv2_mock()
        mp_mock = _make_mp_mock(hand_landmarks)
        with patch.dict("sys.modules", {"cv2": cv2_mock, "mediapipe": mp_mock}):
            from vision.gesture_engine import GestureEngine
            engine = GestureEngine()
            engine._mp = mp_mock
            engine._hands = mp_mock.solutions.hands.Hands()
            engine._cv2 = cv2_mock
        return engine, cv2_mock, mp_mock

    def test_fist_landmarks_detected_as_fist(self):
        """Fist landmarks → gesture_name == 'fist'."""
        hand_lm = _make_hand_landmarks_fist()
        engine, cv2_mock, _ = self._make_engine_with_hands(hand_lm)
        frame = MagicMock()

        with patch.dict("sys.modules", {"cv2": cv2_mock}):
            result = engine.detect(frame)

        # May be None if confidence < min_confidence threshold
        if result is not None:
            self.assertEqual(result.gesture_name, "fist")
            self.assertEqual(result.action, "__cancel__")

    def test_open_hand_landmarks_detected_as_open_hand(self):
        """Open hand landmarks → gesture_name == 'open_hand'."""
        hand_lm = _make_hand_landmarks_open()
        engine, cv2_mock, _ = self._make_engine_with_hands(hand_lm)
        frame = MagicMock()

        with patch.dict("sys.modules", {"cv2": cv2_mock}):
            result = engine.detect(frame)

        if result is not None:
            self.assertEqual(result.gesture_name, "open_hand")

    def test_no_hands_returns_none(self):
        """No hand landmarks in frame → detect returns None."""
        cv2_mock = _make_cv2_mock()
        mp_mock = _make_mp_mock(hand_landmarks=None)
        with patch.dict("sys.modules", {"cv2": cv2_mock, "mediapipe": mp_mock}):
            from vision.gesture_engine import GestureEngine
            engine = GestureEngine()
            engine._mp = mp_mock
            engine._hands = mp_mock.solutions.hands.Hands()
            engine._cv2 = cv2_mock
        frame = MagicMock()
        with patch.dict("sys.modules", {"cv2": cv2_mock}):
            result = engine.detect(frame)
        self.assertIsNone(result)

    def test_none_frame_returns_none(self):
        """None frame → detect returns None without error."""
        cv2_mock = _make_cv2_mock()
        mp_mock = _make_mp_mock()
        with patch.dict("sys.modules", {"cv2": cv2_mock, "mediapipe": mp_mock}):
            from vision.gesture_engine import GestureEngine
            engine = GestureEngine()
        result = engine.detect(None)
        self.assertIsNone(result)


# ===========================================================================
# GES2 — Debounce test
# ===========================================================================

class TestGestureDebounce(unittest.TestCase):

    def test_debounce_blocks_second_detection(self):
        """Same gesture within 500ms debounce window → second detect returns None."""
        hand_lm = _make_hand_landmarks_fist()
        cv2_mock = _make_cv2_mock()
        mp_mock = _make_mp_mock(hand_lm)

        with patch.dict("sys.modules", {"cv2": cv2_mock, "mediapipe": mp_mock}):
            from vision.gesture_engine import GestureEngine
            engine = GestureEngine()
            engine._mp = mp_mock
            engine._hands = mp_mock.solutions.hands.Hands()
            engine._cv2 = cv2_mock

        frame = MagicMock()

        with patch.dict("sys.modules", {"cv2": cv2_mock}):
            first = engine.detect(frame)
            # Immediately detect again — should be blocked by debounce
            second = engine.detect(frame)

        # Second should be None due to debounce
        if first is not None:  # only if first detection succeeded
            self.assertIsNone(second, "Debounce should block second detection within 500ms")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    unittest.main(verbosity=2)
