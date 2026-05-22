from __future__ import annotations

import logging
from dataclasses import dataclass

from pydantic import ValidationError

from app.ai.groq_client import groq_client
from app.ai.prompts import build_intent_system_prompt, build_intent_user_prompt
from app.ai.query_normalizer import query_normalizer
from app.schemas.intent import IntentClassification, IntentType

logger = logging.getLogger(__name__)


@dataclass
class IntentClassifierConfig:
    model_name: str = "llama-3.3-70b-versatile"
    max_retries: int = 2
    timeout_seconds: float = 15.0
    fallback_confidence: float = 0.15


class AIIntentClassifier:
    def __init__(self, config: IntentClassifierConfig | None = None) -> None:
        self.config = config or IntentClassifierConfig()

    def classify(self, query: str) -> IntentClassification:
        text = query.strip()
        if not text:
            return self._fallback("empty_query", "No input query provided")
        if self._is_conversational_identity_query(text):
            return IntentClassification(
                intent=IntentType.CONVERSATIONAL_IDENTITY,
                confidence=0.98,
                entities={"conversation_type": "identity_context"},
                reasoning="Conversational identity query detected",
            )
        if query_normalizer.is_smalltalk(text.lower().strip()):
            return IntentClassification(
                intent=IntentType.SMALLTALK,
                confidence=0.98,
                entities={"conversation_type": "smalltalk"},
                reasoning="Short conversational phrase detected",
            )

        if not groq_client.is_configured:
            return self._fallback("groq_not_configured", "AI provider not configured")

        try:
            payload = groq_client.chat_json(
                user_message=build_intent_user_prompt(text),
                system_prompt=build_intent_system_prompt(),
                max_retries=self.config.max_retries,
                timeout_seconds=self.config.timeout_seconds,
                temperature=0.0,
            )
            result = IntentClassification.model_validate(payload)
            result = self._normalize(result)
            return result
        except TimeoutError:
            logger.warning("intent_classification_timeout", extra={"query": text[:120]})
            return self._fallback("timeout", "AI request timed out")
        except ValidationError:
            logger.warning("intent_classification_malformed_response", extra={"query": text[:120]}, exc_info=True)
            return self._fallback("malformed_response", "AI returned malformed JSON schema")
        except ValueError:
            logger.warning("intent_classification_malformed_response", extra={"query": text[:120]}, exc_info=True)
            return self._fallback("malformed_response", "AI returned malformed JSON content")
        except Exception as exc:
            logger.warning("intent_classification_failed", extra={"query": text[:120]}, exc_info=True)
            return self._fallback("api_failure", f"AI classification failed: {type(exc).__name__}")

    def _normalize(self, result: IntentClassification) -> IntentClassification:
        # Guard unknown or malformed intent-like values by forcing UNKNOWN safely.
        if result.intent not in set(IntentType):
            return self._fallback("unknown_intent", "Model returned unsupported intent")

        confidence = max(0.0, min(1.0, result.confidence))
        if result.intent == IntentType.UNKNOWN:
            confidence = min(confidence, 0.4)

        return IntentClassification(
            intent=result.intent,
            confidence=round(confidence, 3),
            entities=result.entities,
            reasoning=result.reasoning,
        )

    def _fallback(self, reason: str, reasoning: str) -> IntentClassification:
        return IntentClassification(
            intent=IntentType.UNKNOWN,
            confidence=self.config.fallback_confidence,
            entities={"fallback_reason": reason},
            reasoning=reasoning,
        )

    def _is_conversational_identity_query(self, text: str) -> bool:
        lowered = text.lower().strip()
        patterns = (
            "who am i",
            "what is my name",
            "what's my name",
            "which account am i using",
            "which account is active",
            "am i logged in",
            "am i login",
            "main kaun hu",
            "mera naam kya hai",
            "kaunsa account",
            "my account name",
        )
        return any(p in lowered for p in patterns)


ai_intent_classifier = AIIntentClassifier()
