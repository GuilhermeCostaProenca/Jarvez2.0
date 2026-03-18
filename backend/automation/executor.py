from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from actions_core import ActionContext, ActionResult

from .rules import (
    AUTOMATION_STATUS_DRY_RUN_COMPLETE,
    AUTOMATION_STATUS_EXECUTED,
    AUTOMATION_STATUS_EXECUTING,
    AUTOMATION_STATUS_FAILED,
    AUTOMATION_STATUS_IDLE,
    append_bounded,
    build_evidence,
    build_trace_entry,
    ensure_automation_state,
    new_trace_id,
    to_iso,
)
from .scheduler import SchedulerTickResult, collect_daily_briefing_runs
from .triggers import evaluate_arrival_presence_trigger

JsonObject = dict[str, Any]


@dataclass(slots=True)
class AutomationCycleResult:
    automation_state: JsonObject
    run_rows: list[JsonObject]
    trace_rows: list[JsonObject]
    evidence_rows: list[JsonObject]
    scheduler_status: list[JsonObject]
    arrival_status: JsonObject
    message: str
    trace_id: str | None = None


async def execute_automation_cycle(
    *,
    params: JsonObject,
    ctx: ActionContext,
    automation_state: Any,
    research_schedules: Any,
    arrival_prefs: Any,
    now: datetime | None = None,
    run_daily_briefing: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]] | None = None,
    run_arrival_prepare: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]] | None = None,
    allow_arrival_live: Callable[[ActionContext, JsonObject], tuple[bool, JsonObject]] | None = None,
    default_briefing_cooldown_seconds: int = 3_600,
    default_arrival_cooldown_seconds: int = 2_700,
) -> AutomationCycleResult:
    utc_now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    base_state = ensure_automation_state(automation_state, now=utc_now)
    loop = base_state["loop"]
    daily_state = loop["daily_briefing"]
    arrival_state = loop["arrival"]
    cycle_dry_run = bool(params.get("automation_dry_run", params.get("dry_run", True)))

    scheduler_tick: SchedulerTickResult = collect_daily_briefing_runs(
        schedules=research_schedules,
        last_run_by_schedule=daily_state.get("last_run_by_schedule"),
        now=utc_now,
        default_cooldown_seconds=default_briefing_cooldown_seconds,
    )
    arrival_trigger, arrival_status = evaluate_arrival_presence_trigger(
        params=params,
        arrival_prefs=arrival_prefs,
        arrival_state=arrival_state,
        now=utc_now,
        default_cooldown_seconds=default_arrival_cooldown_seconds,
    )

    run_rows: list[JsonObject] = []
    trace_rows: list[JsonObject] = []
    evidence_rows: list[JsonObject] = []

    async def _record_run(
        *,
        automation_type: str,
        source: str,
        stage: str,
        payload: JsonObject,
        action_name: str,
        result: ActionResult,
        dry_run: bool,
        schedule_id: str | None = None,
        policy_decision: str | None = None,
    ) -> None:
        trace_id = new_trace_id("auto")
        run_row: JsonObject = {
            "automation_type": automation_type,
            "source": source,
            "stage": stage,
            "action_name": action_name,
            "success": bool(result.success),
            "message": result.message,
            "error": result.error,
            "dry_run": bool(dry_run),
            "trace_id": trace_id,
            "executed_at": to_iso(utc_now),
            "schedule_id": schedule_id,
            "payload": payload,
        }
        if policy_decision:
            run_row["policy_decision"] = policy_decision
        run_rows.append(run_row)
        evidence = build_evidence(
            automation_type=automation_type,
            source=source,
            dry_run=dry_run,
            success=bool(result.success),
            detail={
                "stage": stage,
                "action_name": action_name,
                "message": result.message,
                "error": result.error,
                "policy_decision": policy_decision,
            },
            now=utc_now,
        )
        evidence_rows.append(evidence)
        trace_rows.append(
            build_trace_entry(
                trace_id=trace_id,
                action_name=f"automation.{automation_type}.{stage}",
                success=bool(result.success),
                message=result.message,
                policy_decision=policy_decision or result.policy_decision,
                now=utc_now,
                metadata={
                    "source": source,
                    "dry_run": dry_run,
                    "schedule_id": schedule_id,
                    "payload": payload,
                },
            )
        )

    for due in scheduler_tick.due_runs:
        schedule_id = str(due.get("schedule_id") or "").strip() or None
        requested_dry_run = bool(due.get("dry_run", False))
        effective_dry_run = cycle_dry_run or requested_dry_run
        query = str(due.get("query") or "").strip()
        if not query:
            continue
        if run_daily_briefing is None:
            await _record_run(
                automation_type="daily_briefing",
                source="scheduler",
                stage="skipped",
                payload=due,
                action_name="web_search_dashboard",
                result=ActionResult(
                    success=False,
                    message="Runner de briefing indisponivel.",
                    error="runner unavailable",
                ),
                dry_run=effective_dry_run,
                schedule_id=schedule_id,
            )
            continue
        result = await run_daily_briefing(
            {
                "query": query,
                "max_results": int(due.get("max_results", 5)),
                "dry_run": effective_dry_run,
            },
            ctx,
        )
        await _record_run(
            automation_type="daily_briefing",
            source="scheduler",
            stage="executed",
            payload=due,
            action_name="web_search_dashboard",
            result=result,
            dry_run=effective_dry_run,
            schedule_id=schedule_id,
        )
        if result.success and schedule_id and not effective_dry_run:
            daily_state["last_run_by_schedule"][schedule_id] = to_iso(utc_now)

    if arrival_trigger is not None:
        arrival_state["last_trigger_at"] = arrival_trigger["triggered_at"]
        if run_arrival_prepare is None:
            await _record_run(
                automation_type="arrival_prepare",
                source="presence_trigger",
                stage="skipped",
                payload=arrival_trigger,
                action_name="ac_prepare_arrival",
                result=ActionResult(
                    success=False,
                    message="Runner de chegada indisponivel.",
                    error="runner unavailable",
                ),
                dry_run=True,
            )
        else:
            dry_result = await run_arrival_prepare(
                {
                    "dry_run": True,
                    "trigger_source": arrival_trigger.get("source"),
                },
                ctx,
            )
            await _record_run(
                automation_type="arrival_prepare",
                source="presence_trigger",
                stage="dry_run",
                payload=arrival_trigger,
                action_name="ac_prepare_arrival",
                result=dry_result,
                dry_run=True,
            )
            policy_details: JsonObject = {
                "decision": "deny",
                "reason": "live execution disabled by policy",
            }
            allow_live = False
            if allow_arrival_live is not None:
                allow_live, policy_details = allow_arrival_live(ctx, arrival_trigger)
            elif bool(params.get("allow_arrival_live", False)):
                allow_live = True
                policy_details = {"decision": "allow", "reason": "manual override via params"}

            if not cycle_dry_run and dry_result.success and allow_live and bool(arrival_trigger.get("run_live_after_dry_run", True)):
                live_result = await run_arrival_prepare(
                    {
                        "dry_run": False,
                        "trigger_source": arrival_trigger.get("source"),
                    },
                    ctx,
                )
                await _record_run(
                    automation_type="arrival_prepare",
                    source="presence_trigger",
                    stage="live",
                    payload=arrival_trigger,
                    action_name="ac_prepare_arrival",
                    result=live_result,
                    dry_run=False,
                    policy_decision=str(policy_details.get("decision") or "allow"),
                )
                if live_result.success:
                    arrival_state["last_live_run_at"] = to_iso(utc_now)
            else:
                await _record_run(
                    automation_type="arrival_prepare",
                    source="presence_trigger",
                    stage="live_skipped",
                    payload=arrival_trigger,
                    action_name="ac_prepare_arrival",
                    result=ActionResult(
                        success=True,
                        message=f"Execucao live nao iniciada: {policy_details.get('reason') or 'policy deny'}.",
                    ),
                    dry_run=True,
                    policy_decision=str(policy_details.get("decision") or "deny"),
                )
        arrival_state["last_presence_state"] = (
            (arrival_trigger.get("presence_transition") or {}).get("to")
            if isinstance(arrival_trigger.get("presence_transition"), dict)
            else None
        )

    for row in scheduler_tick.status_rows:
        daily_state["recent_status"] = append_bounded(
            daily_state["recent_status"],
            row,
            limit=30,
        )
    arrival_state["recent_status"] = append_bounded(
        arrival_state["recent_status"],
        arrival_status,
        limit=30,
    )
    for run in run_rows:
        loop["recent_runs"] = append_bounded(loop["recent_runs"], run, limit=80)
    for trace in trace_rows:
        loop["recent_traces"] = append_bounded(loop["recent_traces"], trace, limit=120)

    all_dry = all(bool(r.get("dry_run")) for r in run_rows) if run_rows else True
    any_failed = any(not bool(r.get("success")) for r in run_rows)
    if not run_rows:
        new_status = AUTOMATION_STATUS_IDLE
    elif any_failed:
        new_status = AUTOMATION_STATUS_FAILED
    elif all_dry:
        new_status = AUTOMATION_STATUS_DRY_RUN_COMPLETE
    else:
        new_status = AUTOMATION_STATUS_EXECUTED
    base_state["status"] = new_status
    base_state["last_cycle_at"] = to_iso(utc_now)
    base_state["last_scheduler_due_at"] = scheduler_tick.next_due_at
    base_state["scheduler_status"] = scheduler_tick.status_rows[:20]
    base_state["arrival_status"] = arrival_status
    base_state["last_evidence"] = evidence_rows[0] if evidence_rows else None
    base_state["updated_at"] = to_iso(utc_now)

    if run_rows:
        message = f"Loop proativo executou {len(run_rows)} etapa(s)."
    else:
        message = "Loop proativo sem acoes pendentes."
    return AutomationCycleResult(
        automation_state=base_state,
        run_rows=run_rows,
        trace_rows=trace_rows,
        evidence_rows=evidence_rows,
        scheduler_status=scheduler_tick.status_rows,
        arrival_status=arrival_status,
        message=message,
        trace_id=trace_rows[0]["traceId"] if trace_rows else None,
    )
