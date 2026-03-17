from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import AsyncMock, patch

if "numpy" not in sys.modules:
    numpy_stub = types.ModuleType("numpy")
    numpy_stub.ndarray = object
    sys.modules["numpy"] = numpy_stub

import actions as actions_module
from actions import ActionContext, ActionResult, dispatch_action
from backend_mcp import McpToolCallResult


class WhatsAppMcpRoutingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        actions_module.STATE_STORE.clear_all()

    async def test_whatsapp_channel_status_routes_through_mcp(self) -> None:
        ctx = ActionContext(job_id="job-wa-1", room="room-wa", participant_identity="user-wa")

        async def _fake_call(server_name, tool_name, params, legacy_handler=None):  # noqa: ANN001
            self.assertEqual(server_name, "whatsapp")
            self.assertEqual(tool_name, "list_chats")
            self.assertEqual(
                params,
                {"limit": 1, "page": 0, "include_last_message": False, "sort_by": "last_active"},
            )
            self.assertIsNotNone(legacy_handler)
            return (
                McpToolCallResult(
                    ok=True,
                    status="ok",
                    structured_content=[{"jid": "5511999999999@s.whatsapp.net", "name": "Contato"}],
                    raw_result={"structuredContent": [{"jid": "5511999999999@s.whatsapp.net"}]},
                ),
                None,
                None,
            )

        with patch("actions.call_mcp_tool_with_legacy_fallback", side_effect=_fake_call):
            with patch("actions_domains.whatsapp_channel.build_whatsapp_channel_status", return_value={"mode": "mcp"}):
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
        self.assertEqual(result.evidence.get("mcp_tool"), "list_chats")
        channel = result.data.get("whatsapp_channel")
        self.assertEqual(channel.get("messages", {}).get("total"), 5)
        self.assertEqual(channel.get("mcp_stdio", {}).get("probe_result_count"), 1)

    async def test_whatsapp_send_text_routes_through_mcp_and_persists_journal(self) -> None:
        ctx = ActionContext(job_id="job-wa-2", room="room-wa", participant_identity="user-wa")

        async def _fake_call(server_name, tool_name, params, legacy_handler=None):  # noqa: ANN001
            self.assertEqual(server_name, "whatsapp")
            self.assertEqual(tool_name, "send_message")
            self.assertEqual(params, {"recipient": "5511999999999", "message": "Oi do Jarvez"})
            self.assertIsNotNone(legacy_handler)
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

        with patch("actions.call_mcp_tool_with_legacy_fallback", side_effect=_fake_call):
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

    async def test_whatsapp_send_text_uses_legacy_fallback_when_mcp_fails(self) -> None:
        ctx = ActionContext(job_id="job-wa-3", room="room-wa", participant_identity="user-wa")
        legacy_result = ActionResult(
            success=True,
            message="Mensagem enviada para 5511999999999.",
            data={
                "whatsapp_transport": "legacy_v1",
                "whatsapp_response": {"messages": [{"id": "wamid.legacy"}]},
            },
        )
        legacy_mock = AsyncMock(return_value=legacy_result)

        async def _fake_call(server_name, tool_name, params, legacy_handler=None):  # noqa: ANN001
            self.assertEqual(server_name, "whatsapp")
            self.assertEqual(tool_name, "send_message")
            self.assertIsNotNone(legacy_handler)
            fallback_value = await legacy_handler()
            return (
                McpToolCallResult(
                    ok=False,
                    status="transport_error",
                    detail="stdio unavailable",
                ),
                fallback_value,
                "transport_error",
            )

        with patch("actions.call_mcp_tool_with_legacy_fallback", side_effect=_fake_call):
            with patch("actions.domain_whatsapp_send_text", legacy_mock):
                with patch("actions._store_whatsapp_channel_message", return_value=True) as store_mock:
                    result = await dispatch_action(
                        "whatsapp_send_text",
                        {"to": "5511999999999", "text": "Oi do Jarvez"},
                        ctx,
                        skip_confirmation=True,
                        bypass_auth=True,
                    )

        legacy_mock.assert_awaited_once()
        self.assertTrue(result.success)
        self.assertTrue(result.fallback_used)
        self.assertEqual(result.evidence.get("provider"), "legacy")
        self.assertEqual(result.evidence.get("mcp_server"), "whatsapp")
        self.assertEqual(result.evidence.get("mcp_tool"), "send_message")
        self.assertEqual(result.evidence.get("fallback_reason"), "transport_error")
        store_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
