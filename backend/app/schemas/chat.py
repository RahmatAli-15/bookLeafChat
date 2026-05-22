from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    email: EmailStr | None = None
    channel: str = "web-chat"


class ChatResponse(BaseModel):
    response: str
    confidence: float = Field(ge=0.0, le=1.0)
    escalated: bool
    escalation_reason: str | None = None
    intent: str
    latency_ms: int
    retrieval_source: str
    rag_status: str
    workflow_status: str
    escalation_severity: str
    identity_resolution: dict
    confidence_breakdown: dict
    confidence_weights: dict
    escalation_reasons: list[str] = []
    language_detected: str = "english"
    multilingual_detected: bool = False
    normalized_for_workflow: bool = False
    normalized_query: str | None = None
    created_at: datetime

    # Backward compatibility fields for existing frontend clients.
    reply: str
    final_confidence: float = Field(ge=0.0, le=100.0)
