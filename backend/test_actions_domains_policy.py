from __future__ import annotations

from types import SimpleNamespace
import unittest

from actions_core import ActionContext
from actions_domains.policy import (
    autonomy_set_mode_action,
    policy_action_risk_matrix_action,
    policy_trust_drift_report_action,
)


class _DomainTrust:
    def __init__(self, domain: str, score: float):
        self.domain = domain
        self.score = score

    def to_payload(self) -> dict[str, object]:
        return {"domain": self.domain, "score": self.score}


class PolicyActionsDomainTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.ctx = ActionContext(job_id="job-1", room="room-1", participant_identity="user-1")

    async def test_autonomy_set_mode_rejects_invalid_mode(self) -> None:
        result = await autonomy_set_mode_action(
            {"mode": "turbo"},
            self.ctx,
            require_feature=lambda _feature: None,
            allowed_autonomy_modes={"manual", "safe"},
            set_autonomy_mode=lambda _pid, _room, mode: mode,
            get_killswitch_status=lambda: SimpleNamespace(to_payload=lambda: {"global": False}),
            capability_payload=lambda _pid, _room: {},
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "invalid mode")

    async def test_autonomy_set_mode_applies_value(self) -> None:
        result = await autonomy_set_mode_action(
            {"mode": "safe"},
            self.ctx,
            require_feature=lambda _feature: None,
            allowed_autonomy_modes={"manual", "safe"},
            set_autonomy_mode=lambda _pid, _room, mode: mode,
            get_killswitch_status=lambda: SimpleNamespace(to_payload=lambda: {"global": False}),
            capability_payload=lambda _pid, _room: {"capability_mode": "safe"},
        )
        self.assertTrue(result.success)
        self.assertEqual(result.data["autonomy_mode"], "safe")
        self.assertEqual(result.data["kill_switch"]["global"], False)

    async def test_policy_action_risk_matrix_filters_by_query(self) -> None:
        registry = {
            "ops_incident_snapshot": SimpleNamespace(
                name="ops_incident_snapshot",
                requires_confirmation=False,
                requires_auth=True,
                expose_to_model=True,
            ),
            "workflow_cancel": SimpleNamespace(
                name="workflow_cancel",
                requires_confirmation=True,
                requires_auth=True,
                expose_to_model=True,
            ),
        }
        result = await policy_action_risk_matrix_action(
            {"query": "workflow"},
            self.ctx,
            action_registry=registry,
            classify_action_risk=lambda action_name: "R2" if action_name == "workflow_cancel" else "R1",
            infer_action_domain=lambda action_name: "workflow" if "workflow" in action_name else "ops",
            get_domain_trust=lambda domain: _DomainTrust(domain=domain, score=0.9),
            capability_payload=lambda _pid, _room: {},
        )
        self.assertTrue(result.success)
        rows = result.data["risk_matrix"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["action_name"], "workflow_cancel")

    async def test_policy_trust_drift_report_requires_rows_list(self) -> None:
        result = await policy_trust_drift_report_action(
            {"rows": "invalid"},
            self.ctx,
            replace_trust_drift=lambda *_args, **_kwargs: [],
            capability_payload=lambda _pid, _room: {},
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "invalid rows")


if __name__ == "__main__":
    unittest.main()
