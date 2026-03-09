from __future__ import annotations

import hashlib
import json
import logging
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable

logger = logging.getLogger(__name__)

SUPPORTED_CODE_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".md",
    ".css",
    ".html",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".ps1",
    ".cmd",
    ".sql",
}
IGNORED_DIR_NAMES = {
    ".git",
    ".next",
    "node_modules",
    ".venv",
    "__pycache__",
    "dist",
    "build",
    "output",
    "tmp",
}
DEFAULT_CHUNK_SIZE = 2200
DEFAULT_CHUNK_OVERLAP = 300
STOPWORDS_CODE = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "then",
    "true",
    "false",
    "null",
    "none",
    "void",
    "const",
    "let",
    "var",
    "def",
    "class",
    "return",
    "import",
}


def _normalize_whitespace(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def _read_text(path: Path) -> str:
    return _normalize_whitespace(path.read_text(encoding="utf-8", errors="ignore"))


def _split_chunks(text: str, *, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_CHUNK_OVERLAP) -> list[str]:
    if len(text) <= chunk_size:
        return [text] if text else []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks


class CodeKnowledgeIndex:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 30000")
        try:
            conn.execute("PRAGMA journal_mode = WAL")
        except sqlite3.OperationalError:
            pass
        try:
            yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                  project_id TEXT PRIMARY KEY,
                  name TEXT NOT NULL,
                  root_path TEXT NOT NULL,
                  aliases_json TEXT NOT NULL,
                  last_indexed_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS project_documents (
                  project_id TEXT NOT NULL,
                  source_path TEXT NOT NULL,
                  source_name TEXT NOT NULL,
                  source_type TEXT NOT NULL,
                  source_hash TEXT NOT NULL,
                  updated_at TEXT NOT NULL,
                  PRIMARY KEY (project_id, source_path)
                )
                """
            )
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS project_chunks USING fts5(
                  project_id UNINDEXED,
                  source_path UNINDEXED,
                  source_name UNINDEXED,
                  source_type UNINDEXED,
                  source_hash UNINDEXED,
                  chunk_index UNINDEXED,
                  content,
                  metadata
                )
                """
            )
            conn.commit()

    def _iter_supported_files(self, source: Path) -> Iterable[Path]:
        seen: set[str] = set()
        if not source.exists():
            return
        for path in source.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in SUPPORTED_CODE_EXTENSIONS:
                continue
            if any(part in IGNORED_DIR_NAMES for part in path.parts):
                continue
            resolved = str(path.resolve())
            if resolved in seen:
                continue
            seen.add(resolved)
            yield path

    def _remove_project_document(self, conn: sqlite3.Connection, project_id: str, source_path: str) -> None:
        conn.execute("DELETE FROM project_chunks WHERE project_id = ? AND source_path = ?", (project_id, source_path))
        conn.execute("DELETE FROM project_documents WHERE project_id = ? AND source_path = ?", (project_id, source_path))

    def register_project(
        self,
        project_id: str,
        *,
        name: str,
        root_path: str,
        aliases: Iterable[str] | None = None,
        last_indexed_at: str | None = None,
    ) -> None:
        aliases_json = json.dumps(list(aliases or []), ensure_ascii=False)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO projects (project_id, name, root_path, aliases_json, last_indexed_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                  name = excluded.name,
                  root_path = excluded.root_path,
                  aliases_json = excluded.aliases_json,
                  last_indexed_at = COALESCE(excluded.last_indexed_at, projects.last_indexed_at)
                """,
                (project_id, name, root_path, aliases_json, last_indexed_at),
            )
            conn.commit()

    def index_project(
        self,
        project_id: str,
        project_root: Path,
        *,
        project_name: str,
        aliases: Iterable[str] | None = None,
    ) -> dict[str, int]:
        files = list(self._iter_supported_files(project_root))
        indexed_docs = 0
        indexed_chunks = 0
        skipped_docs = 0
        failed_docs = 0

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO projects (project_id, name, root_path, aliases_json, last_indexed_at)
                VALUES (?, ?, ?, ?, NULL)
                ON CONFLICT(project_id) DO UPDATE SET
                  name = excluded.name,
                  root_path = excluded.root_path,
                  aliases_json = excluded.aliases_json
                """,
                (
                    project_id,
                    project_name or project_root.name,
                    str(project_root.resolve(strict=False)),
                    json.dumps(list(aliases or []), ensure_ascii=False),
                ),
            )
            for path in files:
                source_path = str(path.resolve())
                source_name = path.name
                source_type = path.suffix.lower().lstrip(".")
                try:
                    text = _read_text(path)
                    if not text:
                        skipped_docs += 1
                        continue
                    source_hash = _sha256_text(text)
                    existing = conn.execute(
                        "SELECT source_hash FROM project_documents WHERE project_id = ? AND source_path = ?",
                        (project_id, source_path),
                    ).fetchone()
                    if existing and existing["source_hash"] == source_hash:
                        skipped_docs += 1
                        continue

                    self._remove_project_document(conn, project_id, source_path)
                    chunks = _split_chunks(text)
                    if not chunks:
                        skipped_docs += 1
                        continue

                    for idx, chunk in enumerate(chunks):
                        metadata = {
                            "project_id": project_id,
                            "source_path": source_path,
                            "chunk_index": idx,
                        }
                        conn.execute(
                            """
                            INSERT INTO project_chunks (
                              project_id, source_path, source_name, source_type, source_hash, chunk_index, content, metadata
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                project_id,
                                source_path,
                                source_name,
                                source_type,
                                source_hash,
                                idx,
                                chunk,
                                json.dumps(metadata, ensure_ascii=False),
                            ),
                        )

                    conn.execute(
                        """
                        INSERT OR REPLACE INTO project_documents (
                          project_id, source_path, source_name, source_type, source_hash, updated_at
                        ) VALUES (?, ?, ?, ?, ?, datetime('now'))
                        """,
                        (project_id, source_path, source_name, source_type, source_hash),
                    )
                    indexed_docs += 1
                    indexed_chunks += len(chunks)
                except Exception as error:
                    failed_docs += 1
                    logger.warning("code_ingest_failed project=%s file=%s error=%s", project_id, source_path, error)

            conn.execute(
                "UPDATE projects SET last_indexed_at = datetime('now') WHERE project_id = ?",
                (project_id,),
            )
            conn.commit()

        return {
            "files_scanned": len(files),
            "documents_indexed": indexed_docs,
            "chunks_indexed": indexed_chunks,
            "documents_skipped": skipped_docs,
            "documents_failed": failed_docs,
        }

    def ingest_paths(self, sources: Iterable[Path]) -> dict[str, int]:
        total = {
            "files_scanned": 0,
            "documents_indexed": 0,
            "chunks_indexed": 0,
            "documents_skipped": 0,
            "documents_failed": 0,
        }
        for idx, source in enumerate(sources):
            root = source.resolve(strict=False)
            summary = self.index_project(
                f"legacy-{idx}-{root.name.casefold()}",
                root,
                project_name=root.name,
                aliases=[],
            )
            for key, value in summary.items():
                total[key] += value
        return total

    def _fetch_rows(self, query: str, *, limit: int, project_id: str | None) -> list[sqlite3.Row]:
        safe_query = re.sub(r"[^\w\s:\"*./-]+", " ", query).strip() or query
        tokens = [t.lower() for t in re.findall(r"[\w./-]+", safe_query, flags=re.UNICODE)]
        tokens = [t for t in tokens if len(t) >= 2 and t not in STOPWORDS_CODE]
        or_query = " OR ".join(tokens[:8]) if tokens else ""
        like_tokens = tokens[:6] if tokens else []

        with self._connect() as conn:
            params: list[object] = []
            base_filter = ""
            if project_id:
                base_filter = "AND project_id = ?"
                params.append(project_id)
            rows = conn.execute(
                f"""
                SELECT project_id, source_path, source_name, source_type, chunk_index, content, rank
                FROM (
                  SELECT project_id, source_path, source_name, source_type, chunk_index, content,
                         bm25(project_chunks) AS rank
                  FROM project_chunks
                  WHERE project_chunks MATCH ? {base_filter}
                  ORDER BY rank ASC
                  LIMIT ?
                )
                """,
                [safe_query, *params, limit],
            ).fetchall()
            if not rows and or_query:
                rows = conn.execute(
                    f"""
                    SELECT project_id, source_path, source_name, source_type, chunk_index, content, rank
                    FROM (
                      SELECT project_id, source_path, source_name, source_type, chunk_index, content,
                             bm25(project_chunks) AS rank
                      FROM project_chunks
                      WHERE project_chunks MATCH ? {base_filter}
                      ORDER BY rank ASC
                      LIMIT ?
                    )
                    """,
                    [or_query, *params, limit],
                ).fetchall()
            if not rows:
                like_filter = "project_id = ? AND " if project_id else ""
                rows = conn.execute(
                    f"""
                    SELECT project_id, source_path, source_name, source_type, chunk_index, content, 9999.0 AS rank
                    FROM project_chunks
                    WHERE {like_filter} content LIKE ?
                    LIMIT ?
                    """,
                    ([project_id] if project_id else []) + [f"%{query[:120]}%", limit],
                ).fetchall()
            if not rows and like_tokens:
                clauses = " AND ".join(["content LIKE ?"] * len(like_tokens))
                if project_id:
                    clauses = f"project_id = ? AND {clauses}"
                rows = conn.execute(
                    f"""
                    SELECT project_id, source_path, source_name, source_type, chunk_index, content, 9998.0 AS rank
                    FROM project_chunks
                    WHERE {clauses}
                    LIMIT ?
                    """,
                    ([project_id] if project_id else [])
                    + [f"%{token[:60]}%" for token in like_tokens]
                    + [limit],
                ).fetchall()
        return rows

    def search(self, query: str, *, limit: int = 5, project_id: str | None = None) -> list[dict[str, str | int | float]]:
        query = query.strip()
        if not query:
            return []
        rows = self._fetch_rows(query, limit=max(1, min(limit, 20)), project_id=project_id)

        project_names: dict[str, str] = {}
        if rows:
            with self._connect() as conn:
                for row in conn.execute("SELECT project_id, name FROM projects").fetchall():
                    project_names[str(row["project_id"])] = str(row["name"])

        results: list[dict[str, str | int | float]] = []
        for row in rows:
            snippet = str(row["content"]).strip()
            if len(snippet) > 700:
                snippet = f"{snippet[:700].rstrip()}..."
            resolved_project_id = str(row["project_id"])
            results.append(
                {
                    "project_id": resolved_project_id,
                    "project_name": project_names.get(resolved_project_id, resolved_project_id),
                    "source_path": str(row["source_path"]),
                    "source_name": str(row["source_name"]),
                    "source_type": str(row["source_type"]),
                    "chunk_index": int(row["chunk_index"]),
                    "content": snippet,
                    "score": float(row["rank"]),
                }
            )
        return results

    def list_projects(self) -> list[dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT project_id, name, root_path, aliases_json, last_indexed_at FROM projects ORDER BY name ASC"
            ).fetchall()
        return [
            {
                "project_id": str(row["project_id"]),
                "name": str(row["name"]),
                "root_path": str(row["root_path"]),
                "aliases_json": str(row["aliases_json"]),
                "last_indexed_at": str(row["last_indexed_at"] or ""),
            }
            for row in rows
        ]

    def stats(self, *, project_id: str | None = None) -> dict[str, int]:
        with self._connect() as conn:
            if project_id:
                docs = conn.execute(
                    "SELECT COUNT(*) FROM project_documents WHERE project_id = ?",
                    (project_id,),
                ).fetchone()[0]
                chunks = conn.execute(
                    "SELECT COUNT(*) FROM project_chunks WHERE project_id = ?",
                    (project_id,),
                ).fetchone()[0]
                projects = conn.execute(
                    "SELECT COUNT(*) FROM projects WHERE project_id = ?",
                    (project_id,),
                ).fetchone()[0]
            else:
                docs = conn.execute("SELECT COUNT(*) FROM project_documents").fetchone()[0]
                chunks = conn.execute("SELECT COUNT(*) FROM project_chunks").fetchone()[0]
                projects = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        return {"projects": int(projects), "documents": int(docs), "chunks": int(chunks)}
