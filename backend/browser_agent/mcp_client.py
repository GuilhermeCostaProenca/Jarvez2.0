from __future__ import annotations

from dataclasses import dataclass
import json
from urllib.parse import urlparse
from typing import Any

import requests


@dataclass(slots=True)
class McpHealth:
    ok: bool
    status: str
    detail: str | None = None
    tools: list[str] | None = None


@dataclass(slots=True)
class McpToolCall:
    ok: bool
    status: str
    detail: str | None = None
    result: dict[str, Any] | None = None


class PlaywrightMcpClient:
    def __init__(self, base_url: str, *, timeout_seconds: int = 6):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        if self.base_url.endswith("/mcp"):
            self.mcp_url = self.base_url
        else:
            self.mcp_url = f"{self.base_url}/mcp" if self.base_url else ""
        self._session_id: str | None = None
        self._request_id = 0

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        if self._session_id:
            headers["mcp-session-id"] = self._session_id
        return headers

    def _extract_payload(self, response: requests.Response) -> dict[str, Any] | None:
        text = response.text or ""
        payloads: list[dict[str, Any]] = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.startswith("data:"):
                continue
            raw = stripped[5:].strip()
            if not raw:
                continue
            try:
                parsed = json.loads(raw)
            except Exception:
                continue
            if isinstance(parsed, dict):
                payloads.append(parsed)
        if payloads:
            return payloads[-1]
        try:
            parsed_json = response.json()
        except ValueError:
            return None
        return parsed_json if isinstance(parsed_json, dict) else None

    def _rpc_request(
        self,
        *,
        method: str,
        params: dict[str, Any] | None = None,
        request_id: int | None = None,
        timeout_seconds: int | None = None,
    ) -> tuple[dict[str, Any] | None, str | None]:
        if not self.mcp_url:
            return None, "missing_mcp_url"
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        if request_id is not None:
            payload["id"] = request_id
        try:
            response = requests.post(
                self.mcp_url,
                headers=self._headers(),
                json=payload,
                timeout=timeout_seconds or self.timeout_seconds,
            )
        except Exception as exc:  # noqa: BLE001
            return None, str(exc)
        session_id = response.headers.get("mcp-session-id")
        if session_id:
            self._session_id = session_id
        if response.status_code >= 400:
            payload_error = self._extract_payload(response)
            if isinstance(payload_error, dict):
                err_obj = payload_error.get("error")
                if isinstance(err_obj, dict):
                    message = str(err_obj.get("message") or "").strip()
                    if message:
                        return payload_error, message
            text = (response.text or "").strip()
            return None, text or f"http_{response.status_code}"
        parsed = self._extract_payload(response)
        return parsed, None

    def _ensure_initialized(self) -> tuple[bool, str | None]:
        if self._session_id:
            return True, None
        init_params = {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {
                "name": "jarvez-browser-agent",
                "version": "0.1",
            },
        }
        payload, error = self._rpc_request(
            method="initialize",
            params=init_params,
            request_id=self._next_id(),
            timeout_seconds=max(self.timeout_seconds, 15),
        )
        if error is not None:
            return False, error
        if self._session_id is None:
            return False, "missing_session_id"
        if not isinstance(payload, dict) or not isinstance(payload.get("result"), dict):
            return False, "invalid_initialize_response"
        _, notify_error = self._rpc_request(
            method="notifications/initialized",
            params={},
        )
        if notify_error is not None:
            return False, notify_error
        return True, None

    def healthcheck(self) -> McpHealth:
        if not self.mcp_url:
            return McpHealth(ok=False, status="missing_url", detail="MCP URL not configured")
        ok, init_error = self._ensure_initialized()
        if not ok:
            return McpHealth(ok=False, status="unreachable", detail=init_error)
        payload, error = self._rpc_request(
            method="tools/list",
            params={},
            request_id=self._next_id(),
            timeout_seconds=max(self.timeout_seconds, 20),
        )
        if error is not None:
            return McpHealth(ok=False, status="tools_list_error", detail=error)
        tools: list[str] = []
        if isinstance(payload, dict):
            result = payload.get("result")
            if isinstance(result, dict):
                rows = result.get("tools")
                if isinstance(rows, list):
                    for row in rows:
                        if not isinstance(row, dict):
                            continue
                        name = str(row.get("name") or "").strip()
                        if name:
                            tools.append(name)
        return McpHealth(ok=True, status="ok", tools=tools)

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> McpToolCall:
        tool_name = str(name or "").strip()
        if not tool_name:
            return McpToolCall(ok=False, status="invalid_tool", detail="tool name is required")
        ok, init_error = self._ensure_initialized()
        if not ok:
            return McpToolCall(ok=False, status="unreachable", detail=init_error)
        payload, error = self._rpc_request(
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": arguments or {},
            },
            request_id=self._next_id(),
            timeout_seconds=max(self.timeout_seconds, 60),
        )
        if error is not None:
            return McpToolCall(ok=False, status="tool_call_error", detail=error)
        if not isinstance(payload, dict):
            return McpToolCall(ok=False, status="invalid_response", detail="missing payload")
        rpc_error = payload.get("error")
        if isinstance(rpc_error, dict):
            message = str(rpc_error.get("message") or "").strip() or "jsonrpc error"
            return McpToolCall(ok=False, status="jsonrpc_error", detail=message)
        result = payload.get("result")
        if not isinstance(result, dict):
            return McpToolCall(ok=False, status="invalid_result", detail="missing result")
        is_error = bool(result.get("isError"))
        detail: str | None = None
        if is_error:
            detail = self.extract_text(result) or "tool returned error"
        return McpToolCall(
            ok=not is_error,
            status="ok" if not is_error else "tool_error",
            detail=detail,
            result=result,
        )

    @staticmethod
    def extract_text(result: dict[str, Any] | None) -> str:
        if not isinstance(result, dict):
            return ""
        content = result.get("content")
        if not isinstance(content, list):
            return ""
        chunks: list[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            if str(item.get("type") or "").strip() != "text":
                continue
            text = str(item.get("text") or "").strip()
            if text:
                chunks.append(text)
        return "\n\n".join(chunks)

    @staticmethod
    def extract_page_url(text: str) -> str | None:
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.lower().startswith("- page url:"):
                continue
            value = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
            if not value:
                continue
            parsed = urlparse(value)
            if parsed.scheme and parsed.netloc:
                return value
        return None
