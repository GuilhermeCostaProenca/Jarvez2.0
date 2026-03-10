import unittest
from unittest.mock import patch

from actions_domains.whatsapp_channel import build_whatsapp_channel_status
from channels.whatsapp_adapter import normalize_bridge_payload, normalize_inbound_webhook_message


class WhatsAppChannelAdapterTests(unittest.TestCase):
    def test_normalize_inbound_webhook_message_accepts_string_text(self):
        envelope = normalize_inbound_webhook_message(
            {
                "id": "wamid.1",
                "from": "5511999990000",
                "text": "bom dia",
                "source": "whatsapp_mcp_bridge",
                "received_at": "2026-03-09T12:00:00+00:00",
            }
        )
        self.assertEqual(envelope.identity.channel, "whatsapp")
        self.assertEqual(envelope.identity.participant_identity, "5511999990000")
        self.assertEqual(envelope.identity.room, "whatsapp_mcp_bridge")
        self.assertEqual(envelope.text, "bom dia")
        self.assertEqual(envelope.received_at, "2026-03-09T12:00:00+00:00")

    def test_normalize_bridge_payload_discards_invalid_rows(self):
        envelopes = normalize_bridge_payload(
            {
                "messages": [
                    {"from": "5511888880000", "text": {"body": "oi"}},
                    "invalid",
                    {"sender": "5511777770000", "caption": "anexo"},
                ]
            }
        )
        self.assertEqual(len(envelopes), 2)
        self.assertEqual(envelopes[0].identity.participant_identity, "5511888880000")
        self.assertEqual(envelopes[0].text, "oi")
        self.assertEqual(envelopes[1].identity.participant_identity, "5511777770000")
        self.assertEqual(envelopes[1].text, "anexo")

    def test_build_whatsapp_channel_status_reports_fallback_signals(self):
        with patch("actions_domains.whatsapp_channel.os.getenv") as getenv:
            getenv.side_effect = lambda key, default="": {
                "JARVEZ_WHATSAPP_MCP_URL": "",
                "JARVEZ_WHATSAPP_MCP_MESSAGES_DB_PATH": "",
                "WHATSAPP_PHONE_NUMBER_ID": "123456",
            }.get(key, default)
            status = build_whatsapp_channel_status()
        self.assertEqual(status["mode"], "legacy_v1")
        self.assertTrue(status["fallback_active"])
        self.assertEqual(status["history_source"], "legacy_json")
        self.assertFalse(status["mcp"]["connected"])


if __name__ == "__main__":
    unittest.main()
