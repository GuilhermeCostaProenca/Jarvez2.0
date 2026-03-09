from __future__ import annotations

from typing import Any


def merge_event_state(current: Any, incoming: Any) -> Any:
    if isinstance(current, list) and isinstance(incoming, list):
        return incoming
    if isinstance(current, dict) and isinstance(incoming, dict):
        merged = dict(current)
        merged.update(incoming)
        return merged
    return incoming
