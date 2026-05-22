from __future__ import annotations

from app.ai.intent_classifier import ai_intent_classifier
from app.schemas.intent import IntentClassification


class IntentClassifierService:
    def classify(self, message: str) -> IntentClassification:
        return ai_intent_classifier.classify(message)


intent_classifier_service = IntentClassifierService()
