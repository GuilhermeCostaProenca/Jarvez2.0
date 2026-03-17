from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import unittest

from actions_core import ActionContext, ActionResult
from actions_domains.home_assistant import (
    call_service as home_assistant_call_service,
    git_clone_repository as home_assistant_git_clone_repository,
    open_desktop_resource as home_assistant_open_desktop_resource,
    run_local_command as home_assistant_run_local_command,
    turn_light_on as home_assistant_turn_light_on,
)
from actions_domains.ac import (
    ac_apply_preset,
    ac_configure_arrival_prefs,
    ac_prepare_arrival,
    ac_send_command,
    ac_set_mode,
)
from actions_domains.code_actions import (
    code_propose_change_action,
    code_read_file_action,
    code_run_command_action,
    code_search_repo,
    code_worker_status_action,
)
from actions_domains.codex import codex_cancel_task_action, codex_exec_status_action
from actions_domains.onenote import onenote_append_to_page, onenote_list_pages
from actions_domains.ops import (
    ops_apply_playbook_action,
    ops_auto_remediate_action,
    ops_canary_rollout_set_action,
    ops_canary_promote_action,
    ops_canary_set_action,
    ops_control_loop_tick_action,
    ops_feature_flags_set_action,
    ops_incident_snapshot_action,
    ops_rollback_scenario_action,
)
from actions_domains.orchestration import (
    providers_health_check_action,
    skills_list_action,
    subagent_cancel_action,
    subagent_spawn_action,
)
from actions_domains.policy import (
    autonomy_killswitch_action,
    autonomy_set_mode_action,
    policy_trust_drift_report_action,
)
from actions_domains.projects import (
    github_find_repo_action,
    project_list_action,
    project_update_action,
)
from actions_domains.rpg import (
    rpg_assume_character,
    rpg_clear_character_mode,
    rpg_create_character_sheet,
    rpg_create_threat_sheet,
    rpg_get_character_mode,
    rpg_get_knowledge_stats,
    rpg_ideate_next_session,
    rpg_reindex_sources,
    rpg_save_lore_note,
    rpg_search_knowledge,
    rpg_session_recording,
    rpg_write_session_summary,
)
from actions_domains.research import save_web_briefing_schedule
from actions_domains.session import confirm_action, set_persona_mode_action
from actions_domains.spotify import spotify_play, spotify_transfer_playback
from actions_domains.thinq import thinq_control_device, thinq_get_device_profile, thinq_status
from actions_domains.whatsapp import whatsapp_send_text


class ActionsDomainsSplitTests(unittest.IsolatedAsyncioTestCase):
    async def test_save_web_briefing_schedule_validates_time(self) -> None:
        ctx = ActionContext(job_id="j", room="r", participant_identity="p")
        result = await save_web_briefing_schedule(
            {"query": "ia", "time_of_day": "25:00"},
            ctx,
            collapse_spaces=lambda text: text.strip(),
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "invalid time_of_day")

    async def test_set_persona_mode_action_runs_callback(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        called: list[str] = []

        result = await set_persona_mode_action(
            {"mode": "rpg"},
            ctx,
            normalize_persona_mode=lambda value: value.strip().lower(),
            persona_modes={"default": {"label": "Default", "style": "x"}, "rpg": {"label": "RPG", "style": "y"}},
            set_persona_mode=lambda _pid, _room, _mode: "rpg",
            persona_payload=lambda mode: {"persona_mode": mode},
            on_mode_applied=lambda mode: called.append(mode),
        )
        self.assertTrue(result.success)
        self.assertEqual(called, ["rpg"])
        self.assertEqual(result.data["applied_persona_mode"], "rpg")

    async def test_confirm_action_requires_explicit_confirmation(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid", session=object())
        pending = SimpleNamespace(
            token="tok",
            action_name="do_it",
            params={"x": 1},
            participant_identity="pid",
            room="room",
            expires_at=object(),
        )
        result = await confirm_action(
            {"confirmation_token": "tok"},
            ctx,
            peek_confirmation=lambda _token: pending,
            pop_confirmation=lambda _token: pending,
            extract_last_user_text=lambda _session: "talvez",
            is_explicit_confirmation=lambda _text: False,
            remaining_seconds=lambda _expires_at: 30,
            dispatch_action=lambda _name, _params, _ctx: _async_result(ActionResult(True, "ok")),
        )
        self.assertFalse(result.success)
        self.assertEqual(result.data["confirmation_token"], "tok")

    async def test_whatsapp_send_text_sets_success_message(self) -> None:
        ctx = ActionContext(job_id="j", room="r", participant_identity="p")
        result = await whatsapp_send_text(
            {"to": "(11) 99999-9999", "text": "oi"},
            ctx,
            normalize_whatsapp_to=lambda _raw: "5511999999999",
            whatsapp_send_message=lambda _payload: ActionResult(success=True, message="raw", data={}),
        )
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Mensagem enviada para 5511999999999.")

    async def test_spotify_play_query_searches_and_plays_track(self) -> None:
        ctx = ActionContext(job_id="j", room="r", participant_identity="p")
        calls: list[tuple[str, str]] = []

        def _spotify_api_request(method, endpoint, **kwargs):
            calls.append((method, endpoint))
            if method == "GET" and endpoint == "search":
                return {
                    "tracks": {
                        "items": [
                            {
                                "uri": "spotify:track:123",
                                "name": "Song",
                                "artists": [{"name": "Artist"}],
                            }
                        ]
                    }
                }, None
            if method == "PUT" and endpoint == "me/player/play":
                return {}, None
            self.fail(f"unexpected call: {method} {endpoint}")

        result = await spotify_play(
            {"query": "song"},
            ctx,
            coerce_optional_str=lambda value: str(value).strip() if value else None,
            normalize_spotify_uri=lambda value: value.strip(),
            spotify_find_device=lambda _name, _device_id: (None, None),
            spotify_api_request=_spotify_api_request,
            is_spotify_restriction_error=lambda _error: False,
            spotify_remember_device_alias=lambda _alias, _device_id: None,
        )

        self.assertTrue(result.success)
        self.assertEqual(result.data["uri"], "spotify:track:123")
        self.assertIn(("GET", "search"), calls)
        self.assertIn(("PUT", "me/player/play"), calls)

    async def test_spotify_transfer_playback_returns_error_when_device_missing(self) -> None:
        ctx = ActionContext(job_id="j", room="r", participant_identity="p")
        result = await spotify_transfer_playback(
            {"device_name": "sala"},
            ctx,
            coerce_optional_str=lambda value: str(value).strip() if value else None,
            spotify_find_device=lambda _name, _device_id: (None, None),
            spotify_api_request=lambda _method, _endpoint, **_kwargs: ({}, None),
            spotify_remember_device_alias=lambda _alias, _device_id: None,
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "device not found")

    async def test_onenote_list_pages_requires_section_filter(self) -> None:
        ctx = ActionContext(job_id="j", room="r", participant_identity="p")
        result = await onenote_list_pages(
            {},
            ctx,
            onenote_api_request=lambda _method, _endpoint, **_kwargs: ({}, None),
            quote_path_segment=lambda value: value,
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "missing section")

    async def test_onenote_append_to_page_escapes_html_content(self) -> None:
        ctx = ActionContext(job_id="j", room="r", participant_identity="p")
        captured: dict[str, object] = {}

        def _onenote_api_request(method, endpoint, **kwargs):
            captured["method"] = method
            captured["endpoint"] = endpoint
            captured["body"] = kwargs.get("body")
            return {}, None

        result = await onenote_append_to_page(
            {"page_id": "p1", "content": "<b>oi</b>"},
            ctx,
            onenote_api_request=_onenote_api_request,
            quote_path_segment=lambda value: value,
        )

        self.assertTrue(result.success)
        self.assertEqual(captured["method"], "PATCH")
        self.assertEqual(captured["endpoint"], "me/onenote/pages/p1/content")
        self.assertIn("&lt;b&gt;oi&lt;/b&gt;", str(captured["body"]))

    async def test_home_assistant_open_desktop_resource_requires_target(self) -> None:
        ctx = ActionContext(job_id="j", room="r", participant_identity="p")
        result = await home_assistant_open_desktop_resource(
            {},
            ctx,
            resolve_open_resource_target=lambda _target, _kind: ("url", "https://example.com", None),
            open_browser=lambda _url: True,
            has_startfile=False,
            startfile=lambda _path: None,
            launch_detached=lambda _command, cwd=None: None,
            workspace_root=lambda: Path("."),
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "missing target")

    async def test_home_assistant_run_local_command_validates_arguments(self) -> None:
        ctx = ActionContext(job_id="j", room="r", participant_identity="p")
        result = await home_assistant_run_local_command(
            {"command": "git", "arguments": "not-a-list"},
            ctx,
            resolve_local_command=lambda _command: ("git", None),
            resolve_local_path=lambda _path, must_exist=False: Path("."),
            workspace_root=lambda: Path("."),
            launch_detached=lambda _command, cwd=None: None,
            trim_process_output=lambda value: value,
            run_process=lambda *_args, **_kwargs: None,
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "invalid arguments")

    async def test_home_assistant_call_service_blocks_disallowed_service(self) -> None:
        ctx = ActionContext(job_id="j", room="r", participant_identity="p")
        result = await home_assistant_call_service(
            {"domain": "switch", "service": "turn_on", "service_data": {"entity_id": "switch.a"}},
            ctx,
            is_allowed_service=lambda _domain, _service: False,
            call_home_assistant=lambda **_kwargs: ActionResult(success=True, message="ok"),
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "service not in allowlist")

    async def test_home_assistant_turn_light_on_delegates_to_call_service(self) -> None:
        ctx = ActionContext(job_id="j", room="r", participant_identity="p")
        captured: dict[str, object] = {}

        async def _call_service(params, _ctx):
            captured["params"] = params
            return ActionResult(success=True, message="ok")

        result = await home_assistant_turn_light_on(
            {"entity_id": "light.sala"},
            ctx,
            call_service=_call_service,
        )
        self.assertTrue(result.success)
        self.assertEqual(captured["params"]["domain"], "light")
        self.assertEqual(captured["params"]["service"], "turn_on")

    async def test_home_assistant_git_clone_requires_repository_url(self) -> None:
        ctx = ActionContext(job_id="j", room="r", participant_identity="p")
        result = await home_assistant_git_clone_repository(
            {},
            ctx,
            resolve_local_path=lambda _path, must_exist=False: Path("."),
            workspace_root=lambda: Path("."),
            trim_process_output=lambda value: value,
            run_process=lambda *_args, **_kwargs: None,
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "missing repository url")

    async def test_thinq_status_reports_partial_when_devices_fail(self) -> None:
        ctx = ActionContext(job_id="j", room="r", participant_identity="p")
        result = await thinq_status(
            {},
            ctx,
            thinq_api_request=lambda _method, _path, require_auth=False: ({"status": "ok"}, None),
            thinq_list_devices_payload=lambda: (
                None,
                ActionResult(success=False, message="erro", error="request failed"),
            ),
            thinq_pat=lambda: "token",
            thinq_country=lambda: "BR",
            thinq_api_base=lambda: "https://api.example.com",
        )
        self.assertTrue(result.success)
        self.assertEqual(result.message, "ThinQ parcialmente configurado.")
        self.assertEqual(result.data["devices_error"], "request failed")

    async def test_thinq_get_device_profile_uses_encoded_device_id(self) -> None:
        ctx = ActionContext(job_id="j", room="r", participant_identity="p")
        captured: dict[str, object] = {}
        device = {"id": "device/1", "alias": "AC"}

        def _thinq_api_request(method, path, **_kwargs):
            captured["method"] = method
            captured["path"] = path
            return {"profile": {"ok": True}}, None

        result = await thinq_get_device_profile(
            {"device_id": "device/1"},
            ctx,
            coerce_optional_str=lambda value: str(value).strip() if value else None,
            thinq_find_device=lambda **_kwargs: (device, None),
            thinq_api_request=_thinq_api_request,
            thinq_extract_device_id=lambda item: str(item["id"]),
            thinq_extract_device_alias=lambda item: str(item["alias"]),
            thinq_simplify_device=lambda item: {"id": item["id"]},
            quote_path_segment=lambda value: value.replace("/", "%2F"),
        )

        self.assertTrue(result.success)
        self.assertEqual(captured["method"], "GET")
        self.assertEqual(captured["path"], "devices/device%2F1/profile")

    async def test_thinq_control_device_requires_command_object(self) -> None:
        ctx = ActionContext(job_id="j", room="r", participant_identity="p")
        result = await thinq_control_device(
            {"device_id": "abc"},
            ctx,
            coerce_optional_str=lambda value: str(value).strip() if value else None,
            thinq_find_device=lambda **_kwargs: ({"id": "abc", "alias": "AC"}, None),
            thinq_api_request=lambda _method, _path, **_kwargs: ({}, None),
            thinq_extract_device_id=lambda item: str(item["id"]),
            thinq_extract_device_alias=lambda item: str(item["alias"]),
            thinq_simplify_device=lambda item: {"id": item["id"]},
            quote_path_segment=lambda value: value,
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "missing or invalid command object")

    async def test_ac_set_mode_requires_mode(self) -> None:
        ctx = ActionContext(job_id="j", room="r", participant_identity="p")
        result = await ac_set_mode(
            {},
            ctx,
            coerce_optional_str=lambda value: str(value).strip() if value else None,
            normalize_label=lambda value: value.strip().lower(),
            ac_send_command=lambda _params, _ctx: _async_result(ActionResult(success=True, message="ok")),
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "missing mode")

    async def test_ac_send_command_requires_command_object(self) -> None:
        ctx = ActionContext(job_id="j", room="r", participant_identity="p")
        result = await ac_send_command(
            {"device_name": "ac"},
            ctx,
            coerce_optional_str=lambda value: str(value).strip() if value else None,
            thinq_find_device=lambda **_kwargs: ({"id": "ac-1", "alias": "AC Sala"}, None),
            thinq_api_request=lambda _method, _path, **_kwargs: ({}, None),
            thinq_extract_device_id=lambda item: str(item["id"]),
            thinq_extract_device_alias=lambda item: str(item["alias"]),
            thinq_simplify_device=lambda item: {"id": item["id"]},
            quote_path_segment=lambda value: value,
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "missing or invalid command object")

    async def test_ac_apply_preset_rejects_unknown_preset(self) -> None:
        ctx = ActionContext(job_id="j", room="r", participant_identity="p")
        result = await ac_apply_preset(
            {"preset": "aleatorio"},
            ctx,
            coerce_optional_str=lambda value: str(value).strip() if value else None,
            normalize_label=lambda value: value.strip().lower(),
            ac_turn_on=lambda _params, _ctx: _async_result(ActionResult(success=True, message="ok")),
            ac_set_mode=lambda _params, _ctx: _async_result(ActionResult(success=True, message="ok")),
            ac_set_temperature=lambda _params, _ctx: _async_result(ActionResult(success=True, message="ok")),
            ac_set_fan_speed=lambda _params, _ctx: _async_result(ActionResult(success=True, message="ok")),
            ac_set_sleep_timer=lambda _params, _ctx: _async_result(ActionResult(success=True, message="ok")),
            ac_set_swing=lambda _params, _ctx: _async_result(ActionResult(success=True, message="ok")),
            ac_set_power_save=lambda _params, _ctx: _async_result(ActionResult(success=True, message="ok")),
        )
        self.assertFalse(result.success)
        self.assertIn("unsupported preset", result.error or "")

    async def test_ac_configure_arrival_prefs_validates_thresholds(self) -> None:
        ctx = ActionContext(job_id="j", room="r", participant_identity="p")
        result = await ac_configure_arrival_prefs(
            {"vent_only_threshold": 30, "hot_threshold": 28},
            ctx,
            load_ac_arrival_prefs=lambda: {},
            save_ac_arrival_prefs=lambda _payload: None,
            thinq_default_ac_name=lambda: "ac-sala",
            coerce_optional_str=lambda value: str(value).strip() if value else None,
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "invalid thresholds")

    async def test_ac_prepare_arrival_dry_run_returns_strategy(self) -> None:
        ctx = ActionContext(job_id="j", room="r", participant_identity="p")
        result = await ac_prepare_arrival(
            {"dry_run": True},
            ctx,
            load_ac_arrival_prefs=lambda: {"desired_temperature": 23.0, "hot_threshold": 28.0, "vent_only_threshold": 25.0},
            thinq_default_ac_name=lambda: "ac-sala",
            coerce_optional_str=lambda value: str(value).strip() if value else None,
            ac_get_status=lambda _params, _ctx: _async_result(
                ActionResult(
                    success=True,
                    message="ok",
                    data={"state": {"temperature": {"currentTemperature": 29}}},
                )
            ),
            ac_turn_on=lambda _params, _ctx: _async_result(ActionResult(success=True, message="ok")),
            ac_set_mode=lambda _params, _ctx: _async_result(ActionResult(success=True, message="ok")),
            ac_set_temperature=lambda _params, _ctx: _async_result(ActionResult(success=True, message="ok")),
            ac_set_fan_speed=lambda _params, _ctx: _async_result(ActionResult(success=True, message="ok")),
            ac_set_swing=lambda _params, _ctx: _async_result(ActionResult(success=True, message="ok")),
        )
        self.assertTrue(result.success)
        self.assertEqual(result.data["strategy"], "cool")
        self.assertFalse(result.data["applied"])

    async def test_project_list_action_returns_catalog_payload(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")

        class _Catalog:
            def list_projects(self, include_inactive=False):
                _ = include_inactive
                return [SimpleNamespace(project_id="p1", name="Jarvez")]

        result = await project_list_action(
            {},
            ctx,
            get_project_catalog=lambda: _Catalog(),
            project_record_to_payload=lambda item: {"project_id": item.project_id, "name": item.name},
            active_project_payload=lambda _pid, _room: {"active_project": None},
            capability_payload=lambda _pid, _room: {"capability_mode": "default"},
        )
        self.assertTrue(result.success)
        self.assertEqual(result.data["projects"][0]["project_id"], "p1")

    async def test_project_update_action_requires_project_id(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await project_update_action(
            {},
            ctx,
            get_project_catalog=lambda: object(),
            get_active_project=lambda _pid, _room: None,
            clear_active_project=lambda _pid, _room: None,
            set_active_project_from_record=lambda _record, _ctx, **_kwargs: None,
            project_record_to_payload=lambda _item: {},
            active_project_payload=lambda _pid, _room: {"active_project": None},
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "missing project_id")

    async def test_github_find_repo_action_returns_resolved_repo(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        repo = SimpleNamespace(full_name="owner/repo", name="repo")
        result = await github_find_repo_action(
            {"repository": "repo"},
            ctx,
            resolve_github_repo=lambda _params: (repo, None),
            github_repo_to_payload=lambda item: {"full_name": item.full_name},
        )
        self.assertTrue(result.success)
        self.assertEqual(result.data["github_repo"]["full_name"], "owner/repo")

    async def test_code_worker_status_action_returns_error_payload(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await code_worker_status_action(
            {},
            ctx,
            code_worker_request=lambda _path: (None, ActionResult(success=False, message="offline", error="worker offline")),
            active_project_payload=lambda _pid, _room: {"active_project": None},
            capability_payload=lambda _pid, _room: {"capability_mode": "coding"},
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "worker offline")

    async def test_code_read_file_action_requires_path(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await code_read_file_action(
            {},
            ctx,
            resolve_project_record=lambda _params, _ctx: (None, ActionResult(success=False, message="x", error="x")),
            code_worker_request=lambda _path, _payload=None: ({}, None),
            project_record_to_payload=lambda _record: {},
            active_project_payload=lambda _pid, _room: {"active_project": None},
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "missing path")

    async def test_code_search_repo_requires_query(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await code_search_repo(
            {},
            ctx,
            get_active_project=lambda _pid, _room: None,
            get_code_index=lambda: SimpleNamespace(search=lambda *_args, **_kwargs: []),
            code_repo_root=lambda: Path("."),
            active_project_payload=lambda _pid, _room: {"active_project": None},
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "missing query")

    async def test_code_propose_change_action_requires_request(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await code_propose_change_action(
            {},
            ctx,
            resolve_project_record=lambda _params, _ctx: (None, ActionResult(success=False, message="x", error="x")),
            get_code_index=lambda: SimpleNamespace(search=lambda *_args, **_kwargs: []),
            code_worker_request=lambda _path, _payload=None: ({}, None),
            project_record_to_payload=lambda _record: {},
            propose_patch_plan=lambda **_kwargs: {},
            active_project_payload=lambda _pid, _room: {"active_project": None},
            capability_payload=lambda _pid, _room: {"capability_mode": "coding"},
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "missing request")

    async def test_code_run_command_action_validates_arguments(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await code_run_command_action(
            {"command": "pytest", "arguments": "not-a-list"},
            ctx,
            resolve_project_record=lambda _params, _ctx: (SimpleNamespace(project_id="p1", name="p1"), None),
            code_worker_request=lambda _path, _payload=None: ({}, None),
            project_record_to_payload=lambda _record: {"project_id": "p1"},
            active_project_payload=lambda _pid, _room: {"active_project": {"project_id": "p1"}},
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "invalid arguments")

    async def test_codex_exec_status_action_when_no_task(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await codex_exec_status_action(
            {},
            ctx,
            get_active_codex_task=lambda _pid, _room: None,
            codex_history_payload=lambda _pid, _room: [],
            codex_task_to_payload=lambda _task: {},
            active_project_payload=lambda _pid, _room: {"active_project": None},
            capability_payload=lambda _pid, _room: {"capability_mode": "coding"},
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "no codex task")

    async def test_codex_cancel_task_action_when_no_running_task(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await codex_cancel_task_action(
            {},
            ctx,
            codex_key=lambda _pid, _room: "k",
            codex_running_processes={},
            get_active_codex_task=lambda _pid, _room: None,
            now_iso=lambda: "2026-03-09T00:00:00Z",
            push_codex_history=lambda _pid, _room, _task: None,
            emit_codex_task_event=lambda *_args, **_kwargs: _async_result(None),
            codex_task_to_payload=lambda _task: {},
            codex_history_payload=lambda _pid, _room: [],
            active_project_payload=lambda _pid, _room: {"active_project": None},
            capability_payload=lambda _pid, _room: {"capability_mode": "coding"},
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "no running task")

    async def test_skills_list_action_respects_feature_gate(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await skills_list_action(
            {},
            ctx,
            require_feature=lambda _flag: ActionResult(success=False, message="off", error="feature disabled"),
            list_skills=lambda **_kwargs: [],
            active_project_payload=lambda _pid, _room: {"active_project": None},
            capability_payload=lambda _pid, _room: {"capability_mode": "default"},
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "feature disabled")

    async def test_subagent_cancel_action_requires_id(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await subagent_cancel_action(
            {},
            ctx,
            require_feature=lambda _flag: None,
            cancel_subagent=lambda **_kwargs: None,
            list_subagents=lambda **_kwargs: [],
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "missing subagent id")

    async def test_subagent_spawn_action_uses_runtime_gateway_for_preview(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        state = SimpleNamespace(
            subagent_id="sg_1",
            status="running",
            route_provider=None,
            updated_at="2026-03-09T00:00:00Z",
            to_payload=lambda: {"subagent_id": "sg_1", "status": "running"},
        )
        start_calls: list[dict[str, object]] = []

        def _start_subagent_task(**kwargs) -> None:
            start_calls.append(kwargs)

        result = await subagent_spawn_action(
            {"request": "investigar bug"},
            ctx,
            require_feature=lambda _flag: None,
            build_task_plan=lambda _request: SimpleNamespace(
                task_type="code",
                to_payload=lambda: {"task_type": "code", "steps": [], "assumptions": [], "generated_at": "now"},
            ),
            classify_action_risk=lambda _name: "R2",
            resolve_runtime=lambda **_kwargs: SimpleNamespace(
                primary_provider="anthropic",
                fallback_provider="openai",
                reason="Gateway route.",
            ),
            spawn_subagent=lambda **_kwargs: state,
            route_orchestration=lambda **_kwargs: (
                "ok",
                SimpleNamespace(
                    used_provider="anthropic",
                    fallback_used=False,
                    to_payload=lambda: {"used_provider": "anthropic"},
                    generated_at="2026-03-09T00:00:00Z",
                ),
            ),
            complete_subagent=lambda **_kwargs: state,
            start_subagent_task=_start_subagent_task,
            list_subagents=lambda **_kwargs: [state],
            now_iso=lambda: "2026-03-09T00:00:00Z",
            active_project_payload=lambda _pid, _room: {"active_project": None},
            capability_payload=lambda _pid, _room: {"capability_mode": "default"},
        )
        self.assertTrue(result.success)
        self.assertEqual(result.data["model_route"]["primary_provider"], "anthropic")
        self.assertEqual(result.data["model_route"]["fallback_provider"], "openai")
        self.assertEqual(result.data["model_route"]["reason"], "Gateway route.")
        self.assertEqual(len(start_calls), 1)

    async def test_providers_health_check_action_returns_rows(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await providers_health_check_action(
            {"include_ping": True},
            ctx,
            collect_provider_health=lambda include_ping, ping_prompt: [{"provider": "openai", "status": "ok", "include_ping": include_ping, "prompt": ping_prompt}],
            feature_flags_snapshot=lambda: {"skills_v1": True},
            canary_state_payload=lambda _pid, _room: {"active": False},
            capability_payload=lambda _pid, _room: {"capability_mode": "default"},
        )
        self.assertTrue(result.success)
        self.assertEqual(len(result.data["providers_health"]), 1)

    async def test_ops_incident_snapshot_action_returns_enriched_payload(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await ops_incident_snapshot_action(
            {"include_ping": False, "metrics_limit": 120},
            ctx,
            build_ops_incident_snapshot=lambda **_kwargs: {
                "canary_state": {"active": False},
                "feature_flags": {"skills_v1": True},
                "kill_switch": {"global": False},
                "providers_health": [{"provider": "openai", "status": "ok"}],
                "metrics_summary": {"events": 10},
                "slo_report": {"ok": True},
                "autonomy_mode": "safe",
            },
            capability_payload=lambda _pid, _room: {"capability_mode": "default"},
        )
        self.assertTrue(result.success)
        self.assertEqual(result.data["autonomy_mode"], "safe")
        self.assertEqual(result.data["capability_mode"], "default")

    async def test_ops_canary_set_action_rejects_invalid_operation(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await ops_canary_set_action(
            {"operation": "unknown"},
            ctx,
            set_canary_session_enrollment=lambda _pid, _room, enrolled: None,
            set_runtime_feature_override=lambda _flag, _enabled: True,
            build_ops_incident_snapshot=lambda **_kwargs: {},
            capability_payload=lambda _pid, _room: {},
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "invalid operation")

    async def test_ops_canary_rollout_set_action_requires_percent_on_set(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await ops_canary_rollout_set_action(
            {"operation": "set_percent"},
            ctx,
            get_canary_rollout_percent=lambda: 10,
            is_feature_enabled=lambda _flag, default=False: default,
            rollout_step_percent=lambda current, direction: current,
            set_canary_rollout_percent=lambda _value: None,
            set_runtime_feature_override=lambda _flag, _enabled: True,
            build_ops_incident_snapshot=lambda **_kwargs: {},
            now_iso=lambda: "2026-03-09T00:00:00Z",
            capability_payload=lambda _pid, _room: {},
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "missing percent")

    async def test_ops_feature_flags_set_action_updates_runtime_flag(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        overrides: dict[str, bool] = {}
        result = await ops_feature_flags_set_action(
            {"feature": "skills_v1", "enabled": False},
            ctx,
            feature_flag_overrides=overrides,
            feature_flags_snapshot=lambda: {"skills_v1": overrides.get("skills_v1", True)},
            canary_state_payload=lambda _pid, _room: {"active": False},
            capability_payload=lambda _pid, _room: {"capability_mode": "default"},
        )
        self.assertTrue(result.success)
        self.assertEqual(overrides["skills_v1"], False)
        self.assertEqual(result.data["feature_flags"]["skills_v1"], False)

    async def test_ops_auto_remediate_action_without_signal(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")

        async def _rollback(_params, _ctx):
            return ActionResult(success=False, message="should not run")

        result = await ops_auto_remediate_action(
            {"dry_run": True},
            ctx,
            auto_remediation_last_execution={},
            canary_key=lambda _pid, _room: "k",
            build_ops_incident_snapshot=lambda **_kwargs: {
                "canary_state": {"active": False},
                "feature_flags": {},
                "kill_switch": {"global": False},
                "metrics_summary": {},
                "slo_report": {},
            },
            ops_slo_signal=lambda _snapshot: {"recommended_scenario": ""},
            ops_rollback_scenario_action=_rollback,
            now_ts=lambda: 1000.0,
            now_iso=lambda: "2026-03-09T00:00:00Z",
            capability_payload=lambda _pid, _room: {"capability_mode": "default"},
        )
        self.assertTrue(result.success)
        self.assertFalse(result.data["ops_auto_remediation"]["executed"])
        self.assertEqual(result.data["ops_auto_remediation"]["reason"], "no signal")

    async def test_ops_canary_promote_action_respects_cooldown(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await ops_canary_promote_action(
            {"dry_run": False, "cooldown_seconds": 60},
            ctx,
            canary_promotion_last_execution={"k": 1000.0},
            canary_key=lambda _pid, _room: "k",
            build_ops_incident_snapshot=lambda **_kwargs: {
                "canary_state": {"active": True},
                "feature_flags": {},
                "slo_report": {},
            },
            ops_canary_gate_report=lambda **_kwargs: {"passed": True},
            ops_canary_rollout_set_action=lambda _params, _ctx: _async_result(ActionResult(success=True, message="ok")),
            ops_rollback_scenario_action=lambda _params, _ctx: _async_result(ActionResult(success=True, message="ok")),
            now_ts=lambda: 1010.0,
            now_iso=lambda: "2026-03-09T00:00:00Z",
            capability_payload=lambda _pid, _room: {"capability_mode": "default"},
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "canary promotion cooldown")

    async def test_ops_control_loop_tick_action_records_window(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        breach_history: dict[str, list[float]] = {}
        freeze_state: dict[str, float] = {}
        result = await ops_control_loop_tick_action(
            {"auto_remediate": False, "auto_promote_canary": False, "dry_run": True},
            ctx,
            control_loop_breach_history=breach_history,
            control_loop_freeze_last_trigger=freeze_state,
            canary_key=lambda _pid, _room: "k",
            build_ops_incident_snapshot=lambda **_kwargs: {
                "canary_state": {"active": False},
                "feature_flags": {},
                "kill_switch": {"global": False},
                "slo_report": {},
                "metrics_summary": {},
            },
            ops_slo_signal=lambda _snapshot: {"recommended_scenario": "latency_spike"},
            ops_auto_remediate_action=lambda _params, _ctx: _async_result(ActionResult(success=True, message="ok")),
            ops_canary_promote_action=lambda _params, _ctx: _async_result(ActionResult(success=True, message="ok")),
            set_killswitch_global=lambda _enabled, reason=None: None,
            set_runtime_feature_override=lambda _flag, _enabled: True,
            set_canary_rollout_percent=lambda _value: None,
            now_ts=lambda: 2000.0,
            now_iso=lambda: "2026-03-09T00:00:00Z",
            capability_payload=lambda _pid, _room: {"capability_mode": "default"},
        )
        self.assertTrue(result.success)
        self.assertEqual(len(breach_history["k"]), 1)
        self.assertEqual(result.data["ops_control_tick"]["breach_window"]["count"], 1)

    async def test_ops_apply_playbook_action_rejects_invalid_playbook(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await ops_apply_playbook_action(
            {"playbook": "unknown"},
            ctx,
            feature_flags_snapshot=lambda: {"values": {}, "overrides": {}},
            get_killswitch_payload=lambda: {"global_enabled": False, "domains": {}},
            get_autonomy_mode=lambda _pid, _room: "safe",
            get_domain_autonomy_mode=lambda _pid, _room, _domain: None,
            list_domain_autonomy_modes=lambda _pid, _room: [],
            feature_value_from_env=lambda _flag, default=True: default,
            set_runtime_feature_override=lambda _flag, _enabled: True,
            set_autonomy_mode=lambda _pid, _room, mode: mode,
            set_domain_autonomy_mode=lambda *_args, **_kwargs: None,
            clear_domain_autonomy_mode=lambda _pid, _room, _domain: None,
            set_killswitch_domain=lambda _domain, _enabled, _reason: None,
            feature_flag_overrides={},
            predict_feature_values_from_overrides=lambda overrides: overrides,
            now_iso=lambda: "2026-03-09T00:00:00Z",
            build_ops_incident_snapshot=lambda **_kwargs: {},
            build_domain_autonomy_audit_rows=lambda **_kwargs: [],
            capability_payload=lambda _pid, _room: {},
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "invalid playbook")

    async def test_ops_rollback_scenario_action_rejects_invalid_scenario(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await ops_rollback_scenario_action(
            {"scenario": "invalid"},
            ctx,
            feature_flags_snapshot=lambda: {},
            get_killswitch_payload=lambda: {},
            get_autonomy_mode=lambda _pid, _room: "safe",
            set_autonomy_mode=lambda _pid, _room, mode: mode,
            get_canary_rollout_percent=lambda: 0,
            is_feature_enabled=lambda _flag, default=False: default,
            set_runtime_feature_override=lambda _flag, _enabled: True,
            set_canary_rollout_percent=lambda _value: None,
            feature_flag_overrides={},
            list_domain_autonomy_modes=lambda _pid, _room: [],
            ops_apply_playbook_action=lambda _params, _ctx: _async_result(ActionResult(success=True, message="ok")),
            now_iso=lambda: "2026-03-09T00:00:00Z",
            build_ops_incident_snapshot=lambda **_kwargs: {},
            build_domain_autonomy_audit_rows=lambda **_kwargs: [],
            capability_payload=lambda _pid, _room: {},
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "invalid scenario")

    async def test_autonomy_set_mode_action_rejects_invalid_mode(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await autonomy_set_mode_action(
            {"mode": "invalid"},
            ctx,
            require_feature=lambda _flag: None,
            allowed_autonomy_modes={"safe", "aggressive"},
            set_autonomy_mode=lambda _pid, _room, _mode: _mode,
            get_killswitch_status=lambda: SimpleNamespace(to_payload=lambda: {"global": False}),
            capability_payload=lambda _pid, _room: {"capability_mode": "default"},
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "invalid mode")

    async def test_autonomy_killswitch_action_requires_domain_when_enable_domain(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await autonomy_killswitch_action(
            {"operation": "enable_domain"},
            ctx,
            require_feature=lambda _flag: None,
            set_killswitch_global=lambda *_args, **_kwargs: SimpleNamespace(to_payload=lambda: {}),
            set_killswitch_domain=lambda *_args, **_kwargs: SimpleNamespace(to_payload=lambda: {}),
            get_killswitch_status=lambda: SimpleNamespace(to_payload=lambda: {}),
            get_autonomy_mode=lambda _pid, _room: "safe",
            capability_payload=lambda _pid, _room: {"capability_mode": "default"},
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "missing domain")

    async def test_policy_trust_drift_report_action_validates_rows_type(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await policy_trust_drift_report_action(
            {"rows": "invalid"},
            ctx,
            replace_trust_drift=lambda *_args, **_kwargs: [],
            capability_payload=lambda _pid, _room: {"capability_mode": "default"},
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "invalid rows")

    async def test_rpg_reindex_sources_requires_configured_paths(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        fake_index = SimpleNamespace(ingest_paths=lambda _paths: {}, stats=lambda: {})
        result = await rpg_reindex_sources(
            {},
            ctx,
            get_rpg_index=lambda: fake_index,
            rpg_sources=lambda: [],
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "missing RPG_SOURCE_PATHS")

    async def test_rpg_search_knowledge_requires_query(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await rpg_search_knowledge(
            {},
            ctx,
            get_rpg_index=lambda: SimpleNamespace(search=lambda _query, limit=5: []),
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "missing query")

    async def test_rpg_get_knowledge_stats_returns_index_stats(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await rpg_get_knowledge_stats(
            {},
            ctx,
            get_rpg_index=lambda: SimpleNamespace(stats=lambda: {"documents": 3}),
        )
        self.assertTrue(result.success)
        self.assertEqual(result.data["knowledge_stats"]["documents"], 3)

    async def test_rpg_get_character_mode_without_active_character(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await rpg_get_character_mode(
            {},
            ctx,
            get_active_character=lambda _pid, _room: None,
            active_character_payload=lambda _pid, _room: {"active_character": None},
        )
        self.assertTrue(result.success)
        self.assertEqual(result.data["active_character"], None)

    async def test_rpg_assume_character_requires_name(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await rpg_assume_character(
            {},
            ctx,
            find_existing_character_sheet_by_name=lambda _name: (None, None),
            rpg_character_pdfs_dir=lambda: Path("."),
            summarize_character_text=lambda text: text,
            find_onenote_character_page=lambda _name, _section=None: None,
            quote_path_segment=lambda value: value,
            onenote_api_request=lambda _method, _endpoint, **_kwargs: ("", None),
            extract_onenote_character_profile=lambda _html: {},
            strip_html_for_preview=lambda _html: "",
            get_rpg_index=lambda: SimpleNamespace(search=lambda _name, limit=3: []),
            ensure_onenote_character_page=lambda **_kwargs: ({}, None),
            build_character_prompt_hint=lambda _name, _summary, _profile: "hint",
            active_character_mode_cls=SimpleNamespace,
            now_iso=lambda: "2026-03-09T00:00:00Z",
            set_active_character=lambda _pid, _room, _active: None,
            active_character_payload=lambda _pid, _room: {"active_character": None},
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "missing name")

    async def test_rpg_clear_character_mode_without_active_character(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await rpg_clear_character_mode(
            {},
            ctx,
            get_active_character=lambda _pid, _room: None,
            clear_active_character=lambda _pid, _room: None,
            active_character_payload=lambda _pid, _room: {"active_character": None},
        )
        self.assertTrue(result.success)
        self.assertTrue(result.data["active_character_cleared"])

    async def test_rpg_create_character_sheet_requires_name(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await rpg_create_character_sheet(
            {},
            ctx,
            safe_file_part=lambda value: value,
            rpg_characters_dir=lambda: Path("."),
            rpg_character_pdfs_dir=lambda: Path("."),
            generate_character_sheet=lambda _params: None,
            invalid_character_build_error_cls=ValueError,
            rpg_pdf_export_enabled=lambda: False,
            export_tormenta20_sheet_pdf=lambda _sheet, _path: (False, None),
            get_active_character=lambda _pid, _room: None,
            find_onenote_character_page=lambda _name: None,
            onenote_append_to_page=lambda _params, _ctx: _async_result(ActionResult(success=True, message="ok")),
            set_active_character=lambda _pid, _room, _active: None,
            tormenta20_pdf_template_path=lambda: Path("."),
            log_info=lambda *_args, **_kwargs: None,
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "missing name")

    async def test_rpg_create_threat_sheet_requires_name(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await rpg_create_threat_sheet(
            {},
            ctx,
            generate_threat_sheet=lambda _params: None,
            invalid_threat_definition_error_cls=ValueError,
            safe_file_part=lambda value: value,
            rpg_threats_dir=lambda: Path("."),
            rpg_threat_pdfs_dir=lambda: Path("."),
            export_tormenta20_threat_pdf=lambda _sheet, _path: (False, None),
            log_info=lambda *_args, **_kwargs: None,
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "missing name")

    async def test_rpg_save_lore_note_requires_content(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await rpg_save_lore_note(
            {"title": "Nota"},
            ctx,
            get_rpg_index=lambda: SimpleNamespace(),
            rpg_notes_dir=lambda: Path("."),
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "missing content")

    async def test_rpg_session_recording_status_without_active_recording(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await rpg_session_recording(
            {"mode": "status"},
            ctx,
            recording_key=lambda _pid, _room: "k",
            rpg_active_recordings={},
            rpg_last_session_files={},
            recording_state_cls=SimpleNamespace,
            extract_history_since=lambda _session, _index: [],
            safe_file_part=lambda value: value,
            rpg_session_logs_dir=lambda: Path("."),
            build_session_markdown=lambda state, messages: "",
            get_active_character=lambda _pid, _room: None,
            infer_character_session_notes=lambda _messages: {},
            onenote_append_to_page=lambda _params, _ctx: _async_result(ActionResult(success=True, message="ok")),
        )
        self.assertTrue(result.success)
        self.assertFalse(result.data["recording_active"])

    async def test_rpg_session_recording_stop_without_active_recording(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await rpg_session_recording(
            {"mode": "stop"},
            ctx,
            recording_key=lambda _pid, _room: "k",
            rpg_active_recordings={},
            rpg_last_session_files={},
            recording_state_cls=SimpleNamespace,
            extract_history_since=lambda _session, _index: [],
            safe_file_part=lambda value: value,
            rpg_session_logs_dir=lambda: Path("."),
            build_session_markdown=lambda state, messages: "",
            get_active_character=lambda _pid, _room: None,
            infer_character_session_notes=lambda _messages: {},
            onenote_append_to_page=lambda _params, _ctx: _async_result(ActionResult(success=True, message="ok")),
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "no active recording")

    async def test_rpg_write_session_summary_requires_session_file(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await rpg_write_session_summary(
            {},
            ctx,
            recording_key=lambda _pid, _room: "k",
            rpg_last_session_files={},
            build_session_summary=lambda _title, _messages: "x",
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "missing session file")

    async def test_rpg_ideate_next_session_requires_session_file(self) -> None:
        ctx = ActionContext(job_id="j", room="room", participant_identity="pid")
        result = await rpg_ideate_next_session(
            {},
            ctx,
            recording_key=lambda _pid, _room: "k",
            rpg_last_session_files={},
            rpg_notes_dir=lambda: Path("."),
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "missing session file")


def _async_result(result: ActionResult):
    async def _runner() -> ActionResult:
        return result

    return _runner()


if __name__ == "__main__":
    unittest.main()
