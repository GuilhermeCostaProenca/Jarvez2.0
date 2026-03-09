from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from rpg_knowledge import RPGKnowledgeIndex


def _env_sources() -> list[Path]:
    raw = os.getenv("RPG_SOURCE_PATHS", "").strip()
    if not raw:
        return []
    return [Path(item.strip()) for item in raw.split(";") if item.strip()]


def _db_path() -> Path:
    raw = os.getenv("RPG_KNOWLEDGE_DB_PATH", "data/rpg_knowledge.db").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path
    return path


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Indexa PDFs/textos de RPG em SQLite FTS local.")
    parser.add_argument("paths", nargs="*", help="Pastas/arquivos adicionais para indexar")
    args = parser.parse_args()

    sources = _env_sources() + [Path(p) for p in args.paths]
    if not sources:
        raise SystemExit("Nenhuma fonte informada. Defina RPG_SOURCE_PATHS no .env ou passe caminhos no comando.")

    index = RPGKnowledgeIndex(_db_path())
    summary = index.ingest_paths(sources)
    stats = index.stats()

    print("Ingestao RPG finalizada.")
    print(summary)
    print(stats)


if __name__ == "__main__":
    main()
