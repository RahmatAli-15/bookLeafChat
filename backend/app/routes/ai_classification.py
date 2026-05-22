from __future__ import annotations

import logging

from fastapi import APIRouter

from app.ai.intent_classifier import ai_intent_classifier
from app.schemas.intent import IntentClassification, IntentClassificationRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ai/classify", response_model=IntentClassification)
def classify_intent(payload: IntentClassificationRequest) -> IntentClassification:
    logger.info("ai_classify_request", extra={"query_preview": payload.query[:120]})
    result = ai_intent_classifier.classify(payload.query)
    logger.info(
        "ai_classify_result",
        extra={
            "intent": result.intent.value,
            "confidence": result.confidence,
            "entity_count": len(result.entities),
        },
    )
    return result
