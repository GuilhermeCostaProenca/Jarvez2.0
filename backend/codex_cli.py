from __future__ import annotations

import asyncio
import json
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable


JsonObject = dict[str, Any]
ProgressCallback = Callable[[JsonObject], Awaitable[None]]


def _candidate_codex_paths() -> list[Path]:
    configured = os.getenv("CODEX_CLI_PATH", "").strip()
    candidates: list[Path] = []
    if configured:
        candidates.append(Path(configured).expanduser())

    home = Path.home()
    extension_root = home / ".vscode" / "extensions"
    if extension_root.exists():
        for entry in sorted(extension_root.glob("openai.chatgpt-*/bin/windows-x86_64/codex.exe")):
            candidates.append(entry)
    return candidates


def get_codex_executable() -> str | None:
    direct = shutil.which("codex")
    if direct:
        return direct

    for candidate in _candidate_codex_paths():
        if candidate.exists():
            return str(candidate)
    return None


def is_codex_available() -> bool:
    return get_codex_executable() is not None


def build_exec_command(
    *,
    prompt: str,
    working_directory: str | Path,
    sandbox_mode: str = "read-only",
    ephemeral: bool = True,
) -> list[str]:
    executable = get_codex_executable()
    if executable is None:
        raise FileNotFoundError("codex executable not found")

    command = [
        executable,
        "exec",
        "--json",
        "--skip-git-repo-check",
        "--sandbox",
        sandbox_mode,
        "-C",
        str(working_directory),
        prompt,
    ]
    if ephemeral:
        command.insert(6, "--ephemeral")
    return command


def _extract_message(payload: JsonObject) -> str | None:
    for key in ("message", "summary", "text", "content", "delta"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    item = payload.get("item")
    if isinstance(item, dict):
        for key in ("text", "content", "summary"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return None


def parse_json_line(raw_line: str) -> JsonObject | None:
    line = raw_line.strip()
    if not line:
        return None
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


@dataclass(slots=True)
class CodexRunResult:
    success: bool
    exit_code: int
    summary: str
    last_event: JsonObject | None
    events: list[JsonObject] = field(default_factory=list)
    command_line: list[str] = field(default_factory=list)
    stderr: str = ""


async def run_exec_streaming(
    *,
    prompt: str,
    working_directory: str | Path,
    sandbox_mode: str = "read-only",
    ephemeral: bool = True,
    on_progress: ProgressCallback | None = None,
    process_registry: dict[str, asyncio.subprocess.Process] | None = None,
    registry_key: str | None = None,
) -> CodexRunResult:
    command_line = build_exec_command(
        prompt=prompt,
        working_directory=working_directory,
        sandbox_mode=sandbox_mode,
        ephemeral=ephemeral,
    )
    process = await asyncio.create_subprocess_exec(
        *command_line,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    if process_registry is not None and registry_key:
        process_registry[registry_key] = process

    events: list[JsonObject] = []
    stderr_chunks: list[str] = []
    last_event: JsonObject | None = None
    last_message = ""

    async def consume_stdout() -> None:
        nonlocal last_event, last_message
        assert process.stdout is not None
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            text = line.decode("utf-8", errors="replace").strip()
            if not text:
                continue

            parsed = parse_json_line(text)
            event = parsed or {"type": "raw_output", "message": text}
            if not parsed:
                event["raw_line"] = text

            events.append(event)
            last_event = event
            message = _extract_message(event)
            if message:
                last_message = message
            if on_progress is not None:
                await on_progress(event)

    async def consume_stderr() -> None:
        assert process.stderr is not None
        while True:
            line = await process.stderr.readline()
            if not line:
                break
            stderr_chunks.append(line.decode("utf-8", errors="replace"))

    await asyncio.gather(consume_stdout(), consume_stderr())
    exit_code = await process.wait()

    if process_registry is not None and registry_key:
        process_registry.pop(registry_key, None)

    stderr_text = "".join(stderr_chunks).strip()
    success = exit_code == 0
    summary = last_message or (stderr_text[:400] if stderr_text else "")
    if not summary:
        summary = "Tarefa concluida." if success else "A tarefa falhou sem resumo."

    return CodexRunResult(
        success=success,
        exit_code=exit_code,
        summary=summary,
        last_event=last_event,
        events=events,
        command_line=command_line,
        stderr=stderr_text,
    )
