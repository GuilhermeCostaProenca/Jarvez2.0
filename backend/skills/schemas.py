from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass(slots=True)
class SkillMetadata:
    skill_id: str
    name: str
    description: str
    path: Path
    tags: list[str] = field(default_factory=list)
    source: str = "workspace"
    updated_at: str | None = None

    def to_payload(self) -> dict[str, object]:
        return {
            "id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "path": str(self.path),
            "tags": self.tags,
            "source": self.source,
            "updated_at": self.updated_at,
        }


@dataclass(slots=True)
class SkillDocument:
    metadata: SkillMetadata
    content: str
    excerpt: str

    def to_payload(self) -> dict[str, object]:
        return {
            "skill": self.metadata.to_payload(),
            "content": self.content,
            "excerpt": self.excerpt,
        }


def iso_updated_at(path: Path) -> str | None:
    try:
        stamp = datetime.fromtimestamp(path.stat().st_mtime)
    except OSError:
        return None
    return stamp.isoformat()
