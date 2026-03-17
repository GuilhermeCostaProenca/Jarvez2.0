from __future__ import annotations

import os
from typing import Any

import requests


class AnthropicProvider:
    provider_name = "anthropic"

    def _configured(self) -> bool:
        return bool(str(os.getenv("ANTHROPIC_API_KEY", "")).strip())

    def supports_tools(self) -> bool:
        return True

    def supports_realtime(self) -> bool:
        return False

    def _model(self) -> str:
        return str(os.getenv("JARVEZ_ANTHROPIC_MODEL", "")).strip() or "claude-3-5-sonnet-latest"

    def _timeout_seconds(self) -> int:
        raw = str(os.getenv("JARVEZ_PROVIDER_TIMEOUT_SECONDS", "25")).strip()
        try:
            return max(5, min(90, int(raw)))
        except ValueError:
            return 25

    def _parse_content(self, payload: dict[str, Any]) -> str | None:
        content = payload.get("content")
        if not isinstance(content, list):
            return None
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                parts.append(item.get("text", ""))
        text = "\n".join(part.strip() for part in parts if part.strip())
        return text or None

    def generate_text(self, request: str) -> tuple[str | None, str | None]:
        if not self._configured():
            return None, "ANTHROPIC_API_KEY not configured"
        key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self._model(),
                    "max_tokens": 700,
                    "system": "Responda de forma objetiva em portugues brasileiro, com foco em execucao tecnica.",
                    "messages": [{"role": "user", "content": request}],
                },
                timeout=self._timeout_seconds(),
            )
        except requests.RequestException as error:
            return None, f"anthropic request failed: {error}"

        if not (200 <= response.status_code < 300):
            return None, f"anthropic http {response.status_code}: {response.text[:240]}"
        payload = response.json() if response.content else {}
        if not isinstance(payload, dict):
            return None, "anthropic invalid response"
        parsed = self._parse_content(payload)
        if not parsed:
            return None, "anthropic empty content"
        return parsed, None

    def stream_text(self, request: str) -> tuple[str | None, str | None]:
        return self.generate_text(request)

    def realtime_turn(self, request: str) -> tuple[str | None, str | None]:
        return None, "realtime not supported"
