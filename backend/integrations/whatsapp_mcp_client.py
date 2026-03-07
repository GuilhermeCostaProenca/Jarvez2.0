from __future__ import annotations

from dataclasses import dataclass

import requests


@dataclass(slots=True)
class WhatsAppMcpStatus:
    enabled: bool
    connected: bool
    mode: str
    detail: str | None = None


class WhatsAppMcpClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def status(self) -> WhatsAppMcpStatus:
        if not self.base_url:
            return WhatsAppMcpStatus(
                enabled=False,
                connected=False,
                mode="legacy",
                detail="JARVEZ_WHATSAPP_MCP_URL not configured",
            )
        try:
            response = requests.get(f"{self.base_url}/health", timeout=6)
        except Exception as exc:  # noqa: BLE001
            return WhatsAppMcpStatus(enabled=True, connected=False, mode="mcp", detail=str(exc))
        if response.status_code >= 400:
            return WhatsAppMcpStatus(
                enabled=True,
                connected=False,
                mode="mcp",
                detail=f"http_{response.status_code}",
            )
        return WhatsAppMcpStatus(enabled=True, connected=True, mode="mcp")
