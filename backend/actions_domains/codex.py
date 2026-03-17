from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any
import uuid

from actions_core import ActionContext, ActionResult

JsonObject = dict[str, Any]


async def run_codex_task(
    *,
    params: JsonObject,
    ctx: ActionContext,
    default_request: str,
    review_mode: bool,
    is_codex_available: Callable[[], bool],
    resolve_project_record: Callable[[JsonObject, ActionContext], tuple[Any | None, ActionResult | None]],
    build_codex_request_prompt: Callable[..., str],
    now_iso: Callable[[], str],
    codex_task_factory: Callable[..., Any],
    set_active_codex_task: Callable[[str, str, Any], None],
    emit_codex_task_event: Callable[..., Awaitable[None]],
    codex_progress_message: Callable[[JsonObject], str],
    codex_key: Callable[[str, str], str],
    run_exec_streaming: Callable[..., Awaitable[Any]],
    codex_running_processes: dict[str, Any],
    push_codex_history: Callable[[str, str, Any], None],
    codex_task_to_payload: Callable[[Any], JsonObject],
    codex_history_payload: Callable[[str, str], list[JsonObject]],
    active_project_payload: Callable[[str, str], JsonObject],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    user_request = (
        str(params.get("request", "")).strip()
        or str(params.get("query", "")).strip()
        or str(params.get("prompt", "")).strip()
        or default_request
    )
    if not user_request:
        return ActionResult(success=False, message="Descreva a tarefa para o Codex.", error="missing request")

    if not is_codex_available():
        return ActionResult(success=False, message="Codex CLI nao esta disponivel neste ambiente.", error="codex unavailable")

    record, error = resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None

    root = Path(record.root_path).resolve(strict=False)
    if not root.exists():
        return ActionResult(success=False, message="A raiz do projeto nao existe.", error="missing project root")

    prompt = build_codex_request_prompt(record=record, user_request=user_request, review_mode=review_mode)
    command_preview = (
        "codex exec --json --skip-git-repo-check --sandbox read-only "
        f'--ephemeral -C "{root}" "<prompt>"'
    )
    task = codex_task_factory(
        task_id=f"codex_{uuid.uuid4().hex[:12]}",
        status="running",
        project_id=record.project_id,
        project_name=record.name,
        working_directory=str(root),
        request=user_request,
        started_at=now_iso(),
        current_phase="starting",
        command_preview=command_preview,
    )
    set_active_codex_task(ctx.participant_identity, ctx.room, task)
    await emit_codex_task_event(
        ctx,
        event_type="codex_task_started",
        task=task,
        phase="starting",
        message=f"Iniciando Codex em {record.name}.",
    )

    async def on_progress(event: JsonObject) -> None:
        task.current_phase = str(event.get("type", "")).strip() or "progress"
        task.raw_last_event = event
        task.summary = codex_progress_message(event)
        await emit_codex_task_event(
            ctx,
            event_type="codex_task_progress",
            task=task,
            phase=task.current_phase,
            message=task.summary,
            raw_event_type=str(event.get("type", "")).strip() or None,
        )

    key = codex_key(ctx.participant_identity, ctx.room)
    try:
        result = await run_exec_streaming(
            prompt=prompt,
            working_directory=root,
            on_progress=on_progress,
            process_registry=codex_running_processes,
            registry_key=key,
        )
    except FileNotFoundError:
        task.status = "failed"
        task.finished_at = now_iso()
        task.current_phase = "missing_cli"
        task.error = "codex unavailable"
        task.summary = "Codex CLI nao esta disponivel neste ambiente."
        push_codex_history(ctx.participant_identity, ctx.room, task)
        await emit_codex_task_event(
            ctx,
            event_type="codex_task_failed",
            task=task,
            phase="missing_cli",
            message=task.summary,
        )
        return ActionResult(success=False, message=task.summary, error=task.error)
    except Exception as error:  # noqa: BLE001
        task.status = "failed"
        task.finished_at = now_iso()
        task.current_phase = "runtime_error"
        task.error = str(error)
        task.summary = "A tarefa do Codex falhou durante a execucao."
        push_codex_history(ctx.participant_identity, ctx.room, task)
        await emit_codex_task_event(
            ctx,
            event_type="codex_task_failed",
            task=task,
            phase="runtime_error",
            message=task.summary,
        )
        return ActionResult(success=False, message=task.summary, error=str(error))

    if task.status == "cancelled":
        task.exit_code = result.exit_code
        task.raw_last_event = result.last_event
        return ActionResult(
            success=False,
            message="Tarefa do Codex cancelada.",
            data={
                "codex_task": codex_task_to_payload(task),
                "codex_history": codex_history_payload(ctx.participant_identity, ctx.room),
                **active_project_payload(ctx.participant_identity, ctx.room),
                **capability_payload(ctx.participant_identity, ctx.room),
            },
            error="cancelled",
        )

    task.status = "completed" if result.success else "failed"
    task.finished_at = now_iso()
    task.current_phase = "completed" if result.success else "failed"
    task.summary = result.summary
    task.exit_code = result.exit_code
    task.raw_last_event = result.last_event
    if not result.success:
        task.error = result.stderr[:400] or f"exit code {result.exit_code}"
    push_codex_history(ctx.participant_identity, ctx.room, task)

    await emit_codex_task_event(
        ctx,
        event_type="codex_task_completed" if result.success else "codex_task_failed",
        task=task,
        phase=task.current_phase,
        message=result.summary,
        raw_event_type=str(result.last_event.get("type", "")).strip() if isinstance(result.last_event, dict) else None,
    )

    data = {
        "codex_task": codex_task_to_payload(task),
        "codex_history": codex_history_payload(ctx.participant_identity, ctx.room),
        **active_project_payload(ctx.participant_identity, ctx.room),
        **capability_payload(ctx.participant_identity, ctx.room),
    }
    if result.success:
        return ActionResult(success=True, message=f"Codex concluiu a tarefa em {record.name}.", data=data)
    return ActionResult(
        success=False,
        message=f"Codex falhou na tarefa em {record.name}.",
        data=data,
        error=task.error,
    )


async def codex_exec_task_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    run_codex_task_fn: Callable[..., Awaitable[ActionResult]],
) -> ActionResult:
    # DEPRECATED: migrated to jarvez-mcp-codex for pure task submission; keep legacy compatibility while session history, events and participant glue stay local.
    return await run_codex_task_fn(
        params=params,
        ctx=ctx,
        default_request="Analise o projeto atual e explique o estado tecnico com proximos passos.",
        review_mode=False,
    )


async def codex_exec_review_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    run_codex_task_fn: Callable[..., Awaitable[ActionResult]],
) -> ActionResult:
    # DEPRECATED: migrated to jarvez-mcp-codex for pure review submission; keep legacy compatibility while session history, events and participant glue stay local.
    return await run_codex_task_fn(
        params=params,
        ctx=ctx,
        default_request="Revise o estado atual do projeto e destaque riscos e pontos de atencao sem editar arquivos.",
        review_mode=True,
    )


async def codex_exec_status_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    get_active_codex_task: Callable[[str, str], Any | None],
    codex_history_payload: Callable[[str, str], list[JsonObject]],
    codex_task_to_payload: Callable[[Any], JsonObject],
    active_project_payload: Callable[[str, str], JsonObject],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    # DEPRECATED: migrated to jarvez-mcp-codex for pure task status; keep legacy compatibility while session history, events and participant glue stay local.
    _ = params
    task = get_active_codex_task(ctx.participant_identity, ctx.room)
    if task is None:
        return ActionResult(
            success=False,
            message="Nenhuma tarefa do Codex na sessao.",
            data={"codex_task": None, "codex_history": codex_history_payload(ctx.participant_identity, ctx.room)},
            error="no codex task",
        )
    return ActionResult(
        success=True,
        message=f"Tarefa do Codex em estado {task.status}.",
        data={
            "codex_task": codex_task_to_payload(task),
            "codex_history": codex_history_payload(ctx.participant_identity, ctx.room),
            **active_project_payload(ctx.participant_identity, ctx.room),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def codex_cancel_task_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    codex_key: Callable[[str, str], str],
    codex_running_processes: dict[str, Any],
    get_active_codex_task: Callable[[str, str], Any | None],
    now_iso: Callable[[], str],
    push_codex_history: Callable[[str, str, Any], None],
    emit_codex_task_event: Callable[..., Awaitable[None]],
    codex_task_to_payload: Callable[[Any], JsonObject],
    codex_history_payload: Callable[[str, str], list[JsonObject]],
    active_project_payload: Callable[[str, str], JsonObject],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    # DEPRECATED: migrated to jarvez-mcp-codex for pure task cancel; keep legacy compatibility while session history, events and participant glue stay local.
    _ = params
    key = codex_key(ctx.participant_identity, ctx.room)
    process = codex_running_processes.get(key)
    task = get_active_codex_task(ctx.participant_identity, ctx.room)
    if process is None or task is None or task.status != "running":
        return ActionResult(success=False, message="Nenhuma tarefa do Codex em andamento.", error="no running task")

    process.terminate()
    task.status = "cancelled"
    task.finished_at = now_iso()
    task.current_phase = "cancelled"
    task.summary = "Tarefa cancelada pelo usuario."
    task.error = None
    codex_running_processes.pop(key, None)
    push_codex_history(ctx.participant_identity, ctx.room, task)
    await emit_codex_task_event(
        ctx,
        event_type="codex_task_cancelled",
        task=task,
        phase="cancelled",
        message=task.summary,
    )
    return ActionResult(
        success=True,
        message="Tarefa do Codex cancelada.",
        data={
            "codex_task": codex_task_to_payload(task),
            "codex_history": codex_history_payload(ctx.participant_identity, ctx.room),
            **active_project_payload(ctx.participant_identity, ctx.room),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )
