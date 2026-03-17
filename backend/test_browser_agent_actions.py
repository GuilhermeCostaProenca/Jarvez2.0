from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sys
import types
import unittest
from unittest.mock import patch

if "numpy" not in sys.modules:
    sys.modules["numpy"] = types.SimpleNamespace()

from actions import _browser_agent_run
from actions_core import ActionContext, PendingConfirmation


class BrowserAgentActionTests(unittest.IsolatedAsyncioTestCase):
    async def test_browser_agent_write_mode_requires_confirmation_gate(self) -> None:
        ctx = ActionContext(job_id="job-1", room="room-1", participant_identity="user-1")
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        pending = PendingConfirmation(
            token="token-123",
            action_name="browser_agent_run",
            params={},
            participant_identity=ctx.participant_identity,
            room=ctx.room,
            expires_at=expires_at,
        )
        with patch("actions._store_confirmation", return_value=pending) as store_confirmation_mock:
            result = await _browser_agent_run(
                {
                    "request": "faca login no portal",
                    "allowed_domains": ["example.com"],
                    "read_only": False,
                },
                ctx,
            )

        self.assertFalse(result.success)
        self.assertEqual(result.error, "write_confirmation_required")
        self.assertTrue(bool((result.data or {}).get("confirmation_required")))
        self.assertEqual((result.data or {}).get("confirmation_token"), "token-123")
        confirmed_params = store_confirmation_mock.call_args.args[1]
        self.assertTrue(bool(confirmed_params.get("write_confirmed")))


if __name__ == "__main__":
    unittest.main()
