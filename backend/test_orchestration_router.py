from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from orchestration.router import route_orchestration
from providers.provider_router import ModelRouteDecision


class OrchestrationRouterTests(unittest.TestCase):
    @patch("orchestration.router.route_request")
    @patch("orchestration.router.build_provider_registry")
    @patch("orchestration.router.resolve_runtime")
    def test_route_orchestration_applies_runtime_gateway_order(
        self,
        resolve_runtime_mock,
        build_provider_registry_mock,
        route_request_mock,
    ) -> None:
        resolve_runtime_mock.return_value = SimpleNamespace(
            primary_provider="google",
            fallback_provider="openai",
            reason="Gateway selected providers.",
        )
        build_provider_registry_mock.return_value = {"google": object(), "openai": object()}
        route_request_mock.return_value = (
            "ok",
            ModelRouteDecision(
                task_type="chat",
                risk="R1",
                primary_provider="openai",
                fallback_provider="anthropic",
                used_provider="google",
                fallback_used=False,
                reason="Provider selecionado por task_type/risk.",
                generated_at="2026-03-09T00:00:00Z",
            ),
        )

        output, decision = route_orchestration(request="resuma", task_type="chat", risk="R1")

        self.assertEqual(output, "ok")
        self.assertEqual(decision.primary_provider, "google")
        self.assertEqual(decision.fallback_provider, "openai")
        self.assertIn("Gateway selected providers.", decision.reason)
        self.assertIn("Provider selecionado", decision.reason)
        route_kwargs = route_request_mock.call_args.kwargs
        self.assertEqual(route_kwargs["provider_order"][:2], ["google", "openai"])


if __name__ == "__main__":
    unittest.main()
