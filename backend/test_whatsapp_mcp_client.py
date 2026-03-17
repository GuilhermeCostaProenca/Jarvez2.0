import sqlite3
import tempfile
import unittest
import gc
import shutil
from pathlib import Path
from unittest.mock import patch

from integrations.whatsapp_mcp_client import WhatsAppMcpClient


class _FakeResponse:
    def __init__(self, status_code: int, payload=None, text: str = ""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("no json payload")
        return self._payload


class WhatsAppMcpClientTests(unittest.TestCase):
    def test_status_reports_disabled_without_url(self):
        client = WhatsAppMcpClient("")
        status = client.status()
        self.assertFalse(status.enabled)
        self.assertFalse(status.connected)
        self.assertEqual(status.mode, "legacy")

    def test_status_accepts_send_endpoint_probe(self):
        client = WhatsAppMcpClient("http://localhost:8080")
        with patch("integrations.whatsapp_mcp_client.requests.get") as mocked_get:
            mocked_get.side_effect = [
                _FakeResponse(404, text="not found"),
                _FakeResponse(405, text="method not allowed"),
            ]
            status = client.status()
        self.assertTrue(status.enabled)
        self.assertTrue(status.connected)
        self.assertEqual(status.mode, "mcp")
        self.assertEqual(status.detail, "http_405")

    def test_send_text_returns_success_payload(self):
        client = WhatsAppMcpClient("http://localhost:8080")
        with patch("integrations.whatsapp_mcp_client.requests.post") as mocked_post:
            mocked_post.return_value = _FakeResponse(
                200,
                payload={"success": True, "message": "Message sent", "id": "abc"},
            )
            result = client.send_text(recipient="5511999990000", message="oi")
        self.assertTrue(result.success)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.payload.get("id"), "abc")

    def test_send_text_tries_alternative_payload_shapes(self):
        client = WhatsAppMcpClient("http://localhost:8080")
        payloads: list[dict[str, str]] = []

        def _post_side_effect(_url, json, timeout):  # noqa: ANN001
            _ = timeout
            payloads.append(dict(json))
            if json == {"recipient": "5511999990000", "message": "oi"}:
                return _FakeResponse(422, payload={"error": "wrong schema"})
            return _FakeResponse(200, payload={"success": True, "message": "ok"})

        with patch("integrations.whatsapp_mcp_client.requests.post", side_effect=_post_side_effect):
            result = client.send_text(recipient="5511999990000", message="oi")

        self.assertTrue(result.success)
        self.assertGreaterEqual(len(payloads), 2)
        self.assertIn({"to": "5511999990000", "message": "oi"}, payloads)

    def test_list_recent_messages_reads_sqlite_history(self):
        tmp_dir = Path(tempfile.mkdtemp(prefix="jarvez_whatsapp_mcp_"))
        db_path = tmp_dir / "messages.db"
        try:
            with sqlite3.connect(db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE messages (
                        id TEXT,
                        chat_jid TEXT,
                        sender TEXT,
                        content TEXT,
                        timestamp TEXT,
                        is_from_me BOOLEAN,
                        media_type TEXT,
                        filename TEXT
                    )
                    """
                )
                conn.execute(
                    """
                    INSERT INTO messages (id, chat_jid, sender, content, timestamp, is_from_me, media_type, filename)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    ("m1", "5511999990000@s.whatsapp.net", "5511999990000", "bom dia", "2026-03-09T10:00:00+00:00", 0, "", None),
                )
                conn.execute(
                    """
                    INSERT INTO messages (id, chat_jid, sender, content, timestamp, is_from_me, media_type, filename)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    ("m2", "5511999990000@s.whatsapp.net", "me", "resposta", "2026-03-09T10:01:00+00:00", 1, "", None),
                )
                conn.commit()

            client = WhatsAppMcpClient("http://localhost:8080", messages_db_path=str(db_path))
            entries = client.list_recent_messages(limit=10)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["id"], "m1")
            self.assertEqual(entries[0]["from"], "5511999990000")
            self.assertEqual(entries[0]["direction"], "inbound")
        finally:
            gc.collect()
            for suffix in ("", "-wal", "-shm"):
                path = Path(f"{db_path}{suffix}")
                if path.exists():
                    try:
                        path.unlink()
                    except PermissionError:
                        pass
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_list_recent_messages_handles_string_flags_and_limit_fallback(self):
        tmp_dir = Path(tempfile.mkdtemp(prefix="jarvez_whatsapp_mcp_"))
        db_path = tmp_dir / "messages.db"
        try:
            with sqlite3.connect(db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE messages (
                        id TEXT,
                        chat_jid TEXT,
                        sender TEXT,
                        content TEXT,
                        timestamp TEXT,
                        is_from_me TEXT,
                        media_type TEXT,
                        filename TEXT
                    )
                    """
                )
                conn.execute(
                    """
                    INSERT INTO messages (id, chat_jid, sender, content, timestamp, is_from_me, media_type, filename)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    ("m1", "5511999990000@s.whatsapp.net", "5511999990000", "inbound", "1741514400", "0", "", None),
                )
                conn.execute(
                    """
                    INSERT INTO messages (id, chat_jid, sender, content, timestamp, is_from_me, media_type, filename)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    ("m2", "5511999990000@s.whatsapp.net", "me", "outbound", "1741514401", "1", "", None),
                )
                conn.commit()

            client = WhatsAppMcpClient("http://localhost:8080", messages_db_path=str(db_path))
            entries = client.list_recent_messages(limit="invalid")
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["id"], "m1")
            self.assertIn("T", entries[0]["timestamp"])
        finally:
            gc.collect()
            for suffix in ("", "-wal", "-shm"):
                path = Path(f"{db_path}{suffix}")
                if path.exists():
                    try:
                        path.unlink()
                    except PermissionError:
                        pass
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
