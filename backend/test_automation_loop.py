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


class AutomationStatusConstantsTests(unittest.TestCase):
    def test_status_constants_exported(self) -> None:
        from automation.rules import (
            AUTOMATION_STATUS_DRY_RUN_COMPLETE,
            AUTOMATION_STATUS_EXECUTED,
            AUTOMATION_STATUS_EXECUTING,
            AUTOMATION_STATUS_FAILED,
            AUTOMATION_STATUS_IDLE,
        )
        self.assertEqual(AUTOMATION_STATUS_IDLE, "idle")
        self.assertEqual(AUTOMATION_STATUS_EXECUTING, "executing")
        self.assertEqual(AUTOMATION_STATUS_DRY_RUN_COMPLETE, "dry_run_complete")
        self.assertEqual(AUTOMATION_STATUS_EXECUTED, "executed")
        self.assertEqual(AUTOMATION_STATUS_FAILED, "failed")

    def test_status_constants_reexported_from_executor(self) -> None:
        from automation.executor import (
            AUTOMATION_STATUS_DRY_RUN_COMPLETE,
            AUTOMATION_STATUS_EXECUTED,
            AUTOMATION_STATUS_EXECUTING,
            AUTOMATION_STATUS_FAILED,
            AUTOMATION_STATUS_IDLE,
        )
        self.assertEqual(AUTOMATION_STATUS_IDLE, "idle")
        self.assertEqual(AUTOMATION_STATUS_EXECUTING, "executing")


class AutomationRunNowBridgeTests(unittest.IsolatedAsyncioTestCase):
    async def test_automation_run_now_dry_run_calls_executor_and_returns_run_rows(self) -> None:
        """F2.3-A: automation_run_now with dry_run=True calls executor and returns run_rows."""
        now = datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc)
        ctx = ActionContext(job_id="j10", room="room", participant_identity="user")
        briefings: list[str] = []

        async def _run_briefing(params, _ctx):
            briefings.append(str(params.get("query")))
            return ActionResult(success=True, message="briefing ok", data={"web_dashboard": {}})

        cycle = await execute_automation_cycle(
            params={"automation_dry_run": True, "dry_run": True},
            ctx=ctx,
            automation_state=None,
            research_schedules=[
                {
                    "id": "research-x",
                    "query": "tech news",
                    "time_of_day": "08:00",
                    "timezone": "UTC",
                    "enabled": True,
                }
            ],
            arrival_prefs={},
            now=now,
            run_daily_briefing=_run_briefing,
        )
        # dry_run=True means the scheduler still runs, but schedule-level dry_run flag is True
        # The executor runs the briefing with dry_run=True
        self.assertEqual(len(briefings), 1)
        self.assertGreater(len(cycle.run_rows), 0)
        # All runs are dry so status should be dry_run_complete
        self.assertEqual(cycle.automation_state["status"], "dry_run_complete")

    async def test_automation_run_now_live_sets_executed_status(self) -> None:
        """F2.3-A: automation_run_now with dry_run=False and live run sets status=executed."""
        now = datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc)
        ctx = ActionContext(job_id="j11", room="room", participant_identity="user")

        async def _run_briefing(params, _ctx):
            return ActionResult(success=True, message="briefing ok", data={"web_dashboard": {}})

        cycle = await execute_automation_cycle(
            params={"automation_dry_run": False, "dry_run": False},
            ctx=ctx,
            automation_state=None,
            research_schedules=[
                {
                    "id": "research-live",
                    "query": "markets",
                    "time_of_day": "08:00",
                    "timezone": "UTC",
                    "enabled": True,
                    "dry_run": False,
                }
            ],
            arrival_prefs={},
            now=now,
            run_daily_briefing=_run_briefing,
        )
        self.assertEqual(cycle.automation_state["status"], "executed")


class SchedulerNextDueAtTests(unittest.TestCase):
    def test_scheduler_tick_returns_next_due_at(self) -> None:
        """F2.3-D: scheduler tick returns next_due_at."""
        now = datetime(2026, 3, 9, 6, 0, tzinfo=timezone.utc)
        result = collect_daily_briefing_runs(
            schedules=[
                {
                    "id": "sched-1",
                    "query": "news",
                    "time_of_day": "08:00",
                    "timezone": "UTC",
                    "enabled": True,
                    "cooldown_seconds": 300,
                }
            ],
            last_run_by_schedule={},
            now=now,
        )
        self.assertIsNotNone(result.next_due_at)
        # Schedule is at 08:00, now is 06:00 → not due yet → next_due_at should be today 08:00
        self.assertIn("2026-03-09", result.next_due_at or "")

    def test_cooldown_blocks_reexecution_within_window(self) -> None:
        """F2.3-D: cooldown blocks reexecution within the window."""
        now = datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc)
        last_run = (now - timedelta(seconds=60)).isoformat()
        result = collect_daily_briefing_runs(
            schedules=[
                {
                    "id": "sched-2",
                    "query": "finance",
                    "time_of_day": "08:00",
                    "timezone": "UTC",
                    "enabled": True,
                    "cooldown_seconds": 3600,
                }
            ],
            last_run_by_schedule={"sched-2": last_run},
            now=now,
        )
        self.assertEqual(len(result.due_runs), 0)
        self.assertEqual(result.status_rows[0]["status"], "cooldown")
        cooldown_remaining = result.status_rows[0].get("cooldown_remaining_seconds", 0)
        self.assertGreater(cooldown_remaining, 0)


def _async_result(value):
    async def _runner(*_args, **_kwargs):
        return value

    return _runner()


if __name__ == "__main__":
    unittest.main()
