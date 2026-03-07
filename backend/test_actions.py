import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from actions import (
    AUTHENTICATED_SESSIONS,
    ActionContext,
    ActionResult,
    MEMORY_SCOPE_OVERRIDES,
    PENDING_CONFIRMATIONS,
    PARTICIPANT_PENDING_TOKENS,
    VOICE_STEP_UP_PENDING,
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


class _FakeVoiceStore:
    def __init__(self, score: float):
        self.score = score

    def verify_identity(self, *, participant_identity: str):  # noqa: ARG002
        class _Result:
            def __init__(self, score: float):
                self.score = score
                self.profile_name = "Guilherme"

        return _Result(self.score)


class _FakeMemoryClient:
    def __init__(self):
        self.deleted_ids: list[str] = []

    async def search(self, query, filters=None):  # noqa: ARG002
        return {"results": [{"id": "m1", "memory": "segredo teste"}, {"id": "m2", "memory": "outra memoria"}]}

    async def delete(self, memory_id):
        self.deleted_ids.append(memory_id)


class ActionsTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        PENDING_CONFIRMATIONS.clear()
        PARTICIPANT_PENDING_TOKENS.clear()
        AUTHENTICATED_SESSIONS.clear()
        VOICE_STEP_UP_PENDING.clear()
        MEMORY_SCOPE_OVERRIDES.clear()

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
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)
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
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                if key == "HOME_ASSISTANT_ALLOWED_SERVICES":
                    return "light.turn_on,light.turn_off"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)
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
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)
            result = await dispatch_action("turn_light_on", {"entity_id": "light.sala"}, ctx)
        self.assertFalse(result.success)
        self.assertTrue(result.data and result.data.get("confirmation_required"))
        self.assertTrue(result.data and result.data.get("confirmation_token"))

    async def test_confirm_action_executes_when_token_valid(self):
        session = _FakeSession([_FakeMessage("user", "sim, confirmo")])
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a", session=session)

        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)
            initial = await dispatch_action("turn_light_on", {"entity_id": "light.sala"}, ctx)
            token = str(initial.data["confirmation_token"])

            with patch("actions._call_home_assistant", return_value=ActionResult(True, "ok")):
                result = await dispatch_action("confirm_action", {"confirmation_token": token}, ctx)

        self.assertTrue(result.success)
        self.assertEqual(result.message, "ok")

    async def test_confirm_action_fails_for_other_identity(self):
        owner_ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, owner_ctx)
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
        self.assertIn("bloqueada", result.message)

    async def test_confirm_action_fails_when_expired(self):
        session = _FakeSession([_FakeMessage("user", "sim, confirmo")])
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a", session=session)

        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)
            initial = await dispatch_action("turn_light_on", {"entity_id": "light.sala"}, ctx)
            token = str(initial.data["confirmation_token"])
            pending = PENDING_CONFIRMATIONS[token]
            pending.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            result = await dispatch_action("confirm_action", {"confirmation_token": token}, ctx)
        self.assertFalse(result.success)
        self.assertIn("expirado", result.message)

    async def test_authenticate_identity_requires_correct_pin(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            result = await dispatch_action("authenticate_identity", {"pin": "1111"}, ctx)
        self.assertFalse(result.success)
        self.assertIn("Falha na autenticacao", result.message)

    async def test_authenticate_identity_accepts_passphrase_only(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return ""
                if key == "JARVEZ_SECURITY_PASSPHRASE":
                    return "tony"
                return default

            getenv.side_effect = _fake_getenv
            result = await dispatch_action("authenticate_identity", {"passphrase": "Tony"}, ctx)
        self.assertTrue(result.success)
        self.assertEqual(result.data.get("auth_method"), "passphrase")

    async def test_authenticate_identity_accepts_security_phrase_alias(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return ""
                if key == "JARVEZ_SECURITY_PASSPHRASE":
                    return "tony"
                return default

            getenv.side_effect = _fake_getenv
            result = await dispatch_action("authenticate_identity", {"security_phrase": "tony"}, ctx)
        self.assertTrue(result.success)

    async def test_verify_voice_identity_high_confidence_authenticates(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.VOICE_PROFILE_STORE", _FakeVoiceStore(0.95)):
            result = await dispatch_action("verify_voice_identity", {}, ctx)
        self.assertTrue(result.success)
        self.assertEqual(result.data.get("auth_method"), "voice")

    async def test_verify_voice_identity_medium_confidence_requires_stepup(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.VOICE_PROFILE_STORE", _FakeVoiceStore(0.8)):
            result = await dispatch_action("verify_voice_identity", {}, ctx)
        self.assertFalse(result.success)
        self.assertTrue(result.data.get("step_up_required"))

    async def test_set_memory_scope(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        result = await dispatch_action("set_memory_scope", {"scope": "private"}, ctx)
        self.assertTrue(result.success)

    async def test_forget_memory_public(self):
        fake_memory = _FakeMemoryClient()
        ctx = ActionContext(
            job_id="j1",
            room="room-a",
            participant_identity="user-a",
            memory_client=fake_memory,
            user_id="user-a",
        )
        result = await dispatch_action("forget_memory", {"query": "segredo", "scope": "public", "limit": 1}, ctx)
        self.assertTrue(result.success)
        self.assertEqual(fake_memory.deleted_ids, ["m1"])

    async def test_auth_gate_blocks_sensitive_action_without_auth(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        result = await dispatch_action("turn_light_on", {"entity_id": "light.sala"}, ctx)
        self.assertFalse(result.success)
        self.assertTrue(result.data and result.data.get("authentication_required"))

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
