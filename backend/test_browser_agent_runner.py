from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from browser_agent.runner import run_browser_task


class BrowserAgentRunnerTests(unittest.TestCase):
    @patch("browser_agent.runner.PlaywrightMcpClient")
    def test_run_browser_task_fails_when_healthcheck_fails(self, client_cls_mock) -> None:
        client_instance = client_cls_mock.return_value
        client_instance.healthcheck.return_value.ok = False
        client_instance.healthcheck.return_value.status = "unreachable"
        client_instance.healthcheck.return_value.detail = "connection refused"

        state, ok, error = run_browser_task(
            task_id="browser_1",
            request="resuma a pagina inicial",
            allowed_domains=["example.com"],
            read_only=True,
            mcp_url="http://127.0.0.1:3333",
        )

        self.assertFalse(ok)
        self.assertEqual(error, "browser_agent_not_configured")
        self.assertEqual(state.status, "failed")
        self.assertIsNotNone(state.finished_at)

    @patch("browser_agent.runner.PlaywrightMcpClient")
    def test_run_browser_task_completes_execution_mode(self, client_cls_mock) -> None:
        client_instance = client_cls_mock.return_value
        client_instance.healthcheck.return_value.ok = True
        client_instance.healthcheck.return_value.status = "ok"
        client_instance.healthcheck.return_value.detail = None
        client_instance.healthcheck.return_value.tools = ["browser_navigate", "browser_snapshot"]
        client_cls_mock.extract_text.side_effect = [
            "### Page\n- Page URL: https://example.com/\n- Page Title: Example Domain",
            "### Page\n- Page URL: https://example.com/\n- Page Title: Example Domain\n### Snapshot",
            "### Page\n- Page URL: https://example.com/\n- Page Title: Example Domain",
            "### Page\n- Page URL: https://example.com/\n- Page Title: Example Domain\n### Snapshot",
        ]
        client_cls_mock.extract_page_url.return_value = "https://example.com/"
        client_instance.call_tool.side_effect = [
            SimpleNamespace(
                ok=True,
                status="ok",
                detail=None,
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": "### Page\n- Page URL: https://example.com/\n- Page Title: Example Domain",
                        }
                    ]
                },
            ),
            SimpleNamespace(
                ok=True,
                status="ok",
                detail=None,
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": "### Page\n- Page URL: https://example.com/\n- Page Title: Example Domain\n### Snapshot",
                        }
                    ]
                },
            ),
            SimpleNamespace(
                ok=True,
                status="ok",
                detail=None,
                result={"content": [{"type": "text", "text": "screenshot saved"}]},
            ),
        ]

        state, ok, error = run_browser_task(
            task_id="browser_2",
            request="captura evidencias da home",
            allowed_domains=["example.com"],
            read_only=True,
            mcp_url="http://127.0.0.1:3333",
        )

        self.assertTrue(ok)
        self.assertIsNone(error)
        self.assertEqual(state.status, "completed")
        self.assertIsNotNone(state.finished_at)
        self.assertEqual((state.evidence or {}).get("mode"), "execution")
        self.assertEqual((state.evidence or {}).get("resolved_page_url"), "https://example.com/")

    def test_run_browser_task_blocks_write_mode(self) -> None:
        state, ok, error = run_browser_task(
            task_id="browser_3",
            request="faca login no portal",
            allowed_domains=["example.com"],
            read_only=False,
            mcp_url="http://127.0.0.1:3333",
        )
        self.assertFalse(ok)
        self.assertEqual(error, "write_mode_not_enabled")
        self.assertEqual(state.status, "failed")

    @patch("browser_agent.runner.PlaywrightMcpClient")
    def test_run_browser_task_supports_cooperative_cancellation(self, client_cls_mock) -> None:
        client_instance = client_cls_mock.return_value
        client_instance.healthcheck.return_value.ok = True
        client_instance.healthcheck.return_value.status = "ok"
        client_instance.healthcheck.return_value.detail = None
        client_instance.call_tool.return_value = SimpleNamespace(ok=True, status="ok", detail=None, result={})

        state, ok, error = run_browser_task(
            task_id="browser_4",
            request="resuma https://example.com",
            allowed_domains=["example.com"],
            read_only=True,
            mcp_url="http://127.0.0.1:3333",
            is_cancel_requested=lambda: True,
        )
        self.assertFalse(ok)
        self.assertEqual(error, "cancelled_by_user")
        self.assertEqual(state.status, "cancelled")


if __name__ == "__main__":
    unittest.main()
