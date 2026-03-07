import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from actions import (
    ActionContext,
    ActionResult,
    PENDING_CONFIRMATIONS,
    PARTICIPANT_PENDING_TOKENS,
    _redact,
    dispatch_action,
    validate_params,
)


class _FakeMessage:
    def __init__(self, role: str, content):
        self.role = role
        self.content = content


class _FakeHistory:
    def __init__(self, items):
        self.items = items


class _FakeSession:
    def __init__(self, items):
        self.history = _FakeHistory(items)


class ActionsTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        PENDING_CONFIRMATIONS.clear()
        PARTICIPANT_PENDING_TOKENS.clear()

    def test_validate_params_success(self):
        ok, err = validate_params(
            {"entity_id": "light.sala"},
            {
                "type": "object",
                "properties": {"entity_id": {"type": "string"}},
                "required": ["entity_id"],
                "additionalProperties": False,
            },
        )
        self.assertTrue(ok)
        self.assertIsNone(err)

    def test_validate_params_missing_required(self):
        ok, err = validate_params(
            {},
            {
                "type": "object",
                "properties": {"entity_id": {"type": "string"}},
                "required": ["entity_id"],
                "additionalProperties": False,
            },
        )
        self.assertFalse(ok)
        self.assertIn("missing required parameter", err or "")

    async def test_brightness_out_of_range(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        result = await dispatch_action(
            "set_light_brightness",
            {"entity_id": "light.sala", "brightness": 999},
            ctx,
        )
        self.assertFalse(result.success)
        self.assertIn("Invalid parameters", result.message)

    async def test_call_service_blocked_by_allowlist(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "HOME_ASSISTANT_ALLOWED_SERVICES":
                    return "light.turn_on,light.turn_off"
                return default

            getenv.side_effect = _fake_getenv
            result = await dispatch_action(
                "call_service",
                {
                    "domain": "switch",
                    "service": "turn_on",
                    "service_data": {"entity_id": "switch.tomada"},
                },
                ctx,
                skip_confirmation=True,
            )
        self.assertFalse(result.success)
        self.assertIn("Servico nao permitido", result.message)

    async def test_sensitive_action_returns_confirmation_required(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        result = await dispatch_action("turn_light_on", {"entity_id": "light.sala"}, ctx)
        self.assertFalse(result.success)
        self.assertTrue(result.data and result.data.get("confirmation_required"))
        self.assertTrue(result.data and result.data.get("confirmation_token"))

    async def test_confirm_action_executes_when_token_valid(self):
        session = _FakeSession([_FakeMessage("user", "sim, confirmo")])
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a", session=session)

        initial = await dispatch_action("turn_light_on", {"entity_id": "light.sala"}, ctx)
        token = str(initial.data["confirmation_token"])

        with patch("actions._call_home_assistant", return_value=ActionResult(True, "ok")):
            result = await dispatch_action("confirm_action", {"confirmation_token": token}, ctx)

        self.assertTrue(result.success)
        self.assertEqual(result.message, "ok")

    async def test_confirm_action_fails_for_other_identity(self):
        owner_ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        initial = await dispatch_action("turn_light_on", {"entity_id": "light.sala"}, owner_ctx)
        token = str(initial.data["confirmation_token"])

        other_session = _FakeSession([_FakeMessage("user", "sim, confirmo")])
        other_ctx = ActionContext(
            job_id="j2",
            room="room-a",
            participant_identity="user-b",
            session=other_session,
        )
        result = await dispatch_action("confirm_action", {"confirmation_token": token}, other_ctx)
        self.assertFalse(result.success)
        self.assertIn("outro participante", result.message)

    async def test_confirm_action_fails_when_expired(self):
        session = _FakeSession([_FakeMessage("user", "sim, confirmo")])
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a", session=session)

        initial = await dispatch_action("turn_light_on", {"entity_id": "light.sala"}, ctx)
        token = str(initial.data["confirmation_token"])
        pending = PENDING_CONFIRMATIONS[token]
        pending.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)

        result = await dispatch_action("confirm_action", {"confirmation_token": token}, ctx)
        self.assertFalse(result.success)
        self.assertIn("expirado", result.message)

    def test_redaction_hides_secret_fields(self):
        redacted = _redact(
            {
                "token": "abc",
                "nested": {
                    "api_key": "123",
                    "ok": "value",
                },
            }
        )
        self.assertEqual(redacted["token"], "[REDACTED]")
        self.assertEqual(redacted["nested"]["api_key"], "[REDACTED]")
        self.assertEqual(redacted["nested"]["ok"], "value")


if __name__ == "__main__":
    unittest.main()
