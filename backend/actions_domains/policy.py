from __future__ import annotations

from collections.abc import Callable
from typing import Any

from actions_core import ActionContext, ActionResult

JsonObject = dict[str, Any]


async def policy_explain_decision_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    require_feature: Callable[[str], ActionResult | None],
    get_action: Callable[[str], Any | None],
    classify_action_risk: Callable[[str], str],
    infer_action_domain: Callable[[str], str],
    get_domain_trust: Callable[[str], Any],
    get_trust_drift: Callable[[str, str, str], Any | None],
    get_autonomy_mode: Callable[[str, str], str],
    get_domain_autonomy_details: Callable[[str, str, str], JsonObject | None],
    get_domain_autonomy_mode: Callable[[str, str, str], str | None],
    get_effective_autonomy_mode: Callable[..., str],
    is_blocked: Callable[..., tuple[bool, str | None]],
    action_domain: Callable[[str], str],
    evaluate_policy: Callable[..., Any],
    get_killswitch_status: Callable[[], Any],
) -> ActionResult:
    feature_error = require_feature("policy_v1")
    if feature_error is not None:
        return feature_error
    action_name = str(params.get("action_name", "")).strip()
    if not action_name:
        return ActionResult(success=False, message="Informe o nome da action para analisar politica.", error="missing action name")
    spec = get_action(action_name)
    risk = classify_action_risk(action_name)
    domain = infer_action_domain(action_name)
    domain_trust = get_domain_trust(domain)
    trust_drift = get_trust_drift(ctx.participant_identity, ctx.room, domain)
    mode = get_autonomy_mode(ctx.participant_identity, ctx.room)
    domain_details = get_domain_autonomy_details(ctx.participant_identity, ctx.room, domain) or {}
    domain_mode = get_domain_autonomy_mode(ctx.participant_identity, ctx.room, domain)
    effective_mode = get_effective_autonomy_mode(ctx.participant_identity, ctx.room, domain=domain)
    blocked, reason = is_blocked(domain=action_domain(action_name))
    policy_eval = evaluate_policy(
        risk=risk,
        mode=effective_mode,
        requires_confirmation=bool(spec.requires_confirmation) if spec is not None else False,
        kill_switch_active=blocked,
        kill_switch_reason=reason,
        domain=domain,
        domain_trust_score=domain_trust.score,
        trust_drift_active=bool(trust_drift and trust_drift.active),
        trust_drift_reason=trust_drift.reason if trust_drift is not None else None,
    )
    payload = {
        "action_name": action_name,
        "domain": domain,
        "domain_trust": domain_trust.to_payload(),
        "trust_drift": trust_drift.to_payload() if trust_drift is not None else None,
        "risk": risk,
        "autonomy_mode": mode,
        "effective_autonomy_mode": effective_mode,
        "domain_autonomy_mode": domain_mode,
        "domain_autonomy_reason": str(domain_details.get("reason") or "") or None,
        "domain_autonomy_source": str(domain_details.get("source") or "") or None,
        "domain_autonomy_updated_at": str(domain_details.get("updated_at") or "") or None,
        "decision": policy_eval.decision,
        "reason": policy_eval.reason,
        "kill_switch": get_killswitch_status().to_payload(),
    }
    return ActionResult(success=True, message=f"Politica para {action_name}: {policy_eval.decision}.", data={"policy": payload})


async def autonomy_set_mode_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    require_feature: Callable[[str], ActionResult | None],
    allowed_autonomy_modes: set[str] | list[str] | tuple[str, ...],
    set_autonomy_mode: Callable[[str, str, str], str],
    get_killswitch_status: Callable[[], Any],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    feature_error = require_feature("policy_v1")
    if feature_error is not None:
        return feature_error
    mode = str(params.get("mode", "")).strip().lower()
    if not mode:
        return ActionResult(success=False, message="Informe o modo de autonomia.", error="missing mode")
    if mode not in allowed_autonomy_modes:
        return ActionResult(
            success=False,
            message=f"Modo invalido. Use: {', '.join(sorted(allowed_autonomy_modes))}.",
            error="invalid mode",
        )
    applied = set_autonomy_mode(ctx.participant_identity, ctx.room, mode)
    return ActionResult(
        success=True,
        message=f"Modo de autonomia ajustado para {applied}.",
        data={
            "autonomy_mode": applied,
            "kill_switch": get_killswitch_status().to_payload(),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def autonomy_killswitch_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    require_feature: Callable[[str], ActionResult | None],
    set_killswitch_global: Callable[..., Any],
    set_killswitch_domain: Callable[..., Any],
    get_killswitch_status: Callable[[], Any],
    get_autonomy_mode: Callable[[str, str], str],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    feature_error = require_feature("policy_v1")
    if feature_error is not None:
        return feature_error
    operation = str(params.get("operation", "status")).strip().lower()
    domain = str(params.get("domain", "")).strip().lower()
    reason = str(params.get("reason", "")).strip() or None
    if operation == "enable":
        state = set_killswitch_global(True, reason=reason)
    elif operation == "disable":
        state = set_killswitch_global(False, reason=None)
    elif operation == "enable_domain":
        if not domain:
            return ActionResult(success=False, message="Informe `domain` para enable_domain.", error="missing domain")
        state = set_killswitch_domain(domain, True, reason=reason)
    elif operation == "disable_domain":
        if not domain:
            return ActionResult(success=False, message="Informe `domain` para disable_domain.", error="missing domain")
        state = set_killswitch_domain(domain, False)
    else:
        state = get_killswitch_status()

    return ActionResult(
        success=True,
        message="Kill switch atualizado.",
        data={
            "kill_switch": state.to_payload(),
            "autonomy_mode": get_autonomy_mode(ctx.participant_identity, ctx.room),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def policy_action_risk_matrix_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    action_registry: dict[str, Any],
    classify_action_risk: Callable[[str], str],
    infer_action_domain: Callable[[str], str],
    get_domain_trust: Callable[[str], Any],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    query = str(params.get("query", "")).strip().lower()
    include_internal = bool(params.get("include_internal", False))
    rows: list[JsonObject] = []
    for spec in action_registry.values():
        if not include_internal and not spec.expose_to_model:
            continue
        risk = classify_action_risk(spec.name)
        domain = infer_action_domain(spec.name)
        domain_trust = get_domain_trust(domain)
        row: JsonObject = {
            "action_name": spec.name,
            "risk": risk,
            "requires_confirmation": spec.requires_confirmation,
            "requires_auth": spec.requires_auth,
            "expose_to_model": spec.expose_to_model,
            "domain": domain,
            "domain_trust_score": round(domain_trust.score, 4),
        }
        if query:
            haystack = f"{spec.name} {risk} {domain}".lower()
            if query not in haystack:
                continue
        rows.append(row)
    rows.sort(key=lambda item: (str(item.get("risk", "")), str(item.get("action_name", ""))))
    return ActionResult(
        success=True,
        message=f"Matriz de risco com {len(rows)} action(s).",
        data={
            "risk_matrix": rows,
            "query": query or None,
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def policy_domain_trust_status_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    get_domain_trust: Callable[[str], Any],
    list_domain_trust: Callable[[], list[Any]],
    list_trust_drift: Callable[[str, str], list[Any]],
    list_domain_autonomy_modes: Callable[[str, str], list[JsonObject]],
    get_autonomy_mode: Callable[[str, str], str],
    get_effective_autonomy_mode: Callable[..., str],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    domain = str(params.get("domain", "")).strip().lower()
    if domain:
        snapshots = [get_domain_trust(domain)]
    else:
        snapshots = list_domain_trust()
    drift_rows = {item.domain: item for item in list_trust_drift(ctx.participant_identity, ctx.room)}
    domain_mode_rows = {
        str(item.get("domain") or ""): item
        for item in list_domain_autonomy_modes(ctx.participant_identity, ctx.room)
        if isinstance(item, dict)
    }
    rows: list[JsonObject] = []
    for snapshot in snapshots:
        row = snapshot.to_payload()
        drift = drift_rows.get(snapshot.domain)
        domain_details = domain_mode_rows.get(snapshot.domain, {})
        row["trust_drift_active"] = bool(drift and drift.active)
        row["trust_drift"] = drift.to_payload() if drift is not None else None
        row["autonomy_mode"] = get_autonomy_mode(ctx.participant_identity, ctx.room)
        row["domain_autonomy_mode"] = str(domain_details.get("mode") or "") or None
        row["effective_autonomy_mode"] = get_effective_autonomy_mode(
            ctx.participant_identity,
            ctx.room,
            domain=snapshot.domain,
        )
        row["domain_autonomy_reason"] = str(domain_details.get("reason") or "") or None
        row["domain_autonomy_source"] = str(domain_details.get("source") or "") or None
        row["domain_autonomy_updated_at"] = str(domain_details.get("updated_at") or "") or None
        rows.append(row)
    return ActionResult(
        success=True,
        message=f"Trust score em {len(rows)} dominio(s).",
        data={
            "domain_trust": rows,
            "domain": domain or None,
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def policy_trust_drift_report_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    replace_trust_drift: Callable[..., list[Any]],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    rows_param = params.get("rows")
    if rows_param is None:
        rows: list[JsonObject] = []
    elif isinstance(rows_param, list):
        rows = [item for item in rows_param if isinstance(item, dict)]
    else:
        return ActionResult(
            success=False,
            message="`rows` precisa ser uma lista de objetos.",
            error="invalid rows",
        )
    signature = str(params.get("signature", "")).strip() or None
    updated = replace_trust_drift(
        ctx.participant_identity,
        ctx.room,
        rows,
        source="frontend",
        signature=signature,
    )
    return ActionResult(
        success=True,
        message=f"Trust drift sincronizado para {len(updated)} dominio(s).",
        data={
            "trust_drift": [item.to_payload() for item in updated],
            "signature": signature,
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )
