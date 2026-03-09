import unittest


ACTION_TESTS = [
    "test_open_desktop_resource_uses_site_alias",
    "test_run_local_command_blocks_disallowed_command",
    "test_git_clone_repository_runs_git_clone",
]


def load_tests(loader: unittest.TestLoader, tests, pattern):  # noqa: ARG001
    suite = unittest.TestSuite()
    for test_name in ACTION_TESTS:
        suite.addTests(loader.loadTestsFromName(f"test_actions.ActionsTests.{test_name}"))
    suite.addTests(loader.loadTestsFromName("test_project_catalog"))
    suite.addTests(loader.loadTestsFromName("test_codex_cli"))
    return suite
