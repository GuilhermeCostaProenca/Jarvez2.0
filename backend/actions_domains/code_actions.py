from __future__ import annotations

from pathlib import Path
from typing import Any
from collections.abc import Callable

from actions_core import ActionContext, ActionResult

JsonObject = dict[str, Any]


async def code_reindex_repo(
    params: JsonObject,
    ctx: ActionContext,
    *,
    get_project_catalog: Callable[[], Any],
    get_code_index: Callable[[], Any],
    active_project_payload: Callable[[str, str], JsonObject],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    catalog = get_project_catalog()
    target_project_id = str(params.get("project_id", "")).strip()
    if target_project_id:
        record = catalog.get_project(target_project_id)
        if record is None:
            return ActionResult(success=False, message="Projeto nao encontrado para reindexacao.", error="unknown project")
        records = [record]
    else:
        records = catalog.list_projects()
        if not records:
            catalog.scan()
            records = catalog.list_projects()

    summaries: list[JsonObject] = []
    for record in records:
        root = Path(record.root_path).resolve(strict=False)
        if not root.exists():
            summaries.append({"project_id": record.project_id, "name": record.name, "status": "missing_root"})
            continue
        summary = get_code_index().index_project(
            record.project_id,
            root,
            project_name=record.name,
            aliases=record.aliases,
        )
        catalog.update_last_indexed(record.project_id)
        summaries.append(
            {
                "project_id": record.project_id,
                "name": record.name,
                "summary": summary,
                "knowledge_stats": get_code_index().stats(project_id=record.project_id),
            }
        )

    return ActionResult(
        success=True,
        message="Indice global de codigo atualizado.",
        data={
            "projects_reindexed": summaries,
            "knowledge_stats": get_code_index().stats(),
            **active_project_payload(ctx.participant_identity, ctx.room),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def code_search_repo(
    params: JsonObject,
    ctx: ActionContext,
    *,
    get_active_project: Callable[[str, str], Any | None],
    get_code_index: Callable[[], Any],
    code_repo_root: Callable[[], Path],
    active_project_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    # DEPRECATED: migrated to jarvez-mcp-code-actions for pure knowledge search; keep legacy compatibility while active project and index singletons stay local.
    query = str(params.get("query", "")).strip()
    limit = int(params.get("limit", 5))
    if not query:
        return ActionResult(success=False, message="Informe uma consulta de codigo.", error="missing query")

    active = get_active_project(ctx.participant_identity, ctx.room)
    results = get_code_index().search(query, limit=limit, project_id=active.project_id if active else None)
    if not results:
        return ActionResult(
            success=False,
            message="Nao encontrei trechos de codigo para essa pergunta.",
            data={
                "query": query,
                "repo_root": str(code_repo_root()),
                **active_project_payload(ctx.participant_identity, ctx.room),
            },
            error="not found",
        )
    return ActionResult(
        success=True,
        message=f"Encontrei {len(results)} trecho(s) relevantes do codigo.",
        data={
            "query": query,
            "repo_root": str(code_repo_root()),
            "results": results,
            **active_project_payload(ctx.participant_identity, ctx.room),
        },
    )


async def code_worker_status_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    code_worker_request: Callable[[str, JsonObject | None], tuple[JsonObject | None, ActionResult | None]]
    | Callable[[str], tuple[JsonObject | None, ActionResult | None]],
    active_project_payload: Callable[[str, str], JsonObject],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    _ = params
    response, worker_error = code_worker_request("/health")
    if worker_error is not None:
        return ActionResult(
            success=False,
            message=worker_error.message,
            data={
                "worker_status": {"success": False, "message": worker_error.message},
                **active_project_payload(ctx.participant_identity, ctx.room),
            },
            error=worker_error.error,
        )
    return ActionResult(
        success=True,
        message="Code worker online.",
        data={
            "worker_status": {"success": True, "message": str((response or {}).get("message", "Code worker online."))},
            "worker_info": (response or {}).get("data"),
            **active_project_payload(ctx.participant_identity, ctx.room),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def code_read_file_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    resolve_project_record: Callable[[JsonObject, ActionContext], tuple[Any | None, ActionResult | None]],
    code_worker_request: Callable[[str, JsonObject | None], tuple[JsonObject | None, ActionResult | None]],
    project_record_to_payload: Callable[[Any], JsonObject],
    active_project_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    # DEPRECATED: migrated to jarvez-mcp-code-actions for pure file read; keep legacy compatibility while project resolution and worker singleton stay local.
    path = str(params.get("path", "")).strip()
    if not path:
        return ActionResult(success=False, message="Informe o arquivo que devo ler.", error="missing path")
    record, error = resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None
    worker_payload: JsonObject = {
        "project_id": record.project_id,
        "path": path,
    }
    if isinstance(params.get("start_line"), int):
        worker_payload["start_line"] = params.get("start_line")
    if isinstance(params.get("end_line"), int):
        worker_payload["end_line"] = params.get("end_line")
    response, worker_error = code_worker_request("/read-file", worker_payload)
    if worker_error is not None:
        return worker_error
    return ActionResult(
        success=True,
        message=f"Arquivo lido em {record.name}.",
        data={
            "project": project_record_to_payload(record),
            "file": (response or {}).get("data"),
            **active_project_payload(ctx.participant_identity, ctx.room),
        },
    )


async def code_search_in_active_project_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    resolve_project_record: Callable[[JsonObject, ActionContext], tuple[Any | None, ActionResult | None]],
    get_code_index: Callable[[], Any],
    code_worker_request: Callable[[str, JsonObject | None], tuple[JsonObject | None, ActionResult | None]],
    project_record_to_payload: Callable[[Any], JsonObject],
    active_project_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    query = str(params.get("query", "")).strip()
    if not query:
        return ActionResult(success=False, message="Informe a busca de codigo.", error="missing query")
    limit = int(params.get("limit", 5))
    record, error = resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None
    indexed = get_code_index().search(query, limit=limit, project_id=record.project_id)
    worker_response, worker_error = code_worker_request(
        "/search-files",
        {"project_id": record.project_id, "query": query, "limit": limit},
    )
    file_hits = [] if worker_error is not None else list(((worker_response or {}).get("data") or {}).get("results", []))
    return ActionResult(
        success=True,
        message=f"Busca de codigo concluida em {record.name}.",
        data={
            "project": project_record_to_payload(record),
            "query": query,
            "results": indexed,
            "file_hits": file_hits,
            **active_project_payload(ctx.participant_identity, ctx.room),
        },
    )


async def code_git_status_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    resolve_project_record: Callable[[JsonObject, ActionContext], tuple[Any | None, ActionResult | None]],
    code_worker_request: Callable[[str, JsonObject | None], tuple[JsonObject | None, ActionResult | None]],
    project_record_to_payload: Callable[[Any], JsonObject],
    active_project_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    record, error = resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None
    response, worker_error = code_worker_request("/git-status", {"project_id": record.project_id})
    if worker_error is not None:
        return worker_error
    return ActionResult(
        success=True,
        message=f"Git status coletado para {record.name}.",
        data={
            "project": project_record_to_payload(record),
            "git_status": (response or {}).get("data"),
            **active_project_payload(ctx.participant_identity, ctx.room),
        },
    )


async def code_git_diff_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    resolve_project_record: Callable[[JsonObject, ActionContext], tuple[Any | None, ActionResult | None]],
    code_worker_request: Callable[[str, JsonObject | None], tuple[JsonObject | None, ActionResult | None]],
    project_record_to_payload: Callable[[Any], JsonObject],
    summarize_diff: Callable[..., JsonObject | list[Any] | str | None],
    active_project_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    record, error = resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None
    paths = params.get("paths", [])
    worker_payload: JsonObject = {"project_id": record.project_id}
    if isinstance(paths, list):
        worker_payload["paths"] = [item for item in paths if isinstance(item, str) and item.strip()]
    response, worker_error = code_worker_request("/git-diff", worker_payload)
    if worker_error is not None:
        return worker_error
    diff_data = (response or {}).get("data") if isinstance((response or {}).get("data"), dict) else {}
    diff_text = str(diff_data.get("stdout", "") or diff_data.get("stderr", "")).strip()
    diff_summary = summarize_diff(project=project_record_to_payload(record), diff_text=diff_text) if diff_text else None
    return ActionResult(
        success=True,
        message=f"Git diff coletado para {record.name}.",
        data={
            "project": project_record_to_payload(record),
            "git_diff": diff_data,
            "git_diff_summary": diff_summary,
            **active_project_payload(ctx.participant_identity, ctx.room),
        },
    )


async def code_explain_project_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    resolve_project_record: Callable[[JsonObject, ActionContext], tuple[Any | None, ActionResult | None]],
    get_code_index: Callable[[], Any],
    code_worker_request: Callable[[str, JsonObject | None], tuple[JsonObject | None, ActionResult | None]],
    project_record_to_payload: Callable[[Any], JsonObject],
    explain_project_state: Callable[..., JsonObject | list[Any] | str | None],
    active_project_payload: Callable[[str, str], JsonObject],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    request_text = str(params.get("request", "")).strip() or str(params.get("query", "")).strip()
    if not request_text:
        return ActionResult(success=False, message="Descreva o que devo analisar no projeto.", error="missing request")
    limit = int(params.get("limit", 4))
    record, error = resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None

    snippets = get_code_index().search(request_text, limit=limit, project_id=record.project_id)
    extra_files: list[JsonObject] = []
    read_paths = params.get("read_paths", [])
    if isinstance(read_paths, list):
        for item in read_paths[:2]:
            if not isinstance(item, str) or not item.strip():
                continue
            response, worker_error = code_worker_request(
                "/read-file",
                {"project_id": record.project_id, "path": item},
            )
            if worker_error is None and isinstance((response or {}).get("data"), dict):
                file_payload = (response or {}).get("data") or {}
                extra_files.append(
                    {
                        "path": file_payload.get("relative_path") or file_payload.get("path"),
                        "content": file_payload.get("content", ""),
                    }
                )

    explanation = explain_project_state(
        user_request=request_text,
        project=project_record_to_payload(record),
        snippets=snippets,
        extra_files=extra_files,
    )
    return ActionResult(
        success=True,
        message=f"Analise preparada para {record.name}.",
        data={
            "project": project_record_to_payload(record),
            "project_analysis": explanation,
            "context_results": snippets,
            "context_files": extra_files,
            **active_project_payload(ctx.participant_identity, ctx.room),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def code_propose_change_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    resolve_project_record: Callable[[JsonObject, ActionContext], tuple[Any | None, ActionResult | None]],
    get_code_index: Callable[[], Any],
    code_worker_request: Callable[[str, JsonObject | None], tuple[JsonObject | None, ActionResult | None]],
    project_record_to_payload: Callable[[Any], JsonObject],
    propose_patch_plan: Callable[..., JsonObject | list[Any] | str | None],
    active_project_payload: Callable[[str, str], JsonObject],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    request_text = str(params.get("request", "")).strip() or str(params.get("query", "")).strip()
    if not request_text:
        return ActionResult(success=False, message="Descreva a mudanca ou pergunta de engenharia.", error="missing request")
    limit = int(params.get("limit", 4))
    record, error = resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None

    snippets = get_code_index().search(request_text, limit=limit, project_id=record.project_id)
    extra_files: list[JsonObject] = []
    read_paths = params.get("read_paths", [])
    if isinstance(read_paths, list):
        for item in read_paths[:2]:
            if not isinstance(item, str) or not item.strip():
                continue
            response, worker_error = code_worker_request(
                "/read-file",
                {"project_id": record.project_id, "path": item},
            )
            if worker_error is None and isinstance((response or {}).get("data"), dict):
                file_payload = (response or {}).get("data") or {}
                extra_files.append(
                    {
                        "path": file_payload.get("relative_path") or file_payload.get("path"),
                        "content": file_payload.get("content", ""),
                    }
                )

    proposal = propose_patch_plan(
        user_request=request_text,
        project=project_record_to_payload(record),
        snippets=snippets,
        extra_files=extra_files,
    )
    return ActionResult(
        success=True,
        message=f"Proposta de mudanca preparada para {record.name}.",
        data={
            "project": project_record_to_payload(record),
            "proposed_code_change": proposal,
            "context_results": snippets,
            "context_files": extra_files,
            **active_project_payload(ctx.participant_identity, ctx.room),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def code_apply_patch_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    resolve_project_record: Callable[[JsonObject, ActionContext], tuple[Any | None, ActionResult | None]],
    code_worker_request: Callable[[str, JsonObject | None], tuple[JsonObject | None, ActionResult | None]],
    project_record_to_payload: Callable[[Any], JsonObject],
    active_project_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    # DEPRECATED: migrated to jarvez-mcp-code-actions for pure patch apply; keep legacy compatibility while project resolution and worker singleton stay local.
    changes = params.get("changes", [])
    if not isinstance(changes, list) or not changes:
        return ActionResult(success=False, message="Envie ao menos uma mudanca para aplicar.", error="missing changes")
    record, error = resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None
    response, worker_error = code_worker_request(
        "/apply-patch",
        {"project_id": record.project_id, "changes": changes},
    )
    if worker_error is not None:
        return worker_error
    return ActionResult(
        success=True,
        message=f"Patch aplicado em {record.name}.",
        data={
            "project": project_record_to_payload(record),
            "patch_result": (response or {}).get("data"),
            **active_project_payload(ctx.participant_identity, ctx.room),
        },
    )


async def code_run_command_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    resolve_project_record: Callable[[JsonObject, ActionContext], tuple[Any | None, ActionResult | None]],
    code_worker_request: Callable[[str, JsonObject | None], tuple[JsonObject | None, ActionResult | None]],
    project_record_to_payload: Callable[[Any], JsonObject],
    active_project_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    command = str(params.get("command", "")).strip()
    arguments = params.get("arguments", [])
    if not command:
        return ActionResult(success=False, message="Informe o comando para validacao.", error="missing command")
    if not isinstance(arguments, list) or any(not isinstance(item, str) for item in arguments):
        return ActionResult(success=False, message="`arguments` precisa ser uma lista de textos.", error="invalid arguments")
    record, error = resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None
    response, worker_error = code_worker_request(
        "/run-command",
        {
            "project_id": record.project_id,
            "command": command,
            "arguments": arguments,
            "timeout_seconds": int(params.get("timeout_seconds", 60) or 60),
        },
    )
    if worker_error is not None:
        return worker_error
    return ActionResult(
        success=True,
        message=f"Comando executado em {record.name}.",
        data={
            "project": project_record_to_payload(record),
            "command_execution": (response or {}).get("data"),
            **active_project_payload(ctx.participant_identity, ctx.room),
        },
    )
