from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

JsonObject = dict[str, Any]


class McpClientError(RuntimeError):
    def __init__(self, status: str, detail: str | None = None):
        self.status = status
        self.detail = detail
        message = status if not detail else f"{status}: {detail}"
        super().__init__(message)


@dataclass(slots=True)
class McpServerConfig:
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    cwd: str | None = None
    enabled: bool = True
    timeout_seconds: int = 20
    legacy_fallback_enabled: bool = True
    env_allowlist: list[str] = field(default_factory=list)
    env_overrides: JsonObject = field(default_factory=dict)


@dataclass(slots=True)
class McpToolInfo:
    name: str
    description: str
    input_schema: JsonObject


@dataclass(slots=True)
class McpToolCallResult:
    ok: bool
    status: str
    detail: str | None = None
    structured_content: JsonObject | None = None
    text: str | None = None
    raw_result: JsonObject | None = None


@dataclass(slots=True)
class McpServerStatus:
    server_name: str
    enabled: bool
    process_active: bool
    legacy_fallback_enabled: bool
    discovered_tools: list[str] = field(default_factory=list)
    env_keys: list[str] = field(default_factory=list)
    env_preview: JsonObject = field(default_factory=dict)
    last_discovery_at: str | None = None
    last_success_at: str | None = None
    last_failure_at: str | None = None
    last_error_type: str | None = None
    last_error_detail: str | None = None
    last_response_ms: int | None = None

    def to_payload(self) -> JsonObject:
        return {
            "server_name": self.server_name,
            "enabled": self.enabled,
            "process_active": self.process_active,
            "legacy_fallback_enabled": self.legacy_fallback_enabled,
            "discovered_tools": list(self.discovered_tools),
            "env_keys": list(self.env_keys),
            "env_preview": dict(self.env_preview),
            "last_discovery_at": self.last_discovery_at,
            "last_success_at": self.last_success_at,
            "last_failure_at": self.last_failure_at,
            "last_error_type": self.last_error_type,
            "last_error_detail": self.last_error_detail,
            "last_response_ms": self.last_response_ms,
        }
