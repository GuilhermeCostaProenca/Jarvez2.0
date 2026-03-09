from __future__ import annotations

import time

from .loader import discover_skills, read_skill_document
from .schemas import SkillDocument, SkillMetadata

CACHE_TTL_SECONDS = 20
_cache_until = 0.0
_cache_items: list[SkillMetadata] = []


def list_skills(*, query: str | None = None, refresh: bool = False) -> list[SkillMetadata]:
    global _cache_items, _cache_until
    now = time.time()
    if refresh or now >= _cache_until or query:
        if query:
            return discover_skills(query=query)
        _cache_items = discover_skills()
        _cache_until = now + CACHE_TTL_SECONDS
    return list(_cache_items)


def get_skill(*, skill_id: str | None = None, skill_name: str | None = None) -> SkillDocument | None:
    return read_skill_document(skill_id=skill_id, skill_name=skill_name)
