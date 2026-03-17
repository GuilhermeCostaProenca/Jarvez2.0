from __future__ import annotations

import sys
from pathlib import Path

from .types import McpClientError, McpServerConfig, McpToolInfo


def _jarvez_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _pilot_spotify_config() -> McpServerConfig:
    spotify_root = _jarvez_root().parent / "jarvez-mcp-spotify"
    return McpServerConfig(
        name="spotify",
        command=sys.executable,
        args=["server.py"],
        cwd=str(spotify_root),
        enabled=True,
        timeout_seconds=20,
        legacy_fallback_enabled=True,
    )


def create_default_mcp_registry() -> "McpRegistry":
    return McpRegistry([_pilot_spotify_config()])


class McpRegistry:
    def __init__(self, configs: list[McpServerConfig] | None = None):
        self._servers: dict[str, McpServerConfig] = {}
        self._tools_by_server: dict[str, dict[str, McpToolInfo]] = {}
        for config in configs or []:
            self.register_server(config)

    def register_server(self, config: McpServerConfig) -> None:
        self._servers[config.name] = config
        self._tools_by_server.setdefault(config.name, {})

    def get_server(self, name: str) -> McpServerConfig:
        config = self._servers.get(name)
        if config is None:
            raise McpClientError("unknown_server", f"MCP server '{name}' is not registered.")
        return config

    def list_enabled_servers(self) -> list[McpServerConfig]:
        return [config for config in self._servers.values() if config.enabled]

    def set_discovered_tools(self, server_name: str, tools: list[McpToolInfo]) -> None:
        self.get_server(server_name)
        self._tools_by_server[server_name] = {tool.name: tool for tool in tools}

    def list_discovered_tools(self, server_name: str) -> list[McpToolInfo]:
        self.get_server(server_name)
        return list(self._tools_by_server.get(server_name, {}).values())

    def get_discovered_tool(self, server_name: str, tool_name: str) -> McpToolInfo | None:
        self.get_server(server_name)
        return self._tools_by_server.get(server_name, {}).get(tool_name)

    def manifest_snapshot(self) -> list[dict[str, object]]:
        snapshot: list[dict[str, object]] = []
        for config in self._servers.values():
            snapshot.append(
                {
                    "name": config.name,
                    "command": config.command,
                    "args": list(config.args),
                    "cwd": config.cwd,
                    "enabled": config.enabled,
                    "timeout_seconds": config.timeout_seconds,
                    "legacy_fallback_enabled": config.legacy_fallback_enabled,
                }
            )
        return snapshot
