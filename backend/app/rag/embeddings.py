from __future__ import annotations

import hashlib
import math
from typing import Iterable

from app.ai.groq_client import groq_client


class EmbeddingService:
    def __init__(self, vector_size: int = 384) -> None:
        self.vector_size = vector_size

    def embed_text(self, text: str) -> list[float]:
        text = text.strip()
        if not text:
            return [0.0] * self.vector_size

        # Preferred: use Groq embedding model when available.
        vector = self._embed_with_groq(text)
        if vector is not None:
            return self._normalize(vector)

        # Fallback: deterministic hashed embedding for resilience.
        return self._hash_embed(text)

    def embed_texts(self, texts: Iterable[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]

    def _embed_with_groq(self, text: str) -> list[float] | None:
        if not groq_client.is_configured:
            return None

        client = getattr(groq_client, "_client", None)
        if client is None:
            return None

        try:
            response = client.embeddings.create(
                model="nomic-embed-text-v1.5",
                input=text,
            )
            return list(response.data[0].embedding)
        except Exception:
            return None

    def _hash_embed(self, text: str) -> list[float]:
        vector = [0.0] * self.vector_size
        tokens = [token.lower() for token in text.split()]

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.vector_size
            sign = -1.0 if digest[4] % 2 else 1.0
            vector[index] += sign

        return self._normalize(vector)

    def _normalize(self, vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(v * v for v in vector))
        if norm == 0:
            return vector
        return [v / norm for v in vector]


embedding_service = EmbeddingService()
