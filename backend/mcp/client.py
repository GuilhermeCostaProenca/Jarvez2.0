from __future__ import annotations

import asyncio
from contextlib import AsyncExitStack
from datetime import timedelta
from typing import Any

from ._vendor import ClientSession, StdioServerParameters, stdio_client
from .types import JsonObject, McpClientError, McpServerConfig, McpToolCallResult, McpToolInfo


def _to_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return _to_jsonable(model_dump(mode="json", exclude_none=True))
    dict_dump = getattr(value, "dict", None)
    if callable(dict_dump):
        return _to_jsonable(dict_dump())
    if hasattr(value, "__dict__"):
        return _to_jsonable(vars(value))
    return str(value)


def _extract_text(content: Any) -> str:
    payload = _to_jsonable(content)
    if not isinstance(payload, list):
        return ""
    chunks: list[str] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        if str(item.get("type") or "").strip() != "text":
            continue
        text = str(item.get("text") or "").strip()
        if text:
            chunks.append(text)
    return "\n\n".join(chunks)


class StdioMcpClient:
    def __init__(self, config: McpServerConfig):
        self.config = config
        self._exit_stack: AsyncExitStack | None = None
        self._session: ClientSession | None = None
        self._initialize_payload: JsonObject | None = None

    @property
    def is_running(self) -> bool:
        return self._session is not None

    async def start(self) -> None:
        if self._session is not None:
            return
        if not self.config.enabled:
            raise McpClientError("server_disabled", f"MCP server '{self.config.name}' is disabled.")

        exit_stack = AsyncExitStack()
        try:
            server_params = StdioServerParameters(
                command=self.config.command,
                args=self.config.args,
                cwd=self.config.cwd,
            )
            read_stream, write_stream = await exit_stack.enter_async_context(stdio_client(server_params))
            session = await exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
            initialize_result = await asyncio.wait_for(
                session.initialize(),
                timeout=self.config.timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            await exit_stack.aclose()
            raise McpClientError("timeout", f"Timed out starting MCP server '{self.config.name}'.") from exc
        except Exception as exc:  # noqa: BLE001
            await exit_stack.aclose()
            raise McpClientError("transport_error", str(exc)) from exc

        self._exit_stack = exit_stack
        self._session = session
        payload = _to_jsonable(initialize_result)
        self._initialize_payload = payload if isinstance(payload, dict) else None

    async def stop(self) -> None:
        if self._exit_stack is not None:
            await self._exit_stack.aclose()
        self._exit_stack = None
        self._session = None
        self._initialize_payload = None

    async def list_tools(self) -> list[McpToolInfo]:
        await self.start()
        assert self._session is not None
        try:
            result = await asyncio.wait_for(
                self._session.list_tools(),
                timeout=self.config.timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            raise McpClientError("timeout", f"Timed out listing tools for '{self.config.name}'.") from exc
        except Exception as exc:  # noqa: BLE001
            raise McpClientError("protocol_error", str(exc)) from exc

        payload = _to_jsonable(result)
        tools_payload = payload.get("tools") if isinstance(payload, dict) else None
        if not isinstance(tools_payload, list):
            raise McpClientError("protocol_error", "Invalid tools/list response.")

        tools: list[McpToolInfo] = []
        for row in tools_payload:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or "").strip()
            if not name:
                continue
            description = str(row.get("description") or "").strip()
            input_schema = row.get("inputSchema")
            tools.append(
                McpToolInfo(
                    name=name,
                    description=description,
                    input_schema=input_schema if isinstance(input_schema, dict) else {},
                )
            )
        return tools

    async def call_tool(self, tool_name: str, params: JsonObject | None = None) -> McpToolCallResult:
        await self.start()
        assert self._session is not None
        safe_params = params or {}
        try:
            result = await asyncio.wait_for(
                self._session.call_tool(
                    tool_name,
                    safe_params,
                    read_timeout_seconds=timedelta(seconds=self.config.timeout_seconds),
                ),
                timeout=self.config.timeout_seconds + 1,
            )
        except asyncio.TimeoutError:
            return McpToolCallResult(
                ok=False,
                status="timeout",
                detail=f"Timed out calling '{tool_name}' on MCP server '{self.config.name}'.",
            )
        except McpClientError as exc:
            return McpToolCallResult(ok=False, status=exc.status, detail=exc.detail)
        except Exception as exc:  # noqa: BLE001
            return McpToolCallResult(ok=False, status="transport_error", detail=str(exc))

        payload = _to_jsonable(result)
        if not isinstance(payload, dict):
            return McpToolCallResult(ok=False, status="protocol_error", detail="Invalid tools/call response.")

        text = _extract_text(payload.get("content"))
        structured_content = payload.get("structuredContent")
        normalized_structured = structured_content if isinstance(structured_content, dict) else None
        if bool(payload.get("isError")):
            return McpToolCallResult(
                ok=False,
                status="tool_error",
                detail=text or "Tool returned isError=true.",
                structured_content=normalized_structured,
                text=text or None,
                raw_result=payload,
            )

        return McpToolCallResult(
            ok=True,
            status="ok",
            structured_content=normalized_structured,
            text=text or None,
            raw_result=payload,
        )
