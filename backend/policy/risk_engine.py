from __future__ import annotations

from typing import Literal

RiskTier = Literal["R0", "R1", "R2", "R3"]
PolicyDecision = Literal[
    "allow",
    "allow_with_log",
    "allow_with_guardrail",
    "deny",
    "require_confirmation",
]

R3_ACTIONS = {
    "whatsapp_send_text",
    "whatsapp_send_audio_tts",
    "run_local_command",
    "git_commit_and_push_project",
    "call_service",
    "turn_light_on",
    "turn_light_off",
    "set_light_brightness",
    "ac_send_command",
    "ac_turn_on",
    "ac_turn_off",
    "ac_set_temperature",
    "ac_set_mode",
    "ac_set_fan_speed",
    "ac_set_swing",
    "ac_set_sleep_timer",
    "ac_set_start_timer",
    "ac_set_power_save",
    "ac_apply_preset",
    "ac_prepare_arrival",
}

R2_PREFIXES = (
    "project_",
    "code_",
    "codex_",
    "ops_",
    "thinq_",
    "open_desktop_resource",
    "github_clone",
    "spotify_",
    "onenote_append",
    "onenote_create",
)

R1_PREFIXES = (
    "list_",
    "get_",
    "search_",
    "web_search_dashboard",
    "save_web_briefing_schedule",
    "rpg_search_knowledge",
)


def classify_action_risk(action_name: str) -> RiskTier:
    if action_name in R3_ACTIONS:
        return "R3"
    if action_name == "confirm_action":
        return "R0"
    if any(action_name.startswith(prefix) for prefix in R2_PREFIXES):
        return "R2"
    if any(action_name.startswith(prefix) for prefix in R1_PREFIXES):
        return "R1"
    if action_name.startswith("skills_") or action_name.startswith("subagent_") or action_name.startswith("policy_"):
        return "R1"
    return "R0"
