from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from actions_core import ActionContext, ActionResult
from actions_domains.ops import ops_control_loop_tick_action
from automation.executor import execute_automation_cycle
from automation.scheduler import collect_daily_briefing_runs
from automation.triggers import evaluate_arrival_presence_trigger


class AutomationSchedulerTests(unittest.TestCase):
    def test_collect_daily_briefing_runs_marks_due(self) -> None:
        now = datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc)
        result = collect_daily_briefing_runs(
            schedules=[
                {
                    "id": "research-1",
                    "query": "ai news",
                    "time_of_day": "08:00",
                    "timezone": "UTC",
                    "enabled": True,
                    "cooldown_seconds": 300,
                }
            ],
            last_run_by_schedule={},
            now=now,
        )
        self.assertEqual(len(result.due_runs), 1)
        self.assertEqual(result.due_runs[0]["schedule_id"], "research-1")
        self.assertEqual(result.status_rows[0]["status"], "due")

    def test_collect_daily_briefing_runs_respects_cooldown(self) -> None:
        now = datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc)
        last_run = (now - timedelta(seconds=120)).isoformat()
        result = collect_daily_briefing_runs(
            schedules=[
                {
                    "id": "research-1",
                    "query": "ai news",
                    "time_of_day": "08:00",
                    "timezone": "UTC",
                    "enabled": True,
                    "cooldown_seconds": 600,
                }
            ],
            last_run_by_schedule={"research-1": last_run},
            now=now,
        )
        self.assertEqual(len(result.due_runs), 0)
        self.assertEqual(result.status_rows[0]["status"], "cooldown")


class AutomationTriggerTests(unittest.TestCase):
    def test_arrival_trigger_detects_home_transition(self) -> None:
        now = datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc)
        trigger, status = evaluate_arrival_presence_trigger(
            params={
                "presence_event": {
                    "entity_id": "person.jarvez",
                    "old_state": "not_home",
                    "new_state": "home",
                },
                "automation_dry_run": False,
            },
            arrival_prefs={
                "presence_entity_id": "person.jarvez",
                "automation_enabled": True,
                "cooldown_seconds": 600,
            },
            arrival_state={},
            now=now,
        )
        self.assertIsNotNone(trigger)
        assert trigger is not None
        self.assertEqual(trigger["automation_type"], "arrival_prepare")
        self.assertEqual(status["status"], "triggered")

    def test_arrival_trigger_respects_cooldown(self) -> None:
        now = datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc)
        trigger, status = evaluate_arrival_presence_trigger(
            params={
                "presence_event": {
                    "entity_id": "person.jarvez",
                    "old_state": "not_home",
                    "new_state": "home",
                }
            },
            arrival_prefs={
                "presence_entity_id": "person.jarvez",
                "automation_enabled": True,
                "cooldown_seconds": 600,
            },
            arrival_state={"last_trigger_at": (now - timedelta(seconds=100)).isoformat()},
            now=now,
        )
        self.assertIsNone(trigger)
        self.assertEqual(status["status"], "cooldown")


class AutomationExecutorTests(unittest.IsolatedAsyncioTestCase):
    async def test_execute_automation_cycle_runs_scheduler_and_arrival_live(self) -> None:
        now = datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc)
        ctx = ActionContext(job_id="j1", room="room", participant_identity="user")
        arrivals: list[bool] = []
        briefings: list[str] = []

        async def _run_briefing(params, _ctx):
            briefings.append(str(params.get("query")))
            return ActionResult(success=True, message="briefing ok", data={"web_dashboard": {}})

        async def _run_arrival(params, _ctx):
            arrivals.append(bool(params.get("dry_run")))
            return ActionResult(success=True, message="arrival ok")

        cycle = await execute_automation_cycle(
            params={
                "automation_dry_run": False,
                "presence_event": {
                    "entity_id": "person.jarvez",
                    "old_state": "not_home",
                    "new_state": "home",
                },
            },
            ctx=ctx,
            automation_state=None,
            research_schedules=[
                {
                    "id": "research-1",
                    "query": "ai",
                    "time_of_day": "08:00",
                    "timezone": "UTC",
                    "enabled": True,
                }
            ],
            arrival_prefs={
                "presence_entity_id": "person.jarvez",
                "automation_enabled": True,
                "cooldown_seconds": 600,
                "run_live_after_dry_run": True,
            },
            now=now,
            run_daily_briefing=_run_briefing,
            run_arrival_prepare=_run_arrival,
            allow_arrival_live=lambda _ctx, _trigger: (True, {"decision": "allow", "reason": "policy pass"}),
        )
        self.assertEqual(len(briefings), 1)
        self.assertEqual(arrivals, [True, False])
        self.assertGreaterEqual(len(cycle.trace_rows), 3)
        self.assertEqual(cycle.automation_state["status"], "executed")
        self.assertIn("research-1", cycle.automation_state["loop"]["daily_briefing"]["last_run_by_schedule"])

    async def test_execute_automation_cycle_respects_global_dry_run(self) -> None:
        now = datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc)
        ctx = ActionContext(job_id="j2", room="room", participant_identity="user")
        arrivals: list[bool] = []

        async def _run_arrival(params, _ctx):
            arrivals.append(bool(params.get("dry_run")))
            return ActionResult(success=True, message="arrival ok")

        cycle = await execute_automation_cycle(
            params={
                "automation_dry_run": True,
                "presence_event": {
                    "entity_id": "person.jarvez",
                    "old_state": "not_home",
                    "new_state": "home",
                },
            },
            ctx=ctx,
            automation_state=None,
            research_schedules=[
                {
                    "id": "research-1",
                    "query": "ai",
                    "time_of_day": "08:00",
                    "timezone": "UTC",
                    "enabled": True,
                }
            ],
            arrival_prefs={
                "presence_entity_id": "person.jarvez",
                "automation_enabled": True,
                "cooldown_seconds": 600,
                "run_live_after_dry_run": True,
            },
            now=now,
            run_arrival_prepare=_run_arrival,
            allow_arrival_live=lambda _ctx, _trigger: (True, {"decision": "allow", "reason": "policy pass"}),
        )
        self.assertEqual(arrivals, [True])
        stages = [row.get("stage") for row in cycle.run_rows]
        self.assertIn("live_skipped", stages)
        self.assertNotIn("live", stages)
        self.assertNotIn("research-1", cycle.automation_state["loop"]["daily_briefing"]["last_run_by_schedule"])


class OpsAutomationIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_ops_control_loop_tick_emits_automation_state(self) -> None:
        ctx = ActionContext(job_id="j3", room="room", participant_identity="user")
        now_value = 1_800_000_000.0
        run_calls: list[str] = []

        async def _run_briefing(params, _ctx):
            run_calls.append(f"briefing:{params.get('query')}")
            return ActionResult(success=True, message="briefing ok")

        async def _run_arrival(params, _ctx):
            run_calls.append(f"arrival:{'dry' if params.get('dry_run') else 'live'}")
            return ActionResult(success=True, message="arrival ok")

        result = await ops_control_loop_tick_action(
            {
                "auto_remediate": False,
                "auto_promote_canary": False,
                "dry_run": False,
                "automation_dry_run": False,
                "presence_event": {
                    "entity_id": "person.jarvez",
                    "old_state": "not_home",
                    "new_state": "home",
                },
            },
            ctx,
            control_loop_breach_history={},
            control_loop_freeze_last_trigger={},
            canary_key=lambda _pid, _room: "k",
            build_ops_incident_snapshot=lambda **_kwargs: {
                "canary_state": {"active": False},
                "feature_flags": {},
                "kill_switch": {"global": False},
                "slo_report": {},
                "metrics_summary": {},
            },
            ops_slo_signal=lambda _snapshot: {"recommended_scenario": ""},
            ops_auto_remediate_action=lambda _params, _ctx: _async_result(ActionResult(success=True, message="ok")),
            ops_canary_promote_action=lambda _params, _ctx: _async_result(ActionResult(success=True, message="ok")),
            set_killswitch_global=lambda _enabled, reason=None: None,
            set_runtime_feature_override=lambda _flag, _enabled: True,
            set_canary_rollout_percent=lambda _value: None,
            now_ts=lambda: now_value,
            now_iso=lambda: "2026-03-09T00:00:00Z",
            capability_payload=lambda _pid, _room: {"capability_mode": "default"},
            load_event_namespace=lambda _pid, _room, namespace: (
                [
                    {
                        "id": "research-1",
                        "query": "ai",
                        "time_of_day": "08:00",
                        "timezone": "UTC",
                        "enabled": True,
                    }
                ]
                if namespace == "research_schedules"
                else {}
            ),
            load_ac_arrival_prefs=lambda: {
                "presence_entity_id": "person.jarvez",
                "automation_enabled": True,
                "cooldown_seconds": 600,
                "run_live_after_dry_run": True,
            },
            run_web_briefing=_run_briefing,
            run_arrival_prepare=_run_arrival,
            allow_arrival_live=lambda _ctx, _trigger: (True, {"decision": "allow", "reason": "policy pass"}),
        )
        self.assertTrue(result.success)
        self.assertIn("automation_state", result.data)
        self.assertGreaterEqual(len(result.data["automation_traces"]), 1)
        self.assertIn("briefing:ai", run_calls)
        self.assertIn("arrival:dry", run_calls)
        self.assertIn("arrival:live", run_calls)


def _async_result(value):
    async def _runner(*_args, **_kwargs):
        return value

    return _runner()


if __name__ == "__main__":
    unittest.main()
