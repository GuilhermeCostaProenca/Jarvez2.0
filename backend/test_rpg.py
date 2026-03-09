import unittest


ACTION_TESTS = [
    "test_rpg_create_character_sheet_bridge_pipeline",
    "test_rpg_create_character_sheet_fallback_pipeline",
    "test_rpg_create_character_sheet_level_gt_one_is_partial_and_preserves_level",
    "test_rpg_create_character_sheet_template_missing_returns_failed_pdf_status",
    "test_rpg_create_threat_sheet_generates_files",
    "test_rpg_create_threat_sheet_supports_overrides",
    "test_rpg_create_threat_sheet_rejects_invalid_nd",
]


def load_tests(loader: unittest.TestLoader, tests, pattern):  # noqa: ARG001
    suite = unittest.TestSuite()
    for test_name in ACTION_TESTS:
        suite.addTests(loader.loadTestsFromName(f"test_actions.ActionsTests.{test_name}"))
    suite.addTests(loader.loadTestsFromName("test_rpg_engine"))
    return suite
