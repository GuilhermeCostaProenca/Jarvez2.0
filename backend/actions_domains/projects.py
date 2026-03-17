from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from actions_core import ActionContext, ActionResult

JsonObject = dict[str, Any]


async def github_list_repos_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    get_github_catalog_client: Callable[[], Any],
    github_repo_to_payload: Callable[[Any], JsonObject],
) -> ActionResult:
    # DEPRECATED: migrated to jarvez-mcp-github; keep legacy compatibility until MCP routing replaces github_* metadata handlers.
    _ = ctx
    client = get_github_catalog_client()
    if not client.is_configured():
        return ActionResult(
            success=False,
            message="Configure GITHUB_TOKEN ou GH_TOKEN no backend para listar repositorios.",
            error="github not configured",
        )

    limit = int(params.get("limit", 10) or 10)
    visibility = str(params.get("visibility", "all")).strip().casefold() or "all"
    query = str(params.get("query", "")).strip()

    try:
        repos = client.find_repos(query, limit=limit) if query else client.list_repos(visibility=visibility, limit=limit)
    except Exception as error:
        return ActionResult(
            success=False,
            message=f"Falha ao consultar o GitHub: {error}",
            error=str(error),
        )

    return ActionResult(
        success=True,
        message=f"{len(repos)} repositorio(s) carregado(s) do GitHub.",
        data={
            "github_repos": [github_repo_to_payload(item) for item in repos],
            "query": query or None,
            "visibility": visibility,
        },
    )


async def github_find_repo_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    resolve_github_repo: Callable[[JsonObject], tuple[Any | None, ActionResult | None]],
    github_repo_to_payload: Callable[[Any], JsonObject],
) -> ActionResult:
    # DEPRECATED: migrated to jarvez-mcp-github; keep legacy compatibility until MCP routing replaces github_* metadata handlers.
    _ = ctx
    repo, error = resolve_github_repo(params)
    if error is not None:
        return error
    assert repo is not None
    return ActionResult(
        success=True,
        message=f"Repositorio encontrado: {repo.full_name}.",
        data={"github_repo": github_repo_to_payload(repo)},
    )


async def github_clone_and_register_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    resolve_github_repo: Callable[[JsonObject], tuple[Any | None, ActionResult | None]],
    resolve_local_path: Callable[[str], Path | None] | Callable[[str, bool], Path | None],
    github_default_clone_root: Callable[[], Path],
    git_clone_repository: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
    get_project_catalog: Callable[[], Any],
    ensure_project_index: Callable[[Any], str],
    set_active_project_from_record: Callable[..., None],
    project_record_to_payload: Callable[[Any], JsonObject],
    active_project_payload: Callable[[str, str], JsonObject],
    github_repo_to_payload: Callable[[Any], JsonObject],
) -> ActionResult:
    repo, error = resolve_github_repo(params)
    if error is not None:
        return error
    assert repo is not None

    destination = str(params.get("destination", "")).strip()
    destination_root_raw = str(params.get("destination_root", "")).strip()
    branch = str(params.get("branch", "")).strip() or repo.default_branch
    depth = params.get("depth")

    destination_path: Path
    if destination:
        try:
            resolved_destination = resolve_local_path(destination, must_exist=False)
        except TypeError:
            resolved_destination = resolve_local_path(destination)
        if resolved_destination is None:
            return ActionResult(success=False, message="Destino invalido para o clone.", error="invalid destination")
        destination_path = resolved_destination
    else:
        if destination_root_raw:
            try:
                clone_root = resolve_local_path(destination_root_raw, must_exist=False)
            except TypeError:
                clone_root = resolve_local_path(destination_root_raw)
        else:
            clone_root = github_default_clone_root()
        if clone_root is None:
            return ActionResult(success=False, message="Pasta base invalida para clonar o repositorio.", error="invalid destination root")
        clone_root.mkdir(parents=True, exist_ok=True)
        destination_path = clone_root / repo.name

    clone_result = await git_clone_repository(
        {
            "repository_url": repo.clone_url,
            "destination": str(destination_path),
            "branch": branch,
            "depth": depth,
        },
        ctx,
    )
    if not clone_result.success:
        clone_data = dict(clone_result.data or {})
        clone_data["github_repo"] = github_repo_to_payload(repo)
        clone_result.data = clone_data
        return clone_result

    record = get_project_catalog().create_or_update_project(
        root_path=destination_path,
        name=repo.name,
        aliases=[repo.full_name, repo.owner],
        priority_score=20,
    )
    index_status = ensure_project_index(record)
    set_active_project_from_record(record, ctx, selection_reason=repo.full_name, index_status=index_status)

    return ActionResult(
        success=True,
        message=f"Repositorio {repo.full_name} clonado e registrado no catalogo.",
        data={
            "github_repo": github_repo_to_payload(repo),
            "project": project_record_to_payload(record),
            **active_project_payload(ctx.participant_identity, ctx.room),
        },
    )


async def project_list_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    get_project_catalog: Callable[[], Any],
    project_record_to_payload: Callable[[Any], JsonObject],
    active_project_payload: Callable[[str, str], JsonObject],
    capability_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    include_inactive = bool(params.get("include_inactive", False))
    projects = get_project_catalog().list_projects(include_inactive=include_inactive)
    return ActionResult(
        success=True,
        message=f"{len(projects)} projeto(s) no catalogo.",
        data={
            "projects": [project_record_to_payload(item) for item in projects],
            **active_project_payload(ctx.participant_identity, ctx.room),
            **capability_payload(ctx.participant_identity, ctx.room),
        },
    )


async def project_scan_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    get_project_catalog: Callable[[], Any],
    project_record_to_payload: Callable[[Any], JsonObject],
    active_project_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    _ = params
    discovered = get_project_catalog().scan()
    return ActionResult(
        success=True,
        message=f"Scan finalizado. {len(discovered)} projeto(s) detectado(s).",
        data={
            "projects": [project_record_to_payload(item) for item in discovered],
            "catalog_size": len(get_project_catalog().list_projects(include_inactive=True)),
            **active_project_payload(ctx.participant_identity, ctx.room),
        },
    )


async def project_update_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    get_project_catalog: Callable[[], Any],
    get_active_project: Callable[[str, str], Any | None],
    clear_active_project: Callable[[str, str], None],
    set_active_project_from_record: Callable[..., None],
    project_record_to_payload: Callable[[Any], JsonObject],
    active_project_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    project_id = str(params.get("project_id", "")).strip()
    if not project_id:
        return ActionResult(success=False, message="Informe o project_id para atualizar.", error="missing project_id")

    catalog = get_project_catalog()
    record = catalog.get_project(project_id)
    if record is None:
        return ActionResult(success=False, message="Projeto nao encontrado para atualizacao.", error="unknown project")

    updated = False
    if "name" in params:
        name = str(params.get("name", "")).strip()
        if name:
            catalog.rename_project(project_id, name)
            updated = True
    if "aliases" in params:
        aliases = params.get("aliases", [])
        if isinstance(aliases, list):
            catalog.set_aliases(project_id, [str(item) for item in aliases if str(item).strip()])
            updated = True
    if "priority_score" in params:
        catalog.set_priority(project_id, int(params.get("priority_score", 0) or 0))
        updated = True
    if "is_active" in params:
        catalog.set_active(project_id, is_active=bool(params.get("is_active")))
        updated = True

    refreshed = catalog.get_project(project_id)
    if refreshed is None:
        return ActionResult(success=False, message="Projeto indisponivel apos atualizacao.", error="project missing after update")

    if not refreshed.is_active:
        active = get_active_project(ctx.participant_identity, ctx.room)
        if active and active.project_id == project_id:
            clear_active_project(ctx.participant_identity, ctx.room)
    else:
        active = get_active_project(ctx.participant_identity, ctx.room)
        if active and active.project_id == project_id:
            set_active_project_from_record(refreshed, ctx, selection_reason="project_update", index_status=active.index_status)

    return ActionResult(
        success=True,
        message="Projeto atualizado no catalogo." if updated else "Nenhuma mudanca aplicada ao projeto.",
        data={
            "project": project_record_to_payload(refreshed),
            **active_project_payload(ctx.participant_identity, ctx.room),
        },
    )


async def project_remove_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    get_project_catalog: Callable[[], Any],
    get_active_project: Callable[[str, str], Any | None],
    clear_active_project: Callable[[str, str], None],
    project_record_to_payload: Callable[[Any], JsonObject],
    active_project_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    project_id = str(params.get("project_id", "")).strip()
    if not project_id:
        return ActionResult(success=False, message="Informe o project_id para remover.", error="missing project_id")
    removed = get_project_catalog().remove_project(project_id)
    if removed is None:
        return ActionResult(success=False, message="Projeto nao encontrado para remocao.", error="unknown project")
    active = get_active_project(ctx.participant_identity, ctx.room)
    if active and active.project_id == project_id:
        clear_active_project(ctx.participant_identity, ctx.room)
    return ActionResult(
        success=True,
        message=f"Projeto {removed.name} removido do catalogo.",
        data={
            "removed_project": project_record_to_payload(removed),
            **active_project_payload(ctx.participant_identity, ctx.room),
        },
    )


async def project_select_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    resolve_project_record: Callable[[JsonObject, ActionContext], tuple[Any | None, ActionResult | None]],
    get_active_project: Callable[[str, str], Any | None],
    project_record_to_payload: Callable[[Any], JsonObject],
    active_project_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    record, error = resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None
    active = get_active_project(ctx.participant_identity, ctx.room)
    return ActionResult(
        success=True,
        message=f"Projeto ativo definido para {record.name}.",
        data={
            "selected_project": project_record_to_payload(record),
            **active_project_payload(ctx.participant_identity, ctx.room),
            "active_project": {
                **(active_project_payload(ctx.participant_identity, ctx.room).get("active_project") or {}),
                "index_status": active.index_status if active else "unknown",
            },
        },
    )


async def project_get_active_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    get_active_project: Callable[[str, str], Any | None],
    active_project_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    _ = params
    active = get_active_project(ctx.participant_identity, ctx.room)
    if active is None:
        return ActionResult(
            success=False,
            message="Nenhum projeto ativo na sessao.",
            data=active_project_payload(ctx.participant_identity, ctx.room),
            error="no active project",
        )
    return ActionResult(
        success=True,
        message=f"Projeto ativo: {active.name}.",
        data={**active_project_payload(ctx.participant_identity, ctx.room)},
    )


async def project_clear_active_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    clear_active_project: Callable[[str, str], None],
    active_project_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    _ = params
    clear_active_project(ctx.participant_identity, ctx.room)
    return ActionResult(
        success=True,
        message="Projeto ativo removido da sessao.",
        data={**active_project_payload(ctx.participant_identity, ctx.room)},
    )


async def project_refresh_index_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    resolve_project_record: Callable[[JsonObject, ActionContext], tuple[Any | None, ActionResult | None]],
    get_code_index: Callable[[], Any],
    get_project_catalog: Callable[[], Any],
    set_active_project_from_record: Callable[..., None],
    project_record_to_payload: Callable[[Any], JsonObject],
    active_project_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    record, error = resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None
    root = Path(record.root_path).resolve(strict=False)
    if not root.exists():
        return ActionResult(success=False, message="A raiz do projeto nao existe.", error="missing project root")
    summary = get_code_index().index_project(record.project_id, root, project_name=record.name, aliases=record.aliases)
    get_project_catalog().update_last_indexed(record.project_id)
    set_active_project_from_record(record, ctx, selection_reason="refresh_index", index_status="reindexed")
    return ActionResult(
        success=True,
        message=f"Indice atualizado para {record.name}.",
        data={
            "project": project_record_to_payload(record),
            "ingest_summary": summary,
            "knowledge_stats": get_code_index().stats(project_id=record.project_id),
            **active_project_payload(ctx.participant_identity, ctx.room),
        },
    )


async def project_search_action(
    params: JsonObject,
    ctx: ActionContext,
    *,
    resolve_project_record: Callable[[JsonObject, ActionContext], tuple[Any | None, ActionResult | None]],
    get_code_index: Callable[[], Any],
    project_record_to_payload: Callable[[Any], JsonObject],
    active_project_payload: Callable[[str, str], JsonObject],
) -> ActionResult:
    query = str(params.get("query", "")).strip()
    limit = int(params.get("limit", 5))
    if not query:
        return ActionResult(success=False, message="Informe o que devo procurar no projeto.", error="missing query")
    record, error = resolve_project_record(params, ctx)
    if error is not None:
        return error
    assert record is not None
    results = get_code_index().search(query, limit=limit, project_id=record.project_id)
    if not results:
        return ActionResult(
            success=False,
            message=f"Nao encontrei trechos para '{query}' em {record.name}.",
            data={"query": query, "project": project_record_to_payload(record), **active_project_payload(ctx.participant_identity, ctx.room)},
            error="not found",
        )
    return ActionResult(
        success=True,
        message=f"Encontrei {len(results)} trecho(s) em {record.name}.",
        data={
            "query": query,
            "project": project_record_to_payload(record),
            "results": results,
            **active_project_payload(ctx.participant_identity, ctx.room),
        },
    )
