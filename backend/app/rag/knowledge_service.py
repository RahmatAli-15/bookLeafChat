from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from collections import OrderedDict
from typing import Any

from app.rag.chunker import text_chunker
from app.rag.embeddings import embedding_service
from app.rag.document_loader import document_loader
from app.schemas.knowledge import IngestedDocument, KnowledgeChunk, KnowledgeSearchResponse


class KnowledgeService:
    def __init__(self) -> None:
        self._index: list[dict[str, Any]] = []
        self._loaded = False
        self._route_cache: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._route_cache_limit = 300

    SUPPORT_SHORTCUTS = {
        "dashboard_help": ("dashboard", "login", "portal", "password", "otp", "access"),
        "royalties": ("royalty", "payment", "payout", "statement", "earning"),
        "payments_refunds": ("refund", "package", "billing", "invoice", "charge"),
    }

    def reset_index(self) -> None:
        self._index = []
        self._loaded = False

    def _kb_dir(self) -> Path:
        return Path(__file__).resolve().parents[2] / "knowledge_base"

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return

        kb_dir = self._kb_dir()
        if not kb_dir.exists():
            self._loaded = True
            return

        docs = sorted([p for p in kb_dir.rglob("*") if p.is_file() and p.suffix.lower() in {".md", ".txt", ".markdown", ".pdf"}])

        for doc in docs:
            title, text = document_loader.load_text(str(doc))
            chunks = text_chunker.chunk(text)
            for idx, chunk in enumerate(chunks):
                self._index.append(
                    {
                        "chunk_id": f"{doc.stem}-{idx}",
                        "document_id": doc.stem,
                        "title": title,
                        "source_path": str(doc),
                        "content": chunk,
                        "metadata": {
                            "doc": doc.name,
                            "chunk_index": idx,
                            "category": str(doc.parent.relative_to(kb_dir)) if doc.parent != kb_dir else "root",
                        },
                        "embedding": embedding_service.embed_text(chunk),
                    }
                )

        self._loaded = True

    def ingest_document(self, path: str) -> IngestedDocument:
        file_path = Path(path)
        title, text = document_loader.load_text(str(file_path))
        chunks = text_chunker.chunk(text)

        # Replace chunks for same document if already present.
        self._index = [row for row in self._index if Path(row["source_path"]) != file_path]
        for idx, chunk in enumerate(chunks):
            self._index.append(
                {
                    "chunk_id": f"{file_path.stem}-{idx}",
                    "document_id": file_path.stem,
                    "title": title,
                    "source_path": str(file_path),
                    "content": chunk,
                    "metadata": {"doc": file_path.name, "chunk_index": idx},
                    "embedding": embedding_service.embed_text(chunk),
                }
            )

        self._loaded = True
        return IngestedDocument(
            document_id=file_path.stem,
            title=title,
            source_path=str(file_path),
            chunk_count=len(chunks),
            ingested_at=datetime.now(timezone.utc),
        )

    def _similarity(self, a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        return max(0.0, min(1.0, sum(x * y for x, y in zip(a, b))))

    def normalize_support_query(self, query: str) -> str:
        text = query.strip().lower()
        replacements = {
            "dashboard not working": "dashboard access help",
            "portal issue": "dashboard access help",
            "cannot login": "dashboard access help",
            "can't login": "dashboard access help",
            "forgot password": "dashboard access help",
            "forgot my password": "dashboard access help",
        }
        for raw, normalized in replacements.items():
            if raw in text:
                return normalized
        return text

    def _route_support_query(self, query: str) -> dict[str, Any]:
        key = query.strip().lower()
        if key in self._route_cache:
            self._route_cache.move_to_end(key)
            return self._route_cache[key]

        normalized = self.normalize_support_query(key)
        shortcut = None
        for name, markers in self.SUPPORT_SHORTCUTS.items():
            if any(marker in normalized for marker in markers):
                shortcut = name
                break

        routed = {"normalized_query": normalized, "shortcut": shortcut}
        self._route_cache[key] = routed
        if len(self._route_cache) > self._route_cache_limit:
            self._route_cache.popitem(last=False)
        return routed

    def search_support(self, query: str, top_k: int = 4) -> KnowledgeSearchResponse:
        route = self._route_support_query(query)
        normalized_query = route["normalized_query"]
        shortcut = route["shortcut"]

        min_similarity = 0.30  # lower threshold for support/help phrasing
        return self.search(
            normalized_query,
            top_k=top_k,
            min_similarity=min_similarity,
            route_shortcut=shortcut,
        )

    def search(self, query: str, top_k: int, min_similarity: float, route_shortcut: str | None = None) -> KnowledgeSearchResponse:
        self._ensure_loaded()

        if not self._index:
            return KnowledgeSearchResponse(
                query=query,
                confidence=0.05,
                has_context=False,
                fallback_reason="knowledge_base_empty",
                context_text="Knowledge base is not populated.",
                results=[],
            )

        q_emb = embedding_service.embed_text(query)
        candidates = self._index
        if route_shortcut:
            candidates = [
                row
                for row in self._index
                if route_shortcut in (row.get("document_id", "") + " " + row.get("title", "") + " " + str((row.get("metadata") or {}).get("category", ""))).lower()
            ] or self._index

        scored = []
        for row in candidates:
            sim = self._similarity(q_emb, row["embedding"])
            if sim >= min_similarity:
                scored.append((sim, row))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:top_k]

        if not top:
            return KnowledgeSearchResponse(
                query=query,
                confidence=0.1,
                has_context=False,
                fallback_reason="no_relevant_context",
                context_text="No relevant knowledge base context found.",
                results=[],
            )

        results: list[KnowledgeChunk] = []
        for sim, row in top:
            results.append(
                KnowledgeChunk(
                    chunk_id=row["chunk_id"],
                    document_id=row["document_id"],
                    title=row["title"],
                    content=row["content"],
                    source_path=row["source_path"],
                    metadata=row["metadata"],
                    similarity=round(sim, 4),
                )
            )

        avg = sum([r.similarity or 0.0 for r in results]) / len(results)
        peak = max([r.similarity or 0.0 for r in results])
        confidence = round(min(0.99, (0.65 * avg) + (0.35 * peak)), 3)
        context_text = "\n\n".join([f"[{i+1}] {r.title}: {r.content}" for i, r in enumerate(results)])

        return KnowledgeSearchResponse(
            query=query,
            confidence=confidence,
            has_context=True,
            context_text=context_text,
            results=results,
        )


knowledge_service = KnowledgeService()
