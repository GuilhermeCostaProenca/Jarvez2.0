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


class AcMcpRoutingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        actions_module.STATE_STORE.clear_all()

    async def test_ac_get_status_routes_through_thinq_mcp(self) -> None:
        ctx = ActionContext(job_id="job-ac-1", room="room-ac", participant_identity="user-ac")

        async def _fake_call(server_name, tool_name, params, legacy_handler=None):  # noqa: ANN001
            self.assertEqual(server_name, "thinq")
            self.assertEqual(tool_name, "thinq_get_device_state")
            self.assertEqual(params, {"device_name": "Ar da Sala"})
            self.assertIsNotNone(legacy_handler)
            return (
                McpToolCallResult(
                    ok=True,
                    status="ok",
                    structured_content={
                        "success": True,
                        "message": "Estado carregado para Ar da Sala.",
                        "data": {
                            "device": {"device_id": "ac-1", "alias": "Ar da Sala"},
                            "state": {"operation": {"airConOperationMode": "POWER_ON"}},
                        },
                    },
                    raw_result={"structuredContent": {"success": True}},
                ),
                None,
                None,
            )

        with patch("actions.call_mcp_tool_with_legacy_fallback", side_effect=_fake_call):
            result = await dispatch_action(
                "ac_get_status",
                {"device_name": "Ar da Sala"},
                ctx,
                skip_confirmation=True,
                bypass_auth=True,
            )

        self.assertTrue(result.success)
        self.assertFalse(result.fallback_used)
        self.assertEqual(result.message, "Estado do ar carregado para Ar da Sala.")
        self.assertEqual(result.data.get("device"), {"device_id": "ac-1", "alias": "Ar da Sala"})
        self.assertEqual(result.evidence.get("provider"), "mcp")
        self.assertEqual(result.evidence.get("mcp_server"), "thinq")
        self.assertEqual(result.evidence.get("mcp_tool"), "thinq_get_device_state")

    async def test_ac_turn_off_uses_legacy_fallback_when_mcp_fails(self) -> None:
        ctx = ActionContext(job_id="job-ac-2", room="room-ac", participant_identity="user-ac")
        legacy_result = ActionResult(
            success=True,
            message="Comando enviado para o ar Ar da Sala.",
            data={
                "device": {"device_id": "ac-1", "alias": "Ar da Sala"},
                "conditional": False,
                "command": {"operation": {"airConOperationMode": "POWER_OFF"}},
            },
        )
        legacy_mock = AsyncMock(return_value=legacy_result)

        async def _fake_call(server_name, tool_name, params, legacy_handler=None):  # noqa: ANN001
            self.assertEqual(server_name, "thinq")
            self.assertEqual(tool_name, "thinq_control_device")
            self.assertEqual(
                params,
                {
                    "device_name": "Ar da Sala",
                    "command": {"operation": {"airConOperationMode": "POWER_OFF"}},
                },
            )
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
            with patch("actions.domain_ac_turn_off", legacy_mock):
                result = await dispatch_action(
                    "ac_turn_off",
                    {"device_name": "Ar da Sala"},
                    ctx,
                    skip_confirmation=True,
                    bypass_auth=True,
                )

        legacy_mock.assert_awaited_once()
        self.assertTrue(result.success)
        self.assertTrue(result.fallback_used)
        self.assertEqual(result.message, "Comando enviado para o ar Ar da Sala.")
        self.assertEqual(result.evidence.get("provider"), "legacy")
        self.assertEqual(result.evidence.get("mcp_server"), "thinq")
        self.assertEqual(result.evidence.get("mcp_tool"), "thinq_control_device")
        self.assertEqual(result.evidence.get("fallback_reason"), "transport_error")


if __name__ == "__main__":
    unittest.main()
