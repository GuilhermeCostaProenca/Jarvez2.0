"""
Tests for CTX frente — context events and context rules engine.
Run: python test_vision_ctx.py
"""
from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path
from datetime import datetime, timezone


# ===========================================================================
# CTX1 — VisualEvent contract tests
# ===========================================================================

class TestVisualEvent(unittest.TestCase):

    def _make_event(self, event_type: str = "presence_detected", confidence: float = 0.9):
        from vision.context_events import VisualEvent
        return VisualEvent(
            event_type=event_type,
            source="camera_pipeline",
            confidence=confidence,
            identity="guilherme",
            metadata={"motion_area": 1500.0},
        )

    def test_to_presence_event_presence_detected(self):
        """presence_detected → to_presence_event produces home new_state."""
        evt = self._make_event("presence_detected")
        pe = evt.to_presence_event("camera_entity_1")
        self.assertEqual(pe["entity_id"], "camera_entity_1")
        self.assertEqual(pe["new_state"], "home")
        self.assertEqual(pe["source"], "camera_pipeline")
        self.assertIn("changed_at", pe)

    def test_to_presence_event_left_room(self):
        """left_room → to_presence_event produces not_home new_state."""
        evt = self._make_event("left_room")
        pe = evt.to_presence_event("camera_entity_1")
        self.assertEqual(pe["new_state"], "not_home")

    def test_to_automation_params_has_presence_event(self):
        """to_automation_params includes presence_event key for executor."""
        evt = self._make_event("presence_detected")
        params = evt.to_automation_params()
        self.assertIn("presence_event", params)
        self.assertIn("visual_event_type", params)
        self.assertEqual(params["visual_event_type"], "presence_detected")
        self.assertEqual(params["visual_identity"], "guilherme")

    def test_to_automation_params_confidence_forwarded(self):
        """Confidence is forwarded in automation params."""
        evt = self._make_event("got_up", confidence=0.75)
        params = evt.to_automation_params()
        self.assertAlmostEqual(params["visual_confidence"], 0.75)


# ===========================================================================
# CTX2 — ContextRulesEngine evaluation tests
# ===========================================================================

class TestContextRulesEngine(unittest.TestCase):

    def _make_engine(self):
        from vision.context_rules import ContextRulesEngine
        return ContextRulesEngine()

    def _make_event(self, event_type: str, confidence: float = 0.9):
        from vision.context_events import VisualEvent
        return VisualEvent(
            event_type=event_type,
            source="camera_pipeline",
            confidence=confidence,
        )

    def test_got_up_high_confidence_fires_light_on(self):
        """got_up with high confidence → light_on_got_up rule fires."""
        engine = self._make_engine()
        evt = self._make_event("got_up", confidence=0.85)
        matches = engine.evaluate(evt)
        rule_ids = [m.rule_id for m in matches]
        self.assertIn("light_on_got_up", rule_ids)
        light_match = next(m for m in matches if m.rule_id == "light_on_got_up")
        self.assertTrue(light_match.should_execute)
        self.assertEqual(light_match.action, "turn_light_on")

    def test_got_up_low_confidence_does_not_fire(self):
        """got_up with confidence below min → rule does not execute."""
        engine = self._make_engine()
        evt = self._make_event("got_up", confidence=0.3)
        matches = engine.evaluate(evt)
        for m in matches:
            if m.rule_id == "light_on_got_up":
                self.assertFalse(m.should_execute)

    def test_cooldown_prevents_second_fire(self):
        """Same event within cooldown period → second call should_execute=False."""
        engine = self._make_engine()
        evt = self._make_event("got_up", confidence=0.9)

        first_matches = engine.evaluate(evt)
        first_exec = [m for m in first_matches if m.rule_id == "light_on_got_up" and m.should_execute]
        self.assertEqual(len(first_exec), 1)

        # Second evaluation immediately after
        second_matches = engine.evaluate(evt)
        second_exec = [m for m in second_matches if m.rule_id == "light_on_got_up" and m.should_execute]
        self.assertEqual(len(second_exec), 0, "Should be blocked by cooldown")

    def test_no_match_for_unrelated_event_type(self):
        """Event type not in rules → no matches returned."""
        engine = self._make_engine()
        evt = self._make_event("some_unknown_event", confidence=1.0)
        matches = engine.evaluate(evt)
        self.assertEqual(len(matches), 0)

    def test_lay_down_fires_light_off(self):
        """lay_down event → light_off_lay_down rule fires."""
        engine = self._make_engine()
        evt = self._make_event("lay_down", confidence=0.8)
        matches = engine.evaluate(evt)
        exec_matches = [m for m in matches if m.should_execute]
        self.assertTrue(any(m.rule_id == "light_off_lay_down" for m in exec_matches))


# ===========================================================================
# CTX5 — suggest_new_rules tests
# ===========================================================================

class TestContextRulesSuggestions(unittest.TestCase):

    def test_suggest_got_up_pattern(self):
        """Repeated got_up events at same hour → suggestion returned."""
        from vision.context_rules import ContextRulesEngine
        engine = ContextRulesEngine()

        # Simulate 5 got_up events at hour 7
        recent_events = [
            {"event_type": "got_up", "hour_of_day": 7, "day_of_week": 1}
            for _ in range(5)
        ]
        suggestions = engine.suggest_new_rules(recent_events)
        self.assertTrue(len(suggestions) > 0)
        self.assertTrue(any("acord" in s.lower() or "levantar" in s.lower() or "levan" in s.lower() for s in suggestions))

    def test_no_suggestion_for_sparse_data(self):
        """Only 1 event → not enough data to suggest anything."""
        from vision.context_rules import ContextRulesEngine
        engine = ContextRulesEngine()

        recent_events = [{"event_type": "got_up", "hour_of_day": 8, "day_of_week": 0}]
        suggestions = engine.suggest_new_rules(recent_events)
        self.assertEqual(len(suggestions), 0)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    unittest.main(verbosity=2)
