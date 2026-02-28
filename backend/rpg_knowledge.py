from __future__ import annotations

import hashlib
import json
import logging
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown"}
DEFAULT_CHUNK_SIZE = 1600
DEFAULT_CHUNK_OVERLAP = 250
STOPWORDS_PT = {
    "a",
    "o",
    "as",
    "os",
    "de",
    "da",
    "do",
    "das",
    "dos",
    "e",
    "ou",
    "um",
    "uma",
    "que",
    "qual",
    "quais",
    "como",
    "sobre",
    "no",
    "na",
    "nos",
    "nas",
    "para",
    "por",
    "com",
}


@dataclass(slots=True)
class ChunkRecord:
    source_path: str
    source_name: str
    source_type: str
    source_hash: str
    chunk_index: int
    content: str
    metadata_json: str


def _normalize_whitespace(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def _extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    pages: list[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if text:
            pages.append(text)
    return _normalize_whitespace("\n\n".join(pages))


def _extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf_text(path)
    if suffix in {".txt", ".md", ".markdown"}:
        return _normalize_whitespace(path.read_text(encoding="utf-8", errors="ignore"))
    return ""


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


class RPGKnowledgeIndex:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 30000")
        try:
            conn.execute("PRAGMA journal_mode = WAL")
        except sqlite3.OperationalError:
            # Another process may already hold a lock; keep working with current mode.
            pass
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                  source_path TEXT PRIMARY KEY,
                  source_name TEXT NOT NULL,
                  source_type TEXT NOT NULL,
                  source_hash TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(
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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS notes (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  world TEXT NOT NULL,
                  content TEXT NOT NULL,
                  created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def _remove_document_chunks(self, conn: sqlite3.Connection, source_path: str) -> None:
        conn.execute("DELETE FROM chunks WHERE source_path = ?", (source_path,))
        conn.execute("DELETE FROM documents WHERE source_path = ?", (source_path,))

    def _iter_supported_files(self, sources: Iterable[Path]) -> Iterable[Path]:
        seen: set[str] = set()
        for source in sources:
            if not source.exists():
                continue
            if source.is_file():
                if source.suffix.lower() in SUPPORTED_EXTENSIONS:
                    resolved = str(source.resolve())
                    if resolved not in seen:
                        seen.add(resolved)
                        yield source
                continue
            for path in source.rglob("*"):
                if not path.is_file():
                    continue
                if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                    continue
                resolved = str(path.resolve())
                if resolved in seen:
                    continue
                seen.add(resolved)
                yield path

    def ingest_paths(self, sources: Iterable[Path]) -> dict[str, int]:
        files = list(self._iter_supported_files(sources))
        indexed_docs = 0
        indexed_chunks = 0
        skipped_docs = 0
        failed_docs = 0

        with self._connect() as conn:
            for path in files:
                source_path = str(path.resolve())
                source_name = path.name
                source_type = path.suffix.lower().lstrip(".")
                try:
                    text = _extract_text(path)
                    if not text:
                        skipped_docs += 1
                        continue
                    source_hash = _sha256_text(text)
                    existing = conn.execute(
                        "SELECT source_hash FROM documents WHERE source_path = ?",
                        (source_path,),
                    ).fetchone()
                    if existing and existing["source_hash"] == source_hash:
                        skipped_docs += 1
                        continue

                    self._remove_document_chunks(conn, source_path)
                    chunks = _split_chunks(text)
                    if not chunks:
                        skipped_docs += 1
                        continue
                    for idx, chunk in enumerate(chunks):
                        metadata = {"source_path": source_path, "chunk_index": idx}
                        conn.execute(
                            """
                            INSERT INTO chunks (
                              source_path, source_name, source_type, source_hash, chunk_index, content, metadata
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
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
                        INSERT OR REPLACE INTO documents (
                          source_path, source_name, source_type, source_hash, updated_at
                        ) VALUES (?, ?, ?, ?, datetime('now'))
                        """,
                        (source_path, source_name, source_type, source_hash),
                    )
                    indexed_docs += 1
                    indexed_chunks += len(chunks)
                except Exception as error:
                    failed_docs += 1
                    logger.warning("rpg_ingest_failed file=%s error=%s", source_path, error)
            conn.commit()

        return {
            "files_scanned": len(files),
            "documents_indexed": indexed_docs,
            "chunks_indexed": indexed_chunks,
            "documents_skipped": skipped_docs,
            "documents_failed": failed_docs,
        }

    def search(self, query: str, *, limit: int = 5) -> list[dict[str, str | int | float]]:
        query = query.strip()
        if not query:
            return []
        safe_query = re.sub(r"[^\w\s:\"*]+", " ", query).strip()
        if not safe_query:
            safe_query = query
        limit = max(1, min(limit, 20))

        tokens = [t.lower() for t in re.findall(r"\w+", safe_query, flags=re.UNICODE)]
        tokens = [t for t in tokens if len(t) >= 3 and t not in STOPWORDS_PT]
        or_query = " OR ".join(tokens[:8]) if tokens else ""
        like_tokens = tokens[:6] if tokens else []

        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT source_path, source_name, source_type, chunk_index, content, rank
                FROM (
                  SELECT source_path, source_name, source_type, chunk_index, content,
                         bm25(chunks) AS rank
                  FROM chunks
                  WHERE chunks MATCH ?
                  ORDER BY rank ASC
                  LIMIT ?
                )
                """,
                (safe_query, limit),
            ).fetchall()
            if not rows and or_query:
                rows = conn.execute(
                    """
                    SELECT source_path, source_name, source_type, chunk_index, content, rank
                    FROM (
                      SELECT source_path, source_name, source_type, chunk_index, content,
                             bm25(chunks) AS rank
                      FROM chunks
                      WHERE chunks MATCH ?
                      ORDER BY rank ASC
                      LIMIT ?
                    )
                    """,
                    (or_query, limit),
                ).fetchall()
            if not rows:
                like_query = f"%{query[:120]}%"
                rows = conn.execute(
                    """
                    SELECT source_path, source_name, source_type, chunk_index, content, 9999.0 AS rank
                    FROM chunks
                    WHERE content LIKE ?
                    LIMIT ?
                    """,
                    (like_query, limit),
                ).fetchall()
            if not rows and like_tokens:
                clauses = " OR ".join(["content LIKE ?"] * len(like_tokens))
                params = [f"%{token[:80]}%" for token in like_tokens]
                params.append(limit)
                rows = conn.execute(
                    f"""
                    SELECT source_path, source_name, source_type, chunk_index, content, 9999.0 AS rank
                    FROM chunks
                    WHERE {clauses}
                    LIMIT ?
                    """,
                    tuple(params),
                ).fetchall()

        return [
            {
                "source_path": str(row["source_path"]),
                "source_name": str(row["source_name"]),
                "source_type": str(row["source_type"]),
                "chunk_index": int(row["chunk_index"]),
                "content": str(row["content"]),
                "score": float(row["rank"]),
            }
            for row in rows
        ]

    def stats(self) -> dict[str, int]:
        with self._connect() as conn:
            docs = conn.execute("SELECT COUNT(*) AS c FROM documents").fetchone()
            chunks = conn.execute("SELECT COUNT(*) AS c FROM chunks").fetchone()
            notes = conn.execute("SELECT COUNT(*) AS c FROM notes").fetchone()
        return {
            "documents": int(docs["c"]) if docs else 0,
            "chunks": int(chunks["c"]) if chunks else 0,
            "notes": int(notes["c"]) if notes else 0,
        }

    def save_note(self, *, title: str, content: str, world: str, notes_dir: Path) -> dict[str, str]:
        clean_title = title.strip() or "nota_rpg"
        clean_world = world.strip() or "geral"
        clean_content = content.strip()
        if not clean_content:
            raise ValueError("content vazio")

        notes_dir.mkdir(parents=True, exist_ok=True)
        safe_world = re.sub(r"[^\w\-]+", "_", clean_world, flags=re.UNICODE).strip("_") or "geral"
        safe_title = re.sub(r"[^\w\-]+", "_", clean_title, flags=re.UNICODE).strip("_") or "nota"
        file_path = notes_dir / safe_world / f"{safe_title}.md"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(f"# {clean_title}\n\n{clean_content}\n", encoding="utf-8")

        with self._connect() as conn:
            conn.execute(
                "INSERT INTO notes (title, world, content, created_at) VALUES (?, ?, ?, datetime('now'))",
                (clean_title, clean_world, clean_content),
            )
            conn.commit()

        return {"file_path": str(file_path.resolve()), "title": clean_title, "world": clean_world}
