from __future__ import annotations

from dataclasses import dataclass

import requests


@dataclass(slots=True)
class McpHealth:
    ok: bool
    status: str
    detail: str | None = None


class PlaywrightMcpClient:
    def __init__(self, base_url: str, *, timeout_seconds: int = 6):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def healthcheck(self) -> McpHealth:
        if not self.base_url:
            return McpHealth(ok=False, status="missing_url", detail="MCP URL not configured")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=self.timeout_seconds)
        except Exception as exc:  # noqa: BLE001
            return McpHealth(ok=False, status="unreachable", detail=str(exc))
        if response.status_code >= 400:
            return McpHealth(ok=False, status="error", detail=f"http_{response.status_code}")
        return McpHealth(ok=True, status="ok")
