import unittest


TEST_NAMES = [
    "test_killswitch_domain_blocks_action",
    "test_workspace_policy_blocks_run_local_command_outside_root",
    "test_policy_action_risk_matrix_returns_rows",
    "test_policy_domain_trust_status_returns_rows",
    "test_policy_trust_drift_report_syncs_backend_state",
    "test_low_domain_trust_escalates_r2_to_confirmation_in_aggressive_mode",
    "test_domain_autonomy_mode_safe_escalates_policy_for_single_domain",
    "test_trust_drift_escalates_ops_policy_in_aggressive_mode",
    "test_trust_drift_uses_agent_audio_when_session_supports_say",
    "test_trust_drift_appears_in_metrics_and_incident_snapshot",
    "test_browser_tts_delivery_is_reported_in_metrics_and_slo",
    "test_autonomy_notice_summary_distinguishes_agent_audio_browser_tts_and_unconfirmed",
    "test_evals_list_and_run_baseline",
    "test_providers_health_check_and_feature_flags_runtime_override",
    "test_ops_incident_snapshot_returns_operational_data",
    "test_ops_apply_playbook_provider_degradation_and_restore",
    "test_ops_canary_set_and_status",
    "test_ops_rollback_scenario_recover_to_stable",
    "test_ops_canary_rollout_set_updates_percent",
    "test_ops_auto_remediate_dry_run_uses_reliability_breach",
    "test_ops_auto_remediate_dry_run_uses_trust_drift_breach",
    "test_ops_auto_remediate_dry_run_uses_reliability_breach_when_notice_delivery_unconfirmed",
    "test_ops_canary_promote_steps_up_when_gates_pass",
    "test_ops_control_loop_tick_returns_combined_report",
    "test_ops_control_loop_tick_skips_promotion_on_trust_drift_breach",
    "test_ops_control_loop_tick_applies_freeze_on_repeated_breach",
    "test_ops_control_loop_tick_skips_promotion_when_notice_delivery_is_unconfirmed",
]


def load_tests(loader: unittest.TestLoader, tests, pattern):  # noqa: ARG001
    return unittest.TestSuite(
        loader.loadTestsFromName(f"test_actions.ActionsTests.{test_name}") for test_name in TEST_NAMES
    )
