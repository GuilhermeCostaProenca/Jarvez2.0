from __future__ import annotations

from datetime import datetime, timezone

from .mcp_client import PlaywrightMcpClient
from .policies import normalize_allowed_domains, validate_browser_request
from .state import BrowserTaskState


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_browser_task(
    *,
    task_id: str,
    request: str,
    allowed_domains: list[object] | None,
    read_only: bool,
    mcp_url: str,
) -> tuple[BrowserTaskState, bool, str | None]:
    normalized_domains = normalize_allowed_domains(allowed_domains)
    validation_error = validate_browser_request(request, normalized_domains)
    if validation_error is not None:
        return (
            BrowserTaskState(
                task_id=task_id,
                status="failed",
                request=request,
                allowed_domains=normalized_domains,
                read_only=read_only,
                summary=validation_error,
                error="invalid_request",
                started_at=_now_iso(),
                finished_at=_now_iso(),
            ),
            False,
            "invalid_request",
        )

    client = PlaywrightMcpClient(mcp_url)
    health = client.healthcheck()
    if not health.ok:
        return (
            BrowserTaskState(
                task_id=task_id,
                status="failed",
                request=request,
                allowed_domains=normalized_domains,
                read_only=read_only,
                summary="Browser agent indisponivel.",
                error=health.detail or health.status,
                started_at=_now_iso(),
                finished_at=_now_iso(),
            ),
            False,
            "browser_agent_not_configured",
        )

    return (
        BrowserTaskState(
            task_id=task_id,
            status="running",
            request=request,
            allowed_domains=normalized_domains,
            read_only=read_only,
            summary="Browser agent enfileirado para execucao via MCP.",
            started_at=_now_iso(),
        ),
        True,
        None,
    )
