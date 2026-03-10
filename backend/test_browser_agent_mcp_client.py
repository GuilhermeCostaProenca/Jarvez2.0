from __future__ import annotations

import unittest
from unittest.mock import patch

from browser_agent.mcp_client import PlaywrightMcpClient


class _FakeResponse:
    def __init__(self, status_code: int, *, text: str = "", headers: dict[str, str] | None = None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}

    def json(self):
        raise ValueError("json() not used in this test")


class BrowserAgentMcpClientTests(unittest.TestCase):
    def test_healthcheck_missing_url(self) -> None:
        client = PlaywrightMcpClient("")
        health = client.healthcheck()
        self.assertFalse(health.ok)
        self.assertEqual(health.status, "missing_url")

    @patch("browser_agent.mcp_client.requests.post")
    def test_healthcheck_initializes_session_and_lists_tools(self, post_mock) -> None:
        post_mock.side_effect = [
            _FakeResponse(
                200,
                text='event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-03-26"}}\n\n',
                headers={"mcp-session-id": "session-1"},
            ),
            _FakeResponse(202, text=""),
            _FakeResponse(
                200,
                text='event: message\ndata: {"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"browser_navigate"},{"name":"browser_snapshot"}]}}\n\n',
            ),
        ]
        client = PlaywrightMcpClient("http://localhost:3333")
        health = client.healthcheck()
        self.assertTrue(health.ok)
        self.assertEqual(health.status, "ok")
        self.assertEqual(health.tools, ["browser_navigate", "browser_snapshot"])
        self.assertEqual(post_mock.call_count, 3)

    @patch("browser_agent.mcp_client.requests.post")
    def test_call_tool_returns_tool_error(self, post_mock) -> None:
        post_mock.side_effect = [
            _FakeResponse(
                200,
                text='event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-03-26"}}\n\n',
                headers={"mcp-session-id": "session-2"},
            ),
            _FakeResponse(202, text=""),
            _FakeResponse(
                200,
                text='event: message\ndata: {"jsonrpc":"2.0","id":2,"result":{"isError":true,"content":[{"type":"text","text":"domain blocked"}]}}\n\n',
            ),
        ]
        client = PlaywrightMcpClient("http://localhost:3333")
        result = client.call_tool("browser_navigate", {"url": "https://example.com"})
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "tool_error")
        self.assertIn("domain blocked", result.detail or "")


if __name__ == "__main__":
    unittest.main()
