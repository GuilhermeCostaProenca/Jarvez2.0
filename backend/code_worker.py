from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from code_knowledge import IGNORED_DIR_NAMES, SUPPORTED_CODE_EXTENSIONS
from project_catalog import ProjectCatalog

logger = logging.getLogger("jarvez.code_worker")


def _worker_token() -> str:
    return os.getenv("CODE_WORKER_TOKEN", "jarvez-local-worker").strip() or "jarvez-local-worker"


def _worker_host() -> str:
    return os.getenv("CODE_WORKER_HOST", "127.0.0.1").strip() or "127.0.0.1"


def _worker_port() -> int:
    raw = os.getenv("CODE_WORKER_PORT", "8765").strip()
    try:
        return max(1024, min(65535, int(raw)))
    except ValueError:
        return 8765


def _max_response_chars() -> int:
    raw = os.getenv("CODE_WORKER_MAX_RESPONSE_CHARS", "12000").strip()
    try:
        return max(1000, min(50000, int(raw)))
    except ValueError:
        return 12000


def _command_allowlist() -> list[list[str]]:
    return [
        ["git", "status"],
        ["git", "diff"],
        ["git", "branch"],
        ["git", "log", "--oneline"],
        ["pytest"],
        ["python", "-m", "pytest"],
        ["npm", "test"],
        ["pnpm", "test"],
        ["pnpm", "lint"],
        ["pnpm", "build"],
        ["npm", "run", "build"],
        ["tsc", "--noEmit"],
    ]


def _truncate(value: str, limit: int | None = None) -> str:
    max_chars = limit or _max_response_chars()
    text = value.strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def _catalog() -> ProjectCatalog:
    return ProjectCatalog()


def _project_root(project_id: str) -> tuple[Path | None, dict[str, Any] | None]:
    record = _catalog().get_project(project_id)
    if record is None or not record.is_active:
        return None, None
    root = Path(record.root_path).resolve(strict=False)
    if not root.exists() or not root.is_dir():
        return None, None
    return root, record.to_json()


def _resolve_within_project(project_root: Path, requested_path: str) -> Path:
    candidate = Path(os.path.expandvars(requested_path.strip())).expanduser()
    if not candidate.is_absolute():
        candidate = project_root / candidate
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(project_root)
    except ValueError as error:
        raise PermissionError("path escapes project root") from error
    return resolved


def _search_files(project_root: Path, query: str, limit: int) -> list[dict[str, Any]]:
    needle = query.strip()
    if not needle:
        return []
    lowered = needle.casefold()
    results: list[dict[str, Any]] = []
    for path in project_root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SUPPORTED_CODE_EXTENSIONS:
            continue
        if any(part in IGNORED_DIR_NAMES for part in path.parts):
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if lowered not in content.casefold():
            continue
        snippet = _truncate(content, 800)
        results.append(
            {
                "path": str(path.resolve(strict=False)),
                "relative_path": str(path.resolve(strict=False).relative_to(project_root)),
                "content": snippet,
            }
        )
        if len(results) >= limit:
            break
    return results


def _run_process(command_line: list[str], *, cwd: Path, timeout_seconds: int) -> dict[str, Any]:
    completed = subprocess.run(
        command_line,
        cwd=str(cwd),
        shell=False,
        capture_output=True,
        text=True,
        timeout=max(1, min(timeout_seconds, 600)),
        check=False,
    )
    stdout = _truncate(completed.stdout or "")
    stderr = _truncate(completed.stderr or "")
    return {
        "returncode": completed.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "success": completed.returncode == 0,
    }


def _is_allowed_command(command_line: list[str]) -> bool:
    lowered = [part.casefold() for part in command_line]
    for allowed in _command_allowlist():
        if lowered[: len(allowed)] == [part.casefold() for part in allowed]:
            return True
    return False


class _Handler(BaseHTTPRequestHandler):
    server_version = "JarvezCodeWorker/1.0"

    def _write_json(self, status: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _read_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except Exception:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _authenticate(self) -> bool:
        if self.headers.get("X-Code-Worker-Token", "") == _worker_token():
            return True
        self._write_json(
            HTTPStatus.UNAUTHORIZED,
            {"success": False, "message": "Worker token invalido.", "error": "unauthorized"},
        )
        return False

    def do_GET(self) -> None:  # noqa: N802
        if not self._authenticate():
            return
        if self.path == "/health":
            self._write_json(
                HTTPStatus.OK,
                {"success": True, "message": "Code worker online.", "data": {"allowlist": _command_allowlist()}},
            )
            return
        self._write_json(HTTPStatus.NOT_FOUND, {"success": False, "message": "Endpoint nao encontrado."})

    def do_POST(self) -> None:  # noqa: N802
        if not self._authenticate():
            return

        body = self._read_body()
        project_id = str(body.get("project_id", "")).strip()
        root, record = _project_root(project_id)
        if root is None or record is None:
            self._write_json(
                HTTPStatus.BAD_REQUEST,
                {"success": False, "message": "Projeto invalido ou inativo.", "error": "invalid project"},
            )
            return

        try:
            if self.path == "/read-file":
                self._handle_read_file(root, body)
                return
            if self.path == "/search-files":
                self._handle_search_files(root, body)
                return
            if self.path == "/git-status":
                self._handle_git_status(root)
                return
            if self.path == "/git-diff":
                self._handle_git_diff(root, body)
                return
            if self.path == "/apply-patch":
                self._handle_apply_patch(root, body)
                return
            if self.path == "/run-command":
                self._handle_run_command(root, body)
                return
        except PermissionError as error:
            self._write_json(
                HTTPStatus.FORBIDDEN,
                {"success": False, "message": f"Acesso negado: {error}", "error": "forbidden"},
            )
            return
        except subprocess.TimeoutExpired:
            self._write_json(
                HTTPStatus.REQUEST_TIMEOUT,
                {"success": False, "message": "Comando excedeu o timeout.", "error": "timeout"},
            )
            return
        except Exception as error:  # pragma: no cover - defensive runtime guard
            logger.exception("code_worker_request_failed path=%s", self.path)
            self._write_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"success": False, "message": f"Falha no worker: {error}", "error": "internal"},
            )
            return

        self._write_json(HTTPStatus.NOT_FOUND, {"success": False, "message": "Endpoint nao encontrado."})

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        logger.info("code_worker " + format, *args)

    def _handle_read_file(self, project_root: Path, body: dict[str, Any]) -> None:
        path = _resolve_within_project(project_root, str(body.get("path", "")))
        if not path.exists() or not path.is_file():
            self._write_json(HTTPStatus.BAD_REQUEST, {"success": False, "message": "Arquivo nao encontrado."})
            return
        content = path.read_text(encoding="utf-8", errors="ignore")
        start_line = int(body.get("start_line", 1) or 1)
        end_line = int(body.get("end_line", 0) or 0)
        if start_line > 1 or end_line > 0:
            lines = content.splitlines()
            selected = lines[max(0, start_line - 1) : end_line or None]
            content = "\n".join(selected)
        self._write_json(
            HTTPStatus.OK,
            {
                "success": True,
                "message": "Arquivo lido com sucesso.",
                "data": {
                    "path": str(path),
                    "relative_path": str(path.relative_to(project_root)),
                    "content": _truncate(content),
                },
            },
        )

    def _handle_search_files(self, project_root: Path, body: dict[str, Any]) -> None:
        query = str(body.get("query", "")).strip()
        limit = int(body.get("limit", 5) or 5)
        results = _search_files(project_root, query, max(1, min(limit, 20)))
        self._write_json(
            HTTPStatus.OK,
            {
                "success": True,
                "message": f"Encontrei {len(results)} arquivo(s) com esse termo.",
                "data": {"results": results},
            },
        )

    def _handle_git_status(self, project_root: Path) -> None:
        result = _run_process(["git", "status", "--short", "--branch"], cwd=project_root, timeout_seconds=20)
        self._write_json(
            HTTPStatus.OK if result["success"] else HTTPStatus.BAD_REQUEST,
            {
                "success": bool(result["success"]),
                "message": "Status do git coletado." if result["success"] else "Falha ao consultar git status.",
                "data": result,
            },
        )

    def _handle_git_diff(self, project_root: Path, body: dict[str, Any]) -> None:
        paths = body.get("paths", [])
        command_line = ["git", "diff"]
        if isinstance(paths, list):
            clean_paths = []
            for item in paths:
                if not isinstance(item, str) or not item.strip():
                    continue
                resolved = _resolve_within_project(project_root, item)
                clean_paths.append(str(resolved.relative_to(project_root)))
            if clean_paths:
                command_line.extend(["--", *clean_paths])
        result = _run_process(command_line, cwd=project_root, timeout_seconds=20)
        self._write_json(
            HTTPStatus.OK if result["success"] else HTTPStatus.BAD_REQUEST,
            {
                "success": bool(result["success"]),
                "message": "Diff do git coletado." if result["success"] else "Falha ao consultar git diff.",
                "data": result,
            },
        )

    def _handle_apply_patch(self, project_root: Path, body: dict[str, Any]) -> None:
        changes = body.get("changes", [])
        if not isinstance(changes, list) or not changes:
            self._write_json(HTTPStatus.BAD_REQUEST, {"success": False, "message": "Nenhuma mudanca recebida."})
            return

        applied: list[dict[str, Any]] = []
        for change in changes:
            if not isinstance(change, dict):
                continue
            path = _resolve_within_project(project_root, str(change.get("path", "")))
            old_text = str(change.get("old_text", ""))
            new_text = str(change.get("new_text", ""))
            create_if_missing = bool(change.get("create_if_missing", False))

            if path.exists():
                original = path.read_text(encoding="utf-8", errors="ignore")
            elif create_if_missing:
                original = ""
                path.parent.mkdir(parents=True, exist_ok=True)
            else:
                self._write_json(
                    HTTPStatus.BAD_REQUEST,
                    {"success": False, "message": f"Arquivo nao existe: {path.relative_to(project_root)}"},
                )
                return

            if old_text:
                if old_text not in original:
                    self._write_json(
                        HTTPStatus.BAD_REQUEST,
                        {
                            "success": False,
                            "message": f"O trecho esperado nao foi encontrado em {path.relative_to(project_root)}.",
                            "error": "old text not found",
                        },
                    )
                    return
                updated = original.replace(old_text, new_text, 1)
            else:
                updated = new_text

            path.write_text(updated, encoding="utf-8")
            applied.append(
                {
                    "path": str(path),
                    "relative_path": str(path.relative_to(project_root)),
                    "chars_before": len(original),
                    "chars_after": len(updated),
                }
            )

        self._write_json(
            HTTPStatus.OK,
            {
                "success": True,
                "message": f"Patch aplicado em {len(applied)} arquivo(s).",
                "data": {"changes": applied},
            },
        )

    def _handle_run_command(self, project_root: Path, body: dict[str, Any]) -> None:
        command = str(body.get("command", "")).strip()
        arguments = body.get("arguments", [])
        if not command:
            self._write_json(HTTPStatus.BAD_REQUEST, {"success": False, "message": "Comando ausente."})
            return
        if not isinstance(arguments, list) or any(not isinstance(item, str) for item in arguments):
            self._write_json(HTTPStatus.BAD_REQUEST, {"success": False, "message": "`arguments` invalido."})
            return

        command_line = [command, *arguments]
        if not _is_allowed_command(command_line):
            self._write_json(
                HTTPStatus.FORBIDDEN,
                {"success": False, "message": "Comando fora da allowlist.", "error": "command blocked"},
            )
            return

        timeout_seconds = int(body.get("timeout_seconds", 60) or 60)
        result = _run_process(command_line, cwd=project_root, timeout_seconds=timeout_seconds)
        self._write_json(
            HTTPStatus.OK if result["success"] else HTTPStatus.BAD_REQUEST,
            {
                "success": bool(result["success"]),
                "message": "Comando executado." if result["success"] else "Comando terminou com erro.",
                "data": {
                    **result,
                    "command_line": command_line,
                },
            },
        )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    server = ThreadingHTTPServer((_worker_host(), _worker_port()), _Handler)
    logger.info("code worker listening on http://%s:%s", _worker_host(), _worker_port())
    server.serve_forever()


if __name__ == "__main__":
    main()
