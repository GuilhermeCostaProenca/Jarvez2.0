import unittest
from unittest.mock import patch

from codex_cli import build_exec_command, parse_json_line


class CodexCliTests(unittest.TestCase):
    def test_build_exec_command_uses_safe_defaults(self):
        with patch("codex_cli.get_codex_executable", return_value="codex"):
            command = build_exec_command(
                prompt="analise o projeto",
                working_directory="C:\\repos\\demo",
            )

        self.assertEqual(command[:2], ["codex", "exec"])
        self.assertIn("--json", command)
        self.assertIn("--skip-git-repo-check", command)
        self.assertIn("--sandbox", command)
        self.assertIn("read-only", command)
        self.assertIn("--ephemeral", command)
        self.assertEqual(command[-1], "analise o projeto")

    def test_parse_json_line_returns_none_for_invalid_json(self):
        self.assertIsNone(parse_json_line("not-json"))

    def test_parse_json_line_parses_dict_payload(self):
        payload = parse_json_line('{"type":"task.progress","message":"Lendo o projeto"}')
        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload["type"], "task.progress")
        self.assertEqual(payload["message"], "Lendo o projeto")


if __name__ == "__main__":
    unittest.main()
