from __future__ import annotations

import os
import re
from pathlib import Path

from .schemas import SkillDocument, SkillMetadata, iso_updated_at

SKILL_FILE = "SKILL.md"
FRONTMATTER_BOUNDARY = "---"
DEFAULT_EXCERPT_CHARS = 2200


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _candidate_skill_roots() -> list[Path]:
    roots: list[Path] = []

    env_roots = str(os.getenv("JARVEZ_SKILLS_DIRS", "")).strip()
    if env_roots:
        for raw in env_roots.split(os.pathsep):
            item = raw.strip()
            if item:
                roots.append(Path(item).expanduser().resolve(strict=False))

    repo_root = _workspace_root()
    roots.append((repo_root / "skills").resolve(strict=False))
    roots.append((repo_root / ".codex" / "skills").resolve(strict=False))
    return roots


def _parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    if not content.startswith(FRONTMATTER_BOUNDARY):
        return {}, content

    parts = content.split(FRONTMATTER_BOUNDARY, 2)
    if len(parts) < 3:
        return {}, content

    frontmatter_block = parts[1]
    body = parts[2].lstrip("\r\n")

    result: dict[str, str] = {}
    for line in frontmatter_block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        cleaned_key = key.strip().lower()
        cleaned_value = value.strip().strip('"').strip("'")
        if cleaned_key:
            result[cleaned_key] = cleaned_value
    return result, body


def _derive_skill_id(path: Path, root: Path) -> str:
    rel = path.relative_to(root)
    parent = str(rel.parent).replace("\\", "/").strip("/")
    if parent:
        return parent
    return path.stem


def _extract_tags(frontmatter: dict[str, str], body: str) -> list[str]:
    tags: list[str] = []
    raw_tags = frontmatter.get("tags", "")
    if raw_tags:
        for item in re.split(r"[,;|]", raw_tags):
            normalized = item.strip().lower()
            if normalized and normalized not in tags:
                tags.append(normalized)
    body_hint = body.lower()
    for hint in ("figma", "openai", "linear", "playwright", "notion"):
        if hint in body_hint and hint not in tags:
            tags.append(hint)
    return tags


def discover_skills(query: str | None = None) -> list[SkillMetadata]:
    normalized_query = (query or "").strip().lower()
    items: list[SkillMetadata] = []

    for root in _candidate_skill_roots():
        if not root.exists() or not root.is_dir():
            continue
        for skill_file in root.rglob(SKILL_FILE):
            try:
                content = skill_file.read_text(encoding="utf-8")
            except OSError:
                continue
            frontmatter, body = _parse_frontmatter(content)
            skill_id = _derive_skill_id(skill_file, root)
            name = (
                frontmatter.get("name")
                or frontmatter.get("title")
                or skill_file.parent.name
                or skill_id
            ).strip()
            first_line = body.splitlines()[0].strip() if body.splitlines() else ""
            description = frontmatter.get("description") or frontmatter.get("summary") or first_line or "Skill sem descricao."
            tags = _extract_tags(frontmatter, body)
            skill = SkillMetadata(
                skill_id=skill_id,
                name=name,
                description=description or "Skill sem descricao.",
                path=skill_file.resolve(strict=False),
                tags=tags,
                source="workspace" if ".codex" not in str(root).lower() else "codex",
                updated_at=iso_updated_at(skill_file),
            )

            if normalized_query:
                haystack = " ".join([skill.skill_id, skill.name, skill.description, " ".join(skill.tags)]).lower()
                if normalized_query not in haystack:
                    continue
            items.append(skill)

    items.sort(key=lambda item: item.name.lower())
    return items


def read_skill_document(*, skill_id: str | None = None, skill_name: str | None = None) -> SkillDocument | None:
    normalized_id = (skill_id or "").strip().lower()
    normalized_name = (skill_name or "").strip().lower()
    if not normalized_id and not normalized_name:
        return None

    for skill in discover_skills():
        if normalized_id and skill.skill_id.lower() != normalized_id:
            continue
        if normalized_name and skill.name.strip().lower() != normalized_name:
            continue
        try:
            content = skill.path.read_text(encoding="utf-8")
        except OSError:
            return None
        _, body = _parse_frontmatter(content)
        excerpt = body[:DEFAULT_EXCERPT_CHARS].strip()
        return SkillDocument(metadata=skill, content=content, excerpt=excerpt)

    if normalized_name:
        # fallback by fuzzy contains for UX
        for skill in discover_skills():
            if normalized_name in skill.name.strip().lower():
                try:
                    content = skill.path.read_text(encoding="utf-8")
                except OSError:
                    return None
                _, body = _parse_frontmatter(content)
                excerpt = body[:DEFAULT_EXCERPT_CHARS].strip()
                return SkillDocument(metadata=skill, content=content, excerpt=excerpt)

    return None
