from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any

import requests


@dataclass(slots=True)
class WhatsAppMcpStatus:
    enabled: bool
    connected: bool
    mode: str
    detail: str | None = None
    history_available: bool = False
    messages_db_path: str | None = None


@dataclass(slots=True)
class WhatsAppMcpSendResult:
    success: bool
    message: str
    status_code: int | None = None
    payload: dict[str, Any] | None = None


class WhatsAppMcpClient:
    def __init__(self, base_url: str, *, messages_db_path: str | None = None):
        self.base_url = base_url.rstrip("/")
        if self.base_url.endswith("/api"):
            self.api_base = self.base_url
        else:
            self.api_base = f"{self.base_url}/api" if self.base_url else ""
        raw_messages_path = str(messages_db_path or "").strip()
        self.messages_db_path = raw_messages_path or None

    def _probe_url_candidates(self) -> list[str]:
        candidates: list[str] = []
        if self.base_url:
            candidates.append(f"{self.base_url}/health")
            candidates.append(f"{self.api_base}/send")
            candidates.append(f"{self.base_url}/send")
        unique: list[str] = []
        for url in candidates:
            if url and url not in unique:
                unique.append(url)
        return unique

    def _send_url_candidates(self) -> list[str]:
        candidates: list[str] = []
        if self.base_url:
            candidates.append(f"{self.api_base}/send")
            candidates.append(f"{self.base_url}/send")
        unique: list[str] = []
        for url in candidates:
            if url and url not in unique:
                unique.append(url)
        return unique

    @staticmethod
    def _send_payload_candidates(*, recipient: str, message: str) -> list[dict[str, str]]:
        candidates = [
            {"recipient": recipient, "message": message},
            {"to": recipient, "message": message},
            {"recipient": recipient, "text": message},
            {"to": recipient, "text": message},
            {"number": recipient, "text": message},
        ]
        unique: list[dict[str, str]] = []
        seen: set[tuple[tuple[str, str], ...]] = set()
        for payload in candidates:
            key = tuple(sorted(payload.items()))
            if key in seen:
                continue
            seen.add(key)
            unique.append(payload)
        return unique

    @staticmethod
    def _extract_status_detail(
        *,
        status_code: int,
        response_payload: dict[str, Any] | None,
        response_text: str,
    ) -> str:
        if response_payload:
            for key in ("message", "error", "detail"):
                value = response_payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
                if isinstance(value, dict):
                    nested = value.get("message")
                    if isinstance(nested, str) and nested.strip():
                        return nested.strip()
        return response_text.strip() or f"http_{status_code}"

    @staticmethod
    def _is_truthy(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        text = str(value or "").strip().lower()
        return text in {"1", "true", "yes", "y", "on"}

    @staticmethod
    def _normalize_timestamp(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
            except Exception:
                return str(value)
        text = str(value).strip()
        if not text:
            return ""
        if text.isdigit():
            try:
                return datetime.fromtimestamp(float(text), tz=timezone.utc).isoformat()
            except Exception:
                return text
        return text

    def _history_path(self) -> Path | None:
        if not self.messages_db_path:
            return None
        path = Path(self.messages_db_path).expanduser()
        if not path.exists():
            return None
        return path

    def _can_read_history(self) -> bool:
        path = self._history_path()
        if path is None:
            return False
        try:
            with sqlite3.connect(path, timeout=2.0) as conn:
                row = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='messages'"
                ).fetchone()
                return row is not None
        except Exception:
            return False

    def status(self) -> WhatsAppMcpStatus:
        history_available = self._can_read_history()
        if not self.base_url:
            return WhatsAppMcpStatus(
                enabled=history_available,
                connected=False,
                mode="legacy",
                detail="JARVEZ_WHATSAPP_MCP_URL not configured",
                history_available=history_available,
                messages_db_path=self.messages_db_path,
            )
        last_detail: str | None = None
        for url in self._probe_url_candidates():
            try:
                response = requests.get(url, timeout=4)
            except Exception as exc:  # noqa: BLE001
                last_detail = str(exc)
                continue
            status_code = int(response.status_code)
            if 200 <= status_code < 300:
                detail = "health_ok" if url.endswith("/health") else f"http_{status_code}"
                return WhatsAppMcpStatus(
                    enabled=True,
                    connected=True,
                    mode="mcp",
                    detail=detail,
                    history_available=history_available,
                    messages_db_path=self.messages_db_path,
                )
            if status_code in {400, 401, 403, 405, 415}:
                return WhatsAppMcpStatus(
                    enabled=True,
                    connected=True,
                    mode="mcp",
                    detail=f"http_{status_code}",
                    history_available=history_available,
                    messages_db_path=self.messages_db_path,
                )
            last_detail = f"http_{status_code}"
        return WhatsAppMcpStatus(
            enabled=True,
            connected=False,
            mode="mcp",
            detail=last_detail,
            history_available=history_available,
            messages_db_path=self.messages_db_path,
        )

    def send_text(self, *, recipient: str, message: str) -> WhatsAppMcpSendResult:
        recipient_value = str(recipient or "").strip()
        message_value = str(message or "").strip()
        if not recipient_value:
            return WhatsAppMcpSendResult(success=False, message="recipient is required")
        if not message_value:
            return WhatsAppMcpSendResult(success=False, message="message is required")
        try:
            last_detail: str | None = None
            for url in self._send_url_candidates():
                for payload in self._send_payload_candidates(recipient=recipient_value, message=message_value):
                    try:
                        response = requests.post(url, json=payload, timeout=10)
                    except Exception as exc:  # noqa: BLE001
                        last_detail = str(exc)
                        continue
                    status_code = int(response.status_code)
                    response_payload: dict[str, Any] | None = None
                    try:
                        parsed = response.json()
                        if isinstance(parsed, dict):
                            response_payload = parsed
                    except ValueError:
                        response_payload = None

                    if 200 <= status_code < 300:
                        success = bool(response_payload.get("success", True)) if response_payload else True
                        message_text = (
                            str(response_payload.get("message") or "").strip()
                            if response_payload
                            else "Message sent via MCP bridge."
                        )
                        return WhatsAppMcpSendResult(
                            success=success,
                            message=message_text or "Message sent via MCP bridge.",
                            status_code=status_code,
                            payload=response_payload,
                        )
                    detail = self._extract_status_detail(
                        status_code=status_code,
                        response_payload=response_payload,
                        response_text=response.text,
                    )
                    if status_code in {400, 404, 405, 415, 422}:
                        last_detail = detail
                        continue
                    return WhatsAppMcpSendResult(
                        success=False,
                        message=detail,
                        status_code=status_code,
                        payload=response_payload,
                    )
            return WhatsAppMcpSendResult(
                success=False,
                message=last_detail or "unable to reach MCP bridge",
            )
        except Exception as exc:  # noqa: BLE001
            return WhatsAppMcpSendResult(success=False, message=str(exc))

    def list_recent_messages(self, *, limit: int = 200) -> list[dict[str, Any]]:
        path = self._history_path()
        if path is None:
            return []
        try:
            requested_limit = int(limit)
        except (TypeError, ValueError):
            requested_limit = 200
        safe_limit = max(1, min(requested_limit, 500))
        rows: list[dict[str, Any]] = []
        try:
            with sqlite3.connect(path, timeout=4.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """
                    SELECT
                        id,
                        chat_jid,
                        sender,
                        content,
                        timestamp,
                        is_from_me,
                        media_type,
                        filename
                    FROM messages
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (safe_limit,),
                )
                for row in cursor.fetchall():
                    is_from_me = self._is_truthy(row["is_from_me"])
                    if is_from_me:
                        continue
                    sender = str(row["sender"] or "").strip()
                    chat_jid = str(row["chat_jid"] or "").strip()
                    content = str(row["content"] or "").strip()
                    media_type = str(row["media_type"] or "").strip()
                    timestamp = self._normalize_timestamp(row["timestamp"])
                    message_id = str(row["id"] or "").strip()
                    rows.append(
                        {
                            "id": message_id or None,
                            "from": sender or chat_jid,
                            "chat_jid": chat_jid or None,
                            "text": content,
                            "type": media_type or "text",
                            "timestamp": timestamp,
                            "received_at": timestamp,
                            "direction": "inbound",
                            "source": "whatsapp_mcp_bridge",
                            "filename": str(row["filename"] or "").strip() or None,
                        }
                    )
        except Exception:
            return []
        return rows
