from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from actions_core import ActionContext, ActionResult

JsonObject = dict[str, Any]


async def skills_list_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    require_feature: Callable[[str], ActionResult | None],
    list_skills: Callable[..., list[Any]],
    active_project_payload: Callable[[str, str], JsonObject],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    feature_error = require_feature("skills_v1")
    if feature_error is not None:
        return feature_error
    query = str(params.get("query", "")).strip() or None
    refresh = bool(params.get("refresh", False))
    items = list_skills(query=query, refresh=refresh)
    payload = [item.to_payload() for item in items]
    return ActionResult(
        success=True,
        message=f"Encontrei {len(payload)} skill(s) disponiveis.",
        data={
            "skills": payload,
            "skills_total": len(payload),
            "query": query,
            **active_project_payload(ctx.participant_identity, ctx.room),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def skills_read_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    require_feature: Callable[[str], ActionResult | None],
    get_skill: Callable[..., Any | None],
    active_project_payload: Callable[[str, str], JsonObject],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    feature_error = require_feature("skills_v1")
    if feature_error is not None:
        return feature_error
    skill_id = str(params.get("skill_id", "")).strip() or None
    skill_name = str(params.get("skill_name", "")).strip() or None
    doc = get_skill(skill_id=skill_id, skill_name=skill_name)
    if doc is None:
        return ActionResult(
            success=False,
            message="Skill nao encontrada. Use skills_list para conferir os ids.",
            error="skill not found",
        )
    return ActionResult(
        success=True,
        message=f"Skill carregada: {doc.metadata.name}.",
        data={
            "skill_document": doc.to_payload(),
            **active_project_payload(ctx.participant_identity, ctx.room),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def orchestrate_task_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    require_feature: Callable[[str], ActionResult | None],
    build_task_plan: Callable[[str], Any],
    classify_action_risk: Callable[[str], str],
    route_orchestration: Callable[..., tuple[str, Any]],
    now_iso: Callable[[], str],
    active_project_payload: Callable[[str, str], JsonObject],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    feature_error = require_feature("multi_model_router_v1")
    if feature_error is not None:
        return feature_error
    request_text = (
        str(params.get("request", "")).strip()
        or str(params.get("query", "")).strip()
        or str(params.get("prompt", "")).strip()
    )
    if not request_text:
        return ActionResult(success=False, message="Descreva a tarefa para orquestrar.", error="missing request")

    plan = build_task_plan(request_text)
    task_type = plan.task_type
    risk = classify_action_risk(str(params.get("action_hint", "")).strip() or "orchestrate_task")
    response_text, route_decision = route_orchestration(request=request_text, task_type=task_type, risk=risk)
    orchestration_payload = {
        "request": request_text,
        "task_plan": plan.to_payload(),
        "model_route": route_decision.to_payload(),
        "response_preview": response_text,
    }
    return ActionResult(
        success=True,
        message=f"Tarefa orquestrada com provider {route_decision.used_provider}.",
        data={
            "orchestration": orchestration_payload,
            "model_route": route_decision.to_payload(),
            **active_project_payload(ctx.participant_identity, ctx.room),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
        evidence={
            "provider": route_decision.used_provider,
            "request_id": route_decision.generated_at,
            "executed_at": now_iso(),
        },
        fallback_used=route_decision.fallback_used,
    )


async def subagent_spawn_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    require_feature: Callable[[str], ActionResult | None],
    build_task_plan: Callable[[str], Any],
    classify_action_risk: Callable[[str], str],
    resolve_runtime: Callable[..., Any],
    spawn_subagent: Callable[..., Any],
    route_orchestration: Callable[..., tuple[str, Any]],
    complete_subagent: Callable[..., Any | None],
    start_subagent_task: Callable[..., None],
    list_subagents: Callable[..., list[Any]],
    now_iso: Callable[[], str],
    active_project_payload: Callable[[str, str], JsonObject],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    feature_error = require_feature("subagents_v1")
    if feature_error is not None:
        return feature_error
    request_text = str(params.get("request", "")).strip()
    if not request_text:
        return ActionResult(success=False, message="Descreva a tarefa do subagente.", error="missing request")
    plan = build_task_plan(request_text)
    risk = classify_action_risk(str(params.get("action_hint", "")).strip() or "subagent_spawn")
    runtime_decision = resolve_runtime(
        intent="subagent_spawn",
        task_type=plan.task_type,
        risk=risk,
        required_capabilities=["tools"],
    )
    primary_provider = str(getattr(runtime_decision, "primary_provider", "") or "").strip() or "local_mock"
    fallback_provider_raw = str(getattr(runtime_decision, "fallback_provider", "") or "").strip()
    fallback_provider = fallback_provider_raw or None
    route_reason = str(getattr(runtime_decision, "reason", "") or "").strip()
    state = spawn_subagent(
        participant_identity=ctx.participant_identity,
        room=ctx.room,
        request=request_text,
        task_type=plan.task_type,
        risk=risk,
        route_provider=primary_provider,
        initial_summary="Subagente iniciado.",
    )
    wait_for_completion_raw = params.get("wait_for_completion")
    if isinstance(wait_for_completion_raw, bool):
        wait_for_completion = wait_for_completion_raw
    else:
        wait_for_completion = bool(params.get("auto_complete", False))

    route_payload: JsonObject = {
        "task_type": plan.task_type,
        "risk": risk,
        "primary_provider": primary_provider,
        "fallback_provider": fallback_provider,
        "used_provider": primary_provider,
        "fallback_used": False,
        "reason": route_reason or "Subagente enfileirado para execucao assincrona.",
        "generated_at": now_iso(),
    }
    fallback_used = False

    async def _runner() -> str:
        text, decision = route_orchestration(request=request_text, task_type=plan.task_type, risk=risk)
        state.route_provider = decision.used_provider
        state.updated_at = now_iso()
        return text[:1200]

    if wait_for_completion:
        response_text, route_decision = route_orchestration(request=request_text, task_type=plan.task_type, risk=risk)
        state.route_provider = route_decision.used_provider
        completed = complete_subagent(
            participant_identity=ctx.participant_identity,
            room=ctx.room,
            subagent_id=state.subagent_id,
            summary=response_text[:1200],
        )
        if completed is not None:
            state = completed
        route_payload = route_decision.to_payload()
        fallback_used = route_decision.fallback_used
    else:
        start_subagent_task(
            participant_identity=ctx.participant_identity,
            room=ctx.room,
            state=state,
            runner=_runner,
        )

    return ActionResult(
        success=True,
        message=f"Subagente {state.subagent_id} em estado {state.status}.",
        data={
            "subagent_state": state.to_payload(),
            "subagent_states": [item.to_payload() for item in list_subagents(participant_identity=ctx.participant_identity, room=ctx.room)],
            "model_route": route_payload,
            **active_project_payload(ctx.participant_identity, ctx.room),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
        evidence={
            "provider": state.route_provider or primary_provider,
            "request_id": state.subagent_id,
            "executed_at": now_iso(),
        },
        fallback_used=fallback_used,
    )


async def subagent_status_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    require_feature: Callable[[str], ActionResult | None],
    list_subagents: Callable[..., list[Any]],
) -> ActionResult:
    feature_error = require_feature("subagents_v1")
    if feature_error is not None:
        return feature_error
    subagent_id = str(params.get("subagent_id", "")).strip()
    if subagent_id:
        target = None
        for item in list_subagents(participant_identity=ctx.participant_identity, room=ctx.room):
            if item.subagent_id == subagent_id:
                target = item
                break
        if target is None:
            return ActionResult(success=False, message="Subagente nao encontrado.", error="subagent not found")
        return ActionResult(
            success=True,
            message=f"Subagente {target.subagent_id} em estado {target.status}.",
            data={"subagent_state": target.to_payload()},
        )

    states = [item.to_payload() for item in list_subagents(participant_identity=ctx.participant_identity, room=ctx.room)]
    return ActionResult(
        success=True,
        message=f"{len(states)} subagente(s) neste contexto.",
        data={"subagent_states": states},
    )


async def subagent_cancel_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    require_feature: Callable[[str], ActionResult | None],
    cancel_subagent: Callable[..., Any | None],
    list_subagents: Callable[..., list[Any]],
) -> ActionResult:
    feature_error = require_feature("subagents_v1")
    if feature_error is not None:
        return feature_error
    subagent_id = str(params.get("subagent_id", "")).strip()
    if not subagent_id:
        return ActionResult(success=False, message="Informe o subagent_id para cancelar.", error="missing subagent id")
    cancelled = cancel_subagent(participant_identity=ctx.participant_identity, room=ctx.room, subagent_id=subagent_id)
    if cancelled is None:
        return ActionResult(success=False, message="Subagente nao encontrado.", error="subagent not found")
    return ActionResult(
        success=True,
        message=f"Subagente {cancelled.subagent_id} cancelado.",
        data={
            "subagent_state": cancelled.to_payload(),
            "subagent_states": [item.to_payload() for item in list_subagents(participant_identity=ctx.participant_identity, room=ctx.room)],
        },
    )


async def providers_health_check_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    collect_provider_health: Callable[..., list[JsonObject]],
    feature_flags_snapshot: Callable[[], JsonObject],
    canary_state_payload: Callable[[str, str], JsonObject],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    include_ping = bool(params.get("include_ping", False))
    ping_prompt = str(params.get("ping_prompt", "")).strip() or "Responda apenas: ok"
    rows = collect_provider_health(include_ping=include_ping, ping_prompt=ping_prompt)
    return ActionResult(
        success=True,
        message=f"Health check de {len(rows)} provider(s) concluido.",
        data={
            "providers_health": rows,
            "feature_flags": feature_flags_snapshot(),
            "canary_state": canary_state_payload(ctx.participant_identity, ctx.room),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )
