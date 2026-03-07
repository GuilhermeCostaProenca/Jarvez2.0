import unittest


TEST_NAMES = [
    "test_validate_params_success",
    "test_validate_params_missing_required",
    "test_brightness_out_of_range",
    "test_call_service_blocked_by_allowlist",
    "test_action_result_envelope_includes_trace_risk_policy_and_evidence",
    "test_skills_list_and_read_from_temp_directory",
    "test_subagent_spawn_status_and_cancel",
    "test_browser_agent_run_reports_missing_backend_configuration",
    "test_workflow_run_returns_checkpointed_plan",
    "test_whatsapp_channel_status_reports_legacy_mode_when_mcp_missing",
    "test_redaction_hides_secret_fields",
]


def load_tests(loader: unittest.TestLoader, tests, pattern):  # noqa: ARG001
    return unittest.TestSuite(
        loader.loadTestsFromName(f"test_actions.ActionsTests.{test_name}") for test_name in TEST_NAMES
    )
