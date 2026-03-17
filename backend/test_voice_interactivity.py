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
from actions import ActionContext, dispatch_action
from backend_mcp import McpToolCallResult
from voice_interactivity import build_voice_interactivity_payload


class VoiceInteractivityTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        actions_module.STATE_STORE.clear_all()

    def test_supported_state_sequence_payloads(self) -> None:
        sequence = [
            build_voice_interactivity_payload(state=state, source="client")["state"]
            for state in ("idle", "listening", "thinking", "speaking", "idle")
        ]
        self.assertEqual(sequence, ["idle", "listening", "thinking", "speaking", "idle"])

    async def test_latency_sensitive_action_emits_preamble_and_execution(self) -> None:
        ctx = ActionContext(
            job_id="job-voice-1",
            room="room-voice",
            participant_identity="user-voice",
            session=object(),
        )
        published_payloads: list[dict[str, object]] = []

        async def _fake_publish(_session, payload):  # noqa: ANN001
            if isinstance(payload, dict):
                published_payloads.append(dict(payload))

        async def _fake_call(server_name, tool_name, params, legacy_handler=None):  # noqa: ANN001
            self.assertEqual(server_name, "spotify")
            self.assertEqual(tool_name, "spotify_status")
            self.assertIsNotNone(legacy_handler)
            return (
                McpToolCallResult(
                    ok=True,
                    status="ok",
                    structured_content={
                        "success": True,
                        "message": "Spotify configurado.",
                        "data": {"spotify_configured": True},
                    },
                    raw_result={"structuredContent": {"success": True}},
                ),
                None,
                None,
            )

        with patch("actions.call_mcp_tool_with_legacy_fallback", side_effect=_fake_call):
            with patch("actions.publish_session_event", side_effect=_fake_publish):
                with patch("actions._publish_session_snapshot_for_context", AsyncMock()):
                    result = await dispatch_action("spotify_status", {}, ctx)

        self.assertTrue(result.success)
        voice_states = [
            str(payload.get("voice_interactivity", {}).get("state"))
            for payload in published_payloads
            if payload.get("type") == "voice_interactivity_state"
        ]
        self.assertIn("confirming", voice_states)
        self.assertIn("executing", voice_states)
        self.assertEqual(
            actions_module.STATE_STORE.get_event_state(
                participant_identity="user-voice",
                room="room-voice",
                namespace="voice_interactivity",
            )["state"],
            "thinking",
        )

    async def test_failure_publishes_voice_error_and_retry_prompt(self) -> None:
        ctx = ActionContext(
            job_id="job-voice-2",
            room="room-voice",
            participant_identity="user-voice",
            session=object(),
        )

        async def _fake_call(server_name, tool_name, params, legacy_handler=None):  # noqa: ANN001
            self.assertEqual(server_name, "spotify")
            self.assertEqual(tool_name, "spotify_status")
            self.assertIsNotNone(legacy_handler)
            return (
                McpToolCallResult(
                    ok=True,
                    status="ok",
                    structured_content={
                        "success": False,
                        "message": "Spotify nao autenticado.",
                        "error": "spotify_auth_required",
                    },
                    raw_result={"structuredContent": {"success": False}},
                ),
                None,
                None,
            )

        with patch("actions.call_mcp_tool_with_legacy_fallback", side_effect=_fake_call):
            with patch("actions.publish_session_event", AsyncMock()):
                with patch("actions._publish_session_snapshot_for_context", AsyncMock()):
                    result = await dispatch_action("spotify_status", {}, ctx)

        self.assertFalse(result.success)
        payload = actions_module.STATE_STORE.get_event_state(
            participant_identity="user-voice",
            room="room-voice",
            namespace="voice_interactivity",
        )
        self.assertEqual(payload["state"], "error")
        self.assertIn("Quer", str(payload.get("spoken_message") or ""))
        self.assertEqual(payload["error_code"], "spotify_auth_required")


if __name__ == "__main__":
    unittest.main()
