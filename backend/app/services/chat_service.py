from __future__ import annotations

import time

from app.ai.groq_client import groq_client
from app.rag.knowledge_service import knowledge_service
from app.services.intent_classification_service import intent_classifier_service
from app.services.query_logging_service import log_query
from app.utils.exceptions import DatabaseUnavailableError


SYSTEM_PROMPT = (
    "You are BookLeaf AI support assistant. Provide helpful, concise, customer-friendly support replies."
)


def generate_support_reply(user_message: str) -> str:
    start = time.perf_counter()
    classification = intent_classifier_service.classify(user_message)

    if not groq_client.is_configured:
        reply = "Groq is not configured yet. Set GROQ_API_KEY in backend/.env to enable AI-generated responses."
    else:
        retrieval = knowledge_service.search(query=user_message, top_k=4, min_similarity=0.45)
        augmented_input = (
            f"{retrieval.context_text}\n\nUser question:\n{user_message}"
            if retrieval.has_context
            else user_message
        )
        reply = groq_client.chat(user_message=augmented_input, system_prompt=SYSTEM_PROMPT)

    elapsed_ms = int((time.perf_counter() - start) * 1000)

    try:
        log_query(
            message=user_message,
            intent=classification.intent.value,
            status="resolved",
            response_time_ms=elapsed_ms,
            metadata={"intent_confidence": classification.confidence},
        )
    except DatabaseUnavailableError:
        pass

    return reply
