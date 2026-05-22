from __future__ import annotations

import argparse
from pathlib import Path

from app.rag.knowledge_service import knowledge_service


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest knowledge documents into in-memory RAG index")
    parser.add_argument("path", nargs="?", help="Path to PDF/TXT/Markdown file")
    parser.add_argument("--all", action="store_true", help="Ingest all docs from backend/knowledge_base recursively")
    args = parser.parse_args()

    if args.all:
        kb_dir = Path(__file__).resolve().parents[2] / "knowledge_base"
        docs = sorted([p for p in kb_dir.rglob("*") if p.is_file() and p.suffix.lower() in {".md", ".txt", ".markdown", ".pdf"}])
        for doc in docs:
            result = knowledge_service.ingest_document(str(doc))
            print(
                f"Ingested document_id={result.document_id} title={result.title} "
                f"chunks={result.chunk_count} source={result.source_path}"
            )
        return

    if not args.path:
        raise SystemExit("Provide a file path or use --all")

    result = knowledge_service.ingest_document(args.path)
    print(f"Ingested document_id={result.document_id} title={result.title} chunks={result.chunk_count} source={result.source_path}")


if __name__ == "__main__":
    main()
