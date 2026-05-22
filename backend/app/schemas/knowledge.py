from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeChunk(BaseModel):
    model_config = ConfigDict(extra="ignore")

    chunk_id: str
    document_id: str
    title: str
    content: str
    source_path: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    similarity: float | None = None


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)
    min_similarity: float = Field(default=0.45, ge=0.0, le=1.0)


class KnowledgeSearchResponse(BaseModel):
    query: str
    confidence: float
    has_context: bool
    fallback_reason: str | None = None
    context_text: str
    results: list[KnowledgeChunk]


class IngestedDocument(BaseModel):
    document_id: str
    title: str
    source_path: str
    chunk_count: int
    ingested_at: datetime
