from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable

PROJECT_MARKERS = {
    ".git": "git",
    "package.json": "node",
    "pnpm-lock.yaml": "node",
    "package-lock.json": "node",
    "pyproject.toml": "python",
    "requirements.txt": "python",
    "Cargo.toml": "rust",
    "go.mod": "go",
}
DEFAULT_IGNORE_DIRS = {
    ".git",
    "node_modules",
    ".next",
    ".venv",
    "__pycache__",
    "dist",
    "build",
    "output",
    "tmp",
}


@dataclass(slots=True)
class ProjectRecord:
    project_id: str
    name: str
    aliases: list[str]
    root_path: str
    git_remote_url: str | None = None
    stack_tags: list[str] | None = None
    last_indexed_at: str | None = None
    last_scanned_at: str | None = None
    is_active: bool = True
    priority_score: int = 0
    notes: str | None = None

    def to_json(self) -> dict[str, object]:
        return asdict(self)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_token(value: str) -> str:
    lowered = value.casefold()
    canonicalized = (
        lowered.replace("jarvis", "jarvez")
        .replace("jarviz", "jarvez")
        .replace("jarves", "jarvez")
    )
    cleaned = re.sub(r"[^a-z0-9]+", " ", canonicalized)
    return re.sub(r"\s+", " ", cleaned).strip()


def _compact_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", _normalize_token(value))


def _catalog_path() -> Path:
    raw = os.getenv("PROJECT_CATALOG_PATH", "data/project_catalog.json").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _scan_roots() -> list[Path]:
    raw = os.getenv("PROJECT_SCAN_ROOTS", "").strip()
    if raw:
        roots = [Path(item.strip()).expanduser() for item in raw.split(";") if item.strip()]
    else:
        default_root = Path(__file__).resolve().parent.parent
        roots = [default_root.parent, default_root]

    resolved: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        candidate = root.resolve(strict=False)
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        resolved.append(candidate)
    return resolved


def _ignore_dir_names() -> set[str]:
    raw = os.getenv("PROJECT_SCAN_IGNORE_DIRS", "").strip()
    extra = {item.strip() for item in raw.split(";") if item.strip()}
    return DEFAULT_IGNORE_DIRS | extra


def _scan_max_depth() -> int:
    raw = os.getenv("PROJECT_SCAN_MAX_DEPTH", "3").strip()
    try:
        return max(1, min(8, int(raw)))
    except ValueError:
        return 3


def _detect_stack_tags(path: Path) -> list[str]:
    tags: set[str] = set()
    for marker, tag in PROJECT_MARKERS.items():
        if (path / marker).exists():
            tags.add(tag)
    return sorted(tags) or ["unknown"]


def _detect_git_remote(path: Path) -> str | None:
    config_path = path / ".git" / "config"
    if not config_path.exists():
        return None
    try:
        content = config_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    match = re.search(r'url\s*=\s*(.+)', content)
    return match.group(1).strip() if match else None


class ProjectCatalog:
    def __init__(self, path: Path | None = None):
        self.path = path or _catalog_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._records: dict[str, ProjectRecord] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._records = {}
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            self._records = {}
            return
        if not isinstance(payload, list):
            self._records = {}
            return
        records: dict[str, ProjectRecord] = {}
        for item in payload:
            if not isinstance(item, dict):
                continue
            project_id = str(item.get("project_id", "")).strip()
            name = str(item.get("name", "")).strip()
            root_path = str(item.get("root_path", "")).strip()
            if not project_id or not name or not root_path:
                continue
            records[project_id] = ProjectRecord(
                project_id=project_id,
                name=name,
                aliases=[str(alias).strip() for alias in item.get("aliases", []) if str(alias).strip()],
                root_path=root_path,
                git_remote_url=str(item.get("git_remote_url", "")).strip() or None,
                stack_tags=[str(tag).strip() for tag in item.get("stack_tags", []) if str(tag).strip()] or None,
                last_indexed_at=str(item.get("last_indexed_at", "")).strip() or None,
                last_scanned_at=str(item.get("last_scanned_at", "")).strip() or None,
                is_active=bool(item.get("is_active", True)),
                priority_score=int(item.get("priority_score", 0) or 0),
                notes=str(item.get("notes", "")).strip() or None,
            )
        self._records = records

    def save(self) -> None:
        payload = [record.to_json() for record in self.list_projects(include_inactive=True)]
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def list_projects(self, *, include_inactive: bool = False) -> list[ProjectRecord]:
        items = list(self._records.values())
        if not include_inactive:
            items = [item for item in items if item.is_active]
        return sorted(items, key=lambda item: (-item.priority_score, item.name.casefold()))

    def get_project(self, project_id: str) -> ProjectRecord | None:
        return self._records.get(project_id)

    def find_by_root(self, root_path: str) -> ProjectRecord | None:
        target = str(Path(root_path).resolve(strict=False))
        for record in self._records.values():
            if str(Path(record.root_path).resolve(strict=False)) == target:
                return record
        return None

    def create_or_update_project(
        self,
        *,
        root_path: Path,
        name: str | None = None,
        aliases: Iterable[str] | None = None,
        stack_tags: Iterable[str] | None = None,
        priority_score: int | None = None,
    ) -> ProjectRecord:
        resolved_root = root_path.resolve(strict=False)
        existing = self.find_by_root(str(resolved_root))
        if existing is None:
            existing = ProjectRecord(
                project_id=uuid.uuid4().hex,
                name=name or resolved_root.name,
                aliases=[],
                root_path=str(resolved_root),
                git_remote_url=_detect_git_remote(resolved_root),
                stack_tags=list(stack_tags or _detect_stack_tags(resolved_root)),
                last_scanned_at=_now_iso(),
                is_active=True,
                priority_score=priority_score or 0,
            )
            self._records[existing.project_id] = existing
        else:
            existing.name = name or existing.name
            existing.last_scanned_at = _now_iso()
            existing.git_remote_url = _detect_git_remote(resolved_root) or existing.git_remote_url
            existing.stack_tags = list(stack_tags or existing.stack_tags or _detect_stack_tags(resolved_root))
            if priority_score is not None:
                existing.priority_score = priority_score

        merged_aliases = {alias.strip() for alias in (existing.aliases or []) if alias.strip()}
        if aliases:
            merged_aliases.update(alias.strip() for alias in aliases if str(alias).strip())
        existing.aliases = sorted(merged_aliases)
        self.save()
        return existing

    def set_active(self, project_id: str, *, is_active: bool) -> ProjectRecord | None:
        record = self.get_project(project_id)
        if record is None:
            return None
        record.is_active = is_active
        self.save()
        return record

    def rename_project(self, project_id: str, name: str) -> ProjectRecord | None:
        record = self.get_project(project_id)
        if record is None:
            return None
        record.name = name.strip() or record.name
        self.save()
        return record

    def set_aliases(self, project_id: str, aliases: Iterable[str]) -> ProjectRecord | None:
        record = self.get_project(project_id)
        if record is None:
            return None
        record.aliases = sorted({str(alias).strip() for alias in aliases if str(alias).strip()})
        self.save()
        return record

    def set_priority(self, project_id: str, priority_score: int) -> ProjectRecord | None:
        record = self.get_project(project_id)
        if record is None:
            return None
        record.priority_score = int(priority_score)
        self.save()
        return record

    def remove_project(self, project_id: str) -> ProjectRecord | None:
        record = self._records.pop(project_id, None)
        if record is not None:
            self.save()
        return record

    def update_last_indexed(self, project_id: str, *, timestamp: str | None = None) -> ProjectRecord | None:
        record = self.get_project(project_id)
        if record is None:
            return None
        record.last_indexed_at = timestamp or _now_iso()
        self.save()
        return record

    def scan(self) -> list[ProjectRecord]:
        discovered: list[ProjectRecord] = []
        seen_roots: set[str] = set()
        ignore_names = _ignore_dir_names()
        max_depth = _scan_max_depth()

        def _scan_dir(path: Path, depth: int) -> None:
            if depth > max_depth or not path.exists() or not path.is_dir():
                return
            if path.name in ignore_names:
                return

            has_marker = any((path / marker).exists() for marker in PROJECT_MARKERS)
            if has_marker:
                record = self.create_or_update_project(root_path=path)
                root_key = str(Path(record.root_path).resolve(strict=False))
                if root_key not in seen_roots:
                    seen_roots.add(root_key)
                    discovered.append(record)
                return

            try:
                children = [child for child in path.iterdir() if child.is_dir()]
            except OSError:
                return

            for child in children:
                _scan_dir(child, depth + 1)

        for root in _scan_roots():
            _scan_dir(root, 0)

        self.save()
        return discovered

    def resolve(
        self,
        query: str,
        *,
        active_project_id: str | None = None,
        limit: int = 3,
    ) -> tuple[ProjectRecord | None, str, list[ProjectRecord]]:
        normalized_query = _normalize_token(query)
        projects = self.list_projects()
        if not projects:
            self.scan()
            projects = self.list_projects()
        if not projects:
            return None, "low", []

        if not normalized_query and active_project_id:
            active = self.get_project(active_project_id)
            if active and active.is_active:
                return active, "high", [active]

        scored: list[tuple[float, ProjectRecord]] = []
        for record in projects:
            score = float(record.priority_score)
            name_norm = _normalize_token(record.name)
            name_compact = _compact_token(record.name)
            alias_norms = [_normalize_token(alias) for alias in record.aliases]
            alias_compacts = [_compact_token(alias) for alias in record.aliases]
            query_compact = _compact_token(query)

            if normalized_query and normalized_query == name_norm:
                score += 140.0
            if normalized_query and normalized_query in alias_norms:
                score += 125.0
            if query_compact and query_compact == name_compact:
                score += 150.0
            if query_compact and query_compact in alias_compacts:
                score += 135.0
            if normalized_query and normalized_query and normalized_query in name_norm:
                score += 80.0
            if query_compact and query_compact and query_compact in name_compact:
                score += 90.0
            if normalized_query:
                for index, alias_norm in enumerate(alias_norms):
                    alias_compact = alias_compacts[index] if index < len(alias_compacts) else ""
                    if normalized_query and normalized_query in alias_norm:
                        score += 70.0
                    if query_compact and query_compact in alias_compact:
                        score += 75.0
                    score += SequenceMatcher(None, normalized_query, alias_norm).ratio() * 35.0
                    if query_compact and alias_compact:
                        score += SequenceMatcher(None, query_compact, alias_compact).ratio() * 45.0
                score += SequenceMatcher(None, normalized_query, name_norm).ratio() * 55.0
                if query_compact and name_compact:
                    score += SequenceMatcher(None, query_compact, name_compact).ratio() * 65.0
                for tag in record.stack_tags or []:
                    tag_norm = _normalize_token(tag)
                    if normalized_query == tag_norm:
                        score += 35.0
                    elif normalized_query and normalized_query in tag_norm:
                        score += 15.0

            if active_project_id and record.project_id == active_project_id:
                score += 10.0

            scored.append((score, record))

        scored.sort(key=lambda item: item[0], reverse=True)
        candidates = [record for _, record in scored[: max(1, limit)]]
        if not candidates:
            return None, "low", []

        top_score = scored[0][0]
        second_score = scored[1][0] if len(scored) > 1 else -999.0
        gap = top_score - second_score

        if top_score >= 120.0 or (top_score >= 90.0 and gap >= 25.0):
            return candidates[0], "high", candidates
        if top_score >= 55.0:
            return candidates[0], "medium", candidates
        return None, "low", candidates
