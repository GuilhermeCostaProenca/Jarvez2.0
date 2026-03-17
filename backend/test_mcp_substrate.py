from __future__ import annotations

import asyncio
import unittest
from pathlib import Path

from dotenv import load_dotenv

from backend_mcp import McpManager, create_default_mcp_registry

load_dotenv(Path(__file__).with_name(".env"), override=False)


class McpSubstrateTests(unittest.TestCase):
    def test_spotify_manifest_registers_only_pilot_server(self) -> None:
        registry = create_default_mcp_registry()
        snapshot = registry.manifest_snapshot()
        self.assertEqual(len(snapshot), 1)
        self.assertEqual(snapshot[0]["name"], "spotify")
        self.assertTrue(snapshot[0]["enabled"])
        self.assertTrue(str(snapshot[0]["cwd"]).endswith("jarvez-mcp-spotify"))

    def test_spotify_pilot_can_list_tools_and_call_real_tool(self) -> None:
        async def _run() -> tuple[list[str], object]:
            registry = create_default_mcp_registry()
            manager = McpManager(registry)
            try:
                tools = await manager.list_tools("spotify")
                result = await manager.call_tool("spotify", "spotify_status", {})
                return [tool.name for tool in tools], result
            finally:
                await manager.shutdown_all()

        tool_names, result = asyncio.run(_run())
        self.assertIn("spotify_status", tool_names)
        self.assertEqual(result.status, "ok")
        self.assertIsInstance(result.raw_result, dict)
        self.assertIsInstance(result.structured_content, dict)
        self.assertIn("message", result.structured_content or {})


if __name__ == "__main__":
    unittest.main()
