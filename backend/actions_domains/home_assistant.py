from __future__ import annotations

import subprocess
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from actions_core import ActionContext, ActionResult

JsonObject = dict[str, Any]


async def open_desktop_resource(
    params: JsonObject,
    ctx: ActionContext,
    *,
    resolve_open_resource_target: Callable[[str, str], tuple[str | None, Any, str | None]],
    open_browser: Callable[[str], bool],
    has_startfile: bool,
    startfile: Callable[[str], None],
    launch_detached: Callable[[list[str]], None] | Callable[[list[str], Path | None], None],
    workspace_root: Callable[[], Path],
) -> ActionResult:
    _ = ctx
    target = str(params.get("target", "")).strip()
    target_kind = str(params.get("target_kind", "auto")).strip().casefold() or "auto"
    if not target:
        return ActionResult(success=False, message="Informe o recurso que devo abrir.", error="missing target")

    resolved_kind, resolved_value, resolution_error = resolve_open_resource_target(target, target_kind)
    if resolved_kind is None:
        return ActionResult(success=False, message=resolution_error or "Nao consegui abrir o recurso.", error="invalid target")

    try:
        if resolved_kind == "url":
            opened = open_browser(str(resolved_value))
            if not opened:
                return ActionResult(success=False, message="O navegador nao aceitou abrir o link.", error="browser open failed")
        elif resolved_kind == "path":
            if not has_startfile:
                return ActionResult(
                    success=False,
                    message="Abrir arquivos/pastas so esta disponivel no Windows.",
                    error="startfile unavailable",
                )
            startfile(str(resolved_value))
        else:
            try:
                launch_detached(list(resolved_value), cwd=workspace_root())
            except TypeError:
                launch_detached(list(resolved_value))
    except OSError as error:
        return ActionResult(success=False, message=f"Falha ao abrir o recurso: {error}", error=str(error))

    return ActionResult(
        success=True,
        message=f"Recurso aberto: {target}.",
        data={
            "target": target,
            "resolved_target": str(resolved_value),
            "target_kind": resolved_kind,
        },
    )


async def run_local_command(
    params: JsonObject,
    ctx: ActionContext,
    *,
    resolve_local_command: Callable[[str], tuple[str | None, str | None]],
    resolve_local_path: Callable[[str], Path | None] | Callable[[str, bool], Path | None],
    workspace_root: Callable[[], Path],
    launch_detached: Callable[[list[str], Path | None], None] | Callable[[list[str]], None],
    trim_process_output: Callable[[str], str] | Callable[[str, int], str],
    run_process: Callable[..., subprocess.CompletedProcess[str]],
) -> ActionResult:
    _ = ctx
    command = str(params.get("command", "")).strip()
    arguments = params.get("arguments", [])
    working_directory = str(params.get("working_directory", "")).strip()
    wait_for_exit = bool(params.get("wait_for_exit", True))
    timeout_seconds = int(params.get("timeout_seconds", 60))

    if not isinstance(arguments, list) or any(not isinstance(item, str) for item in arguments):
        return ActionResult(success=False, message="`arguments` precisa ser uma lista de textos.", error="invalid arguments")

    resolved_command, command_error = resolve_local_command(command)
    if resolved_command is None:
        return ActionResult(success=False, message=command_error or "Comando nao permitido.", error="command blocked")

    if working_directory:
        try:
            cwd = resolve_local_path(working_directory, must_exist=True)
        except TypeError:
            cwd = resolve_local_path(working_directory)
        if cwd is None or not cwd.is_dir():
            return ActionResult(success=False, message="Diretorio de trabalho nao encontrado.", error="invalid working directory")
    else:
        cwd = workspace_root()

    command_line = [resolved_command, *arguments]

    try:
        if not wait_for_exit:
            try:
                launch_detached(command_line, cwd=cwd)
            except TypeError:
                launch_detached(command_line)
            return ActionResult(
                success=True,
                message="Comando iniciado em segundo plano.",
                data={
                    "command_line": command_line,
                    "working_directory": str(cwd),
                    "wait_for_exit": False,
                },
            )

        completed = run_process(
            command_line,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=max(1, min(timeout_seconds, 600)),
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return ActionResult(success=False, message=f"Falha ao executar o comando: {error}", error=str(error))

    stdout = trim_process_output(completed.stdout or "")
    stderr = trim_process_output(completed.stderr or "")
    success = completed.returncode == 0
    return ActionResult(
        success=success,
        message="Comando executado com sucesso." if success else "O comando terminou com erro.",
        data={
            "command_line": command_line,
            "working_directory": str(cwd),
            "returncode": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "wait_for_exit": True,
        },
        error=None if success else stderr or f"exit code {completed.returncode}",
    )


async def git_clone_repository(
    params: JsonObject,
    ctx: ActionContext,
    *,
    resolve_local_path: Callable[[str], Path | None] | Callable[[str, bool], Path | None],
    workspace_root: Callable[[], Path],
    trim_process_output: Callable[[str], str] | Callable[[str, int], str],
    run_process: Callable[..., subprocess.CompletedProcess[str]],
) -> ActionResult:
    _ = ctx
    repository_url = str(params.get("repository_url", "")).strip()
    destination = str(params.get("destination", "")).strip()
    branch = str(params.get("branch", "")).strip()
    depth = params.get("depth")

    if not repository_url:
        return ActionResult(success=False, message="Informe a URL do repositorio.", error="missing repository url")

    destination_path: Path | None = None
    if destination:
        try:
            destination_path = resolve_local_path(destination, must_exist=False)
        except TypeError:
            destination_path = resolve_local_path(destination)
        if destination_path is None:
            return ActionResult(success=False, message="Destino invalido.", error="invalid destination")
        if destination_path.exists():
            return ActionResult(success=False, message="O destino informado ja existe.", error="destination exists")
        destination_path.parent.mkdir(parents=True, exist_ok=True)

    command_line = ["git", "clone"]
    if branch:
        command_line.extend(["--branch", branch])
    if isinstance(depth, int) and depth > 0:
        command_line.extend(["--depth", str(depth)])
    command_line.append(repository_url)
    if destination_path is not None:
        command_line.append(str(destination_path))

    try:
        completed = run_process(
            command_line,
            cwd=str(workspace_root()),
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return ActionResult(success=False, message=f"Falha ao executar git clone: {error}", error=str(error))

    stdout = trim_process_output(completed.stdout or "")
    stderr = trim_process_output(completed.stderr or "")
    if completed.returncode != 0:
        return ActionResult(
            success=False,
            message="O git clone falhou.",
            data={
                "command_line": command_line,
                "stdout": stdout,
                "stderr": stderr,
                "returncode": completed.returncode,
            },
            error=stderr or f"exit code {completed.returncode}",
        )

    return ActionResult(
        success=True,
        message="Repositorio clonado com sucesso.",
        data={
            "command_line": command_line,
            "destination": str(destination_path) if destination_path is not None else str(workspace_root()),
            "stdout": stdout,
            "stderr": stderr,
            "returncode": completed.returncode,
        },
    )


async def turn_light_on(
    params: JsonObject,
    ctx: ActionContext,
    *,
    call_service: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
) -> ActionResult:
    entity_id = str(params["entity_id"])
    return await call_service(
        {
            "domain": "light",
            "service": "turn_on",
            "service_data": {"entity_id": entity_id},
        },
        ctx,
    )


async def turn_light_off(
    params: JsonObject,
    ctx: ActionContext,
    *,
    call_service: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
) -> ActionResult:
    entity_id = str(params["entity_id"])
    return await call_service(
        {
            "domain": "light",
            "service": "turn_off",
            "service_data": {"entity_id": entity_id},
        },
        ctx,
    )


async def set_light_brightness(
    params: JsonObject,
    ctx: ActionContext,
    *,
    call_service: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
) -> ActionResult:
    entity_id = str(params["entity_id"])
    brightness = int(params["brightness"])
    return await call_service(
        {
            "domain": "light",
            "service": "turn_on",
            "service_data": {"entity_id": entity_id, "brightness": brightness},
        },
        ctx,
    )


async def call_service(
    params: JsonObject,
    ctx: ActionContext,
    *,
    is_allowed_service: Callable[[str, str], bool],
    call_home_assistant: Callable[[str, str, JsonObject], ActionResult] | Callable[..., ActionResult],
) -> ActionResult:
    _ = ctx
    domain = str(params["domain"]).strip().lower()
    service = str(params["service"]).strip().lower()
    service_data = params.get("service_data")

    if not isinstance(service_data, dict):
        return ActionResult(success=False, message="service_data invalido.", error="service_data must be object")

    if not is_allowed_service(domain, service):
        return ActionResult(
            success=False,
            message=f"Servico nao permitido: {domain}.{service}.",
            error="service not in allowlist",
        )

    return call_home_assistant(domain=domain, service=service, service_data=service_data)
