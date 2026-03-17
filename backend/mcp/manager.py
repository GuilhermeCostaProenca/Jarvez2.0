from __future__ import annotations

from .client import StdioMcpClient
from .registry import McpRegistry, create_default_mcp_registry
from .types import JsonObject, McpClientError, McpToolCallResult, McpToolInfo


class McpManager:
    def __init__(self, registry: McpRegistry | None = None):
        self.registry = registry or create_default_mcp_registry()
        self._clients: dict[str, StdioMcpClient] = {}

    async def get_client(self, server_name: str) -> StdioMcpClient:
        config = self.registry.get_server(server_name)
        if not config.enabled:
            raise McpClientError("server_disabled", f"MCP server '{server_name}' is disabled.")
        client = self._clients.get(server_name)
        if client is None:
            client = StdioMcpClient(config)
            self._clients[server_name] = client
        await client.start()
        return client

    async def stop_server(self, server_name: str) -> None:
        client = self._clients.pop(server_name, None)
        if client is not None:
            await client.stop()

    async def shutdown_all(self) -> None:
        for server_name in list(self._clients):
            await self.stop_server(server_name)

    async def list_tools(self, server_name: str) -> list[McpToolInfo]:
        client = await self.get_client(server_name)
        tools = await client.list_tools()
        self.registry.set_discovered_tools(server_name, tools)
        return tools

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        params: JsonObject | None = None,
    ) -> McpToolCallResult:
        if self.registry.get_discovered_tool(server_name, tool_name) is None:
            await self.list_tools(server_name)
        client = await self.get_client(server_name)
        return await client.call_tool(tool_name, params)


_DEFAULT_MCP_MANAGER: McpManager | None = None


def get_default_mcp_manager() -> McpManager:
    global _DEFAULT_MCP_MANAGER
    if _DEFAULT_MCP_MANAGER is None:
        _DEFAULT_MCP_MANAGER = McpManager()
    return _DEFAULT_MCP_MANAGER
