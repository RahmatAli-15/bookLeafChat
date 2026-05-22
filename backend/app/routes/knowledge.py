from __future__ import annotations

from fastapi import APIRouter

from app.rag.knowledge_service import knowledge_service
from app.schemas.knowledge import KnowledgeSearchRequest, KnowledgeSearchResponse

router = APIRouter()


@router.post("/knowledge/search", response_model=KnowledgeSearchResponse)
def search_knowledge(payload: KnowledgeSearchRequest) -> KnowledgeSearchResponse:
    return knowledge_service.search(
        query=payload.query,
        top_k=payload.top_k,
        min_similarity=payload.min_similarity,
    )
