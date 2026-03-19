import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import actions as actions_module
from evals import summarize_action_metrics, summarize_slo
from actions import (
    AUTHENTICATED_SESSIONS,
    CANARY_SESSION_OVERRIDES,
    ActionContext,
    ActionResult,
    FEATURE_FLAG_OVERRIDES,
    MEMORY_SCOPE_OVERRIDES,
    PENDING_CONFIRMATIONS,
    PARTICIPANT_PENDING_TOKENS,
    VOICE_STEP_UP_PENDING,
    _redact,
    _rpg_create_character_sheet,
    _rpg_create_threat_sheet,
    dispatch_action,
    record_autonomy_notice_delivery,
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


class _FakeAgentSession(_FakeSession):
    def __init__(self, items):
        super().__init__(items)
        self.spoken_messages: list[dict[str, object]] = []

    def say(self, text, *, allow_interruptions=True, add_to_chat_ctx=False):
        self.spoken_messages.append(
            {
                "text": text,
                "allow_interruptions": allow_interruptions,
                "add_to_chat_ctx": add_to_chat_ctx,
            }
        )
        return None


class _FakeVoiceStore:
    def __init__(self, score: float):
        self.score = score

    def verify_identity(self, *, participant_identity: str, embedding=None):  # noqa: ARG002
        class _Result:
            def __init__(self, score: float):
                self.score = score
                self.profile_name = "Guilherme"
                self.compared_profiles = 1
                self.method = "audio_embedding"

        return _Result(self.score)


class _FakeMemoryClient:
    def __init__(self):
        self.deleted_ids: list[str] = []

    async def search(self, query, filters=None):  # noqa: ARG002
        return {"results": [{"id": "m1", "memory": "segredo teste"}, {"id": "m2", "memory": "outra memoria"}]}

    async def delete(self, memory_id):
        self.deleted_ids.append(memory_id)


class _FakeEnrollVoiceStore:
    def enroll_profile(self, *, name: str, participant_identity: str, embedding=None):  # noqa: ARG002
        return None


class ActionsTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        PENDING_CONFIRMATIONS.clear()
        PARTICIPANT_PENDING_TOKENS.clear()
        AUTHENTICATED_SESSIONS.clear()
        VOICE_STEP_UP_PENDING.clear()
        MEMORY_SCOPE_OVERRIDES.clear()
        FEATURE_FLAG_OVERRIDES.clear()
        CANARY_SESSION_OVERRIDES.clear()
        actions_module.CANARY_ROLLOUT_PERCENT_OVERRIDE = None
        actions_module.AUTO_REMEDIATION_LAST_EXECUTION.clear()
        actions_module.CANARY_PROMOTION_LAST_EXECUTION.clear()
        actions_module.CONTROL_LOOP_BREACH_HISTORY.clear()
        actions_module.CONTROL_LOOP_FREEZE_LAST_TRIGGER.clear()
        actions_module.clear_domain_autonomy_mode()
        actions_module.clear_domain_trust()
        actions_module.clear_trust_drift()
        actions_module.set_killswitch_global(False)
        for domain in list(actions_module.get_killswitch_status().domains.keys()):
            actions_module.set_killswitch_domain(domain, False)
        actions_module.STATE_STORE.clear_all()

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
        from backend_mcp import McpToolCallResult
        session = _FakeSession([_FakeMessage("user", "sim, confirmo")])
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a", session=session)

        async def _fake_mcp(server_name, tool_name, params=None, legacy_handler=None):  # noqa: ANN001
            return (
                McpToolCallResult(
                    ok=True, status="ok",
                    structured_content={"success": True, "message": "ok"},
                    raw_result={"structuredContent": {"success": True}},
                ),
                None, None,
            )

        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            with patch("actions.call_mcp_tool_with_legacy_fallback", side_effect=_fake_mcp):
                await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)
                initial = await dispatch_action("turn_light_on", {"entity_id": "light.sala"}, ctx)
                token = str(initial.data["confirmation_token"])
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
        self.assertTrue(
            "bloqueada" in result.message or "modo privado" in result.message
        )

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
        with patch("actions.VOICE_PROFILE_STORE", _FakeVoiceStore(0.95)), patch(
            "actions.get_recent_voice_embedding", return_value=[0.1] * 54
        ):
            result = await dispatch_action("verify_voice_identity", {}, ctx)
        self.assertTrue(result.success)
        self.assertEqual(result.data.get("auth_method"), "voice")

    async def test_verify_voice_identity_medium_confidence_requires_stepup(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.VOICE_PROFILE_STORE", _FakeVoiceStore(0.8)), patch(
            "actions.get_recent_voice_embedding", return_value=[0.1] * 54
        ):
            result = await dispatch_action("verify_voice_identity", {}, ctx)
        self.assertFalse(result.success)
        self.assertTrue(result.data.get("step_up_required"))

    async def test_verify_voice_identity_requires_recent_audio(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.VOICE_PROFILE_STORE", _FakeVoiceStore(0.8)), patch(
            "actions.get_recent_voice_embedding", return_value=None
        ):
            result = await dispatch_action("verify_voice_identity", {}, ctx)
        self.assertFalse(result.success)
        self.assertEqual(result.error, "insufficient voice sample")

    async def test_enroll_voice_profile_requires_recent_audio(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.VOICE_PROFILE_STORE", _FakeEnrollVoiceStore()), patch(
            "actions.get_recent_voice_embedding", return_value=None
        ):
            result = await dispatch_action("enroll_voice_profile", {"name": "Guil"}, ctx)
        self.assertFalse(result.success)
        self.assertEqual(result.error, "insufficient voice sample")

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

    async def test_rpg_create_character_sheet_bridge_pipeline(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "RPG_CHARACTERS_DIR": os.path.join(tmp, "chars"),
                "RPG_CHARACTER_PDFS_DIR": os.path.join(tmp, "pdfs"),
            }
            with patch.dict(os.environ, env, clear=False):
                result = await _rpg_create_character_sheet(
                    {
                        "name": "TesteBridge",
                        "world": "tormenta20",
                        "race": "humano",
                        "class_name": "guerreiro",
                        "origin": "acolyte",
                        "level": 1,
                        "attributes": {
                            "forca": 16,
                            "destreza": 14,
                            "constituicao": 14,
                            "inteligencia": 10,
                            "sabedoria": 12,
                            "carisma": 8,
                        },
                    },
                    ctx,
                )
                json_exists = os.path.exists(result.data["sheet_json_path"])
                md_exists = os.path.exists(result.data["sheet_markdown_path"])
                pdf_exists = os.path.exists(result.data["sheet_pdf_path"])
        self.assertTrue(result.success)
        self.assertEqual(result.data["sheet_builder_source"], "t20-sheet-builder")
        self.assertEqual(result.data["sheet_pdf_status"], "created")
        self.assertTrue(json_exists)
        self.assertTrue(md_exists)
        self.assertTrue(pdf_exists)

    async def test_rpg_create_character_sheet_fallback_pipeline(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "RPG_CHARACTERS_DIR": os.path.join(tmp, "chars"),
                "RPG_CHARACTER_PDFS_DIR": os.path.join(tmp, "pdfs"),
            }
            with patch.dict(os.environ, env, clear=False):
                result = await _rpg_create_character_sheet(
                    {
                        "name": "TesteFallback",
                        "world": "tormenta20",
                        "race": "humano",
                        "class_name": "arcanista",
                        "origin": "acolyte",
                        "level": 1,
                    },
                    ctx,
                )
                pdf_exists = os.path.exists(result.data["sheet_pdf_path"])
        self.assertTrue(result.success)
        self.assertEqual(result.data["sheet_builder_source"], "fallback")
        self.assertEqual(result.data["sheet_generation_status"], "partial")
        self.assertTrue(result.data["sheet_generation_warnings"])
        self.assertEqual(result.data["sheet_pdf_status"], "created")
        self.assertTrue(pdf_exists)

    async def test_rpg_create_character_sheet_level_gt_one_is_partial_and_preserves_level(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "RPG_CHARACTERS_DIR": os.path.join(tmp, "chars"),
                "RPG_CHARACTER_PDFS_DIR": os.path.join(tmp, "pdfs"),
            }
            with patch.dict(os.environ, env, clear=False):
                result = await _rpg_create_character_sheet(
                    {
                        "name": "TesteNivel5",
                        "world": "tormenta20",
                        "race": "humano",
                        "class_name": "guerreiro",
                        "level": 5,
                    },
                    ctx,
                )
        self.assertTrue(result.success)
        self.assertEqual(result.data["sheet_builder_source"], "fallback")
        self.assertEqual(result.data["sheet_generation_status"], "partial")
        self.assertEqual(result.data["sheet_data"]["level"], 5)

    async def test_rpg_create_character_sheet_template_missing_returns_failed_pdf_status(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "RPG_CHARACTERS_DIR": os.path.join(tmp, "chars"),
                "RPG_CHARACTER_PDFS_DIR": os.path.join(tmp, "pdfs"),
                "RPG_CHARACTER_PDF_TEMPLATE_PATH": os.path.join(tmp, "missing.pdf"),
            }
            with patch.dict(os.environ, env, clear=False):
                result = await _rpg_create_character_sheet(
                    {"name": "SemTemplate", "world": "tormenta20"},
                    ctx,
                )
        self.assertTrue(result.success)
        self.assertEqual(result.data["sheet_pdf_status"], "failed")
        self.assertIsNone(result.data["sheet_pdf_path"])
        self.assertIn("template not found", result.data["sheet_pdf_error"] or "")

    async def test_rpg_create_threat_sheet_generates_files(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "RPG_THREATS_DIR": os.path.join(tmp, "threats"),
            }
            with patch.dict(os.environ, env, clear=False):
                result = await _rpg_create_threat_sheet(
                    {
                        "name": "Arauto do Eclipse",
                        "world": "tormenta20",
                        "role": "Solo",
                        "challenge_level": "10",
                        "threat_type": "Monstro",
                        "size": "Grande",
                        "is_boss": True,
                    },
                    ctx,
                )
                json_exists = os.path.exists(result.data["threat_json_path"])
                md_exists = os.path.exists(result.data["threat_markdown_path"])
                pdf_exists = os.path.exists(result.data["threat_pdf_path"])
        self.assertTrue(result.success)
        self.assertTrue(json_exists)
        self.assertTrue(md_exists)
        self.assertTrue(pdf_exists)
        self.assertEqual(result.data["threat_builder_source"], "jarvez-threat-generator")
        self.assertEqual(result.data["threat_data"]["combat_stats"]["defense"], 36)
        self.assertEqual(result.data["threat_data"]["resistance_assignments"]["Fortitude"], "strong")
        self.assertEqual(result.data["threat_data"]["ability_recommendation"]["min"], 2)
        self.assertTrue(result.data["threat_data"]["qualities"])
        self.assertTrue(result.data["threat_data"]["generated_abilities"])
        self.assertEqual(result.data["threat_data"]["generated_abilities"][0]["category"], "ofensiva")
        self.assertTrue(result.data["threat_data"]["boss_features"]["reactions"])
        self.assertTrue(result.data["threat_data"]["boss_features"]["legendary_actions"])
        self.assertTrue(result.data["threat_data"]["boss_features"]["phases"])
        self.assertEqual(result.data["threat_pdf_status"], "created")
        self.assertEqual(result.data["threat_generation_status"], "success")

    async def test_rpg_create_threat_sheet_supports_overrides(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "RPG_THREATS_DIR": os.path.join(tmp, "threats"),
            }
            with patch.dict(os.environ, env, clear=False):
                result = await _rpg_create_threat_sheet(
                    {
                        "name": "Ameaca Custom",
                        "challenge_level": "5",
                        "attacks_override": [{"name": "Mordida", "attack_bonus": 10, "damage": "20 dano", "action_type": "Padrao"}],
                        "abilities_override": [{"name": "Salto", "summary": "Move 12m", "category": "mobilidade"}],
                    },
                    ctx,
                )
        self.assertTrue(result.success)
        self.assertEqual(result.data["threat_data"]["attacks"][0]["name"], "Mordida")
        self.assertEqual(result.data["threat_data"]["abilities"][0]["name"], "Salto")
        self.assertTrue(result.data["threat_generation_warnings"])

    async def test_rpg_create_threat_sheet_rejects_invalid_nd(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        result = await _rpg_create_threat_sheet(
            {"name": "Ameaca Invalida", "challenge_level": "99"},
            ctx,
        )
        self.assertFalse(result.success)
        self.assertIn("challenge_level must be", result.error or "")

    async def test_open_desktop_resource_uses_site_alias(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)
            with patch("actions.webbrowser.open", return_value=True) as browser_open:
                result = await dispatch_action("open_desktop_resource", {"target": "youtube"}, ctx)

        self.assertTrue(result.success)
        self.assertEqual(result.data["target_kind"], "url")
        browser_open.assert_called_once()
        self.assertIn("youtube.com", browser_open.call_args.args[0])

    async def test_run_local_command_blocks_disallowed_command(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)
            result = await dispatch_action(
                "run_local_command",
                {"command": "format", "arguments": []},
                ctx,
                skip_confirmation=True,
            )

        self.assertFalse(result.success)
        self.assertIn("nao permitido", result.message.lower())

    async def test_git_clone_repository_runs_git_clone(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = os.path.join(temp_dir, "repo-clonado")
            with patch("actions.os.getenv") as getenv:
                def _fake_getenv(key, default=""):
                    if key == "JARVEZ_SECURITY_PIN":
                        return "1234"
                    return default

                getenv.side_effect = _fake_getenv
                await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)
                completed = subprocess.CompletedProcess(
                    args=["git", "clone"],
                    returncode=0,
                    stdout="cloned",
                    stderr="",
                )
                with patch("actions.subprocess.run", return_value=completed) as run_mock:
                    result = await dispatch_action(
                        "git_clone_repository",
                        {
                            "repository_url": "https://github.com/openai/openai-python.git",
                            "destination": destination,
                            "branch": "main",
                            "depth": 1,
                        },
                        ctx,
                        skip_confirmation=True,
                    )

        self.assertTrue(result.success)
        called_command = run_mock.call_args.args[0]
        self.assertEqual(called_command[:2], ["git", "clone"])
        self.assertIn("--branch", called_command)
        self.assertIn("--depth", called_command)
        self.assertEqual(result.data["destination"], destination)

    async def test_action_result_envelope_includes_trace_risk_policy_and_evidence(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        result = await dispatch_action("set_memory_scope", {"scope": "public"}, ctx)
        self.assertTrue(result.success)
        self.assertTrue(result.trace_id)
        self.assertTrue(result.risk)
        self.assertTrue(result.policy_decision)
        self.assertIsInstance(result.evidence, dict)
        self.assertIn("provider", result.evidence)
        self.assertIn("executed_at", result.evidence)

    async def test_skills_list_and_read_from_temp_directory(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = os.path.join(temp_dir, "demo")
            os.makedirs(skill_dir, exist_ok=True)
            skill_file = os.path.join(skill_dir, "SKILL.md")
            with open(skill_file, "w", encoding="utf-8") as handle:
                handle.write(
                    "---\n"
                    "name: demo-skill\n"
                    "description: skill de teste\n"
                    "tags: demo,test\n"
                    "---\n\n"
                    "Use esta skill para testar carregamento.\n"
                )
            with patch.dict(os.environ, {"JARVEZ_SKILLS_DIRS": temp_dir}, clear=False):
                listed = await dispatch_action("skills_list", {"query": "demo"}, ctx)
                self.assertTrue(listed.success)
                self.assertGreaterEqual(int(listed.data.get("skills_total", 0)), 1)

                read = await dispatch_action("skills_read", {"skill_name": "demo-skill"}, ctx)
                self.assertTrue(read.success)
                self.assertIn("skill_document", read.data)
                self.assertIn("Use esta skill", read.data["skill_document"]["excerpt"])

    async def test_subagent_spawn_status_and_cancel(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        spawn = await dispatch_action(
            "subagent_spawn",
            {"request": "Revise o codigo e me diga os riscos de release", "auto_complete": False},
            ctx,
        )
        self.assertTrue(spawn.success)
        self.assertIn("subagent_state", spawn.data)
        subagent_id = spawn.data["subagent_state"]["subagent_id"]
        self.assertTrue(subagent_id)

        status = await dispatch_action("subagent_status", {"subagent_id": subagent_id}, ctx)
        self.assertTrue(status.success)
        self.assertEqual(status.data["subagent_state"]["subagent_id"], subagent_id)

        cancelled = await dispatch_action("subagent_cancel", {"subagent_id": subagent_id}, ctx)
        self.assertTrue(cancelled.success)
        self.assertEqual(cancelled.data["subagent_state"]["status"], "cancelled")

    async def test_browser_agent_run_reports_missing_backend_configuration(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                if key == "JARVEZ_PLAYWRIGHT_MCP_URL":
                    return ""
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)
            result = await dispatch_action(
                "browser_agent_run",
                {
                    "request": "abrir a documentacao interna",
                    "allowed_domains": ["docs.example.com"],
                    "read_only": True,
                },
                ctx,
            )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "browser_agent_not_configured")
        self.assertEqual(result.data["browser_task"]["status"], "failed")

    async def test_workflow_run_returns_checkpointed_plan(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)
            result = await dispatch_action(
                "workflow_run",
                {"request": "tenho uma ideia: revisar o projeto e propor um patch seguro"},
                ctx,
            )
        self.assertTrue(result.success)
        self.assertEqual(result.data["workflow_state"]["status"], "awaiting_confirmation")
        self.assertEqual(result.data["workflow_state"]["workflow_type"], "idea_to_code")
        self.assertIn("task_plan", result.data["orchestration"])

    async def test_whatsapp_channel_status_reports_legacy_mode_when_mcp_missing(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                if key == "JARVEZ_WHATSAPP_MCP_URL":
                    return ""
                if key == "WHATSAPP_PHONE_NUMBER_ID":
                    return "123456"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)
            result = await dispatch_action("whatsapp_channel_status", {}, ctx)
        self.assertTrue(result.success)
        self.assertEqual(result.data["whatsapp_channel"]["mode"], "legacy_v1")

    async def test_killswitch_domain_blocks_action(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)
            enabled = await dispatch_action(
                "autonomy_killswitch",
                {"operation": "enable_domain", "domain": "spotify", "reason": "maintenance"},
                ctx,
            )
            self.assertTrue(enabled.success)

            blocked = await dispatch_action("spotify_status", {}, ctx)
            self.assertFalse(blocked.success)
            self.assertEqual(blocked.error, "policy denied")
            self.assertEqual(blocked.policy_decision, "deny")

            await dispatch_action(
                "autonomy_killswitch",
                {"operation": "disable_domain", "domain": "spotify"},
                ctx,
            )

    async def test_workspace_policy_blocks_run_local_command_outside_root(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                if key == "JARVEZ_ENFORCE_WORKSPACE_ONLY":
                    return "1"
                if key == "JARVEZ_WORKSPACE_ROOT":
                    return "C:\\workspace\\allowed"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)
            result = await dispatch_action(
                "run_local_command",
                {"command": "git", "arguments": ["status"], "working_directory": "C:\\Users\\Public"},
                ctx,
                skip_confirmation=True,
            )

        self.assertFalse(result.success)
        self.assertEqual(result.error, "workspace policy violation")

    async def test_policy_action_risk_matrix_returns_rows(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        result = await dispatch_action("policy_action_risk_matrix", {"query": "spotify"}, ctx)
        self.assertTrue(result.success)
        self.assertIn("risk_matrix", result.data)
        self.assertTrue(any("spotify_" in (row.get("action_name") or "") for row in result.data["risk_matrix"]))

    async def test_policy_domain_trust_status_returns_rows(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        actions_module.record_domain_outcome("shell", "success")
        result = await dispatch_action("policy_domain_trust_status", {}, ctx)
        self.assertTrue(result.success)
        self.assertIn("domain_trust", result.data)
        self.assertTrue(any((row.get("domain") == "shell") for row in result.data["domain_trust"]))

    async def test_policy_trust_drift_report_syncs_backend_state(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        result = await dispatch_action(
            "policy_trust_drift_report",
            {
                "signature": "ops:0.72:0.41",
                "rows": [
                    {
                        "domain": "ops",
                        "state": "drift",
                        "score_delta": 0.31,
                        "recommendation_delta_ms": 15000,
                        "retry_delta": 1,
                    }
                ],
            },
            ctx,
        )
        self.assertTrue(result.success)
        self.assertIn("trust_drift", result.data)
        self.assertTrue(any((row.get("domain") == "ops") for row in result.data["trust_drift"]))

        status = await dispatch_action("policy_domain_trust_status", {"domain": "ops"}, ctx)
        self.assertTrue(status.success)
        row = status.data["domain_trust"][0]
        self.assertEqual(row.get("domain"), "ops")
        self.assertTrue(row.get("trust_drift_active"))
        self.assertIsNotNone(row.get("trust_drift"))

    async def test_low_domain_trust_escalates_r2_to_confirmation_in_aggressive_mode(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        for _ in range(3):
            actions_module.record_domain_outcome("ops", "failure")

        result = await dispatch_action(
            "ops_incident_snapshot",
            {},
            ctx,
            bypass_auth=True,
        )

        self.assertFalse(result.success)
        self.assertTrue(result.data and result.data.get("confirmation_required"))
        self.assertEqual(result.policy_decision, "require_confirmation")
        self.assertEqual(result.data.get("policy", {}).get("domain"), "ops")

    async def test_domain_autonomy_mode_safe_escalates_policy_for_single_domain(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        actions_module.set_domain_autonomy_mode(
            "user-a",
            "room-a",
            "ops",
            "safe",
            reason="test_override",
            source="test_suite",
        )

        result = await dispatch_action(
            "policy_explain_decision",
            {"action_name": "ops_incident_snapshot"},
            ctx,
        )

        self.assertTrue(result.success)
        policy = result.data.get("policy", {})
        self.assertEqual(policy.get("autonomy_mode"), "aggressive")
        self.assertEqual(policy.get("domain_autonomy_mode"), "safe")
        self.assertEqual(policy.get("effective_autonomy_mode"), "safe")
        self.assertEqual(policy.get("domain_autonomy_reason"), "test_override")
        self.assertEqual(policy.get("domain_autonomy_source"), "test_suite")
        self.assertEqual(policy.get("decision"), "require_confirmation")

    async def test_trust_drift_escalates_ops_policy_in_aggressive_mode(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        synced = await dispatch_action(
            "policy_trust_drift_report",
            {
                "signature": "ops:0.70:0.40",
                "rows": [
                    {
                        "domain": "ops",
                        "state": "drift",
                        "score_delta": 0.3,
                        "recommendation_delta_ms": 15000,
                        "retry_delta": 1,
                    }
                ],
            },
            ctx,
        )
        self.assertTrue(synced.success)

        result = await dispatch_action(
            "ops_incident_snapshot",
            {},
            ctx,
            bypass_auth=True,
        )

        self.assertFalse(result.success)
        self.assertTrue(result.data and result.data.get("confirmation_required"))
        self.assertEqual(result.policy_decision, "require_confirmation")
        self.assertTrue(result.data.get("policy", {}).get("trust_drift_active"))
        self.assertEqual((result.data.get("autonomy_notice") or {}).get("scenario"), "trust_drift_breach")
        self.assertEqual((result.data.get("autonomy_notice") or {}).get("signature"), "trust_drift_breach:ops:require_confirmation")
        self.assertTrue((result.data.get("autonomy_notice") or {}).get("spoken_message"))

    async def test_trust_drift_uses_agent_audio_when_session_supports_say(self):
        session = _FakeAgentSession([])
        ctx = ActionContext(
            job_id="j1",
            room="room-a",
            participant_identity="user-a",
            session=session,
        )
        synced = await dispatch_action(
            "policy_trust_drift_report",
            {
                "signature": "ops:0.70:0.40",
                "rows": [
                    {
                        "domain": "ops",
                        "state": "drift",
                        "score_delta": 0.3,
                        "recommendation_delta_ms": 15000,
                        "retry_delta": 1,
                    }
                ],
            },
            ctx,
        )
        self.assertTrue(synced.success)

        result = await dispatch_action(
            "ops_incident_snapshot",
            {},
            ctx,
            bypass_auth=True,
        )

        notice = (result.data or {}).get("autonomy_notice") or {}
        self.assertEqual(notice.get("spoken_channel"), "agent_audio")
        self.assertEqual(len(session.spoken_messages), 1)
        self.assertIn("Reduzi a autonomia no dominio ops", str(session.spoken_messages[0].get("text", "")))
        self.assertTrue(bool(session.spoken_messages[0].get("allow_interruptions")))
        self.assertFalse(bool(session.spoken_messages[0].get("add_to_chat_ctx")))

        summary = await dispatch_action("evals_metrics_summary", {"limit": 100}, ctx)
        self.assertTrue(summary.success)
        self.assertGreaterEqual(
            int(
                (
                    summary.data.get("eval_metrics_summary", {})
                    .get("autonomy_notice", {})
                    .get("by_channel", {})
                    .get("agent_audio", {})
                    .get("total", 0)
                )
            ),
            1,
        )

        slo = await dispatch_action("evals_slo_report", {"limit": 100}, ctx)
        self.assertTrue(slo.success)
        self.assertGreater(
            float(
                slo.data.get("slo_report", {})
                .get("reliability", {})
                .get("autonomy_notice_agent_audio_rate", 0.0)
            ),
            0.0,
        )

        snapshot = await dispatch_action(
            "ops_incident_snapshot",
            {},
            ctx,
            skip_confirmation=True,
            bypass_auth=True,
        )
        self.assertTrue(snapshot.success)
        self.assertIn("autonomy_notice", snapshot.data.get("ops_incident_snapshot", {}))

    async def test_trust_drift_appears_in_metrics_and_incident_snapshot(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        synced = await dispatch_action(
            "policy_trust_drift_report",
            {
                "signature": "ops:0.70:0.40",
                "rows": [
                    {
                        "domain": "ops",
                        "state": "drift",
                        "score_delta": 0.3,
                        "recommendation_delta_ms": 15000,
                        "retry_delta": 1,
                    }
                ],
            },
            ctx,
        )
        self.assertTrue(synced.success)

        status = await dispatch_action("policy_domain_trust_status", {"domain": "ops"}, ctx)
        self.assertTrue(status.success)

        summary = await dispatch_action("evals_metrics_summary", {"limit": 100}, ctx)
        self.assertTrue(summary.success)
        self.assertIn("trust_drift", summary.data.get("eval_metrics_summary", {}))
        self.assertGreaterEqual(
            int(summary.data["eval_metrics_summary"]["trust_drift"].get("active_total", 0)),
            1,
        )

        slo = await dispatch_action("evals_slo_report", {"limit": 100}, ctx)
        self.assertTrue(slo.success)
        self.assertIn("trust_drift_active_rate", slo.data.get("slo_report", {}).get("reliability", {}))

        snapshot = await dispatch_action(
            "ops_incident_snapshot",
            {},
            ctx,
            skip_confirmation=True,
            bypass_auth=True,
        )
        self.assertTrue(snapshot.success)
        self.assertIn("trust_drift", snapshot.data.get("ops_incident_snapshot", {}))
        self.assertGreaterEqual(
            int(snapshot.data["ops_incident_snapshot"]["trust_drift"].get("active_total", 0)),
            1,
        )

    async def test_browser_tts_delivery_is_reported_in_metrics_and_slo(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        synced = await dispatch_action(
            "policy_trust_drift_report",
            {
                "signature": "ops:0.70:0.40",
                "rows": [
                    {
                        "domain": "ops",
                        "state": "drift",
                        "score_delta": 0.3,
                        "recommendation_delta_ms": 15000,
                        "retry_delta": 1,
                    }
                ],
            },
            ctx,
        )
        self.assertTrue(synced.success)

        result = await dispatch_action(
            "ops_incident_snapshot",
            {},
            ctx,
            bypass_auth=True,
        )
        self.assertFalse(result.success)
        notice = (result.data or {}).get("autonomy_notice") or {}
        self.assertTrue(bool(notice.get("trace_id")))
        self.assertFalse(bool(notice.get("spoken_channel")))

        record_autonomy_notice_delivery(
            participant_identity=ctx.participant_identity,
            room=ctx.room,
            trace_id=str(notice.get("trace_id")),
            signature=str(notice.get("signature") or ""),
            channel="browser_tts",
            level=str(notice.get("level") or ""),
            domain=str(notice.get("domain") or ""),
            scenario=str(notice.get("scenario") or ""),
        )

        summary = await dispatch_action("evals_metrics_summary", {"limit": 100}, ctx)
        self.assertTrue(summary.success)
        self.assertGreaterEqual(
            int(
                (
                    summary.data.get("eval_metrics_summary", {})
                    .get("autonomy_notice", {})
                    .get("by_channel", {})
                    .get("browser_tts", {})
                    .get("total", 0)
                )
            ),
            1,
        )
        self.assertIn("unconfirmed_total", summary.data.get("eval_metrics_summary", {}).get("autonomy_notice", {}))

        slo = await dispatch_action("evals_slo_report", {"limit": 100}, ctx)
        self.assertTrue(slo.success)
        reliability = slo.data.get("slo_report", {}).get("reliability", {})
        self.assertGreater(float(reliability.get("autonomy_notice_browser_tts_rate", 0.0)), 0.0)
        self.assertIn("autonomy_notice_unconfirmed_rate", reliability)

        snapshot = await dispatch_action(
            "ops_incident_snapshot",
            {},
            ctx,
            skip_confirmation=True,
            bypass_auth=True,
        )
        self.assertTrue(snapshot.success)
        self.assertIn("autonomy_notice", snapshot.data.get("ops_incident_snapshot", {}))

    def test_autonomy_notice_summary_distinguishes_agent_audio_browser_tts_and_unconfirmed(self):
        metrics = [
            {
                "type": "action_result",
                "timestamp": "2026-03-06T00:00:00Z",
                "payload": {
                    "action_name": "ops_incident_snapshot",
                    "success": False,
                    "risk": "R2",
                    "duration_ms": 120,
                    "evidence_provider": "internal",
                    "fallback_used": False,
                    "trace_id": "trace_agent_audio",
                    "autonomy_notice_active": True,
                    "autonomy_notice_level": "warning",
                    "autonomy_notice_channel": "agent_audio",
                },
            },
            {
                "type": "action_result",
                "timestamp": "2026-03-06T00:00:01Z",
                "payload": {
                    "action_name": "ops_incident_snapshot",
                    "success": False,
                    "risk": "R2",
                    "duration_ms": 120,
                    "evidence_provider": "internal",
                    "fallback_used": False,
                    "trace_id": "trace_browser_tts",
                    "autonomy_notice_active": True,
                    "autonomy_notice_level": "warning",
                    "autonomy_notice_channel": None,
                },
            },
            {
                "type": "action_result",
                "timestamp": "2026-03-06T00:00:02Z",
                "payload": {
                    "action_name": "ops_incident_snapshot",
                    "success": False,
                    "risk": "R2",
                    "duration_ms": 120,
                    "evidence_provider": "internal",
                    "fallback_used": False,
                    "trace_id": "trace_unconfirmed",
                    "autonomy_notice_active": True,
                    "autonomy_notice_level": "warning",
                    "autonomy_notice_channel": None,
                },
            },
            {
                "type": "autonomy_notice_delivery",
                "timestamp": "2026-03-06T00:00:03Z",
                "payload": {
                    "participant_identity": "user-a",
                    "room": "room-a",
                    "trace_id": "trace_browser_tts",
                    "signature": "trust_drift_breach:ops:require_confirmation",
                    "channel": "browser_tts",
                    "level": "warning",
                    "domain": "ops",
                    "scenario": "trust_drift_breach",
                },
            },
        ]

        summary = summarize_action_metrics(metrics)
        autonomy_notice = summary.get("autonomy_notice", {})
        self.assertEqual(int(autonomy_notice.get("active_total", -1)), 3)
        self.assertEqual(int(autonomy_notice.get("unconfirmed_total", -1)), 1)
        self.assertEqual(int(autonomy_notice.get("by_channel", {}).get("agent_audio", {}).get("total", 0)), 1)
        self.assertEqual(int(autonomy_notice.get("by_channel", {}).get("browser_tts", {}).get("total", 0)), 1)

        slo = summarize_slo(metrics)
        reliability = slo.get("reliability", {})
        self.assertEqual(float(reliability.get("autonomy_notice_agent_audio_rate", -1.0)), round(1 / 3, 4))
        self.assertEqual(float(reliability.get("autonomy_notice_browser_tts_rate", -1.0)), round(1 / 3, 4))
        self.assertEqual(float(reliability.get("autonomy_notice_unconfirmed_rate", -1.0)), round(1 / 3, 4))

    async def test_evals_list_and_run_baseline(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        listed = await dispatch_action("evals_list_scenarios", {}, ctx)
        self.assertTrue(listed.success)
        self.assertGreaterEqual(int(listed.data.get("eval_scenarios_total", 0)), 1)

        ran = await dispatch_action("evals_run_baseline", {}, ctx)
        self.assertTrue(ran.success)
        self.assertIn("eval_baseline_summary", ran.data)
        self.assertIn("eval_baseline_results", ran.data)

        metrics = await dispatch_action("evals_get_metrics", {"limit": 5}, ctx)
        self.assertTrue(metrics.success)
        self.assertIn("eval_metrics", metrics.data)

        summary = await dispatch_action("evals_metrics_summary", {"limit": 100}, ctx)
        self.assertTrue(summary.success)
        self.assertIn("eval_metrics_summary", summary.data)

        slo = await dispatch_action("evals_slo_report", {"limit": 100}, ctx)
        self.assertTrue(slo.success)
        self.assertIn("slo_report", slo.data)

    async def test_providers_health_check_and_feature_flags_runtime_override(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)
            health = await dispatch_action("providers_health_check", {"include_ping": False}, ctx)
            self.assertTrue(health.success)
            self.assertIn("providers_health", health.data)
            self.assertGreaterEqual(len(health.data["providers_health"]), 1)

            status_before = await dispatch_action("ops_feature_flags_status", {}, ctx)
            self.assertTrue(status_before.success)
            self.assertIn("feature_flags", status_before.data)

            toggle = await dispatch_action(
                "ops_feature_flags_set",
                {"feature": "skills_v1", "enabled": False},
                ctx,
                skip_confirmation=True,
            )
            self.assertTrue(toggle.success)

            status_after = await dispatch_action("ops_feature_flags_status", {}, ctx)
            self.assertTrue(status_after.success)
            values = status_after.data["feature_flags"]["values"]
            self.assertEqual(values.get("skills_v1"), False)

            await dispatch_action(
                "ops_feature_flags_set",
                {"feature": "skills_v1", "enabled": True},
                ctx,
                skip_confirmation=True,
            )

    async def test_ops_incident_snapshot_returns_operational_data(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)
            snapshot = await dispatch_action("ops_incident_snapshot", {"include_ping": False, "metrics_limit": 80}, ctx)

        self.assertTrue(snapshot.success)
        self.assertIn("ops_incident_snapshot", snapshot.data)
        payload = snapshot.data["ops_incident_snapshot"]
        self.assertIn("providers_health", payload)
        self.assertIn("feature_flags", payload)
        self.assertIn("kill_switch", payload)
        self.assertIn("metrics_summary", payload)
        self.assertIn("slo_report", payload)

    async def test_ops_apply_playbook_provider_degradation_and_restore(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)

            dry_run = await dispatch_action(
                "ops_apply_playbook",
                {"playbook": "provider_degradation", "dry_run": True},
                ctx,
                skip_confirmation=True,
            )
            self.assertTrue(dry_run.success)
            self.assertIn("ops_playbook_report", dry_run.data)
            self.assertTrue(bool(dry_run.data["ops_playbook_report"].get("dry_run")))

            apply_result = await dispatch_action(
                "ops_apply_playbook",
                {"playbook": "provider_degradation"},
                ctx,
                skip_confirmation=True,
            )
            self.assertTrue(apply_result.success)
            values = apply_result.data["feature_flags"]["values"]
            self.assertEqual(values.get("multi_model_router_v1"), False)
            self.assertEqual(values.get("subagents_v1"), False)

            restore = await dispatch_action(
                "ops_apply_playbook",
                {"playbook": "restore_runtime_overrides"},
                ctx,
                skip_confirmation=True,
            )
            self.assertTrue(restore.success)
            self.assertEqual(restore.data["feature_flags"]["overrides"], {})

    async def test_ops_canary_set_and_status(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)

            await dispatch_action(
                "ops_canary_set",
                {"operation": "enable_global"},
                ctx,
                skip_confirmation=True,
            )
            await dispatch_action(
                "ops_canary_set",
                {"operation": "enroll"},
                ctx,
                skip_confirmation=True,
            )
            status_active = await dispatch_action("ops_canary_status", {}, ctx)
            self.assertTrue(status_active.success)
            self.assertTrue(bool(status_active.data["canary_state"].get("active")))
            self.assertEqual(status_active.data["canary_state"].get("cohort"), "canary")

            await dispatch_action(
                "ops_canary_set",
                {"operation": "unenroll"},
                ctx,
                skip_confirmation=True,
            )
            status_stable = await dispatch_action("ops_canary_status", {}, ctx)
            self.assertTrue(status_stable.success)
            self.assertFalse(bool(status_stable.data["canary_state"].get("active")))
            self.assertEqual(status_stable.data["canary_state"].get("cohort"), "stable")

            await dispatch_action(
                "ops_canary_set",
                {"operation": "disable_global"},
                ctx,
                skip_confirmation=True,
            )

    async def test_ops_rollback_scenario_recover_to_stable(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)

            outage = await dispatch_action(
                "ops_rollback_scenario",
                {"scenario": "provider_outage"},
                ctx,
                skip_confirmation=True,
            )
            self.assertTrue(outage.success)

            recover = await dispatch_action(
                "ops_rollback_scenario",
                {"scenario": "recover_to_stable"},
                ctx,
                skip_confirmation=True,
            )
            self.assertTrue(recover.success)
            self.assertIn("ops_playbook_report", recover.data)
            self.assertEqual(recover.data["feature_flags"]["overrides"], {})
            self.assertEqual(recover.data["autonomy_mode"], "aggressive")

    async def test_ops_canary_rollout_set_updates_percent(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)
            await dispatch_action(
                "ops_canary_rollout_set",
                {"operation": "set_percent", "percent": 25},
                ctx,
                skip_confirmation=True,
            )
            status = await dispatch_action("ops_canary_status", {}, ctx)

        self.assertTrue(status.success)
        self.assertEqual(int(status.data["canary_state"].get("rollout_percent", -1)), 25)
        self.assertGreaterEqual(int(status.data["canary_state"].get("assignment_bucket", -1)), 0)
        self.assertLess(int(status.data["canary_state"].get("assignment_bucket", 100)), 100)

    async def test_ops_auto_remediate_dry_run_uses_reliability_breach(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)
            fake_metrics = {
                "updated_at": "2026-03-06T00:00:00Z",
                "items": [
                    {
                        "type": "action_result",
                        "timestamp": "2026-03-06T00:00:00Z",
                        "payload": {
                            "action_name": "search_docs",
                            "success": False,
                            "risk": "R1",
                            "duration_ms": 1400,
                            "evidence_provider": "local_mock",
                            "fallback_used": False,
                        },
                    }
                ],
            }
            healthy_providers = [
                {
                    "provider": "local_mock",
                    "configured": True,
                    "supports_tools": True,
                    "supports_realtime": False,
                    "status": "ok",
                }
            ]
            with patch("actions.read_metrics", return_value=fake_metrics), patch(
                "actions._collect_provider_health", return_value=healthy_providers
            ):
                remediation = await dispatch_action(
                    "ops_auto_remediate",
                    {"dry_run": True},
                    ctx,
                    skip_confirmation=True,
                )

        self.assertTrue(remediation.success)
        self.assertTrue(bool(remediation.data["ops_auto_remediation"].get("executed")))
        self.assertEqual(remediation.data["ops_auto_remediation"].get("scenario"), "reliability_breach")
        self.assertIn("ops_playbook_report", remediation.data)

    async def test_ops_auto_remediate_dry_run_uses_trust_drift_breach(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)
            await dispatch_action(
                "policy_trust_drift_report",
                {
                    "signature": "ops:0.70:0.40",
                    "rows": [
                        {
                            "domain": "ops",
                            "state": "drift",
                            "score_delta": 0.3,
                            "recommendation_delta_ms": 15000,
                            "retry_delta": 1,
                        }
                    ],
                },
                ctx,
            )
            fake_metrics = {
                "updated_at": "2026-03-06T00:00:00Z",
                "items": [
                    {
                        "type": "action_result",
                        "timestamp": "2026-03-06T00:00:00Z",
                        "payload": {
                            "action_name": "search_docs",
                            "success": True,
                            "risk": "R1",
                            "duration_ms": 700,
                            "evidence_provider": "local_mock",
                            "fallback_used": False,
                        },
                    }
                ],
            }
            healthy_providers = [
                {
                    "provider": "local_mock",
                    "configured": True,
                    "supports_tools": True,
                    "supports_realtime": False,
                    "status": "ok",
                }
            ]
            with patch("actions.read_metrics", return_value=fake_metrics), patch(
                "actions._collect_provider_health", return_value=healthy_providers
            ):
                remediation = await dispatch_action(
                    "ops_auto_remediate",
                    {"dry_run": True},
                    ctx,
                    skip_confirmation=True,
                )

        self.assertTrue(remediation.success)
        self.assertTrue(bool(remediation.data["ops_auto_remediation"].get("executed")))
        self.assertEqual(remediation.data["ops_auto_remediation"].get("scenario"), "trust_drift_breach")

    async def test_ops_auto_remediate_dry_run_uses_reliability_breach_when_notice_delivery_unconfirmed(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)
            fake_metrics = {
                "updated_at": "2026-03-06T00:00:00Z",
                "items": [
                    {
                        "type": "action_result",
                        "timestamp": "2026-03-06T00:00:00Z",
                        "payload": {
                            "action_name": "ops_incident_snapshot",
                            "success": False,
                            "risk": "R2",
                            "duration_ms": 700,
                            "evidence_provider": "internal",
                            "fallback_used": False,
                            "trace_id": "trace_notice_gap",
                            "autonomy_notice_active": True,
                            "autonomy_notice_level": "warning",
                            "autonomy_notice_channel": None,
                            "autonomy_notice_domain": "ops",
                        },
                    }
                ],
            }
            healthy_providers = [
                {
                    "provider": "local_mock",
                    "configured": True,
                    "supports_tools": True,
                    "supports_realtime": False,
                    "status": "ok",
                }
            ]
            with patch("actions.read_metrics", return_value=fake_metrics), patch(
                "actions._collect_provider_health", return_value=healthy_providers
            ):
                remediation = await dispatch_action(
                    "ops_auto_remediate",
                    {"dry_run": True},
                    ctx,
                    skip_confirmation=True,
                )

        self.assertTrue(remediation.success)
        self.assertTrue(bool(remediation.data["ops_auto_remediation"].get("executed")))
        self.assertEqual(remediation.data["ops_auto_remediation"].get("scenario"), "reliability_breach")
        signal = remediation.data["ops_auto_remediation"].get("signal") or {}
        self.assertTrue(bool(signal.get("autonomy_notice_delivery_breach")))
        self.assertGreater(float(signal.get("autonomy_notice_unconfirmed_rate") or 0.0), 0.0)
        report = remediation.data.get("ops_playbook_report") or {}
        self.assertIn("degrade_domain_autonomy", report.get("steps_executed") or [])
        self.assertTrue(
            any(
                (row.get("domain") == "ops" and row.get("mode") == "safe")
                for row in (remediation.data.get("ops_incident_snapshot", {}).get("domain_autonomy_modes") or [])
            )
        )
        self.assertTrue(
            any(
                row.get("domain") == "ops"
                and row.get("effective_autonomy_mode") == "safe"
                and row.get("containment_source") == "ops_playbook"
                and row.get("containment_reason") == "auto remediation"
                for row in (
                    remediation.data.get("ops_incident_snapshot", {}).get("domain_autonomy_status")
                    or []
                )
            )
        )
        self.assertIn("ops_playbook_report", remediation.data)

    async def test_ops_canary_promote_steps_up_when_gates_pass(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)
            await dispatch_action(
                "ops_canary_set",
                {"operation": "enable_global"},
                ctx,
                skip_confirmation=True,
            )
            await dispatch_action(
                "ops_canary_rollout_set",
                {"operation": "set_percent", "percent": 10},
                ctx,
                skip_confirmation=True,
            )

            base_payload = {
                "action_name": "search_docs",
                "risk": "R1",
                "duration_ms": 900,
                "evidence_provider": "local_mock",
                "fallback_used": False,
            }
            fake_items = []
            for index in range(12):
                fake_items.append(
                    {
                        "type": "action_result",
                        "timestamp": "2026-03-06T00:00:00Z",
                        "payload": {**base_payload, "success": True, "canary_cohort": "canary", "trace_id": f"c{index}"},
                    }
                )
            for index in range(12):
                fake_items.append(
                    {
                        "type": "action_result",
                        "timestamp": "2026-03-06T00:00:00Z",
                        "payload": {**base_payload, "success": True, "canary_cohort": "stable", "trace_id": f"s{index}"},
                    }
                )
            fake_metrics = {"updated_at": "2026-03-06T00:00:00Z", "items": fake_items}
            healthy_providers = [
                {
                    "provider": "local_mock",
                    "configured": True,
                    "supports_tools": True,
                    "supports_realtime": False,
                    "status": "ok",
                }
            ]
            with patch("actions.read_metrics", return_value=fake_metrics), patch(
                "actions._collect_provider_health", return_value=healthy_providers
            ):
                promoted = await dispatch_action(
                    "ops_canary_promote",
                    {
                        "dry_run": False,
                        "min_samples": 10,
                        "success_rate_min": 0.9,
                        "max_regression_vs_stable": 0.05,
                        "require_no_alerts": False,
                    },
                    ctx,
                    skip_confirmation=True,
                )

        self.assertTrue(promoted.success)
        self.assertIn("ops_canary_promotion", promoted.data)
        self.assertTrue(bool(promoted.data["ops_canary_promotion"].get("promoted")))
        self.assertEqual(int(promoted.data["canary_state"].get("rollout_percent", -1)), 25)

    async def test_ops_control_loop_tick_returns_combined_report(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)
            await dispatch_action(
                "ops_canary_set",
                {"operation": "enable_global"},
                ctx,
                skip_confirmation=True,
            )
            await dispatch_action(
                "ops_canary_rollout_set",
                {"operation": "set_percent", "percent": 10},
                ctx,
                skip_confirmation=True,
            )

            base_payload = {
                "action_name": "search_docs",
                "risk": "R1",
                "duration_ms": 850,
                "evidence_provider": "local_mock",
                "fallback_used": False,
                "success": True,
            }
            fake_metrics = {
                "updated_at": "2026-03-06T00:00:00Z",
                "items": [
                    {"type": "action_result", "timestamp": "2026-03-06T00:00:00Z", "payload": {**base_payload, "canary_cohort": "canary"}},
                    {"type": "action_result", "timestamp": "2026-03-06T00:00:00Z", "payload": {**base_payload, "canary_cohort": "stable"}},
                ]
                * 12,
            }
            healthy_providers = [
                {
                    "provider": "local_mock",
                    "configured": True,
                    "supports_tools": True,
                    "supports_realtime": False,
                    "status": "ok",
                }
            ]
            with patch("actions.read_metrics", return_value=fake_metrics), patch(
                "actions._collect_provider_health", return_value=healthy_providers
            ):
                tick = await dispatch_action(
                    "ops_control_loop_tick",
                    {"dry_run": True, "auto_remediate": True, "auto_promote_canary": True},
                    ctx,
                    skip_confirmation=True,
                )

        self.assertTrue(tick.success)
        self.assertIn("ops_control_tick", tick.data)
        self.assertIn("ops_auto_remediation", tick.data)
        self.assertIn("ops_canary_promotion", tick.data)

    async def test_ops_control_loop_tick_skips_promotion_on_trust_drift_breach(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)
            await dispatch_action(
                "policy_trust_drift_report",
                {
                    "signature": "ops:0.70:0.40",
                    "rows": [
                        {
                            "domain": "ops",
                            "state": "drift",
                            "score_delta": 0.3,
                            "recommendation_delta_ms": 15000,
                            "retry_delta": 1,
                        }
                    ],
                },
                ctx,
            )
            fake_metrics = {
                "updated_at": "2026-03-06T00:00:00Z",
                "items": [
                    {
                        "type": "action_result",
                        "timestamp": "2026-03-06T00:00:00Z",
                        "payload": {
                            "action_name": "search_docs",
                            "risk": "R1",
                            "duration_ms": 850,
                            "evidence_provider": "local_mock",
                            "fallback_used": False,
                            "success": True,
                            "canary_cohort": "stable",
                        },
                    }
                ]
                * 12,
            }
            healthy_providers = [
                {
                    "provider": "local_mock",
                    "configured": True,
                    "supports_tools": True,
                    "supports_realtime": False,
                    "status": "ok",
                }
            ]
            with patch("actions.read_metrics", return_value=fake_metrics), patch(
                "actions._collect_provider_health", return_value=healthy_providers
            ):
                tick = await dispatch_action(
                    "ops_control_loop_tick",
                    {"dry_run": True, "auto_remediate": True, "auto_promote_canary": True},
                    ctx,
                    skip_confirmation=True,
                )

        self.assertTrue(tick.success)
        self.assertEqual(
            (tick.data.get("ops_auto_remediation") or {}).get("scenario"),
            "trust_drift_breach",
        )
        self.assertEqual(
            (tick.data.get("ops_control_tick") or {}).get("promotion_skipped_reason"),
            "remediacao ativa em cenario `trust_drift_breach`.",
        )

    async def test_ops_control_loop_tick_applies_freeze_on_repeated_breach(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)

            fake_metrics = {
                "updated_at": "2026-03-06T00:00:00Z",
                "items": [
                    {
                        "type": "action_result",
                        "timestamp": "2026-03-06T00:00:00Z",
                        "payload": {
                            "action_name": "search_docs",
                            "success": False,
                            "risk": "R1",
                            "duration_ms": 1000,
                            "evidence_provider": "local_mock",
                            "fallback_used": False,
                            "canary_cohort": "stable",
                        },
                    }
                ],
            }
            healthy_providers = [
                {
                    "provider": "local_mock",
                    "configured": True,
                    "supports_tools": True,
                    "supports_realtime": False,
                    "status": "ok",
                }
            ]
            with patch("actions.read_metrics", return_value=fake_metrics), patch(
                "actions._collect_provider_health", return_value=healthy_providers
            ):
                tick = await dispatch_action(
                    "ops_control_loop_tick",
                    {
                        "dry_run": False,
                        "auto_remediate": True,
                        "auto_promote_canary": False,
                        "freeze_threshold": 1,
                        "freeze_window_seconds": 600,
                        "freeze_cooldown_seconds": 60,
                    },
                    ctx,
                    skip_confirmation=True,
                )

        self.assertTrue(tick.success)
        self.assertTrue(bool(tick.data["ops_control_tick"]["freeze"]["applied"]))
        self.assertTrue(bool((tick.data["kill_switch"] or {}).get("global_enabled")))

    async def test_ops_control_loop_tick_skips_promotion_when_notice_delivery_is_unconfirmed(self):
        ctx = ActionContext(job_id="j1", room="room-a", participant_identity="user-a")
        with patch("actions.os.getenv") as getenv:
            def _fake_getenv(key, default=""):
                if key == "JARVEZ_SECURITY_PIN":
                    return "1234"
                return default

            getenv.side_effect = _fake_getenv
            await dispatch_action("authenticate_identity", {"pin": "1234"}, ctx)
            fake_metrics = {
                "updated_at": "2026-03-06T00:00:00Z",
                "items": [
                    {
                        "type": "action_result",
                        "timestamp": "2026-03-06T00:00:00Z",
                        "payload": {
                            "action_name": "ops_incident_snapshot",
                            "success": False,
                            "risk": "R2",
                            "duration_ms": 700,
                            "evidence_provider": "internal",
                            "fallback_used": False,
                            "trace_id": "trace_notice_gap",
                            "autonomy_notice_active": True,
                            "autonomy_notice_level": "warning",
                            "autonomy_notice_channel": None,
                            "autonomy_notice_domain": "ops",
                            "canary_cohort": "stable",
                        },
                    }
                ]
                * 12,
            }
            healthy_providers = [
                {
                    "provider": "local_mock",
                    "configured": True,
                    "supports_tools": True,
                    "supports_realtime": False,
                    "status": "ok",
                }
            ]
            with patch("actions.read_metrics", return_value=fake_metrics), patch(
                "actions._collect_provider_health", return_value=healthy_providers
            ):
                tick = await dispatch_action(
                    "ops_control_loop_tick",
                    {"dry_run": True, "auto_remediate": True, "auto_promote_canary": True},
                    ctx,
                    skip_confirmation=True,
                )

        self.assertTrue(tick.success)
        self.assertEqual(
            (tick.data.get("ops_auto_remediation") or {}).get("scenario"),
            "reliability_breach",
        )
        signal = ((tick.data.get("ops_auto_remediation") or {}).get("signal") or {})
        self.assertTrue(bool(signal.get("autonomy_notice_delivery_breach")))
        self.assertEqual(
            (tick.data.get("ops_control_tick") or {}).get("promotion_skipped_reason"),
            "remediacao ativa em cenario `reliability_breach`.",
        )

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
