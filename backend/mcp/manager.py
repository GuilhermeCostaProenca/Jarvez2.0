from __future__ import annotations

from datetime import datetime, timezone
import inspect
import logging
import time
from typing import Any, Awaitable, Callable

from actions_core import get_state_store
from .client import StdioMcpClient
from .registry import McpRegistry, create_default_mcp_registry
from .types import JsonObject, McpClientError, McpServerStatus, McpToolCallResult, McpToolInfo

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _truncate(value: Any, *, limit: int = 240) -> str:
    text = str(value or "")
    if len(text) <= limit:
        return text
    return f"{text[:limit - 3]}..."


def _redact_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return _truncate(value)
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    if isinstance(value, tuple):
        return [_redact_value(item) for item in value]
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key or "")
            lowered = key_text.casefold()
            if any(marker in lowered for marker in ("token", "secret", "password", "key", "authorization")):
                redacted[key_text] = "***REDACTED***"
            else:
                redacted[key_text] = _redact_value(item)
        return redacted
    return _truncate(value)


class McpManager:
    def __init__(self, registry: McpRegistry | None = None):
        self.registry = registry or create_default_mcp_registry()
        self._clients: dict[str, StdioMcpClient] = {}
        self._status: dict[str, McpServerStatus] = {
            config.name: McpServerStatus(
                server_name=config.name,
                enabled=config.enabled,
                process_active=False,
                legacy_fallback_enabled=config.legacy_fallback_enabled,
            )
            for config in self.registry.list_enabled_servers()
        }

    def _status_entry(self, server_name: str) -> McpServerStatus:
        config = self.registry.get_server(server_name)
        if server_name not in self._status:
            self._status[server_name] = McpServerStatus(
                server_name=server_name,
                enabled=config.enabled,
                process_active=False,
                legacy_fallback_enabled=config.legacy_fallback_enabled,
            )
        entry = self._status[server_name]
        entry.enabled = config.enabled
        entry.legacy_fallback_enabled = config.legacy_fallback_enabled
        return entry

    def _record_success(
        self,
        server_name: str,
        *,
        duration_ms: int | None = None,
        discovered_tools: list[str] | None = None,
        discovery: bool = False,
    ) -> None:
        entry = self._status_entry(server_name)
        entry.process_active = bool(self._clients.get(server_name) and self._clients[server_name].is_running)
        entry.last_success_at = _now_iso()
        entry.last_error_type = None
        entry.last_error_detail = None
        entry.last_response_ms = duration_ms
        client = self._clients.get(server_name)
        if client is not None:
            entry.env_keys = client.env_keys
            entry.env_preview = client.redacted_env
        if discovered_tools is not None:
            entry.discovered_tools = list(discovered_tools)
        if discovery:
            entry.last_discovery_at = entry.last_success_at

    def _record_failure(self, server_name: str, *, error_type: str, detail: str | None, duration_ms: int | None = None) -> None:
        entry = self._status_entry(server_name)
        entry.process_active = bool(self._clients.get(server_name) and self._clients[server_name].is_running)
        entry.last_failure_at = _now_iso()
        entry.last_error_type = error_type
        entry.last_error_detail = detail
        entry.last_response_ms = duration_ms
        client = self._clients.get(server_name)
        if client is not None:
            entry.env_keys = client.env_keys
            entry.env_preview = client.redacted_env

    def _append_audit_record(
        self,
        *,
        server_name: str,
        tool_name: str,
        success: bool,
        params: JsonObject | None,
        duration_ms: int,
        result: McpToolCallResult | None,
        fallback_used: bool,
        fallback_reason: str | None = None,
        error_type: str | None = None,
    ) -> None:
        summary = {
            "status": result.status if result is not None else ("fallback" if fallback_used else "unknown"),
            "ok": result.ok if result is not None else False,
            "detail": _truncate(result.detail) if result is not None and result.detail else None,
            "text": _truncate(result.text) if result is not None and result.text else None,
            "structured_content": _redact_value(result.structured_content) if result is not None else None,
        }
        try:
            get_state_store().append_mcp_call_audit(
                server_name=server_name,
                tool_name=tool_name,
                success=success,
                args_payload=_redact_value(params or {}),
                duration_ms=duration_ms,
                result_summary=_redact_value(summary),
                error_type=error_type,
                fallback_used=fallback_used,
                fallback_reason=fallback_reason,
            )
        except Exception:
            logger.warning("failed to persist mcp audit server=%s tool=%s", server_name, tool_name, exc_info=True)

    async def get_client(self, server_name: str) -> StdioMcpClient:
        config = self.registry.get_server(server_name)
        if not config.enabled:
            raise McpClientError("server_disabled", f"MCP server '{server_name}' is disabled.")
        client = self._clients.get(server_name)
        if client is None:
            client = StdioMcpClient(config)
            self._clients[server_name] = client
        started_at = time.perf_counter()
        try:
            await client.start()
        except McpClientError as exc:
            self._record_failure(
                server_name,
                error_type=exc.status,
                detail=exc.detail,
                duration_ms=int((time.perf_counter() - started_at) * 1000),
            )
            raise
        self._record_success(
            server_name,
            duration_ms=int((time.perf_counter() - started_at) * 1000),
        )
        return client

    async def stop_server(self, server_name: str) -> None:
        client = self._clients.pop(server_name, None)
        if client is not None:
            await client.stop()
        self._status_entry(server_name).process_active = False

    async def shutdown_all(self) -> None:
        for server_name in list(self._clients):
            await self.stop_server(server_name)

    async def list_tools(self, server_name: str) -> list[McpToolInfo]:
        client = await self.get_client(server_name)
        started_at = time.perf_counter()
        try:
            tools = await client.list_tools()
        except McpClientError as exc:
            self._record_failure(
                server_name,
                error_type=exc.status,
                detail=exc.detail,
                duration_ms=int((time.perf_counter() - started_at) * 1000),
            )
            raise
        self.registry.set_discovered_tools(server_name, tools)
        self._record_success(
            server_name,
            duration_ms=int((time.perf_counter() - started_at) * 1000),
            discovered_tools=[tool.name for tool in tools],
            discovery=True,
        )
        return tools

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        params: JsonObject | None = None,
    ) -> McpToolCallResult:
        if self.registry.get_discovered_tool(server_name, tool_name) is None:
            await self.list_tools(server_name)
        client = await self.get_client(server_name)
        started_at = time.perf_counter()
        result = await client.call_tool(tool_name, params)
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        if result.ok:
            self._record_success(server_name, duration_ms=duration_ms)
        else:
            self._record_failure(server_name, error_type=result.status, detail=result.detail, duration_ms=duration_ms)
        self._append_audit_record(
            server_name=server_name,
            tool_name=tool_name,
            success=result.ok,
            params=params,
            duration_ms=duration_ms,
            result=result,
            fallback_used=False,
            error_type=None if result.ok else result.status,
        )
        return result

    async def call_tool_with_fallback(
        self,
        server_name: str,
        tool_name: str,
        params: JsonObject | None = None,
        legacy_handler: Callable[[], Any] | Callable[[], Awaitable[Any]] | None = None,
    ) -> tuple[McpToolCallResult | None, Any | None, str | None]:
        config = self.registry.get_server(server_name)
        started_at = time.perf_counter()
        try:
            result = await self.call_tool(server_name, tool_name, params)
        except McpClientError as exc:
            duration_ms = int((time.perf_counter() - started_at) * 1000)
            result = McpToolCallResult(
                ok=False,
                status=exc.status,
                detail=exc.detail,
            )
            self._append_audit_record(
                server_name=server_name,
                tool_name=tool_name,
                success=False,
                params=params,
                duration_ms=duration_ms,
                result=result,
                fallback_used=False,
                error_type=exc.status,
            )
        if result.ok:
            return result, None, None
        if not config.legacy_fallback_enabled or legacy_handler is None:
            return result, None, None

        fallback_reason = result.status
        legacy_started_at = time.perf_counter()
        legacy_value = legacy_handler()
        if inspect.isawaitable(legacy_value):
            legacy_value = await legacy_value
        duration_ms = int((time.perf_counter() - legacy_started_at) * 1000)
        self._append_audit_record(
            server_name=server_name,
            tool_name=tool_name,
            success=True,
            params=params,
            duration_ms=duration_ms,
            result=result,
            fallback_used=True,
            fallback_reason=fallback_reason,
            error_type=result.status,
        )
        logger.info(
            "mcp fallback used server=%s tool=%s reason=%s",
            server_name,
            tool_name,
            fallback_reason,
        )
        return result, legacy_value, fallback_reason

    def get_server_status(self, server_name: str) -> JsonObject:
        return self._status_entry(server_name).to_payload()

    def get_status_snapshot(self) -> list[JsonObject]:
        names = {config.name for config in self.registry.list_enabled_servers()} | set(self._status)
        return [self._status_entry(name).to_payload() for name in sorted(names)]


_DEFAULT_MCP_MANAGER: McpManager | None = None


def get_default_mcp_manager() -> McpManager:
    global _DEFAULT_MCP_MANAGER
    if _DEFAULT_MCP_MANAGER is None:
        _DEFAULT_MCP_MANAGER = McpManager()
    return _DEFAULT_MCP_MANAGER


async def shutdown_default_mcp_manager() -> None:
    global _DEFAULT_MCP_MANAGER
    if _DEFAULT_MCP_MANAGER is None:
        return
    await _DEFAULT_MCP_MANAGER.shutdown_all()
    _DEFAULT_MCP_MANAGER = None
