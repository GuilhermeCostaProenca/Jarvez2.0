from __future__ import annotations

from datetime import datetime, timezone
import re
from collections.abc import Callable
from urllib.parse import urlparse

from .mcp_client import PlaywrightMcpClient
from .policies import normalize_allowed_domains, validate_browser_request
from .state import BrowserTaskState


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_host_allowed(host: str, allowed_domains: list[str]) -> bool:
    normalized_host = host.strip().lower()
    if not normalized_host:
        return False
    for allowed in allowed_domains:
        domain = allowed.strip().lower()
        if not domain:
            continue
        if normalized_host == domain or normalized_host.endswith(f".{domain}"):
            return True
    return False


def _extract_target_url(request: str, allowed_domains: list[str]) -> tuple[str | None, str | None]:
    matches = re.findall(r"https?://[^\s)]+", request)
    if matches:
        target_url = matches[0].strip()
        host = urlparse(target_url).netloc.strip().lower()
        if not _is_host_allowed(host, allowed_domains):
            return None, "target_domain_not_allowed"
        return target_url, None
    request_lower = request.lower()
    for domain in allowed_domains:
        if domain in request_lower:
            return f"https://{domain}", None
    if not allowed_domains:
        return None, "missing_allowed_domains"
    return f"https://{allowed_domains[0]}", None


def _summarize_snapshot(text: str, fallback_url: str) -> str:
    page_url = PlaywrightMcpClient.extract_page_url(text) or fallback_url
    page_title = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("- page title:"):
            page_title = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
            break
    if page_title:
        return f"Navegacao concluida em {page_url} ({page_title})."
    return f"Navegacao concluida em {page_url}."


def run_browser_task(
    *,
    task_id: str,
    request: str,
    allowed_domains: list[object] | None,
    read_only: bool,
    mcp_url: str,
    is_cancel_requested: Callable[[], bool] | None = None,
) -> tuple[BrowserTaskState, bool, str | None]:
    def _cancelled_state(summary: str) -> tuple[BrowserTaskState, bool, str | None]:
        return (
            BrowserTaskState(
                task_id=task_id,
                status="cancelled",
                request=request,
                allowed_domains=normalized_domains,
                read_only=read_only,
                summary=summary,
                error="cancelled_by_user",
                started_at=_now_iso(),
                finished_at=_now_iso(),
            ),
            False,
            "cancelled_by_user",
        )

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

    target_url, target_error = _extract_target_url(request, normalized_domains)
    if target_error is not None or not target_url:
        return (
            BrowserTaskState(
                task_id=task_id,
                status="failed",
                request=request,
                allowed_domains=normalized_domains,
                read_only=read_only,
                summary="URL alvo fora do allowlist ou ausente.",
                error=target_error or "target_url_invalid",
                started_at=_now_iso(),
                finished_at=_now_iso(),
            ),
            False,
            target_error or "target_url_invalid",
        )

    client = PlaywrightMcpClient(mcp_url)
    if callable(is_cancel_requested) and is_cancel_requested():
        return _cancelled_state("Cancelada antes de iniciar chamadas MCP.")
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
                evidence={
                    "health_status": health.status,
                    "mcp_url_configured": bool(mcp_url),
                    "mode": "run",
                },
            ),
            False,
            "browser_agent_not_configured",
        )

    navigate_call = client.call_tool("browser_navigate", {"url": target_url})
    if callable(is_cancel_requested) and is_cancel_requested():
        return _cancelled_state("Cancelada apos navegacao inicial.")
    if not navigate_call.ok:
        return (
            BrowserTaskState(
                task_id=task_id,
                status="failed",
                request=request,
                allowed_domains=normalized_domains,
                read_only=read_only,
                summary="Falha ao navegar com o browser agent.",
                error=navigate_call.detail or navigate_call.status,
                started_at=_now_iso(),
                finished_at=_now_iso(),
                evidence={
                    "target_url": target_url,
                    "health_status": health.status,
                    "tools_available": health.tools or [],
                    "navigate_status": navigate_call.status,
                },
            ),
            False,
            "browser_navigation_failed",
        )

    snapshot_call = client.call_tool("browser_snapshot", {})
    if callable(is_cancel_requested) and is_cancel_requested():
        return _cancelled_state("Cancelada antes de consolidar snapshot.")
    if not snapshot_call.ok:
        return (
            BrowserTaskState(
                task_id=task_id,
                status="failed",
                request=request,
                allowed_domains=normalized_domains,
                read_only=read_only,
                summary="Falha ao capturar snapshot apos navegacao.",
                error=snapshot_call.detail or snapshot_call.status,
                started_at=_now_iso(),
                finished_at=_now_iso(),
                evidence={
                    "target_url": target_url,
                    "health_status": health.status,
                    "tools_available": health.tools or [],
                    "navigate_status": navigate_call.status,
                    "snapshot_status": snapshot_call.status,
                },
            ),
            False,
            "browser_snapshot_failed",
        )

    snapshot_text = PlaywrightMcpClient.extract_text(snapshot_call.result)
    resolved_page_url = PlaywrightMcpClient.extract_page_url(snapshot_text) or target_url
    page_host = urlparse(resolved_page_url).netloc.strip().lower()
    if not _is_host_allowed(page_host, normalized_domains):
        return (
            BrowserTaskState(
                task_id=task_id,
                status="failed",
                request=request,
                allowed_domains=normalized_domains,
                read_only=read_only,
                summary="Navegacao bloqueada: pagina final fora do allowlist.",
                error="resolved_domain_not_allowed",
                started_at=_now_iso(),
                finished_at=_now_iso(),
                evidence={
                    "target_url": target_url,
                    "resolved_page_url": resolved_page_url,
                    "allowed_domains": normalized_domains,
                },
            ),
            False,
            "resolved_domain_not_allowed",
        )

    screenshot_taken = False
    request_lower = request.lower()
    if (
        "screenshot" in request_lower
        or "captura" in request_lower
        or "print" in request_lower
        or "evidencia visual" in request_lower
    ):
        screenshot_call = client.call_tool("browser_take_screenshot", {"type": "png", "fullPage": True})
        screenshot_taken = screenshot_call.ok

    summary = _summarize_snapshot(snapshot_text, resolved_page_url)
    return (
        BrowserTaskState(
            task_id=task_id,
            status="completed",
            request=request,
            allowed_domains=normalized_domains,
            read_only=read_only,
            summary=summary,
            started_at=_now_iso(),
            finished_at=_now_iso(),
            evidence={
                "health_status": health.status,
                "mcp_url_configured": True,
                "mode": "execution",
                "read_only": read_only,
                "allowed_domains": normalized_domains,
                "tools_available": health.tools or [],
                "target_url": target_url,
                "resolved_page_url": resolved_page_url,
                "navigate_excerpt": PlaywrightMcpClient.extract_text(navigate_call.result)[:1200],
                "snapshot_excerpt": snapshot_text[:2000],
                "screenshot_taken": screenshot_taken,
            },
        ),
        True,
        None,
    )
