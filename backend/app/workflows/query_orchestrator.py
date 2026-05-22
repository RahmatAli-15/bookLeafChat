from __future__ import annotations

import logging
from collections import OrderedDict
from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.ai.groq_client import groq_client
from app.ai.intent_classifier import ai_intent_classifier
from app.ai.prompts import build_response_system_prompt, build_response_user_prompt
from app.ai.query_normalizer import query_normalizer
from app.models.add_on_service import AddOnService
from app.models.author import Author
from app.models.book import Book
from app.models.escalation import Escalation
from app.identity.resolver import identity_resolver
from app.rag.knowledge_service import knowledge_service
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.identity import IdentityResolveRequest
from app.schemas.intent import IntentType
from app.schemas.knowledge import KnowledgeSearchResponse
from app.services.query_log_service import log_query
from app.utils.exceptions import DatabaseUnavailableError

logger = logging.getLogger(__name__)


class QueryOrchestrator:
    OPERATIONAL_INTENTS = {
        IntentType.BOOK_STATUS,
        IntentType.ROYALTY,
        IntentType.AUTHOR_COPY,
        IntentType.ADDON_STATUS,
    }
    POLICY_INTENTS = {IntentType.GENERAL_POLICY, IntentType.DASHBOARD_ACCESS}
    INTENT_CACHE_LIMIT = 200

    def __init__(self) -> None:
        self._intent_cache: OrderedDict[str, tuple[IntentType, float, dict, str]] = OrderedDict()

    def process(self, db: Session, payload: ChatRequest) -> ChatResponse:
        start = datetime.now(timezone.utc)
        normalized = query_normalizer.normalize(payload.query)
        normalized_query = normalized.normalized_query

        if normalized.smalltalk_detected:
            return self._smalltalk_response(payload, normalized, start)

        intent_payload = self._classify_with_cache(normalized_query)
        intent = intent_payload["intent"]
        intent_confidence = intent_payload["confidence"]

        if intent == IntentType.CONVERSATIONAL_IDENTITY:
            return self._conversational_identity_response(payload, normalized, start)

        identity_resolution = identity_resolver.resolve(
            db,
            IdentityResolveRequest(
                email=payload.email,
                name=(payload.email.split("@")[0].replace(".", " ").title() if payload.email else None),
            ),
        )
        author_candidates, author_confidence = self._resolve_author_candidates(db, identity_resolution.author.id if identity_resolution.author else None)
        author_confidence = max(author_confidence, float(identity_resolution.confidence))
        selected_author = author_candidates[0] if len(author_candidates) == 1 else None

        structured_data, db_retrieval_confidence = self._route_and_fetch_data(db, intent, selected_author)

        rag_required = self._should_use_rag(intent, normalized_query)
        if rag_required:
            retrieval = knowledge_service.search_support(normalized_query, top_k=4)
            rag_status = "Knowledge Base Matched" if retrieval.has_context else "No Relevant Guidance Found"
            retrieval_source = "PostgreSQL + Knowledge Base" if retrieval.has_context else "Knowledge Base"
        else:
            retrieval = self._empty_retrieval(normalized_query, fallback_reason="rag_not_required")
            rag_status = "Not Required"
            retrieval_source = "PostgreSQL"

        confidence_weights, threshold = self._resolve_weights_and_threshold(intent)
        final_confidence, confidence_breakdown = self._calculate_confidence(
            intent=intent,
            intent_confidence=float(intent_confidence),
            retrieval_confidence=float(retrieval.confidence),
            db_retrieval_confidence=db_retrieval_confidence,
            identity_confidence=author_confidence,
            weights=confidence_weights,
        )

        escalation_reasons = self._prioritize_escalation_reasons(
            self._evaluate_escalation(
                final_confidence=final_confidence,
                intent=intent,
                author_candidates=author_candidates,
                threshold=threshold,
                db_retrieval_confidence=db_retrieval_confidence,
                identity_confidence=author_confidence,
                retrieval_has_context=retrieval.has_context,
                retrieval_confidence=float(retrieval.confidence),
                has_author=selected_author is not None,
            )
        )

        escalation_severity, workflow_status = self._resolve_escalation_state(final_confidence)
        escalated = escalation_severity == "Escalated"
        escalation_reason = "; ".join(escalation_reasons) if escalation_reasons else None
        escalation_explanation = self._humanize_escalation_reasons(escalation_reasons, escalation_severity=escalation_severity)

        response_text = self._generate_response(
            query=normalized_query,
            intent=intent,
            data=structured_data,
            rag_context=retrieval.context_text,
            rag_available=retrieval.has_context and rag_required,
            final_confidence=final_confidence,
            escalated=escalated,
            escalation_explanation=escalation_explanation,
            identity_confidence=author_confidence,
            db_retrieval_confidence=db_retrieval_confidence,
        )

        latency_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)

        query_log = self._log_query(
            db=db,
            payload=payload,
            intent=intent.value,
            response_text=response_text,
            confidence=final_confidence,
            escalated=escalated,
            escalation_reason=escalation_reason,
            escalation_explanation=escalation_explanation,
            latency_ms=latency_ms,
            author=selected_author,
            structured_data=structured_data,
            retrieval=retrieval,
            retrieval_source=retrieval_source,
            rag_status=rag_status,
            workflow_status=workflow_status,
            escalation_severity=escalation_severity,
            identity_resolution=identity_resolution.model_dump(),
            confidence_breakdown=confidence_breakdown,
            confidence_weights=confidence_weights,
            escalation_reasons=escalation_reasons,
            query_normalization={
                "language_detected": normalized.language_detected,
                "multilingual_detected": normalized.multilingual_detected,
                "normalized_for_workflow": normalized.normalized_for_workflow,
                "normalized_query": normalized_query,
                "matched_shortcuts": normalized.matched_shortcuts,
            },
        )

        if escalated and query_log is not None:
            self._create_escalation(db, query_log.id, escalation_reason)

        logger.info(
            "orchestrator_complete",
            extra={
                "intent": intent.value,
                "confidence": final_confidence,
                "escalated": escalated,
                "latency_ms": latency_ms,
                "retrieval_source": retrieval_source,
                "rag_status": rag_status,
                "escalation_reasons": escalation_reasons,
                "escalation_severity": escalation_severity,
                "identity_resolution": identity_resolution.model_dump(),
                "confidence_breakdown": confidence_breakdown,
                "query_normalization": {
                    "language_detected": normalized.language_detected,
                    "multilingual_detected": normalized.multilingual_detected,
                    "normalized_for_workflow": normalized.normalized_for_workflow,
                    "normalized_query": normalized_query,
                    "matched_shortcuts": normalized.matched_shortcuts,
                },
            },
        )

        return ChatResponse(
            response=response_text,
            confidence=round(final_confidence, 3),
            escalated=escalated,
            escalation_reason=escalation_explanation,
            intent=intent.value,
            latency_ms=latency_ms,
            retrieval_source=retrieval_source,
            rag_status=rag_status,
            workflow_status=workflow_status,
            escalation_severity=escalation_severity,
            identity_resolution=identity_resolution.model_dump(),
            confidence_breakdown=confidence_breakdown,
            confidence_weights=confidence_weights,
            escalation_reasons=escalation_reasons,
            language_detected=normalized.language_detected,
            multilingual_detected=normalized.multilingual_detected,
            normalized_for_workflow=normalized.normalized_for_workflow,
            normalized_query=normalized_query if normalized.normalized_for_workflow else None,
            created_at=datetime.now(timezone.utc),
            reply=response_text,
            final_confidence=round(final_confidence * 100, 2),
        )

    def _classify_with_cache(self, query: str) -> dict:
        key = query.strip().lower()
        if key in self._intent_cache:
            intent, confidence, entities, reasoning = self._intent_cache[key]
            self._intent_cache.move_to_end(key)
            return {"intent": intent, "confidence": confidence, "entities": entities, "reasoning": reasoning}

        result = ai_intent_classifier.classify(query)
        self._intent_cache[key] = (result.intent, float(result.confidence), result.entities, result.reasoning)
        if len(self._intent_cache) > self.INTENT_CACHE_LIMIT:
            self._intent_cache.popitem(last=False)
        return {"intent": result.intent, "confidence": float(result.confidence), "entities": result.entities, "reasoning": result.reasoning}

    def _smalltalk_response(self, payload: ChatRequest, normalized, start: datetime) -> ChatResponse:
        latency_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
        response_text = self._smalltalk_reply(normalized.original_query)
        return ChatResponse(
            response=response_text,
            confidence=0.98,
            escalated=False,
            escalation_reason=None,
            intent=IntentType.SMALLTALK.value,
            latency_ms=latency_ms,
            retrieval_source="None",
            rag_status="Not Required",
            workflow_status="conversational_response",
            escalation_severity="Conversational Response",
            identity_resolution={
                "author": None,
                "confidence": 1.0,
                "verification_required": False,
                "reasons": ["Conversational query does not require identity resolution"],
                "matching_signals": [],
                "linked_platforms": [],
            },
            confidence_breakdown={
                "intent_type": IntentType.SMALLTALK.value,
                "signals": {"intent": 0.98, "identity": 1.0, "db_retrieval": 1.0, "rag": 1.0},
                "weights": {"intent": 1.0, "identity": 0.0, "db_retrieval": 0.0, "rag": 0.0},
                "contributions": {"intent": 0.98, "identity": 0.0, "db_retrieval": 0.0, "rag": 0.0},
                "weighted_score": 0.98,
            },
            confidence_weights={"intent": 1.0, "identity": 0.0, "db_retrieval": 0.0, "rag": 0.0},
            escalation_reasons=[],
            language_detected=normalized.language_detected,
            multilingual_detected=normalized.multilingual_detected,
            normalized_for_workflow=normalized.normalized_for_workflow,
            normalized_query=normalized.normalized_query if normalized.normalized_for_workflow else None,
            created_at=datetime.now(timezone.utc),
            reply=response_text,
            final_confidence=98.0,
        )

    def _conversational_identity_response(self, payload: ChatRequest, normalized, start: datetime) -> ChatResponse:
        latency_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
        session_name = self._session_display_name(payload.email)
        response_text = (
            f"You are currently identified as {session_name} in this support session."
            if session_name
            else "You are connected to this support session, but I do not have a verified account name yet."
        )
        return ChatResponse(
            response=response_text,
            confidence=0.97,
            escalated=False,
            escalation_reason=None,
            intent=IntentType.CONVERSATIONAL_IDENTITY.value,
            latency_ms=latency_ms,
            retrieval_source="Session Context",
            rag_status="Not Required",
            workflow_status="session_identity_response",
            escalation_severity="Session Identity Response",
            identity_resolution={
                "author": {"id": None, "name": session_name} if session_name else None,
                "confidence": 1.0 if session_name else 0.7,
                "verification_required": False,
                "reasons": ["Session context used for conversational identity query"],
                "matching_signals": ["active_session_email" if payload.email else "session_context_only"],
                "linked_platforms": [payload.channel] if payload.channel else [],
            },
            confidence_breakdown={
                "intent_type": IntentType.CONVERSATIONAL_IDENTITY.value,
                "signals": {"intent": 0.97, "identity": 1.0 if session_name else 0.7, "db_retrieval": 1.0, "rag": 1.0},
                "weights": {"intent": 0.6, "identity": 0.4, "db_retrieval": 0.0, "rag": 0.0},
                "contributions": {"intent": 0.582, "identity": 0.4 if session_name else 0.28, "db_retrieval": 0.0, "rag": 0.0},
                "weighted_score": 0.982 if session_name else 0.862,
            },
            confidence_weights={"intent": 0.6, "identity": 0.4, "db_retrieval": 0.0, "rag": 0.0},
            escalation_reasons=[],
            language_detected=normalized.language_detected,
            multilingual_detected=normalized.multilingual_detected,
            normalized_for_workflow=normalized.normalized_for_workflow,
            normalized_query=normalized.normalized_query if normalized.normalized_for_workflow else None,
            created_at=datetime.now(timezone.utc),
            reply=response_text,
            final_confidence=97.0 if session_name else 86.2,
        )

    def _smalltalk_reply(self, original_query: str) -> str:
        lowered = (original_query or "").strip().lower()
        if any(token in lowered for token in ("thanks", "thank you", "thx")):
            return "You are welcome. I am here whenever you need help with publishing, royalties, dashboard access, or book status updates."
        if any(token in lowered for token in ("aur btao", "aur batao", "acha", "ok", "okay", "hmm", "hmmm")):
            return "I am here to help. You can ask me about royalty updates, book live status, author copy tracking, dashboard access, or add-on services."
        return "Hello. I am here to help with publishing, royalties, dashboard access, and book status updates."

    def _session_display_name(self, email: str | None) -> str | None:
        if not email:
            return None
        local = email.split("@")[0].strip()
        if not local:
            return None
        tokens = [t for t in local.replace("_", ".").split(".") if t]
        if not tokens:
            return None
        return " ".join(token.capitalize() for token in tokens)

    def _should_use_rag(self, intent: IntentType, query: str) -> bool:
        if intent in self.OPERATIONAL_INTENTS:
            return False
        if intent in self.POLICY_INTENTS:
            return True
        lowered = query.lower()
        help_markers = ("help", "policy", "faq", "how do i", "what is", "support process")
        return any(marker in lowered for marker in help_markers)

    def _empty_retrieval(self, query: str, fallback_reason: str) -> KnowledgeSearchResponse:
        return KnowledgeSearchResponse(
            query=query,
            confidence=0.0,
            has_context=False,
            fallback_reason=fallback_reason,
            context_text="",
            results=[],
        )

    def _resolve_author_candidates(self, db: Session, author_id: str | None) -> tuple[list[Author], float]:
        try:
            if author_id:
                exact = db.query(Author).filter(Author.id == author_id).all()
                return exact, 1.0 if len(exact) == 1 else (0.5 if len(exact) > 1 else 0.2)
            return [], 0.3
        except SQLAlchemyError as exc:
            raise DatabaseUnavailableError("Failed to resolve author profile") from exc

    def _route_and_fetch_data(self, db: Session, intent: IntentType, author: Author | None) -> tuple[dict, float]:
        if author is None:
            return {"author": None, "books": [], "addons": [], "intent_payload": {}}, 0.35

        try:
            books = db.query(Book).filter(Book.author_id == author.id).all()
            addons = db.query(AddOnService).join(Book, AddOnService.book_id == Book.id).filter(Book.author_id == author.id).all()
        except SQLAlchemyError as exc:
            raise DatabaseUnavailableError("Failed to fetch structured data") from exc

        payload = self._intent_payload(intent, books, addons)
        completeness = self._data_completeness(intent, books, addons)
        return {"author": author, "books": books, "addons": addons, "intent_payload": payload}, completeness

    def _intent_payload(self, intent: IntentType, books: list[Book], addons: list[AddOnService]) -> dict:
        if intent == IntentType.BOOK_STATUS:
            return {"books": [{"title": b.title, "status": b.status, "live_date": b.publication_date.isoformat() if isinstance(b.publication_date, date) else None} for b in books]}
        if intent == IntentType.ROYALTY:
            return {"royalties": [{"title": b.title, "royalty_status": b.royalty_status} for b in books]}
        if intent == IntentType.AUTHOR_COPY:
            return {"author_copy": [{"title": b.title, "status": "dispatch_within_5_to_10_business_days"} for b in books]}
        if intent == IntentType.ADDON_STATUS:
            return {"add_ons": [{"service_name": a.service_name, "status": a.status} for a in addons]}
        if intent == IntentType.DASHBOARD_ACCESS:
            return {"dashboard_help": ["password_reset", "check_email", "activation_delay"]}
        if intent == IntentType.GENERAL_POLICY:
            return {"policy_context": "use_knowledge_base"}
        return {}

    def _data_completeness(self, intent: IntentType, books: list[Book], addons: list[AddOnService]) -> float:
        if intent == IntentType.BOOK_STATUS:
            return 1.0 if any(b.publication_date for b in books) else 0.5
        if intent == IntentType.ROYALTY:
            return 1.0 if any(b.royalty_status for b in books) else 0.5
        if intent == IntentType.AUTHOR_COPY:
            return 0.9 if books else 0.4
        if intent == IntentType.ADDON_STATUS:
            return 1.0 if addons else 0.4
        if intent in {IntentType.DASHBOARD_ACCESS, IntentType.GENERAL_POLICY}:
            return 0.9
        return 0.3

    def _resolve_weights_and_threshold(self, intent: IntentType) -> tuple[dict[str, float], float]:
        if intent in self.OPERATIONAL_INTENTS:
            return ({"identity": 0.40, "db_retrieval": 0.35, "intent": 0.15, "rag": 0.10}, 0.78)
        if intent in self.POLICY_INTENTS:
            return ({"rag": 0.50, "intent": 0.30, "identity": 0.20, "db_retrieval": 0.0}, 0.75)
        return ({"identity": 0.30, "db_retrieval": 0.25, "intent": 0.25, "rag": 0.20}, 0.76)

    def _calculate_confidence(
        self,
        *,
        intent: IntentType,
        intent_confidence: float,
        retrieval_confidence: float,
        db_retrieval_confidence: float,
        identity_confidence: float,
        weights: dict[str, float],
    ) -> tuple[float, dict]:
        signals = {
            "identity": max(0.0, min(1.0, identity_confidence)),
            "db_retrieval": max(0.0, min(1.0, db_retrieval_confidence)),
            "intent": max(0.0, min(1.0, intent_confidence)),
            "rag": max(0.0, min(1.0, retrieval_confidence)),
        }
        contributions = {name: round(signals[name] * weight, 4) for name, weight in weights.items()}
        final = max(0.0, min(1.0, sum(contributions.values())))
        return final, {"intent_type": intent.value, "signals": signals, "weights": weights, "contributions": contributions, "weighted_score": round(final, 4)}

    def _evaluate_escalation(
        self,
        *,
        final_confidence: float,
        intent: IntentType,
        author_candidates: list[Author],
        threshold: float,
        db_retrieval_confidence: float,
        identity_confidence: float,
        retrieval_has_context: bool,
        retrieval_confidence: float,
        has_author: bool,
    ) -> list[str]:
        reasons: list[str] = []
        if len(author_candidates) > 1:
            reasons.append("multiple_author_matches")
        if identity_confidence < 0.55 or not has_author:
            reasons.append("low_identity_confidence")
        if intent in self.OPERATIONAL_INTENTS and db_retrieval_confidence < 0.60:
            reasons.append("missing_db_retrieval")
        if intent in self.POLICY_INTENTS and (not retrieval_has_context or retrieval_confidence < 0.50):
            reasons.append("no_reliable_kb_retrieval")
        if final_confidence < threshold:
            reasons.append("final_score_below_threshold")

        if intent in self.OPERATIONAL_INTENTS:
            strong_db_backed = identity_confidence >= 0.90 and db_retrieval_confidence >= 0.85 and final_confidence >= 0.70
            if strong_db_backed and "multiple_author_matches" not in reasons:
                reasons = [r for r in reasons if r != "final_score_below_threshold"]
        return reasons

    def _prioritize_escalation_reasons(self, reasons: list[str]) -> list[str]:
        priority = {
            "multiple_author_matches": 1,
            "low_identity_confidence": 2,
            "missing_db_retrieval": 3,
            "no_reliable_kb_retrieval": 4,
            "final_score_below_threshold": 5,
        }
        return sorted(list(dict.fromkeys(reasons)), key=lambda r: priority.get(r, 99))

    def _resolve_escalation_state(self, final_confidence: float) -> tuple[str, str]:
        if final_confidence >= 0.85:
            return ("Auto Resolved", "resolved")
        if final_confidence >= 0.65:
            return ("Support Review Recommended", "support_review_recommended")
        return ("Escalated", "escalated")

    def _humanize_escalation_reasons(self, reasons: list[str], *, escalation_severity: str) -> str | None:
        if escalation_severity == "Auto Resolved":
            return "This request was resolved automatically with high confidence."
        if not reasons:
            if escalation_severity == "Support Review Recommended":
                return "Support review is recommended to confirm this response."
            return "This request requires specialist assistance."

        mapping = {
            "final_score_below_threshold": "the request needs specialist review before automation can safely complete it",
            "multiple_author_matches": "multiple author profiles matched your request",
            "missing_db_retrieval": "required publishing records were not available",
            "no_reliable_kb_retrieval": "policy guidance could not be confirmed automatically",
            "low_identity_confidence": "we could not confidently verify your author profile",
        }
        readable = [mapping.get(reason, reason.replace("_", " ")) for reason in reasons]
        prefix = "Support review is recommended because" if escalation_severity == "Support Review Recommended" else "Your request has been escalated because"
        return f"{prefix} {', '.join(readable)}."

    def _generate_response(
        self,
        *,
        query: str,
        intent: IntentType,
        data: dict,
        rag_context: str,
        rag_available: bool,
        final_confidence: float,
        escalated: bool,
        escalation_explanation: str | None,
        identity_confidence: float,
        db_retrieval_confidence: float,
    ) -> str:
        author = data.get("author")
        structured_context = data.get("intent_payload", {})

        use_llm = groq_client.is_configured and not (
            intent in self.OPERATIONAL_INTENTS and identity_confidence >= 0.85 and db_retrieval_confidence >= 0.85
        )

        if not use_llm:
            return self._template_response(
                intent=intent,
                structured_context=structured_context,
                rag_context=rag_context,
                rag_available=rag_available,
                escalated=escalated,
                escalation_explanation=escalation_explanation,
                confidence=final_confidence,
                author_name=author.full_name if author else None,
            )

        prompt = build_response_user_prompt(
            query=query,
            intent=intent,
            author_name=author.full_name if author else "Unknown",
            structured_context=structured_context,
            rag_context=rag_context,
            rag_available=rag_available,
            workflow_summary={"escalated": escalated, "confidence": round(final_confidence, 3)},
        )
        try:
            text = groq_client.chat(user_message=prompt, system_prompt=build_response_system_prompt()).strip()
            return text if text else self._template_response(
                intent=intent,
                structured_context=structured_context,
                rag_context=rag_context,
                rag_available=rag_available,
                escalated=escalated,
                escalation_explanation=escalation_explanation,
                confidence=final_confidence,
                author_name=author.full_name if author else None,
            )
        except Exception:
            logger.warning("groq_response_generation_failed", exc_info=True)
            return self._template_response(
                intent=intent,
                structured_context=structured_context,
                rag_context=rag_context,
                rag_available=rag_available,
                escalated=escalated,
                escalation_explanation=escalation_explanation,
                confidence=final_confidence,
                author_name=author.full_name if author else None,
            )

    def _template_response(
        self,
        *,
        intent: IntentType,
        structured_context: dict,
        rag_context: str,
        rag_available: bool,
        escalated: bool,
        escalation_explanation: str | None,
        confidence: float,
        author_name: str | None,
    ) -> str:
        greeting = f"Hi {author_name}," if author_name else "Hello,"

        if intent == IntentType.BOOK_STATUS and structured_context.get("books"):
            book = structured_context["books"][0]
            return f"{greeting} your book '{book['title']}' is currently '{book['status']}' and its live date is {book.get('live_date')}."
        if intent == IntentType.ROYALTY and structured_context.get("royalties"):
            row = structured_context["royalties"][0]
            return f"{greeting} your royalty status for '{row['title']}' is '{row['royalty_status']}'."
        if intent == IntentType.AUTHOR_COPY:
            return f"{greeting} author copies are typically dispatched within 5 to 10 business days after the book goes live."
        if intent == IntentType.ADDON_STATUS and structured_context.get("add_ons"):
            row = structured_context["add_ons"][0]
            return f"{greeting} your add-on service '{row['service_name']}' is currently '{row['status']}'."
        if intent == IntentType.DASHBOARD_ACCESS:
            return f"{greeting} I understand this is frustrating. Please reset your password, verify your registered email, and allow up to 15 minutes after activation."
        if intent == IntentType.GENERAL_POLICY and rag_available and rag_context:
            return f"{greeting} based on policy guidance: {rag_context.splitlines()[0]}"

        if escalated:
            return f"{greeting} {escalation_explanation or 'Your request has been escalated to a specialist for manual review.'}"
        if confidence < 0.5:
            return f"{greeting} I can share a preliminary update now, and a specialist can review this further if needed."
        return f"{greeting} I have shared the most accurate support update available at this stage."

    def _log_query(
        self,
        *,
        db: Session,
        payload: ChatRequest,
        intent: str,
        response_text: str,
        confidence: float,
        escalated: bool,
        escalation_reason: str | None,
        escalation_explanation: str | None,
        latency_ms: int,
        author: Author | None,
        structured_data: dict,
        retrieval,
        retrieval_source: str,
        rag_status: str,
        workflow_status: str,
        escalation_severity: str,
        identity_resolution: dict,
        confidence_breakdown: dict,
        confidence_weights: dict,
        escalation_reasons: list[str],
        query_normalization: dict,
    ):
        try:
            return log_query(
                db,
                {
                    "author_id": author.id if author else None,
                    "channel": payload.channel,
                    "customer_email": str(payload.email) if payload.email else None,
                    "message": payload.query,
                    "intent": intent,
                    "status": workflow_status,
                    "response_time_ms": latency_ms,
                    "metadata": {
                        "response": response_text,
                        "confidence": confidence,
                        "escalated": escalated,
                        "escalation_reason": escalation_reason,
                        "escalation_explanation": escalation_explanation,
                        "escalation_reasons": escalation_reasons,
                        "escalation_severity": escalation_severity,
                        "latency_ms": latency_ms,
                        "retrieval_source": retrieval_source,
                        "rag_status": rag_status,
                        "workflow_status": workflow_status,
                        "confidence_weights": confidence_weights,
                        "confidence_breakdown": confidence_breakdown,
                        "query_normalization": query_normalization,
                        "identity_resolution": identity_resolution,
                        "retrieved_chunks": [{"chunk_id": c.chunk_id, "title": c.title, "similarity": c.similarity} for c in retrieval.results],
                        "retrieval_confidence": retrieval.confidence,
                        "data_summary": {
                            "book_count": len(structured_data.get("books", [])),
                            "addon_count": len(structured_data.get("addons", [])),
                        },
                    },
                },
            )
        except Exception as exc:
            logger.warning("query_log_persist_failed", exc_info=True)
            raise DatabaseUnavailableError("Failed to persist query log") from exc

    def _create_escalation(self, db: Session, query_id: str, reason: str | None) -> None:
        try:
            record = Escalation(
                id=str(uuid4()),
                query_id=query_id,
                escalation_level=1,
                reason=reason or "unspecified",
                assigned_to="support.ops@bookleaf.ai",
                priority="medium",
                status="open",
            )
            db.add(record)
            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            logger.warning("escalation_persist_failed", exc_info=True)
            raise DatabaseUnavailableError("Failed to persist escalation record") from exc


query_orchestrator = QueryOrchestrator()
