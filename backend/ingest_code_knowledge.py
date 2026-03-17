from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from code_knowledge import CodeKnowledgeIndex


def _repo_root() -> Path:
    raw = os.getenv("CODE_REPO_ROOT", "").strip()
    if not raw:
        return Path(__file__).resolve().parent.parent
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path
    return path


def _db_path() -> Path:
    raw = os.getenv("CODE_KNOWLEDGE_DB_PATH", "data/code_knowledge.db").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path
    return path


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Indexa o codigo do projeto em SQLite FTS local.")
    parser.add_argument("paths", nargs="*", help="Pastas/arquivos adicionais para indexar")
    args = parser.parse_args()

    sources = [_repo_root()] + [Path(item) for item in args.paths]

    index = CodeKnowledgeIndex(_db_path())
    summary = index.ingest_paths(sources)
    stats = index.stats()

    print("Ingestao de codigo finalizada.")
    print(summary)
    print(stats)


if __name__ == "__main__":
    main()
