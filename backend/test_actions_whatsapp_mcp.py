from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import patch

if "numpy" not in sys.modules:
    numpy_stub = types.ModuleType("numpy")
    numpy_stub.ndarray = object
    sys.modules["numpy"] = numpy_stub

import actions as actions_module
from actions import ActionContext, dispatch_action
from backend_mcp import McpToolCallResult


class WhatsAppMcpRoutingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        actions_module.STATE_STORE.clear_all()

    async def test_whatsapp_channel_status_routes_through_mcp(self) -> None:
        ctx = ActionContext(job_id="job-wa-1", room="room-wa", participant_identity="user-wa")

        async def _fake_call(server_name, tool_name, params=None):  # noqa: ANN001
            self.assertEqual(server_name, "whatsapp")
            self.assertEqual(tool_name, "list_chats")
            return McpToolCallResult(
                ok=True,
                status="ok",
                structured_content=[{"jid": "5511999999999@s.whatsapp.net", "name": "Contato"}],
                raw_result={"structuredContent": [{"jid": "5511999999999@s.whatsapp.net"}]},
            )

        with patch("actions.call_mcp_tool", side_effect=_fake_call):
            with patch.object(actions_module.STATE_STORE, "count_channel_messages", side_effect=[5, 3, 2]):
                with patch.object(
                    actions_module.STATE_STORE,
                    "latest_channel_message",
                    side_effect=[{"created_at": "2026-03-17T10:00:00Z"}, {"created_at": "2026-03-17T11:00:00Z"}],
                ):
                    result = await dispatch_action(
                        "whatsapp_channel_status",
                        {},
                        ctx,
                        skip_confirmation=True,
                        bypass_auth=True,
                    )

        self.assertTrue(result.success)
        self.assertFalse(result.fallback_used)
        self.assertEqual(result.evidence.get("provider"), "mcp")
        self.assertEqual(result.evidence.get("mcp_server"), "whatsapp")
        channel = result.data.get("whatsapp_channel")
        self.assertIsNotNone(channel)
        self.assertEqual(channel.get("messages", {}).get("total"), 5)
        self.assertTrue(channel.get("mcp_stdio", {}).get("connected"))

    async def test_whatsapp_send_text_routes_through_mcp_and_persists_journal(self) -> None:
        ctx = ActionContext(job_id="job-wa-2", room="room-wa", participant_identity="user-wa")

        async def _fake_fallback(server_name, tool_name, params=None, legacy_handler=None):  # noqa: ANN001
            self.assertEqual(server_name, "whatsapp")
            self.assertEqual(tool_name, "send_message")
            self.assertIsNone(legacy_handler)
            return (
                McpToolCallResult(
                    ok=True,
                    status="ok",
                    structured_content={"success": True, "message": "Message sent via MCP bridge."},
                    raw_result={"structuredContent": {"success": True}},
                ),
                None,
                None,
            )

        with patch("actions.call_mcp_tool_with_legacy_fallback", side_effect=_fake_fallback):
            with patch("actions._store_whatsapp_channel_message", return_value=True) as store_mock:
                result = await dispatch_action(
                    "whatsapp_send_text",
                    {"to": "5511999999999", "text": "Oi do Jarvez"},
                    ctx,
                    skip_confirmation=True,
                    bypass_auth=True,
                )

        self.assertTrue(result.success)
        self.assertFalse(result.fallback_used)
        self.assertEqual(result.message, "Mensagem enviada para 5511999999999.")
        self.assertEqual(result.evidence.get("provider"), "mcp")
        self.assertEqual(result.evidence.get("mcp_server"), "whatsapp")
        self.assertEqual(result.evidence.get("mcp_tool"), "send_message")
        self.assertEqual(result.data.get("whatsapp_transport"), "mcp_stdio")
        store_mock.assert_called_once()

    async def test_whatsapp_send_text_mcp_failure_surfaces_error(self) -> None:
        """When MCP fails, the error surfaces directly — no fallback."""
        ctx = ActionContext(job_id="job-wa-3", room="room-wa", participant_identity="user-wa")

        async def _fake_fallback(server_name, tool_name, params=None, legacy_handler=None):  # noqa: ANN001
            return (
                McpToolCallResult(ok=False, status="transport_error", detail="stdio unavailable"),
                None,
                None,
            )

        with patch("actions.call_mcp_tool_with_legacy_fallback", side_effect=_fake_fallback):
            result = await dispatch_action(
                "whatsapp_send_text",
                {"to": "5511999999999", "text": "Oi do Jarvez"},
                ctx,
                skip_confirmation=True,
                bypass_auth=True,
            )

        self.assertFalse(result.success)
        self.assertFalse(result.fallback_used)
        self.assertEqual(result.evidence.get("provider"), "mcp")
        self.assertEqual(result.evidence.get("mcp_server"), "whatsapp")


if __name__ == "__main__":
    unittest.main()
