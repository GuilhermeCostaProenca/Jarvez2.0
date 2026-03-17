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


class SpotifyMcpRoutingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        actions_module.STATE_STORE.clear_all()

    async def test_spotify_status_routes_through_mcp(self) -> None:
        ctx = ActionContext(job_id="job-spotify-1", room="room-spotify", participant_identity="user-spotify")

        async def _fake_call(server_name, tool_name, params, legacy_handler=None):  # noqa: ANN001
            self.assertEqual(server_name, "spotify")
            self.assertEqual(tool_name, "spotify_status")
            self.assertEqual(params, {})
            self.assertIsNotNone(legacy_handler)
            return (
                McpToolCallResult(
                    ok=True,
                    status="ok",
                    structured_content={
                        "success": False,
                        "message": "Spotify nao autenticado. Abra /api/spotify/login para conectar.",
                        "data": {"authorization_url": "http://127.0.0.1:3001/api/spotify/login"},
                        "error": "spotify_auth_required",
                    },
                    raw_result={"structuredContent": {"success": False}},
                ),
                None,
                None,
            )

        with patch("actions.call_mcp_tool_with_legacy_fallback", side_effect=_fake_call):
            result = await dispatch_action("spotify_status", {}, ctx)

        self.assertFalse(result.success)
        self.assertEqual(result.error, "spotify_auth_required")
        self.assertFalse(result.fallback_used)
        self.assertIsInstance(result.evidence, dict)
        self.assertEqual(result.evidence.get("provider"), "mcp")
        self.assertEqual(result.evidence.get("mcp_server"), "spotify")
        self.assertEqual(result.evidence.get("mcp_tool"), "spotify_status")

    async def test_spotify_get_devices_uses_legacy_fallback_when_mcp_fails(self) -> None:
        ctx = ActionContext(job_id="job-spotify-2", room="room-spotify", participant_identity="user-spotify")
        legacy_result = ActionResult(
            success=True,
            message="1 device(s) Spotify encontrados.",
            data={"devices": [{"id": "speaker-1", "name": "Sala"}]},
        )
        legacy_mock = AsyncMock(return_value=legacy_result)

        async def _fake_call(server_name, tool_name, params, legacy_handler=None):  # noqa: ANN001
            self.assertEqual(server_name, "spotify")
            self.assertEqual(tool_name, "spotify_get_devices")
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
            with patch("actions.domain_spotify_get_devices", legacy_mock):
                result = await dispatch_action("spotify_get_devices", {}, ctx)

        legacy_mock.assert_awaited_once()
        self.assertTrue(result.success)
        self.assertTrue(result.fallback_used)
        self.assertEqual(result.message, "1 device(s) Spotify encontrados.")
        self.assertIsInstance(result.data, dict)
        self.assertEqual(result.data.get("devices"), [{"id": "speaker-1", "name": "Sala"}])
        self.assertIsInstance(result.evidence, dict)
        self.assertEqual(result.evidence.get("provider"), "legacy")
        self.assertEqual(result.evidence.get("fallback_reason"), "transport_error")


if __name__ == "__main__":
    unittest.main()
