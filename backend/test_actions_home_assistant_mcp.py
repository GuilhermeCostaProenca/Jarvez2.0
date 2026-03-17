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


class HomeAssistantMcpRoutingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        actions_module.STATE_STORE.clear_all()

    async def test_turn_light_on_routes_through_mcp(self) -> None:
        ctx = ActionContext(job_id="job-ha-1", room="room-ha", participant_identity="user-ha")

        async def _fake_call(server_name, tool_name, params, legacy_handler=None):  # noqa: ANN001
            self.assertEqual(server_name, "home_assistant")
            self.assertEqual(tool_name, "turn_light_on")
            self.assertEqual(params, {"entity_id": "light.sala"})
            self.assertIsNotNone(legacy_handler)
            return (
                McpToolCallResult(
                    ok=True,
                    status="ok",
                    structured_content={
                        "success": True,
                        "message": "Servico executado: light.turn_on.",
                        "data": {"service_response": [{"entity_id": "light.sala", "state": "on"}]},
                    },
                    raw_result={"structuredContent": {"success": True}},
                ),
                None,
                None,
            )

        with patch("actions.call_mcp_tool_with_legacy_fallback", side_effect=_fake_call):
            result = await dispatch_action("turn_light_on", {"entity_id": "light.sala"}, ctx, skip_confirmation=True, bypass_auth=True)

        self.assertTrue(result.success)
        self.assertFalse(result.fallback_used)
        self.assertEqual(result.message, "Servico executado: light.turn_on.")
        self.assertEqual(result.data.get("service_response"), [{"entity_id": "light.sala", "state": "on"}])
        self.assertEqual(result.evidence.get("provider"), "mcp")
        self.assertEqual(result.evidence.get("mcp_server"), "home_assistant")
        self.assertEqual(result.evidence.get("mcp_tool"), "turn_light_on")

    async def test_turn_light_off_uses_legacy_fallback_when_mcp_fails(self) -> None:
        ctx = ActionContext(job_id="job-ha-2", room="room-ha", participant_identity="user-ha")
        legacy_result = ActionResult(
            success=True,
            message="Servico executado: light.turn_off.",
            data={"service_response": [{"entity_id": "light.sala", "state": "off"}]},
        )
        legacy_mock = AsyncMock(return_value=legacy_result)

        async def _fake_call(server_name, tool_name, params, legacy_handler=None):  # noqa: ANN001
            self.assertEqual(server_name, "home_assistant")
            self.assertEqual(tool_name, "turn_light_off")
            self.assertEqual(params, {"entity_id": "light.sala"})
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
            with patch("actions.domain_turn_light_off", legacy_mock):
                result = await dispatch_action("turn_light_off", {"entity_id": "light.sala"}, ctx, skip_confirmation=True, bypass_auth=True)

        legacy_mock.assert_awaited_once()
        self.assertTrue(result.success)
        self.assertTrue(result.fallback_used)
        self.assertEqual(result.message, "Servico executado: light.turn_off.")
        self.assertEqual(result.data.get("service_response"), [{"entity_id": "light.sala", "state": "off"}])
        self.assertEqual(result.evidence.get("provider"), "legacy")
        self.assertEqual(result.evidence.get("mcp_tool"), "turn_light_off")
        self.assertEqual(result.evidence.get("fallback_reason"), "transport_error")

    async def test_call_service_routes_through_mcp(self) -> None:
        ctx = ActionContext(job_id="job-ha-3", room="room-ha", participant_identity="user-ha")

        async def _fake_call(server_name, tool_name, params, legacy_handler=None):  # noqa: ANN001
            self.assertEqual(server_name, "home_assistant")
            self.assertEqual(tool_name, "call_service")
            self.assertEqual(
                params,
                {
                    "domain": "light",
                    "service": "turn_on",
                    "service_data": {"entity_id": "light.sala", "brightness": 128},
                },
            )
            self.assertIsNotNone(legacy_handler)
            return (
                McpToolCallResult(
                    ok=True,
                    status="ok",
                    structured_content={
                        "success": True,
                        "message": "Servico executado: light.turn_on.",
                        "data": {"service_response": [{"entity_id": "light.sala", "brightness": 128}]},
                    },
                    raw_result={"structuredContent": {"success": True}},
                ),
                None,
                None,
            )

        with patch("actions.call_mcp_tool_with_legacy_fallback", side_effect=_fake_call):
            result = await dispatch_action(
                "call_service",
                {"domain": "light", "service": "turn_on", "service_data": {"entity_id": "light.sala", "brightness": 128}},
                ctx,
                skip_confirmation=True,
                bypass_auth=True,
            )

        self.assertTrue(result.success)
        self.assertFalse(result.fallback_used)
        self.assertEqual(result.evidence.get("provider"), "mcp")
        self.assertEqual(result.evidence.get("mcp_tool"), "call_service")


if __name__ == "__main__":
    unittest.main()
