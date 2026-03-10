from __future__ import annotations

import os
from typing import Any

from integrations.whatsapp_mcp_client import WhatsAppMcpClient


def build_whatsapp_channel_status() -> dict[str, Any]:
    mcp_url = os.getenv("JARVEZ_WHATSAPP_MCP_URL", "").strip()
    mcp_messages_db_path = os.getenv("JARVEZ_WHATSAPP_MCP_MESSAGES_DB_PATH", "").strip() or None
    legacy_enabled = bool(os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip())
    client = WhatsAppMcpClient(mcp_url, messages_db_path=mcp_messages_db_path)
    mcp_status = client.status()
    mode = "mcp" if mcp_status.connected else "legacy_v1" if legacy_enabled else "disabled"
    fallback_active = (not mcp_status.connected) and legacy_enabled
    history_source = "mcp_sqlite" if mcp_status.history_available else "legacy_json"
    return {
        "mode": mode,
        "legacy_enabled": legacy_enabled,
        "fallback_active": fallback_active,
        "history_source": history_source,
        "mcp": {
            "enabled": mcp_status.enabled,
            "connected": mcp_status.connected,
            "detail": mcp_status.detail,
            "url_configured": bool(mcp_url),
            "history_available": mcp_status.history_available,
            "messages_db_path": mcp_status.messages_db_path,
        },
    }
