from __future__ import annotations

import os
from typing import Any

import requests


class OpenAIProvider:
    provider_name = "openai"

    def _configured(self) -> bool:
        return bool(str(os.getenv("OPENAI_API_KEY", "")).strip())

    def supports_tools(self) -> bool:
        return True

    def supports_realtime(self) -> bool:
        return True

    def _model(self) -> str:
        return str(os.getenv("JARVEZ_OPENAI_MODEL", "")).strip() or "gpt-4.1-mini"

    def _timeout_seconds(self) -> int:
        raw = str(os.getenv("JARVEZ_PROVIDER_TIMEOUT_SECONDS", "25")).strip()
        try:
            return max(5, min(90, int(raw)))
        except ValueError:
            return 25

    def _parse_content(self, payload: dict[str, Any]) -> str | None:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            return None
        first = choices[0] if isinstance(choices[0], dict) else None
        message = first.get("message") if isinstance(first, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, str):
            text = content.strip()
            return text or None
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"])
            text = "\n".join(part.strip() for part in parts if part.strip())
            return text or None
        return None

    def generate_text(self, request: str) -> tuple[str | None, str | None]:
        if not self._configured():
            return None, "OPENAI_API_KEY not configured"
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY', '').strip()}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model(),
                    "temperature": 0.2,
                    "max_tokens": 700,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Responda de forma objetiva em portugues brasileiro, com foco em execucao tecnica.",
                        },
                        {"role": "user", "content": request},
                    ],
                },
                timeout=self._timeout_seconds(),
            )
        except requests.RequestException as error:
            return None, f"openai request failed: {error}"

        if not (200 <= response.status_code < 300):
            return None, f"openai http {response.status_code}: {response.text[:240]}"

        payload = response.json() if response.content else {}
        if not isinstance(payload, dict):
            return None, "openai invalid response"
        parsed = self._parse_content(payload)
        if not parsed:
            return None, "openai empty content"
        return parsed, None

    def stream_text(self, request: str) -> tuple[str | None, str | None]:
        return self.generate_text(request)

    def realtime_turn(self, request: str) -> tuple[str | None, str | None]:
        return self.generate_text(request)
