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


class RpgMcpRoutingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        actions_module.STATE_STORE.clear_all()

    async def test_rpg_get_knowledge_stats_routes_through_mcp(self) -> None:
        ctx = ActionContext(job_id="job-rpg-1", room="room-rpg", participant_identity="user-rpg")
        actions_module.set_persona_mode(ctx.participant_identity, ctx.room, "rpg")

        async def _fake_call(server_name, tool_name, params=None, legacy_handler=None):  # noqa: ANN001
            self.assertEqual(server_name, "rpg")
            self.assertEqual(tool_name, "rpg_get_knowledge_stats")
            self.assertIsNone(legacy_handler)
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

    async def test_rpg_search_knowledge_mcp_failure_surfaces_error(self) -> None:
        """Legacy fallback is disabled. MCP failure surfaces an error result directly."""
        ctx = ActionContext(job_id="job-rpg-2", room="room-rpg", participant_identity="user-rpg")
        actions_module.set_persona_mode(ctx.participant_identity, ctx.room, "rpg")

        async def _fake_call(server_name, tool_name, params=None, legacy_handler=None):  # noqa: ANN001
            self.assertEqual(server_name, "rpg")
            self.assertEqual(tool_name, "rpg_search_knowledge")
            self.assertIsNone(legacy_handler)
            return (
                McpToolCallResult(ok=False, status="transport_error", detail="stdio unavailable"),
                None,
                None,
            )

        with patch("actions.call_mcp_tool_with_legacy_fallback", side_effect=_fake_call):
            result = await dispatch_action(
                "rpg_search_knowledge",
                {"query": "Arton", "limit": 3},
                ctx,
                skip_confirmation=True,
                bypass_auth=True,
            )

        self.assertFalse(result.success)
        self.assertFalse(result.fallback_used)
        self.assertEqual(result.evidence.get("provider"), "mcp")
        self.assertEqual(result.evidence.get("mcp_server"), "rpg")


if __name__ == "__main__":
    unittest.main()
