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
