from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def publish_session_event(session: Any | None, payload: dict[str, object]) -> None:
    if session is None:
        return
    room_io = getattr(session, "room_io", None)
    room = getattr(room_io, "room", None)
    participant = getattr(room, "local_participant", None)
    if participant is None:
        return
    try:
        await participant.publish_data(
            json.dumps(payload, ensure_ascii=False),
            topic="lk.agent.events",
        )
    except Exception:
        logger.warning("failed to publish agent event", exc_info=True)
