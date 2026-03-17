from __future__ import annotations

import unittest

from providers.provider_router import ModelRouteDecision, route_request


class _FailingProvider:
    def __init__(self, name: str):
        self.provider_name = name

    def supports_tools(self) -> bool:
        return True

    def supports_realtime(self) -> bool:
        return False

    def generate_text(self, request: str) -> tuple[str | None, str | None]:
        _ = request
        return None, f"{self.provider_name} unavailable"

    def stream_text(self, request: str) -> tuple[str | None, str | None]:
        return self.generate_text(request)

    def realtime_turn(self, request: str) -> tuple[str | None, str | None]:
        return self.generate_text(request)


class _SuccessProvider:
    def __init__(self, name: str, prefix: str):
        self.provider_name = name
        self._prefix = prefix

    def supports_tools(self) -> bool:
        return True

    def supports_realtime(self) -> bool:
        return False

    def generate_text(self, request: str) -> tuple[str | None, str | None]:
        return f"[{self._prefix}] {request}", None

    def stream_text(self, request: str) -> tuple[str | None, str | None]:
        return self.generate_text(request)

    def realtime_turn(self, request: str) -> tuple[str | None, str | None]:
        return self.generate_text(request)


class ProviderRouterTests(unittest.TestCase):
    def test_route_request_respects_custom_provider_order(self) -> None:
        providers = {
            "openai": _FailingProvider("openai"),
            "anthropic": _SuccessProvider("anthropic", "anthropic"),
            "google": _SuccessProvider("google", "google"),
            "local_mock": _SuccessProvider("local_mock", "local"),
        }
        text, decision = route_request(
            request="ola",
            task_type="chat",
            risk="R1",
            providers=providers,
            provider_order=["google", "anthropic"],
        )
        self.assertEqual(text, "[google] ola")
        self.assertIsInstance(decision, ModelRouteDecision)
        self.assertEqual(decision.primary_provider, "google")
        self.assertEqual(decision.fallback_provider, "anthropic")
        self.assertEqual(decision.used_provider, "google")
        self.assertFalse(decision.fallback_used)


if __name__ == "__main__":
    unittest.main()
