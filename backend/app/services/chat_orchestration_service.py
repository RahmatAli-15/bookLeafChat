from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.ai.groq_client import groq_client
from app.rag.knowledge_service import knowledge_service
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.intent_classification_service import intent_classifier_service
from app.services.query_logging_service import log_query

logger = logging.getLogger(__name__)


class ChatOrchestrationService:
    """Extensible orchestration skeleton for future advanced workflows."""

    def handle_query(self, payload: ChatRequest) -> ChatResponse:
        started = datetime.now(timezone.utc)

        intent = intent_classifier_service.classify(payload.message)
        retrieval = knowledge_service.search(payload.message, top_k=3, min_similarity=0.45)

        if groq_client.is_configured:
            input_text = f"{retrieval.context_text}\n\nUser query: {payload.message}" if retrieval.has_context else payload.message
            reply = groq_client.chat(user_message=input_text, system_prompt="You are a helpful publishing support assistant.")
        else:
            reply = "AI provider is not configured. Your request is captured for manual support follow-up."

        final_confidence = round((intent.confidence * 100) * 0.7 + (retrieval.confidence * 100) * 0.3, 2)
        escalated = final_confidence < 80
        escalation_reason = "Confidence below threshold" if escalated else None

        try:
            log_query(
                message=payload.message,
                intent=intent.intent.value,
                status="escalated" if escalated else "resolved",
                metadata={
                    "intent_confidence": intent.confidence,
                    "rag_confidence": retrieval.confidence,
                    "rag_has_context": retrieval.has_context,
                },
            )
        except Exception:
            logger.warning("query_log_failed", exc_info=True)

        latency_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
        return ChatResponse(
            reply=reply,
            final_confidence=final_confidence,
            escalated=escalated,
            escalation_reason=escalation_reason,
            intent=intent.intent.value,
            latency_ms=latency_ms,
            observability={"orchestration": "v1", "rag_enabled": retrieval.has_context},
            created_at=datetime.now(timezone.utc),
        )


chat_orchestration_service = ChatOrchestrationService()
