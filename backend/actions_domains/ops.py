from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
import os
import sys
import time
from typing import Any

from actions_core import ActionContext, ActionResult
from automation.executor import execute_automation_cycle

JsonObject = dict[str, Any]


def _actions_module() -> Any | None:
    return sys.modules.get("actions")


def _actions_callable(name: str) -> Any | None:
    module = _actions_module()
    if module is None:
        return None
    return getattr(module, name, None)


async def _run_web_briefing_via_actions(params: JsonObject, ctx: ActionContext) -> ActionResult:
    runner = _actions_callable("_web_search_dashboard")
    if callable(runner):
        return await runner(params, ctx)
    return ActionResult(
        success=False,
        message="Runner de briefing indisponivel.",
        error="web briefing runner unavailable",
    )


async def _run_arrival_prepare_via_actions(params: JsonObject, ctx: ActionContext) -> ActionResult:
    runner = _actions_callable("_ac_prepare_arrival")
    if callable(runner):
        return await runner(params, ctx)
    return ActionResult(
        success=False,
        message="Runner de chegada indisponivel.",
        error="arrival runner unavailable",
    )


def _allow_arrival_live_by_policy(ctx: ActionContext, trigger: JsonObject) -> tuple[bool, JsonObject]:
    try:
        from policy import (
            classify_action_risk,
            evaluate_policy,
            get_domain_trust,
            get_effective_autonomy_mode,
            get_trust_drift,
            is_blocked,
        )
    except Exception:
        return False, {"decision": "deny", "reason": "policy_module_unavailable"}

    domain = "home"
    kill_active, kill_reason = is_blocked(domain=domain)
    trust = get_domain_trust(domain)
    trust_drift = get_trust_drift(ctx.participant_identity, ctx.room, domain)
    policy_eval = evaluate_policy(
        risk=classify_action_risk("ac_prepare_arrival"),
        mode=get_effective_autonomy_mode(ctx.participant_identity, ctx.room, domain=domain),
        requires_confirmation=False,
        kill_switch_active=kill_active,
        kill_switch_reason=kill_reason,
        domain=domain,
        domain_trust_score=trust.score,
        trust_drift_active=bool(trust_drift and trust_drift.active),
        trust_drift_reason=(trust_drift.reason if trust_drift else None),
    )
    decision = str(policy_eval.decision)
    details = {
        "decision": decision,
        "reason": policy_eval.reason,
        "domain": domain,
        "trigger": trigger.get("source"),
    }
    allow_live = decision in {"allow", "allow_with_log", "allow_with_guardrail"}
    return allow_live, details


async def ops_incident_snapshot_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    build_ops_incident_snapshot: Callable[..., JsonObject],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    include_ping = bool(params.get("include_ping", False))
    ping_prompt = str(params.get("ping_prompt", "")).strip() or "Responda apenas: ok"
    metrics_limit = int(params.get("metrics_limit", 300))
    snapshot = build_ops_incident_snapshot(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        include_ping=include_ping,
        ping_prompt=ping_prompt,
        metrics_limit=metrics_limit,
    )
    return ActionResult(
        success=True,
        message="Snapshot operacional gerado.",
        data={
            "ops_incident_snapshot": snapshot,
            "canary_state": snapshot.get("canary_state"),
            "autonomy_mode": snapshot.get("autonomy_mode"),
            "feature_flags": snapshot.get("feature_flags"),
            "kill_switch": snapshot.get("kill_switch"),
            "providers_health": snapshot.get("providers_health"),
            "eval_metrics_summary": snapshot.get("metrics_summary"),
            "slo_report": snapshot.get("slo_report"),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def ops_canary_status_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    build_ops_incident_snapshot: Callable[..., JsonObject],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    metrics_limit = int(params.get("metrics_limit", 300))
    snapshot = build_ops_incident_snapshot(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        include_ping=False,
        ping_prompt="Responda apenas: ok",
        metrics_limit=metrics_limit,
    )
    canary_state = snapshot.get("canary_state") if isinstance(snapshot.get("canary_state"), dict) else {}
    return ActionResult(
        success=True,
        message=(
            f"Canario {'ativo' if bool(canary_state.get('active')) else 'inativo'} "
            f"para a sessao ({str(canary_state.get('cohort') or 'stable')})."
        ),
        data={
            "canary_state": canary_state,
            "ops_incident_snapshot": snapshot,
            "feature_flags": snapshot.get("feature_flags"),
            "eval_metrics_summary": snapshot.get("metrics_summary"),
            "slo_report": snapshot.get("slo_report"),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def ops_canary_set_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    set_canary_session_enrollment: Callable[[str, str, bool], None],
    set_runtime_feature_override: Callable[[str, bool], bool],
    build_ops_incident_snapshot: Callable[..., JsonObject],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    operation = str(params.get("operation", "")).strip().lower()
    allowed = {"enroll", "unenroll", "enable_global", "disable_global"}
    if operation not in allowed:
        return ActionResult(
            success=False,
            message=f"Operacao invalida. Opcoes: {', '.join(sorted(allowed))}.",
            error="invalid operation",
        )

    if operation == "enroll":
        set_canary_session_enrollment(ctx.participant_identity, ctx.room, enrolled=True)
    elif operation == "unenroll":
        set_canary_session_enrollment(ctx.participant_identity, ctx.room, enrolled=False)
    elif operation == "enable_global":
        set_runtime_feature_override("canary_v1", True)
    elif operation == "disable_global":
        set_runtime_feature_override("canary_v1", False)

    snapshot = build_ops_incident_snapshot(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        include_ping=False,
        ping_prompt="Responda apenas: ok",
        metrics_limit=300,
    )
    canary_state = snapshot.get("canary_state") if isinstance(snapshot.get("canary_state"), dict) else {}
    return ActionResult(
        success=True,
        message=f"Canario atualizado via `{operation}`.",
        data={
            "canary_state": canary_state,
            "ops_incident_snapshot": snapshot,
            "feature_flags": snapshot.get("feature_flags"),
            "eval_metrics_summary": snapshot.get("metrics_summary"),
            "slo_report": snapshot.get("slo_report"),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def ops_canary_rollout_set_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    get_canary_rollout_percent: Callable[[], int],
    is_feature_enabled: Callable[[str], bool] | Callable[..., bool],
    rollout_step_percent: Callable[[int, str], int] | Callable[..., int],
    set_canary_rollout_percent: Callable[[int], None],
    set_runtime_feature_override: Callable[[str, bool], bool],
    build_ops_incident_snapshot: Callable[..., JsonObject],
    now_iso: Callable[[], str],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    operation = str(params.get("operation", "")).strip().lower()
    percent_param = params.get("percent")
    dry_run = bool(params.get("dry_run", False))
    allowed = {"set_percent", "step_up", "step_down", "pause", "resume"}
    if operation not in allowed:
        return ActionResult(
            success=False,
            message=f"Operacao invalida. Opcoes: {', '.join(sorted(allowed))}.",
            error="invalid operation",
        )

    current_percent = get_canary_rollout_percent()
    next_percent = current_percent
    before_enabled = is_feature_enabled("canary_v1", default=False)
    next_enabled = before_enabled

    if operation == "set_percent":
        if not isinstance(percent_param, int):
            return ActionResult(success=False, message="Informe `percent` (0..100).", error="missing percent")
        next_percent = max(0, min(100, int(percent_param)))
        if next_percent > 0:
            next_enabled = True
    elif operation == "step_up":
        next_percent = rollout_step_percent(current_percent, direction="up")
        if next_percent > 0:
            next_enabled = True
    elif operation == "step_down":
        next_percent = rollout_step_percent(current_percent, direction="down")
    elif operation == "pause":
        next_enabled = False
    elif operation == "resume":
        next_enabled = True
        if current_percent <= 0:
            next_percent = 10

    if not dry_run:
        set_canary_rollout_percent(next_percent)
        set_runtime_feature_override("canary_v1", next_enabled)

    snapshot = build_ops_incident_snapshot(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        include_ping=False,
        ping_prompt="Responda apenas: ok",
        metrics_limit=300,
    )
    canary_state = snapshot.get("canary_state") if isinstance(snapshot.get("canary_state"), dict) else {}
    report: JsonObject = {
        "playbook": "canary_rollout",
        "dry_run": dry_run,
        "applied": not dry_run,
        "changes": [
            {
                "type": "canary_rollout",
                "target": "rollout_percent",
                "from": current_percent,
                "to": next_percent,
                "note": f"Operacao {operation}",
            },
            {
                "type": "feature_flag_override",
                "target": "canary_v1",
                "from": before_enabled,
                "to": next_enabled if dry_run else bool(is_feature_enabled("canary_v1", default=False)),
                "note": "Controle global de canario.",
            },
        ],
        "generated_at": now_iso(),
    }
    return ActionResult(
        success=True,
        message=f"Rollout canario {'simulado' if dry_run else 'atualizado'} via `{operation}`.",
        data={
            "ops_playbook_report": report,
            "canary_state": canary_state,
            "ops_incident_snapshot": snapshot,
            "feature_flags": snapshot.get("feature_flags"),
            "eval_metrics_summary": snapshot.get("metrics_summary"),
            "slo_report": snapshot.get("slo_report"),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def ops_feature_flags_status_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    feature_flags_snapshot: Callable[[], JsonObject],
    canary_state_payload: Callable[[str, str], JsonObject],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    _ = params
    return ActionResult(
        success=True,
        message="Status das feature flags coletado.",
        data={
            "feature_flags": feature_flags_snapshot(),
            "canary_state": canary_state_payload(ctx.participant_identity, ctx.room),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def ops_feature_flags_set_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    feature_flag_overrides: dict[str, bool],
    feature_flags_snapshot: Callable[[], JsonObject],
    canary_state_payload: Callable[[str, str], JsonObject],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    feature_name = str(params.get("feature", "")).strip().lower()
    if not feature_name:
        return ActionResult(success=False, message="Informe `feature`.", error="missing feature")
    enabled = bool(params.get("enabled", True))
    feature_flag_overrides[feature_name] = enabled
    return ActionResult(
        success=True,
        message=f"Feature `{feature_name}` ajustada para {'on' if enabled else 'off'} (runtime).",
        data={
            "feature_flags": feature_flags_snapshot(),
            "canary_state": canary_state_payload(ctx.participant_identity, ctx.room),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def ops_auto_remediate_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    auto_remediation_last_execution: dict[str, float],
    canary_key: Callable[[str, str], str],
    build_ops_incident_snapshot: Callable[..., JsonObject],
    ops_slo_signal: Callable[[JsonObject], JsonObject],
    ops_rollback_scenario_action: Callable[[JsonObject, ActionContext], Any],
    now_ts: Callable[[], float],
    now_iso: Callable[[], str],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    dry_run = bool(params.get("dry_run", True))
    force = bool(params.get("force", False))
    domain = str(params.get("domain", "")).strip().lower()
    metrics_limit = int(params.get("metrics_limit", 400))
    cooldown_seconds = int(
        params.get("cooldown_seconds", int(str(os.getenv("JARVEZ_AUTO_REMEDIATION_COOLDOWN_SECONDS", "180"))))
    )
    cooldown_seconds = max(30, min(cooldown_seconds, 3600))

    snapshot = build_ops_incident_snapshot(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        include_ping=False,
        ping_prompt="Responda apenas: ok",
        metrics_limit=metrics_limit,
    )
    signal = ops_slo_signal(snapshot)
    scenario = str(signal.get("recommended_scenario") or "").strip()
    signal_domains = signal.get("trust_drift_active_domains") if isinstance(signal.get("trust_drift_active_domains"), list) else []
    notice_delivery_domains = (
        signal.get("autonomy_notice_delivery_domains")
        if isinstance(signal.get("autonomy_notice_delivery_domains"), list)
        else []
    )
    resolved_domain = domain
    if (
        not resolved_domain
        and scenario == "trust_drift_breach"
        and len(signal_domains) == 1
        and isinstance(signal_domains[0], str)
        and signal_domains[0].strip()
    ):
        resolved_domain = str(signal_domains[0]).strip().lower()
    if (
        not resolved_domain
        and scenario == "reliability_breach"
        and bool(signal.get("autonomy_notice_delivery_breach"))
        and len(notice_delivery_domains) == 1
        and isinstance(notice_delivery_domains[0], str)
        and notice_delivery_domains[0].strip()
    ):
        resolved_domain = str(notice_delivery_domains[0]).strip().lower()
    now_value = now_ts()
    room_key = canary_key(ctx.participant_identity, ctx.room)
    last_run = float(auto_remediation_last_execution.get(room_key, 0.0))
    remaining_cooldown = max(0, int(cooldown_seconds - (now_value - last_run)))

    if not scenario and not force:
        return ActionResult(
            success=True,
            message="Sem violacao de SLO para auto-remediacao.",
            data={
                "ops_auto_remediation": {
                    "executed": False,
                    "dry_run": dry_run,
                    "reason": "no signal",
                    "signal": signal,
                    "cooldown_remaining_seconds": remaining_cooldown,
                    "generated_at": now_iso(),
                },
                "ops_incident_snapshot": snapshot,
                "canary_state": snapshot.get("canary_state"),
                "feature_flags": snapshot.get("feature_flags"),
                "kill_switch": snapshot.get("kill_switch"),
                "eval_metrics_summary": snapshot.get("metrics_summary"),
                "slo_report": snapshot.get("slo_report"),
                **capability_payload(ctx.participant_identity, ctx.room),
            },
        )

    if force and not scenario:
        scenario = "reliability_breach"

    if not dry_run and remaining_cooldown > 0:
        return ActionResult(
            success=False,
            message=f"Cooldown ativo para auto-remediacao ({remaining_cooldown}s).",
            data={
                "ops_auto_remediation": {
                    "executed": False,
                    "dry_run": dry_run,
                    "reason": "cooldown",
                    "signal": signal,
                    "cooldown_remaining_seconds": remaining_cooldown,
                    "generated_at": now_iso(),
                },
                "ops_incident_snapshot": snapshot,
                "canary_state": snapshot.get("canary_state"),
                "feature_flags": snapshot.get("feature_flags"),
                "kill_switch": snapshot.get("kill_switch"),
                **capability_payload(ctx.participant_identity, ctx.room),
            },
            error="auto remediation cooldown",
        )

    rollback = await ops_rollback_scenario_action(
        {
            "scenario": scenario,
            "dry_run": dry_run,
            "domain": resolved_domain,
            "containment_strategy": (
                "domain_autonomy"
                if scenario == "reliability_breach"
                and bool(signal.get("autonomy_notice_delivery_breach"))
                and bool(resolved_domain)
                else "default"
            ),
            "reason": "auto remediation",
        },
        ctx,
    )
    if not rollback.success:
        return rollback

    if not dry_run:
        auto_remediation_last_execution[room_key] = now_value

    rollback_data = rollback.data if isinstance(rollback.data, dict) else {}
    return ActionResult(
        success=True,
        message=f"Auto-remediacao {'simulada' if dry_run else 'aplicada'} via `{scenario}`.",
        data={
            **rollback_data,
            "ops_auto_remediation": {
                "executed": True,
                "dry_run": dry_run,
                "scenario": scenario,
                "signal": signal,
                "cooldown_remaining_seconds": 0 if not dry_run else remaining_cooldown,
                "generated_at": now_iso(),
            },
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def ops_canary_promote_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    canary_promotion_last_execution: dict[str, float],
    canary_key: Callable[[str, str], str],
    build_ops_incident_snapshot: Callable[..., JsonObject],
    ops_canary_gate_report: Callable[..., JsonObject],
    ops_canary_rollout_set_action: Callable[[JsonObject, ActionContext], Any],
    ops_rollback_scenario_action: Callable[[JsonObject, ActionContext], Any],
    now_ts: Callable[[], float],
    now_iso: Callable[[], str],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    dry_run = bool(params.get("dry_run", True))
    force = bool(params.get("force", False))
    step_if_passed = bool(params.get("step_if_passed", True))
    rollback_on_fail = bool(params.get("rollback_on_fail", False))
    min_samples = int(params.get("min_samples", 20))
    min_samples = max(5, min(min_samples, 200))
    success_rate_min = float(params.get("success_rate_min", 0.95))
    success_rate_min = max(0.5, min(success_rate_min, 1.0))
    max_regression_vs_stable = float(params.get("max_regression_vs_stable", 0.03))
    max_regression_vs_stable = max(0.0, min(max_regression_vs_stable, 0.4))
    require_no_alerts = bool(params.get("require_no_alerts", True))
    metrics_limit = int(params.get("metrics_limit", 400))
    cooldown_seconds = int(
        params.get("cooldown_seconds", int(str(os.getenv("JARVEZ_CANARY_PROMOTION_COOLDOWN_SECONDS", "600"))))
    )
    cooldown_seconds = max(30, min(cooldown_seconds, 7200))

    snapshot = build_ops_incident_snapshot(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        include_ping=False,
        ping_prompt="Responda apenas: ok",
        metrics_limit=metrics_limit,
    )
    gate = ops_canary_gate_report(
        snapshot=snapshot,
        min_samples=min_samples,
        success_rate_min=success_rate_min,
        max_regression_vs_stable=max_regression_vs_stable,
        require_no_alerts=require_no_alerts,
    )

    now_value = now_ts()
    room_key = canary_key(ctx.participant_identity, ctx.room)
    last_run = float(canary_promotion_last_execution.get(room_key, 0.0))
    remaining_cooldown = max(0, int(cooldown_seconds - (now_value - last_run)))
    if not dry_run and remaining_cooldown > 0 and not force:
        return ActionResult(
            success=False,
            message=f"Cooldown ativo para promocao de canario ({remaining_cooldown}s).",
            data={
                "ops_canary_promotion": {
                    "executed": False,
                    "promoted": False,
                    "dry_run": dry_run,
                    "reason": "cooldown",
                    "gate": gate,
                    "cooldown_remaining_seconds": remaining_cooldown,
                    "generated_at": now_iso(),
                },
                "ops_incident_snapshot": snapshot,
                "canary_state": snapshot.get("canary_state"),
                "feature_flags": snapshot.get("feature_flags"),
                "slo_report": snapshot.get("slo_report"),
                **capability_payload(ctx.participant_identity, ctx.room),
            },
            error="canary promotion cooldown",
        )

    gate_passed = bool(gate.get("passed"))
    if force:
        gate_passed = True

    rollback_result: ActionResult | None = None
    promoted = False
    rollout_result: ActionResult | None = None
    if gate_passed and step_if_passed:
        rollout_result = await ops_canary_rollout_set_action(
            {"operation": "step_up", "dry_run": dry_run},
            ctx,
        )
        promoted = bool(rollout_result.success)
        if rollout_result.success and not dry_run:
            canary_promotion_last_execution[room_key] = now_value
        if rollout_result.success and isinstance(rollout_result.data, dict):
            maybe_snapshot = rollout_result.data.get("ops_incident_snapshot")
            if isinstance(maybe_snapshot, dict):
                snapshot = maybe_snapshot
    elif (not gate_passed) and rollback_on_fail:
        rollback_result = await ops_rollback_scenario_action(
            {
                "scenario": "reliability_breach",
                "dry_run": dry_run,
                "reason": "canary promotion gate failed",
            },
            ctx,
        )
        if rollback_result.success and isinstance(rollback_result.data, dict):
            maybe_snapshot = rollback_result.data.get("ops_incident_snapshot")
            if isinstance(maybe_snapshot, dict):
                snapshot = maybe_snapshot

    report: JsonObject = {
        "executed": True,
        "promoted": promoted,
        "dry_run": dry_run,
        "force": force,
        "step_if_passed": step_if_passed,
        "rollback_on_fail": rollback_on_fail,
        "gate": gate,
        "cooldown_remaining_seconds": 0 if not dry_run else remaining_cooldown,
        "generated_at": now_iso(),
    }
    if rollout_result is not None:
        report["rollout_status"] = {"success": rollout_result.success, "message": rollout_result.message}
    if rollback_result is not None:
        report["rollback_status"] = {"success": rollback_result.success, "message": rollback_result.message}

    return ActionResult(
        success=True,
        message=(
            "Promocao de canario aplicada."
            if promoted and not dry_run
            else "Promocao de canario simulada."
            if promoted and dry_run
            else "Gate de promocao nao aprovado."
        ),
        data={
            "ops_canary_promotion": report,
            "ops_playbook_report": (
                rollout_result.data.get("ops_playbook_report") if rollout_result and isinstance(rollout_result.data, dict) else None
            ) or (
                rollback_result.data.get("ops_playbook_report") if rollback_result and isinstance(rollback_result.data, dict) else None
            ),
            "ops_incident_snapshot": snapshot,
            "canary_state": snapshot.get("canary_state"),
            "feature_flags": snapshot.get("feature_flags"),
            "kill_switch": snapshot.get("kill_switch"),
            "slo_report": snapshot.get("slo_report"),
            "eval_metrics_summary": snapshot.get("metrics_summary"),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def ops_control_loop_tick_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    control_loop_breach_history: dict[str, list[float]],
    control_loop_freeze_last_trigger: dict[str, float],
    canary_key: Callable[[str, str], str],
    build_ops_incident_snapshot: Callable[..., JsonObject],
    ops_slo_signal: Callable[[JsonObject], JsonObject],
    ops_auto_remediate_action: Callable[[JsonObject, ActionContext], Any],
    ops_canary_promote_action: Callable[[JsonObject, ActionContext], Any],
    set_killswitch_global: Callable[..., Any],
    set_runtime_feature_override: Callable[[str, bool], bool],
    set_canary_rollout_percent: Callable[[int], None],
    now_ts: Callable[[], float],
    now_iso: Callable[[], str],
    capability_payload: Callable[[str, str], JsonObject],
    load_event_namespace: Callable[[str, str, str], Any] | None = None,
    load_ac_arrival_prefs: Callable[[], JsonObject] | None = None,
    run_web_briefing: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]] | None = None,
    run_arrival_prepare: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]] | None = None,
    allow_arrival_live: Callable[[ActionContext, JsonObject], tuple[bool, JsonObject]] | None = None,
) -> ActionResult:
    dry_run = bool(params.get("dry_run", True))
    auto_remediate = bool(params.get("auto_remediate", True))
    auto_promote_canary = bool(params.get("auto_promote_canary", True))
    force_remediation = bool(params.get("force_remediation", False))
    force_promotion = bool(params.get("force_promotion", False))
    metrics_limit = int(params.get("metrics_limit", 400))
    domain = str(params.get("domain", "")).strip().lower()
    freeze_threshold = int(
        params.get("freeze_threshold", int(str(os.getenv("JARVEZ_CONTROL_LOOP_FREEZE_THRESHOLD", "3"))))
    )
    freeze_window_seconds = int(
        params.get("freeze_window_seconds", int(str(os.getenv("JARVEZ_CONTROL_LOOP_FREEZE_WINDOW_SECONDS", "900"))))
    )
    freeze_cooldown_seconds = int(
        params.get("freeze_cooldown_seconds", int(str(os.getenv("JARVEZ_CONTROL_LOOP_FREEZE_COOLDOWN_SECONDS", "1800"))))
    )
    freeze_threshold = max(1, min(freeze_threshold, 20))
    freeze_window_seconds = max(60, min(freeze_window_seconds, 86400))
    freeze_cooldown_seconds = max(60, min(freeze_cooldown_seconds, 86400))

    initial_snapshot = build_ops_incident_snapshot(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        include_ping=False,
        ping_prompt="Responda apenas: ok",
        metrics_limit=metrics_limit,
    )
    remediation_result: ActionResult | None = None
    promotion_result: ActionResult | None = None

    if auto_remediate:
        remediation_result = await ops_auto_remediate_action(
            {
                "dry_run": dry_run,
                "force": force_remediation,
                "domain": domain,
                "metrics_limit": metrics_limit,
            },
            ctx,
        )

    room_key = canary_key(ctx.participant_identity, ctx.room)
    now_value = now_ts()
    initial_signal = ops_slo_signal(initial_snapshot)
    current_breach = str(initial_signal.get("recommended_scenario") or "").strip()
    history = [
        stamp
        for stamp in control_loop_breach_history.get(room_key, [])
        if (now_value - float(stamp)) <= float(freeze_window_seconds)
    ]
    if current_breach:
        history.append(now_value)
    control_loop_breach_history[room_key] = history

    last_freeze = float(control_loop_freeze_last_trigger.get(room_key, 0.0))
    freeze_cooldown_remaining = max(0, int(freeze_cooldown_seconds - (now_value - last_freeze)))
    freeze_should_apply = bool(
        len(history) >= freeze_threshold and (freeze_cooldown_remaining == 0)
    )

    remediation_data = remediation_result.data if remediation_result and isinstance(remediation_result.data, dict) else {}
    auto_remediation_payload = remediation_data.get("ops_auto_remediation")
    remediation_triggered = bool(isinstance(auto_remediation_payload, dict) and auto_remediation_payload.get("executed"))
    remediation_scenario = (
        str(auto_remediation_payload.get("scenario") or "")
        if isinstance(auto_remediation_payload, dict)
        else ""
    ).strip()

    skip_promotion_reason = ""
    if auto_promote_canary:
        if remediation_triggered and remediation_scenario in {"provider_outage", "reliability_breach", "latency_spike", "trust_drift_breach"}:
            skip_promotion_reason = f"remediacao ativa em cenario `{remediation_scenario}`."
        else:
            promotion_result = await ops_canary_promote_action(
                {
                    "dry_run": dry_run,
                    "force": force_promotion,
                    "step_if_passed": True,
                    "rollback_on_fail": False,
                    "metrics_limit": metrics_limit,
                },
                ctx,
            )

    final_snapshot = initial_snapshot
    for result in [remediation_result, promotion_result]:
        if result and isinstance(result.data, dict):
            maybe_snapshot = result.data.get("ops_incident_snapshot")
            if isinstance(maybe_snapshot, dict):
                final_snapshot = maybe_snapshot

    freeze_applied = False
    freeze_reason = ""
    if freeze_should_apply:
        freeze_reason = (
            "control_loop_freeze: "
            f"{len(history)} breach(es) em {freeze_window_seconds}s "
            f"(threshold={freeze_threshold})."
        )
        if dry_run:
            freeze_reason = f"{freeze_reason} [dry-run]"
        else:
            set_killswitch_global(True, reason=freeze_reason)
            set_runtime_feature_override("canary_v1", False)
            set_canary_rollout_percent(0)
            control_loop_freeze_last_trigger[room_key] = now_value
            freeze_applied = True
            final_snapshot = build_ops_incident_snapshot(
                participant_identity=ctx.participant_identity,
                room=ctx.room,
                include_ping=False,
                ping_prompt="Responda apenas: ok",
                metrics_limit=metrics_limit,
            )

    automation_cycle = None
    automation_loop_enabled = bool(params.get("enable_automation_loop", True))
    if automation_loop_enabled:
        namespace_loader = load_event_namespace
        if namespace_loader is None:
            maybe_loader = _actions_callable("_load_event_namespace")
            if callable(maybe_loader):
                namespace_loader = maybe_loader
        prefs_loader = load_ac_arrival_prefs
        if prefs_loader is None:
            maybe_prefs_loader = _actions_callable("_load_ac_arrival_prefs")
            if callable(maybe_prefs_loader):
                prefs_loader = maybe_prefs_loader

        current_automation_state = (
            namespace_loader(ctx.participant_identity, ctx.room, "automation_state")
            if callable(namespace_loader)
            else None
        )
        current_research_schedules = (
            namespace_loader(ctx.participant_identity, ctx.room, "research_schedules")
            if callable(namespace_loader)
            else []
        )
        current_arrival_prefs = prefs_loader() if callable(prefs_loader) else {}
        try:
            default_briefing_cooldown_seconds = int(
                str(os.getenv("JARVEZ_AUTOMATION_BRIEFING_COOLDOWN_SECONDS", "3600"))
            )
        except ValueError:
            default_briefing_cooldown_seconds = 3600
        try:
            default_arrival_cooldown_seconds = int(
                str(os.getenv("JARVEZ_AUTOMATION_ARRIVAL_COOLDOWN_SECONDS", "2700"))
            )
        except ValueError:
            default_arrival_cooldown_seconds = 2700

        automation_cycle = await execute_automation_cycle(
            params=params,
            ctx=ctx,
            automation_state=current_automation_state,
            research_schedules=current_research_schedules,
            arrival_prefs=current_arrival_prefs,
            now=datetime.fromtimestamp(now_value, tz=timezone.utc),
            run_daily_briefing=run_web_briefing or _run_web_briefing_via_actions,
            run_arrival_prepare=run_arrival_prepare or _run_arrival_prepare_via_actions,
            allow_arrival_live=allow_arrival_live or _allow_arrival_live_by_policy,
            default_briefing_cooldown_seconds=default_briefing_cooldown_seconds,
            default_arrival_cooldown_seconds=default_arrival_cooldown_seconds,
        )

    control_report: JsonObject = {
        "executed": True,
        "dry_run": dry_run,
        "auto_remediate": auto_remediate,
        "auto_promote_canary": auto_promote_canary,
        "remediation_triggered": remediation_triggered,
        "remediation_scenario": remediation_scenario or None,
        "promotion_skipped_reason": skip_promotion_reason or None,
        "initial_signal": initial_signal,
        "breach_window": {
            "count": len(history),
            "threshold": freeze_threshold,
            "window_seconds": freeze_window_seconds,
        },
        "freeze": {
            "should_apply": freeze_should_apply,
            "applied": freeze_applied,
            "reason": freeze_reason or None,
            "cooldown_remaining_seconds": max(0, freeze_cooldown_remaining),
            "cooldown_seconds": freeze_cooldown_seconds,
        },
        "automation": {
            "enabled": automation_loop_enabled,
            "message": automation_cycle.message if automation_cycle is not None else "automation loop disabled",
            "runs": len(automation_cycle.run_rows) if automation_cycle is not None else 0,
        },
        "generated_at": now_iso(),
    }
    if remediation_result is not None:
        control_report["remediation_status"] = {
            "success": remediation_result.success,
            "message": remediation_result.message,
        }
    if promotion_result is not None:
        control_report["promotion_status"] = {
            "success": promotion_result.success,
            "message": promotion_result.message,
        }

    return ActionResult(
        success=True,
        message="Tick operacional concluido.",
        data={
            "ops_control_tick": control_report,
            "ops_auto_remediation": remediation_data.get("ops_auto_remediation"),
            "ops_canary_promotion": (
                promotion_result.data.get("ops_canary_promotion")
                if promotion_result and isinstance(promotion_result.data, dict)
                else None
            ),
            "ops_playbook_report": (
                promotion_result.data.get("ops_playbook_report")
                if promotion_result and isinstance(promotion_result.data, dict)
                else remediation_data.get("ops_playbook_report")
            ),
            "ops_incident_snapshot": final_snapshot,
            "canary_state": final_snapshot.get("canary_state"),
            "feature_flags": final_snapshot.get("feature_flags"),
            "kill_switch": final_snapshot.get("kill_switch"),
            "slo_report": final_snapshot.get("slo_report"),
            "eval_metrics_summary": final_snapshot.get("metrics_summary"),
            "automation_state": automation_cycle.automation_state if automation_cycle is not None else None,
            "automation_traces": automation_cycle.trace_rows[:10] if automation_cycle is not None else [],
            "automation_evidence": automation_cycle.evidence_rows[:10] if automation_cycle is not None else [],
            **capability_payload(ctx.participant_identity, ctx.room),
        },
        trace_id=automation_cycle.trace_id if automation_cycle is not None else None,
        evidence=(
            automation_cycle.evidence_rows[0]
            if automation_cycle is not None and automation_cycle.evidence_rows
            else None
        ),
    )


async def ops_apply_playbook_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    feature_flags_snapshot: Callable[[], JsonObject],
    get_killswitch_payload: Callable[[], JsonObject],
    get_autonomy_mode: Callable[[str, str], str],
    get_domain_autonomy_mode: Callable[[str, str, str], str | None],
    list_domain_autonomy_modes: Callable[[str, str], list[JsonObject]],
    feature_value_from_env: Callable[[str, bool], bool],
    set_runtime_feature_override: Callable[[str, bool], bool],
    set_autonomy_mode: Callable[[str, str, str], str],
    set_domain_autonomy_mode: Callable[..., Any],
    clear_domain_autonomy_mode: Callable[[str, str, str], Any],
    set_killswitch_domain: Callable[[str, bool, str | None], Any],
    feature_flag_overrides: dict[str, bool],
    predict_feature_values_from_overrides: Callable[[dict[str, bool]], JsonObject],
    now_iso: Callable[[], str],
    build_ops_incident_snapshot: Callable[..., JsonObject],
    build_domain_autonomy_audit_rows: Callable[..., list[JsonObject]],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    playbook = str(params.get("playbook", "")).strip().lower()
    dry_run = bool(params.get("dry_run", False))
    domain = str(params.get("domain", "")).strip().lower()
    reason = str(params.get("reason", "")).strip()
    allowed = {
        "provider_degradation",
        "strict_guardrails",
        "degrade_domain_autonomy",
        "restore_domain_autonomy",
        "block_domain",
        "unblock_domain",
        "restore_runtime_overrides",
    }
    if playbook not in allowed:
        return ActionResult(
            success=False,
            message=f"Playbook invalido. Opcoes: {', '.join(sorted(allowed))}.",
            error="invalid playbook",
        )
    if playbook in {"degrade_domain_autonomy", "restore_domain_autonomy", "block_domain", "unblock_domain"} and not domain:
        return ActionResult(success=False, message="Informe `domain` para este playbook.", error="missing domain")

    before_flags = feature_flags_snapshot()
    before_killswitch = get_killswitch_payload()
    before_mode = get_autonomy_mode(ctx.participant_identity, ctx.room)
    before_domain_mode = get_domain_autonomy_mode(ctx.participant_identity, ctx.room, domain) if domain else None
    predicted_domain_modes: dict[str, str] = {
        str(item.get("domain") or ""): str(item.get("mode") or "")
        for item in list_domain_autonomy_modes(ctx.participant_identity, ctx.room)
        if isinstance(item, dict) and str(item.get("domain") or "")
    }

    predicted_overrides: dict[str, bool] = {
        str(key).strip().lower(): bool(value)
        for key, value in dict(before_flags.get("overrides", {})).items()
    }
    predicted_killswitch = {
        "global_enabled": bool(before_killswitch.get("global_enabled", False)),
        "global_reason": before_killswitch.get("global_reason"),
        "domains": dict(before_killswitch.get("domains", {})),
    }
    predicted_mode = before_mode
    predicted_domain_mode = before_domain_mode
    changes: list[JsonObject] = []

    def _track_override(flag_name: str, enabled: bool, note: str) -> None:
        normalized = flag_name.strip().lower()
        previous_override = predicted_overrides.get(normalized)
        previous_effective = (
            bool(previous_override) if previous_override is not None else feature_value_from_env(normalized, True)
        )
        changes.append(
            {
                "type": "feature_flag_override",
                "target": normalized,
                "from": previous_effective,
                "to": enabled,
                "note": note,
            }
        )
        predicted_overrides[normalized] = enabled
        if not dry_run:
            set_runtime_feature_override(normalized, enabled)

    if playbook == "provider_degradation":
        _track_override("multi_model_router_v1", False, "Desliga roteador multi-model para reduzir variacao.")
        _track_override("subagents_v1", False, "Desliga subagentes para simplificar execucao.")
        _track_override("policy_v1", True, "Mantem politica ativa durante degradacao.")
        _track_override("skills_v1", True, "Mantem skills disponiveis para operacao manual assistida.")
    elif playbook == "strict_guardrails":
        changes.append(
            {
                "type": "autonomy_mode",
                "target": f"{ctx.participant_identity}:{ctx.room}",
                "from": before_mode,
                "to": "safe",
                "note": "Forca guardrails mais conservadores durante incidente.",
            }
        )
        predicted_mode = "safe"
        if not dry_run:
            set_autonomy_mode(ctx.participant_identity, ctx.room, "safe")
        _track_override("policy_v1", True, "Garante engine de politica habilitada.")
    elif playbook == "degrade_domain_autonomy":
        changes.append(
            {
                "type": "domain_autonomy_mode",
                "target": domain,
                "from": before_domain_mode,
                "to": "safe",
                "note": "Reduz autonomia apenas no dominio afetado.",
            }
        )
        predicted_domain_mode = "safe"
        predicted_domain_modes[domain] = "safe"
        if not dry_run:
            set_domain_autonomy_mode(
                ctx.participant_identity,
                ctx.room,
                domain,
                "safe",
                reason=reason or "ops_playbook_degrade_domain_autonomy",
                source="ops_playbook",
            )
    elif playbook == "restore_domain_autonomy":
        changes.append(
            {
                "type": "domain_autonomy_mode",
                "target": domain,
                "from": before_domain_mode,
                "to": None,
                "note": "Remove floor de autonomia por dominio apos estabilizacao.",
            }
        )
        predicted_domain_mode = None
        predicted_domain_modes.pop(domain, None)
        if not dry_run:
            clear_domain_autonomy_mode(ctx.participant_identity, ctx.room, domain)
    elif playbook == "block_domain":
        previous_reason = str(predicted_killswitch["domains"].get(domain, "")) or None
        applied_reason = reason or "blocked by ops playbook"
        changes.append(
            {
                "type": "domain_killswitch",
                "target": domain,
                "from": previous_reason,
                "to": applied_reason,
                "note": "Bloqueia dominio para conter erro em acao real.",
            }
        )
        predicted_killswitch["domains"][domain] = applied_reason
        if not dry_run:
            set_killswitch_domain(domain, True, applied_reason)
    elif playbook == "unblock_domain":
        previous_reason = str(predicted_killswitch["domains"].get(domain, "")) or None
        changes.append(
            {
                "type": "domain_killswitch",
                "target": domain,
                "from": previous_reason,
                "to": None,
                "note": "Reabre dominio bloqueado apos estabilizacao.",
            }
        )
        predicted_killswitch["domains"].pop(domain, None)
        if not dry_run:
            set_killswitch_domain(domain, False, None)
    elif playbook == "restore_runtime_overrides":
        existing = dict(feature_flag_overrides)
        changes.append(
            {
                "type": "feature_flag_override",
                "target": "*",
                "from": len(existing),
                "to": 0,
                "note": "Limpa overrides runtime e volta para estado de env.",
            }
        )
        predicted_overrides = {}
        if not dry_run:
            feature_flag_overrides.clear()

    if dry_run:
        after_flags = {
            "values": predict_feature_values_from_overrides(predicted_overrides),
            "overrides": dict(predicted_overrides),
        }
        after_killswitch = {
            "global_enabled": predicted_killswitch["global_enabled"],
            "global_reason": predicted_killswitch["global_reason"],
            "domains": dict(predicted_killswitch["domains"]),
            "updated_at": now_iso(),
        }
        after_mode = predicted_mode
        after_domain_mode = predicted_domain_mode
        after_domain_modes = [
            {
                "domain": item_domain,
                "mode": item_mode,
                "reason": reason if item_domain == domain and playbook == "degrade_domain_autonomy" else "",
                "source": "ops_playbook" if item_domain == domain and playbook == "degrade_domain_autonomy" else "",
                "updated_at": now_iso() if item_domain == domain and playbook == "degrade_domain_autonomy" else "",
            }
            for item_domain, item_mode in sorted(predicted_domain_modes.items(), key=lambda item: item[0])
        ]
    else:
        after_flags = feature_flags_snapshot()
        after_killswitch = get_killswitch_payload()
        after_mode = get_autonomy_mode(ctx.participant_identity, ctx.room)
        after_domain_mode = get_domain_autonomy_mode(ctx.participant_identity, ctx.room, domain) if domain else None
        after_domain_modes = list_domain_autonomy_modes(ctx.participant_identity, ctx.room)

    report = {
        "playbook": playbook,
        "dry_run": dry_run,
        "applied": not dry_run,
        "changes": changes,
        "before": {
            "feature_flags": before_flags,
            "kill_switch": before_killswitch,
            "autonomy_mode": before_mode,
            "domain_autonomy_mode": before_domain_mode,
            "domain_autonomy_modes": list_domain_autonomy_modes(ctx.participant_identity, ctx.room),
        },
        "after": {
            "feature_flags": after_flags,
            "kill_switch": after_killswitch,
            "autonomy_mode": after_mode,
            "domain_autonomy_mode": after_domain_mode,
            "domain_autonomy_modes": after_domain_modes,
        },
        "generated_at": now_iso(),
    }

    snapshot = build_ops_incident_snapshot(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        include_ping=False,
        ping_prompt="Responda apenas: ok",
        metrics_limit=300,
    )
    snapshot["autonomy_mode"] = after_mode
    snapshot["domain_autonomy_modes"] = after_domain_modes
    snapshot["domain_autonomy_status"] = build_domain_autonomy_audit_rows(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        metrics_summary=snapshot.get("metrics_summary") if isinstance(snapshot.get("metrics_summary"), dict) else None,
        domain_mode_rows_override=after_domain_modes,
        autonomy_mode_override=after_mode,
    )
    snapshot["feature_flags"] = after_flags
    snapshot["kill_switch"] = after_killswitch

    return ActionResult(
        success=True,
        message=f"Playbook `{playbook}` {'simulado' if dry_run else 'aplicado'} com {len(changes)} ajuste(s).",
        data={
            "ops_playbook_report": report,
            "ops_incident_snapshot": snapshot,
            "canary_state": snapshot.get("canary_state"),
            "autonomy_mode": after_mode,
            "domain_autonomy_mode": after_domain_mode,
            "feature_flags": after_flags,
            "kill_switch": after_killswitch,
            "providers_health": snapshot.get("providers_health"),
            "eval_metrics_summary": snapshot.get("metrics_summary"),
            "slo_report": snapshot.get("slo_report"),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def ops_rollback_scenario_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    feature_flags_snapshot: Callable[[], JsonObject],
    get_killswitch_payload: Callable[[], JsonObject],
    get_autonomy_mode: Callable[[str, str], str],
    set_autonomy_mode: Callable[[str, str, str], str],
    get_canary_rollout_percent: Callable[[], int],
    is_feature_enabled: Callable[..., bool],
    set_runtime_feature_override: Callable[[str, bool], bool],
    set_canary_rollout_percent: Callable[[int], None],
    feature_flag_overrides: dict[str, bool],
    list_domain_autonomy_modes: Callable[[str, str], list[JsonObject]],
    ops_apply_playbook_action: Callable[[JsonObject, ActionContext], Any],
    now_iso: Callable[[], str],
    build_ops_incident_snapshot: Callable[..., JsonObject],
    build_domain_autonomy_audit_rows: Callable[..., list[JsonObject]],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    scenario = str(params.get("scenario", "")).strip().lower()
    dry_run = bool(params.get("dry_run", False))
    domain = str(params.get("domain", "")).strip().lower()
    containment_strategy = str(params.get("containment_strategy", "default")).strip().lower() or "default"
    reason = str(params.get("reason", "")).strip()
    allowed = {"provider_outage", "latency_spike", "reliability_breach", "trust_drift_breach", "recover_to_stable"}
    if scenario not in allowed:
        return ActionResult(
            success=False,
            message=f"Cenario invalido. Opcoes: {', '.join(sorted(allowed))}.",
            error="invalid scenario",
        )

    steps: list[JsonObject] = []
    if scenario == "provider_outage":
        steps = [{"playbook": "provider_degradation"}, {"playbook": "strict_guardrails"}]
        if domain:
            steps.append({"playbook": "block_domain", "domain": domain, "reason": reason or "provider outage containment"})
    elif scenario == "latency_spike":
        steps = [{"playbook": "provider_degradation"}]
    elif scenario == "reliability_breach":
        steps = [{"playbook": "strict_guardrails"}]
        if domain:
            if containment_strategy == "domain_autonomy":
                steps.append(
                    {
                        "playbook": "degrade_domain_autonomy",
                        "domain": domain,
                        "reason": reason or "reliability containment via domain autonomy",
                    }
                )
            else:
                steps.append({"playbook": "block_domain", "domain": domain, "reason": reason or "reliability containment"})
    elif scenario == "trust_drift_breach":
        steps = [{"playbook": "strict_guardrails"}]
        if domain:
            steps.append({"playbook": "block_domain", "domain": domain, "reason": reason or "trust drift containment"})
    elif scenario == "recover_to_stable":
        steps = [{"playbook": "restore_runtime_overrides"}]
        if domain:
            steps.append({"playbook": "unblock_domain", "domain": domain})
            steps.append({"playbook": "restore_domain_autonomy", "domain": domain})

    before_flags = feature_flags_snapshot()
    before_killswitch = get_killswitch_payload()
    before_mode = get_autonomy_mode(ctx.participant_identity, ctx.room)
    before_rollout = get_canary_rollout_percent()
    before_canary_enabled = is_feature_enabled("canary_v1", default=False)
    step_reports: list[JsonObject] = []

    for step in steps:
        playbook_params: JsonObject = {"playbook": step.get("playbook"), "dry_run": dry_run}
        if isinstance(step.get("domain"), str) and step.get("domain"):
            playbook_params["domain"] = step.get("domain")
        if isinstance(step.get("reason"), str) and step.get("reason"):
            playbook_params["reason"] = step.get("reason")
        step_result = await ops_apply_playbook_action(playbook_params, ctx)
        if not step_result.success:
            return step_result
        if isinstance(step_result.data, dict) and isinstance(step_result.data.get("ops_playbook_report"), dict):
            step_reports.append(dict(step_result.data["ops_playbook_report"]))

    mode_change: JsonObject | None = None
    if scenario == "recover_to_stable":
        if dry_run:
            mode_change = {
                "type": "autonomy_mode",
                "target": f"{ctx.participant_identity}:{ctx.room}",
                "from": before_mode,
                "to": "aggressive",
                "note": "Dry-run: retornaria autonomia para agressivo apos recuperacao.",
            }
        else:
            after_set = set_autonomy_mode(ctx.participant_identity, ctx.room, "aggressive")
            mode_change = {
                "type": "autonomy_mode",
                "target": f"{ctx.participant_identity}:{ctx.room}",
                "from": before_mode,
                "to": after_set,
                "note": "Retorno para perfil padrao apos rollback.",
            }
    if mode_change is not None:
        step_reports.append({"playbook": "autonomy_mode_adjustment", "changes": [mode_change], "dry_run": dry_run})

    canary_changes: list[JsonObject] = []
    if scenario in {"provider_outage", "latency_spike", "reliability_breach", "trust_drift_breach"}:
        canary_changes.append(
            {
                "type": "feature_flag_override",
                "target": "canary_v1",
                "from": before_canary_enabled,
                "to": False,
                "note": "Congela canario durante rollback de incidente.",
            }
        )
        canary_changes.append(
            {
                "type": "canary_rollout",
                "target": "rollout_percent",
                "from": before_rollout,
                "to": 0,
                "note": "Zera rollout para evitar expandir regressao.",
            }
        )
        if not dry_run:
            set_runtime_feature_override("canary_v1", False)
            set_canary_rollout_percent(0)
    elif scenario == "recover_to_stable":
        canary_changes.append(
            {
                "type": "feature_flag_override",
                "target": "canary_v1",
                "from": before_canary_enabled,
                "to": None,
                "note": "Remove override manual de canario e volta para o default configurado.",
            }
        )
        canary_changes.append(
            {
                "type": "canary_rollout",
                "target": "rollout_percent",
                "from": before_rollout,
                "to": 10,
                "note": "Retoma rollout em 10% apos recuperacao.",
            }
        )
        if not dry_run:
            feature_flag_overrides.pop("canary_v1", None)
            set_canary_rollout_percent(10)
    if canary_changes:
        step_reports.append({"playbook": "canary_control", "changes": canary_changes, "dry_run": dry_run})

    after_flags = feature_flags_snapshot()
    after_killswitch = get_killswitch_payload()
    after_mode = get_autonomy_mode(ctx.participant_identity, ctx.room)
    after_domain_modes = list_domain_autonomy_modes(ctx.participant_identity, ctx.room)
    if dry_run:
        mode_rank = {"aggressive": 0, "safe": 1, "manual": 2}
        for step_report in step_reports:
            after_payload = step_report.get("after") if isinstance(step_report, dict) else None
            if not isinstance(after_payload, dict):
                continue
            if isinstance(after_payload.get("autonomy_mode"), str) and after_payload.get("autonomy_mode"):
                candidate_mode = str(after_payload.get("autonomy_mode"))
                if mode_rank.get(candidate_mode, 0) >= mode_rank.get(after_mode, 0):
                    after_mode = candidate_mode
            if isinstance(after_payload.get("domain_autonomy_modes"), list):
                after_domain_modes = [
                    item
                    for item in after_payload.get("domain_autonomy_modes", [])
                    if isinstance(item, dict)
                ]

    scenario_report: JsonObject = {
        "playbook": f"rollback_scenario:{scenario}",
        "dry_run": dry_run,
        "applied": not dry_run,
        "steps_executed": [str(step.get("playbook") or "") for step in steps],
        "step_reports": step_reports,
        "before": {
            "feature_flags": before_flags,
            "kill_switch": before_killswitch,
            "autonomy_mode": before_mode,
        },
        "after": {
            "feature_flags": after_flags,
            "kill_switch": after_killswitch,
            "autonomy_mode": after_mode,
            "domain_autonomy_modes": after_domain_modes,
        },
        "notes": (
            ["Dry-run em multiplos passos e nao transacional; revisar `step_reports` antes de aplicar."]
            if dry_run and len(steps) > 1
            else []
        ),
        "generated_at": now_iso(),
    }

    snapshot = build_ops_incident_snapshot(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        include_ping=False,
        ping_prompt="Responda apenas: ok",
        metrics_limit=300,
    )
    snapshot["autonomy_mode"] = after_mode
    snapshot["domain_autonomy_modes"] = after_domain_modes
    snapshot["domain_autonomy_status"] = build_domain_autonomy_audit_rows(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        metrics_summary=snapshot.get("metrics_summary") if isinstance(snapshot.get("metrics_summary"), dict) else None,
        domain_mode_rows_override=after_domain_modes,
        autonomy_mode_override=after_mode,
    )

    return ActionResult(
        success=True,
        message=f"Rollback de cenario `{scenario}` {'simulado' if dry_run else 'aplicado'} com {len(steps)} passo(s).",
        data={
            "ops_playbook_report": scenario_report,
            "ops_incident_snapshot": snapshot,
            "canary_state": snapshot.get("canary_state"),
            "feature_flags": snapshot.get("feature_flags"),
            "kill_switch": snapshot.get("kill_switch"),
            "autonomy_mode": snapshot.get("autonomy_mode"),
            "domain_autonomy_modes": snapshot.get("domain_autonomy_modes"),
            "providers_health": snapshot.get("providers_health"),
            "eval_metrics_summary": snapshot.get("metrics_summary"),
            "slo_report": snapshot.get("slo_report"),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )
