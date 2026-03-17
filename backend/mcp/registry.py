from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .types import McpClientError, McpServerConfig, McpToolInfo


def _jarvez_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _redact_env_value(name: str, value: Any) -> str:
    text = str(value or "")
    lowered = name.strip().casefold()
    if any(marker in lowered for marker in ("token", "secret", "password", "key")):
        return "***REDACTED***"
    if len(text) > 160:
        return f"{text[:157]}..."
    return text


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
        env_allowlist=[
            "PATH",
            "PATHEXT",
            "SYSTEMROOT",
            "WINDIR",
            "COMSPEC",
            "TEMP",
            "TMP",
            "LOCALAPPDATA",
            "APPDATA",
            "PROGRAMDATA",
            "USERPROFILE",
            "SPOTIFY_CLIENT_ID",
            "SPOTIFY_CLIENT_SECRET",
            "SPOTIFY_REDIRECT_URI",
            "SPOTIFY_SCOPES",
            "SPOTIFY_DEFAULT_DEVICE_NAME",
            "SPOTIFY_ACCESS_TOKEN",
            "SPOTIFY_REFRESH_TOKEN",
            "SPOTIFY_ACCESS_TOKEN_EXPIRES_AT",
            "SPOTIFY_TOKENS_PATH",
            "SPOTIFY_DEVICE_ALIASES_PATH",
            "JARVEZ_FRONTEND_URL",
        ],
    )


def _pilot_onenote_config() -> McpServerConfig:
    onenote_root = _jarvez_root().parent / "jarvez-mcp-onenote"
    return McpServerConfig(
        name="onenote",
        command=sys.executable,
        args=["server.py"],
        cwd=str(onenote_root),
        enabled=True,
        timeout_seconds=20,
        legacy_fallback_enabled=True,
        env_allowlist=[
            "PATH",
            "PATHEXT",
            "SYSTEMROOT",
            "WINDIR",
            "COMSPEC",
            "TEMP",
            "TMP",
            "LOCALAPPDATA",
            "APPDATA",
            "PROGRAMDATA",
            "USERPROFILE",
            "ONENOTE_CLIENT_ID",
            "ONENOTE_CLIENT_SECRET",
            "ONENOTE_REDIRECT_URI",
            "ONENOTE_SCOPES",
            "ONENOTE_ACCESS_TOKEN",
            "ONENOTE_REFRESH_TOKEN",
            "ONENOTE_ACCESS_TOKEN_EXPIRES_AT",
            "ONENOTE_TOKENS_PATH",
            "JARVEZ_FRONTEND_URL",
        ],
    )


def _pilot_home_assistant_config() -> McpServerConfig:
    home_assistant_root = _jarvez_root().parent / "jarvez-mcp-home-assistant"
    return McpServerConfig(
        name="home_assistant",
        command=sys.executable,
        args=["server.py"],
        cwd=str(home_assistant_root),
        enabled=True,
        timeout_seconds=20,
        legacy_fallback_enabled=True,
        env_allowlist=[
            "PATH",
            "PATHEXT",
            "SYSTEMROOT",
            "WINDIR",
            "COMSPEC",
            "TEMP",
            "TMP",
            "LOCALAPPDATA",
            "APPDATA",
            "PROGRAMDATA",
            "USERPROFILE",
            "HOME_ASSISTANT_URL",
            "HOME_ASSISTANT_TOKEN",
            "HOME_ASSISTANT_ALLOWED_SERVICES",
            "HOME_ASSISTANT_RETRY_COUNT",
            "HOME_ASSISTANT_TIMEOUT_SECONDS",
        ],
    )


def create_default_mcp_registry() -> "McpRegistry":
    return McpRegistry([
        _pilot_spotify_config(),
        _pilot_onenote_config(),
        _pilot_home_assistant_config(),
    ])


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
                    "env_allowlist": list(config.env_allowlist),
                    "env_overrides": {
                        str(key): _redact_env_value(str(key), value)
                        for key, value in config.env_overrides.items()
                    },
                }
            )
        return snapshot
