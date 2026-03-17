import unittest


TEST_NAMES = [
    "test_sensitive_action_returns_confirmation_required",
    "test_confirm_action_executes_when_token_valid",
    "test_confirm_action_fails_for_other_identity",
    "test_confirm_action_fails_when_expired",
    "test_authenticate_identity_requires_correct_pin",
    "test_authenticate_identity_accepts_passphrase_only",
    "test_authenticate_identity_accepts_security_phrase_alias",
    "test_verify_voice_identity_high_confidence_authenticates",
    "test_verify_voice_identity_medium_confidence_requires_stepup",
    "test_verify_voice_identity_requires_recent_audio",
    "test_enroll_voice_profile_requires_recent_audio",
    "test_set_memory_scope",
    "test_forget_memory_public",
    "test_auth_gate_blocks_sensitive_action_without_auth",
]


def load_tests(loader: unittest.TestLoader, tests, pattern):  # noqa: ARG001
    return unittest.TestSuite(
        loader.loadTestsFromName(f"test_actions.ActionsTests.{test_name}") for test_name in TEST_NAMES
    )
