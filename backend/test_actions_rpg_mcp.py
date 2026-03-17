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


class RpgMcpRoutingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        actions_module.STATE_STORE.clear_all()

    async def test_rpg_get_knowledge_stats_routes_through_mcp(self) -> None:
        ctx = ActionContext(job_id="job-rpg-1", room="room-rpg", participant_identity="user-rpg")
        actions_module.set_persona_mode(ctx.participant_identity, ctx.room, "rpg")

        async def _fake_call(server_name, tool_name, params, legacy_handler=None):  # noqa: ANN001
            self.assertEqual(server_name, "rpg")
            self.assertEqual(tool_name, "rpg_get_knowledge_stats")
            self.assertEqual(params, {})
            self.assertIsNotNone(legacy_handler)
            return (
                McpToolCallResult(
                    ok=True,
                    status="ok",
                    structured_content={
                        "success": True,
                        "message": "Estatisticas da base RPG.",
                        "data": {
                            "knowledge_stats": {
                                "documents": 12,
                                "chunks": 340,
                                "notes": 5,
                            }
                        },
                    },
                    raw_result={"structuredContent": {"success": True}},
                ),
                None,
                None,
            )

        with patch("actions.call_mcp_tool_with_legacy_fallback", side_effect=_fake_call):
            result = await dispatch_action("rpg_get_knowledge_stats", {}, ctx, skip_confirmation=True, bypass_auth=True)

        self.assertTrue(result.success)
        self.assertFalse(result.fallback_used)
        self.assertEqual(result.message, "Estatisticas da base RPG.")
        self.assertEqual(result.data.get("knowledge_stats", {}).get("documents"), 12)
        self.assertEqual(result.evidence.get("provider"), "mcp")
        self.assertEqual(result.evidence.get("mcp_server"), "rpg")
        self.assertEqual(result.evidence.get("mcp_tool"), "rpg_get_knowledge_stats")

    async def test_rpg_search_knowledge_uses_legacy_fallback_when_mcp_fails(self) -> None:
        ctx = ActionContext(job_id="job-rpg-2", room="room-rpg", participant_identity="user-rpg")
        actions_module.set_persona_mode(ctx.participant_identity, ctx.room, "rpg")
        legacy_result = ActionResult(
            success=True,
            message="Encontrei 1 trecho(s) da base RPG.",
            data={"query": "Arton", "results": [{"title": "Arton", "content": "Mundo de Tormenta."}]},
        )
        legacy_mock = AsyncMock(return_value=legacy_result)

        async def _fake_call(server_name, tool_name, params, legacy_handler=None):  # noqa: ANN001
            self.assertEqual(server_name, "rpg")
            self.assertEqual(tool_name, "rpg_search_knowledge")
            self.assertEqual(params, {"query": "Arton", "limit": 3})
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
            with patch("actions.domain_rpg_search_knowledge", legacy_mock):
                result = await dispatch_action(
                    "rpg_search_knowledge",
                    {"query": "Arton", "limit": 3},
                    ctx,
                    skip_confirmation=True,
                    bypass_auth=True,
                )

        legacy_mock.assert_awaited_once()
        self.assertTrue(result.success)
        self.assertTrue(result.fallback_used)
        self.assertEqual(result.message, "Encontrei 1 trecho(s) da base RPG.")
        self.assertEqual(result.data.get("query"), "Arton")
        self.assertEqual(result.evidence.get("provider"), "legacy")
        self.assertEqual(result.evidence.get("mcp_server"), "rpg")
        self.assertEqual(result.evidence.get("mcp_tool"), "rpg_search_knowledge")
        self.assertEqual(result.evidence.get("fallback_reason"), "transport_error")


if __name__ == "__main__":
    unittest.main()
