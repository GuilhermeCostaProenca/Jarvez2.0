from __future__ import annotations

from typing import Any

from actions_core import publish_session_event


def build_session_snapshot(participant_identity: str, room: str) -> dict[str, Any]:
    import actions as actions_module

    return {
        "type": "session_snapshot",
        "snapshot": {
            "security_session": actions_module._security_status_payload(participant_identity, room),
            "research_schedules": actions_module._load_event_namespace(
                participant_identity,
                room,
                "research_schedules",
            ),
            "model_route": actions_module._load_event_namespace(participant_identity, room, "model_route"),
            "subagent_states": actions_module._load_event_namespace(
                participant_identity,
                room,
                "subagent_states",
            ),
            "policy_events": actions_module._load_event_namespace(participant_identity, room, "policy_events"),
            "execution_traces": actions_module._load_event_namespace(
                participant_identity,
                room,
                "execution_traces",
            ),
            "eval_baseline_summary": actions_module._load_event_namespace(
                participant_identity,
                room,
                "eval_baseline_summary",
            ),
            "eval_metrics": actions_module._load_event_namespace(participant_identity, room, "eval_metrics"),
            "eval_metrics_summary": actions_module._load_event_namespace(
                participant_identity,
                room,
                "eval_metrics_summary",
            ),
            "slo_report": actions_module._load_event_namespace(participant_identity, room, "slo_report"),
            "providers_health": actions_module._load_event_namespace(
                participant_identity,
                room,
                "providers_health",
            ),
            "feature_flags": actions_module._load_event_namespace(participant_identity, room, "feature_flags"),
            "canary_state": actions_module._load_event_namespace(participant_identity, room, "canary_state"),
            "incident_snapshot": actions_module._load_event_namespace(
                participant_identity,
                room,
                "incident_snapshot",
            ),
            "playbook_report": actions_module._load_event_namespace(
                participant_identity,
                room,
                "playbook_report",
            ),
            "auto_remediation": actions_module._load_event_namespace(
                participant_identity,
                room,
                "auto_remediation",
            ),
            "canary_promotion": actions_module._load_event_namespace(
                participant_identity,
                room,
                "canary_promotion",
            ),
            "control_tick": actions_module._load_event_namespace(participant_identity, room, "control_tick"),
            "active_codex_task": actions_module._codex_task_to_payload(task)
            if (task := actions_module.get_active_codex_task(participant_identity, room)) is not None
            else None,
            "codex_history": actions_module._codex_history_payload(participant_identity, room),
            "browser_tasks": actions_module._load_event_namespace(participant_identity, room, "browser_tasks"),
            "workflow_state": actions_module._load_event_namespace(participant_identity, room, "workflow_state"),
            "automation_state": actions_module._load_event_namespace(participant_identity, room, "automation_state"),
            "proactivity_state": actions_module._load_event_namespace(participant_identity, room, "proactivity_state"),
            "whatsapp_channel": actions_module._load_event_namespace(participant_identity, room, "whatsapp_channel"),
            "voice_interactivity": actions_module._load_event_namespace(
                participant_identity,
                room,
                "voice_interactivity",
            ),
        },
    }


async def publish_session_snapshot(session: Any, *, participant_identity: str, room: str) -> None:
    await publish_session_event(session, build_session_snapshot(participant_identity, room))
