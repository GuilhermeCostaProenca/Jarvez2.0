from __future__ import annotations

import asyncio
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dotenv import load_dotenv

from actions_core.store import JarvezStateStore
from backend_mcp import (
    McpManager,
    call_mcp_tool_with_legacy_fallback,
    create_default_mcp_registry,
    shutdown_mcp_runtime,
)

load_dotenv(Path(__file__).with_name(".env"), override=False)


class McpSubstrateTests(unittest.TestCase):
    def test_default_manifest_registers_spotify_onenote_home_assistant_thinq_rpg_and_whatsapp(self) -> None:
        registry = create_default_mcp_registry()
        snapshot = registry.manifest_snapshot()
        self.assertEqual(len(snapshot), 6)
        snapshot_by_name = {row["name"]: row for row in snapshot}

        self.assertIn("spotify", snapshot_by_name)
        self.assertTrue(snapshot_by_name["spotify"]["enabled"])
        self.assertTrue(str(snapshot_by_name["spotify"]["cwd"]).endswith("jarvez-mcp-spotify"))
        self.assertIn("SPOTIFY_CLIENT_ID", snapshot_by_name["spotify"]["env_allowlist"])

        self.assertIn("onenote", snapshot_by_name)
        self.assertTrue(snapshot_by_name["onenote"]["enabled"])
        self.assertTrue(str(snapshot_by_name["onenote"]["cwd"]).endswith("jarvez-mcp-onenote"))
        self.assertIn("ONENOTE_CLIENT_ID", snapshot_by_name["onenote"]["env_allowlist"])

        self.assertIn("home_assistant", snapshot_by_name)
        self.assertTrue(snapshot_by_name["home_assistant"]["enabled"])
        self.assertTrue(str(snapshot_by_name["home_assistant"]["cwd"]).endswith("jarvez-mcp-home-assistant"))
        self.assertIn("HOME_ASSISTANT_URL", snapshot_by_name["home_assistant"]["env_allowlist"])

        self.assertIn("thinq", snapshot_by_name)
        self.assertTrue(snapshot_by_name["thinq"]["enabled"])
        self.assertTrue(str(snapshot_by_name["thinq"]["cwd"]).endswith("jarvez-mcp-thinq"))
        self.assertIn("THINQ_PAT", snapshot_by_name["thinq"]["env_allowlist"])

        self.assertIn("rpg", snapshot_by_name)
        self.assertTrue(snapshot_by_name["rpg"]["enabled"])
        self.assertTrue(str(snapshot_by_name["rpg"]["cwd"]).endswith("jarvez-mcp-rpg"))
        self.assertIn("RPG_KNOWLEDGE_DB_PATH", snapshot_by_name["rpg"]["env_allowlist"])

        self.assertIn("whatsapp", snapshot_by_name)
        self.assertTrue(snapshot_by_name["whatsapp"]["enabled"])
        self.assertTrue(str(snapshot_by_name["whatsapp"]["cwd"]).endswith("references\\whatsapp-mcp\\whatsapp-mcp-server"))

    def test_spotify_pilot_can_list_tools_and_call_real_tool(self) -> None:
        audit_rows: list[dict[str, object]] = []

        class _FakeStore:
            def append_mcp_call_audit(self, **kwargs):  # noqa: ANN003
                audit_rows.append(dict(kwargs))
                return len(audit_rows)

        async def _run() -> tuple[list[str], object]:
            registry = create_default_mcp_registry()
            manager = McpManager(registry)
            try:
                with patch.object(sys.modules["jarvez_backend_mcp.manager"], "get_state_store", return_value=_FakeStore()):
                    tools = await manager.list_tools("spotify")
                    result = await manager.call_tool("spotify", "spotify_status", {})
                    status = manager.get_server_status("spotify")
                return [tool.name for tool in tools], result, status
            finally:
                await manager.shutdown_all()

        tool_names, result, status = asyncio.run(_run())
        self.assertIn("spotify_status", tool_names)
        self.assertEqual(result.status, "ok")
        self.assertIsInstance(result.raw_result, dict)
        self.assertIsInstance(result.structured_content, dict)
        self.assertIn("message", result.structured_content or {})
        self.assertTrue(status["process_active"])
        self.assertIsNotNone(status["last_success_at"])
        self.assertEqual(status["discovered_tools"], tool_names)
        self.assertIn("SPOTIFY_CLIENT_ID", status["env_keys"])
        self.assertEqual(status["env_preview"].get("SPOTIFY_CLIENT_SECRET"), "***REDACTED***")
        self.assertTrue(audit_rows)
        self.assertEqual(audit_rows[-1]["server_name"], "spotify")
        self.assertEqual(audit_rows[-1]["tool_name"], "spotify_status")
        self.assertIn("message", audit_rows[-1]["result_summary"]["structured_content"])

    def test_explicit_legacy_fallback_is_recorded(self) -> None:
        audit_rows: list[dict[str, object]] = []

        class _FakeStore:
            def append_mcp_call_audit(self, **kwargs):  # noqa: ANN003
                audit_rows.append(dict(kwargs))
                return len(audit_rows)

        async def _run() -> tuple[object, object, object]:
            try:
                with patch.object(sys.modules["jarvez_backend_mcp.manager"], "get_state_store", return_value=_FakeStore()):
                    return await call_mcp_tool_with_legacy_fallback(
                        "spotify",
                        "spotify_missing_tool",
                        {},
                        legacy_handler=lambda: {"source": "legacy", "success": True},
                    )
            finally:
                await shutdown_mcp_runtime()

        result, legacy_value, fallback_reason = asyncio.run(_run())
        self.assertIsNotNone(result)
        self.assertFalse(result.ok)
        self.assertEqual(legacy_value, {"source": "legacy", "success": True})
        self.assertEqual(fallback_reason, result.status)
        self.assertGreaterEqual(len(audit_rows), 2)
        self.assertTrue(any(bool(row.get("fallback_used")) for row in audit_rows))

    def test_store_can_persist_mcp_audit_rows(self) -> None:
        tmp_dir = Path(tempfile.mkdtemp(prefix="jarvez_mcp_audit_"))
        db_path = tmp_dir / "state.db"
        try:
            store = JarvezStateStore(db_path=db_path)
            row_id = store.append_mcp_call_audit(
                server_name="spotify",
                tool_name="spotify_status",
                success=False,
                args_payload={"token": "secret-token", "query": "status"},
                duration_ms=42,
                result_summary={"status": "ok", "structured_content": {"message": "hello"}},
                error_type="spotify_auth_required",
                fallback_used=True,
                fallback_reason="tool_error",
            )
            rows = store.list_mcp_call_audit(server_name="spotify", limit=5)
        finally:
            for suffix in ("", "-wal", "-shm"):
                path = Path(f"{db_path}{suffix}")
                if path.exists():
                    try:
                        path.unlink()
                    except PermissionError:
                        pass
            try:
                tmp_dir.rmdir()
            except OSError:
                pass

        self.assertGreater(row_id, 0)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["tool_name"], "spotify_status")
        self.assertTrue(rows[0]["fallback_used"])
        self.assertEqual(rows[0]["fallback_reason"], "tool_error")


if __name__ == "__main__":
    unittest.main()
