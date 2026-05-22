from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ResolutionDecision(StrEnum):
    AUTO_RESOLVE = "AUTO_RESOLVE"
    MANUAL_VERIFICATION = "MANUAL_VERIFICATION"
    REJECT = "REJECT"


class IdentityResolveRequest(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    instagram: str | None = None
    whatsapp: str | None = None


class MatchedAuthor(BaseModel):
    id: str
    name: str
    email: str | None = None

class IdentityCandidate(BaseModel):
    id: str
    name: str
    confidence: float = Field(ge=0.0, le=1.0)


class IdentityResolveResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    author: MatchedAuthor | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    verification_required: bool
    reasons: list[str] = Field(default_factory=list)
    decision: ResolutionDecision
    fallback_reason: str | None = None
    candidate_count: int = 0
    linked_platforms: list[str] = Field(default_factory=list)
    matching_signals: list[str] = Field(default_factory=list)
    candidates: list[IdentityCandidate] = Field(default_factory=list)
