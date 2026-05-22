from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class IntentType(StrEnum):
    SMALLTALK = "SMALLTALK"
    CONVERSATIONAL_IDENTITY = "CONVERSATIONAL_IDENTITY"
    BOOK_STATUS = "BOOK_STATUS"
    ROYALTY = "ROYALTY"
    AUTHOR_COPY = "AUTHOR_COPY"
    ADDON_STATUS = "ADDON_STATUS"
    DASHBOARD_ACCESS = "DASHBOARD_ACCESS"
    GENERAL_POLICY = "GENERAL_POLICY"
    UNKNOWN = "UNKNOWN"


class IntentClassificationRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)


class IntentClassification(BaseModel):
    model_config = ConfigDict(extra="ignore")

    intent: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    entities: dict[str, Any] = Field(default_factory=dict)
    reasoning: str = ""

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, value: Any) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError):
            return 0.0

        if score > 1.0:
            score = score / 100.0
        if score < 0.0:
            return 0.0
        if score > 1.0:
            return 1.0
        return score
