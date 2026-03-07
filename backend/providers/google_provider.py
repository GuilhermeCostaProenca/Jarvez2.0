from __future__ import annotations

import os
from typing import Any

import requests


class GoogleProvider:
    provider_name = "google"

    def _configured(self) -> bool:
        if str(os.getenv("GOOGLE_API_KEY", "")).strip():
            return True
        if str(os.getenv("GEMINI_API_KEY", "")).strip():
            return True
        return False

    def supports_tools(self) -> bool:
        return True

    def supports_realtime(self) -> bool:
        return False

    def _model(self) -> str:
        return str(os.getenv("JARVEZ_GOOGLE_MODEL", "")).strip() or "gemini-2.5-flash"

    def _timeout_seconds(self) -> int:
        raw = str(os.getenv("JARVEZ_PROVIDER_TIMEOUT_SECONDS", "25")).strip()
        try:
            return max(5, min(90, int(raw)))
        except ValueError:
            return 25

    def _key(self) -> str:
        return str(os.getenv("GEMINI_API_KEY", "")).strip() or str(os.getenv("GOOGLE_API_KEY", "")).strip()

    def _parse_content(self, payload: dict[str, Any]) -> str | None:
        candidates = payload.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            return None
        first = candidates[0] if isinstance(candidates[0], dict) else None
        content = first.get("content") if isinstance(first, dict) else None
        parts = content.get("parts") if isinstance(content, dict) else None
        if not isinstance(parts, list):
            return None
        texts: list[str] = []
        for item in parts:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                texts.append(item.get("text", ""))
        text = "\n".join(part.strip() for part in texts if part.strip())
        return text or None

    def generate_text(self, request: str) -> tuple[str | None, str | None]:
        if not self._configured():
            return None, "GOOGLE_API_KEY or GEMINI_API_KEY not configured"
        key = self._key()
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model()}:generateContent"
        try:
            response = requests.post(
                endpoint,
                params={"key": key},
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": request}]}],
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 700},
                },
                timeout=self._timeout_seconds(),
            )
        except requests.RequestException as error:
            return None, f"google request failed: {error}"

        if not (200 <= response.status_code < 300):
            return None, f"google http {response.status_code}: {response.text[:240]}"
        payload = response.json() if response.content else {}
        if not isinstance(payload, dict):
            return None, "google invalid response"
        parsed = self._parse_content(payload)
        if not parsed:
            return None, "google empty content"
        return parsed, None

    def stream_text(self, request: str) -> tuple[str | None, str | None]:
        return self.generate_text(request)

    def realtime_turn(self, request: str) -> tuple[str | None, str | None]:
        return None, "realtime not supported"
