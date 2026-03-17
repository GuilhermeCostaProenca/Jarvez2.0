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


class OneNoteMcpRoutingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        actions_module.STATE_STORE.clear_all()

    async def test_onenote_status_routes_through_mcp(self) -> None:
        ctx = ActionContext(job_id="job-onenote-1", room="room-onenote", participant_identity="user-onenote")

        async def _fake_call(server_name, tool_name, params, legacy_handler=None):  # noqa: ANN001
            self.assertEqual(server_name, "onenote")
            self.assertEqual(tool_name, "onenote_status")
            self.assertEqual(params, {})
            self.assertIsNotNone(legacy_handler)
            return (
                McpToolCallResult(
                    ok=True,
                    status="ok",
                    structured_content={
                        "success": False,
                        "message": "OneNote nao autenticado. Abra /api/onenote/login para conectar.",
                        "data": {"authorization_url": "http://127.0.0.1:3001/api/onenote/login"},
                        "error": "onenote_auth_required",
                    },
                    raw_result={"structuredContent": {"success": False}},
                ),
                None,
                None,
            )

        with patch("actions.call_mcp_tool_with_legacy_fallback", side_effect=_fake_call):
            result = await dispatch_action("onenote_status", {}, ctx)

        self.assertFalse(result.success)
        self.assertEqual(result.error, "onenote_auth_required")
        self.assertFalse(result.fallback_used)
        self.assertIsInstance(result.evidence, dict)
        self.assertEqual(result.evidence.get("provider"), "mcp")
        self.assertEqual(result.evidence.get("mcp_server"), "onenote")
        self.assertEqual(result.evidence.get("mcp_tool"), "onenote_status")

    async def test_onenote_list_notebooks_uses_legacy_fallback_when_mcp_fails(self) -> None:
        ctx = ActionContext(job_id="job-onenote-2", room="room-onenote", participant_identity="user-onenote")
        legacy_result = ActionResult(
            success=True,
            message="1 caderno(s) OneNote encontrado(s).",
            data={"notebooks": [{"id": "nb-1", "displayName": "Jarvez Lore"}]},
        )
        legacy_mock = AsyncMock(return_value=legacy_result)

        async def _fake_call(server_name, tool_name, params, legacy_handler=None):  # noqa: ANN001
            self.assertEqual(server_name, "onenote")
            self.assertEqual(tool_name, "onenote_list_notebooks")
            self.assertEqual(params, {"query": "Jarvez"})
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
            with patch("actions.domain_onenote_list_notebooks", legacy_mock):
                result = await dispatch_action("onenote_list_notebooks", {"query": "Jarvez"}, ctx)

        legacy_mock.assert_awaited_once()
        self.assertTrue(result.success)
        self.assertTrue(result.fallback_used)
        self.assertEqual(result.message, "1 caderno(s) OneNote encontrado(s).")
        self.assertIsInstance(result.data, dict)
        self.assertEqual(result.data.get("notebooks"), [{"id": "nb-1", "displayName": "Jarvez Lore"}])
        self.assertEqual(result.evidence.get("provider"), "legacy")
        self.assertEqual(result.evidence.get("fallback_reason"), "transport_error")
        self.assertEqual(result.evidence.get("mcp_tool"), "onenote_list_notebooks")

    async def test_onenote_list_sections_routes_through_mcp(self) -> None:
        ctx = ActionContext(job_id="job-onenote-3", room="room-onenote", participant_identity="user-onenote")

        async def _fake_call(server_name, tool_name, params, legacy_handler=None):  # noqa: ANN001
            self.assertEqual(server_name, "onenote")
            self.assertEqual(tool_name, "onenote_list_sections")
            self.assertEqual(params, {"notebook_name": "RPG"})
            self.assertIsNotNone(legacy_handler)
            return (
                McpToolCallResult(
                    ok=True,
                    status="ok",
                    structured_content={
                        "success": True,
                        "message": "2 secao(oes) OneNote encontradas.",
                        "data": {
                            "sections": [
                                {"id": "sec-1", "displayName": "Personagens"},
                                {"id": "sec-2", "displayName": "Lore"},
                            ],
                            "total_found": 2,
                            "truncated": False,
                        },
                    },
                    raw_result={"structuredContent": {"success": True}},
                ),
                None,
                None,
            )

        with patch("actions.call_mcp_tool_with_legacy_fallback", side_effect=_fake_call):
            result = await dispatch_action("onenote_list_sections", {"notebook_name": "RPG"}, ctx)

        self.assertTrue(result.success)
        self.assertFalse(result.fallback_used)
        self.assertEqual(result.message, "2 secao(oes) OneNote encontradas.")
        self.assertEqual(result.data.get("total_found"), 2)
        self.assertEqual(result.evidence.get("provider"), "mcp")
        self.assertEqual(result.evidence.get("mcp_tool"), "onenote_list_sections")


if __name__ == "__main__":
    unittest.main()
