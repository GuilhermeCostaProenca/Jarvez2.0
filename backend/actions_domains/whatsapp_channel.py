from __future__ import annotations

import os
from typing import Any

from integrations.whatsapp_mcp_client import WhatsAppMcpClient


def build_whatsapp_channel_status() -> dict[str, Any]:
    mcp_url = os.getenv("JARVEZ_WHATSAPP_MCP_URL", "").strip()
    legacy_enabled = bool(os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip())
    client = WhatsAppMcpClient(mcp_url)
    mcp_status = client.status()
    mode = "mcp" if mcp_status.connected else "legacy_v1" if legacy_enabled else "disabled"
    return {
        "mode": mode,
        "legacy_enabled": legacy_enabled,
        "mcp": {
            "enabled": mcp_status.enabled,
            "connected": mcp_status.connected,
            "detail": mcp_status.detail,
            "url_configured": bool(mcp_url),
        },
    }
