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


class SpotifyMcpRoutingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        actions_module.STATE_STORE.clear_all()

    async def test_spotify_status_routes_through_mcp(self) -> None:
        ctx = ActionContext(job_id="job-spotify-1", room="room-spotify", participant_identity="user-spotify")

        async def _fake_call(server_name, tool_name, params, legacy_handler=None):  # noqa: ANN001
            self.assertEqual(server_name, "spotify")
            self.assertEqual(tool_name, "spotify_status")
            self.assertEqual(params, {})
            self.assertIsNone(legacy_handler)
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
            result = await dispatch_action("spotify_status", {}, ctx, skip_confirmation=True, bypass_auth=True)

        self.assertFalse(result.success)
        self.assertEqual(result.error, "spotify_auth_required")
        self.assertFalse(result.fallback_used)
        self.assertIsInstance(result.evidence, dict)
        self.assertEqual(result.evidence.get("provider"), "mcp")
        self.assertEqual(result.evidence.get("mcp_server"), "spotify")
        self.assertEqual(result.evidence.get("mcp_tool"), "spotify_status")

    async def test_spotify_get_devices_mcp_failure_surfaces_error(self) -> None:
        ctx = ActionContext(job_id="job-spotify-2", room="room-spotify", participant_identity="user-spotify")

        async def _fake_call(server_name, tool_name, params, legacy_handler=None):  # noqa: ANN001
            self.assertEqual(server_name, "spotify")
            self.assertEqual(tool_name, "spotify_get_devices")
            self.assertIsNone(legacy_handler)
            return (
                McpToolCallResult(
                    ok=False,
                    status="transport_error",
                    detail="stdio unavailable",
                ),
                None,
                None,
            )

        with patch("actions.call_mcp_tool_with_legacy_fallback", side_effect=_fake_call):
            result = await dispatch_action("spotify_get_devices", {}, ctx, skip_confirmation=True, bypass_auth=True)

        self.assertFalse(result.success)
        self.assertFalse(result.fallback_used)
        self.assertEqual(result.evidence.get("provider"), "mcp")
        self.assertEqual(result.evidence.get("mcp_server"), "spotify")
        self.assertEqual(result.evidence.get("mcp_tool"), "spotify_get_devices")

    async def test_spotify_pause_routes_through_mcp_for_control_action(self) -> None:
        ctx = ActionContext(job_id="job-spotify-3", room="room-spotify", participant_identity="user-spotify")

        async def _fake_call(server_name, tool_name, params, legacy_handler=None):  # noqa: ANN001
            self.assertEqual(server_name, "spotify")
            self.assertEqual(tool_name, "spotify_pause")
            self.assertEqual(params, {})
            self.assertIsNone(legacy_handler)
            return (
                McpToolCallResult(
                    ok=True,
                    status="ok",
                    structured_content={
                        "success": True,
                        "message": "Playback pausado.",
                        "data": {"transport": "mcp"},
                    },
                    raw_result={"structuredContent": {"success": True}},
                ),
                None,
                None,
            )

        with patch("actions.call_mcp_tool_with_legacy_fallback", side_effect=_fake_call):
            result = await dispatch_action("spotify_pause", {}, ctx, skip_confirmation=True, bypass_auth=True)

        self.assertTrue(result.success)
        self.assertEqual(result.message, "Playback pausado.")
        self.assertFalse(result.fallback_used)
        self.assertIsInstance(result.data, dict)
        self.assertEqual(result.data.get("transport"), "mcp")
        self.assertEqual(result.evidence.get("provider"), "mcp")
        self.assertEqual(result.evidence.get("mcp_tool"), "spotify_pause")

    async def test_spotify_play_mcp_failure_surfaces_error(self) -> None:
        ctx = ActionContext(job_id="job-spotify-4", room="room-spotify", participant_identity="user-spotify")

        async def _fake_call(server_name, tool_name, params, legacy_handler=None):  # noqa: ANN001
            self.assertEqual(server_name, "spotify")
            self.assertEqual(tool_name, "spotify_play")
            self.assertEqual(params, {"query": "musica teste"})
            self.assertIsNone(legacy_handler)
            return (
                McpToolCallResult(
                    ok=False,
                    status="transport_error",
                    detail="spotify mcp unavailable",
                ),
                None,
                None,
            )

        with patch("actions.call_mcp_tool_with_legacy_fallback", side_effect=_fake_call):
            result = await dispatch_action("spotify_play", {"query": "musica teste"}, ctx, skip_confirmation=True, bypass_auth=True)

        self.assertFalse(result.success)
        self.assertFalse(result.fallback_used)
        self.assertEqual(result.evidence.get("provider"), "mcp")
        self.assertEqual(result.evidence.get("mcp_server"), "spotify")
        self.assertEqual(result.evidence.get("mcp_tool"), "spotify_play")


if __name__ == "__main__":
    unittest.main()
