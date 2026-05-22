from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.identity.matcher import exact_match, fuzzy_similarity
from app.identity.normalizer import normalize_email, normalize_handle, normalize_name, normalize_phone
from app.identity.scoring import SignalScore, weighted_confidence
from app.models.author import Author
from app.models.author_identity import AuthorIdentity
from app.schemas.identity import (
    IdentityCandidate,
    IdentityResolveRequest,
    IdentityResolveResponse,
    MatchedAuthor,
    ResolutionDecision,
)
from app.utils.exceptions import DatabaseUnavailableError

logger = logging.getLogger(__name__)


@dataclass
class CandidateResult:
    author: Author
    confidence: float
    reasons: list[str]


class IdentityResolver:
    def resolve(self, db: Session, payload: IdentityResolveRequest) -> IdentityResolveResponse:
        if not any([payload.name, payload.email, payload.phone, payload.instagram, payload.whatsapp]):
            return IdentityResolveResponse(
                confidence=0.0,
                verification_required=True,
                reasons=["No identity fields provided"],
                decision=ResolutionDecision.REJECT,
                fallback_reason="missing_identifiers",
                linked_platforms=[],
                matching_signals=[],
            )

        try:
            identity_rows = db.query(AuthorIdentity).all()
            authors = db.query(Author).all()
            authors_by_id = {a.id: a for a in authors}
        except SQLAlchemyError as exc:
            raise DatabaseUnavailableError("Failed to load identity records") from exc

        # Build rows from identity table + synthetic rows from authors as fallback.
        synthetic_rows: list[AuthorIdentity] = []
        for author in authors:
            synthetic_rows.append(
                AuthorIdentity(
                    id=f"synthetic-{author.id}",
                    author_id=author.id,
                    name_variant=author.full_name,
                    email=author.email,
                    phone=None,
                    instagram=None,
                    whatsapp=None,
                    verified=True,
                )
            )

        rows_to_score = [*identity_rows, *synthetic_rows]
        best_by_author: dict[str, CandidateResult] = {}

        for row in rows_to_score:
            author = authors_by_id.get(row.author_id)
            if not author:
                continue

            score = SignalScore()
            reasons: list[str] = []
            used: list[str] = []

            req_email = normalize_email(payload.email)
            row_email = normalize_email(row.email or author.email)
            if req_email:
                used.append("email")
                score.email = exact_match(req_email, row_email)
                if score.email == 1.0:
                    reasons.append("Email exact match")

            req_phone = normalize_phone(payload.phone)
            row_phone = normalize_phone(row.phone)
            if req_phone:
                used.append("phone")
                score.phone = exact_match(req_phone, row_phone)
                if score.phone == 1.0:
                    reasons.append("Phone exact match")

            req_whatsapp = normalize_phone(payload.whatsapp)
            row_whatsapp = normalize_phone(row.whatsapp)
            if req_whatsapp:
                used.append("whatsapp")
                score.whatsapp = exact_match(req_whatsapp, row_whatsapp)
                if score.whatsapp == 1.0:
                    reasons.append("WhatsApp exact match")

            req_name = normalize_name(payload.name)
            row_name = normalize_name(row.name_variant or author.full_name)
            if req_name:
                used.append("name")
                score.name = fuzzy_similarity(req_name, row_name)
                if score.name >= 0.85:
                    reasons.append("High fuzzy name similarity")

            req_instagram = normalize_handle(payload.instagram)
            row_instagram = normalize_handle(row.instagram)
            if req_instagram:
                used.append("instagram")
                score.instagram = max(exact_match(req_instagram, row_instagram), fuzzy_similarity(req_instagram, row_instagram))
                if exact_match(req_instagram, row_instagram) == 1.0:
                    reasons.append("Instagram exact match")
                elif score.instagram >= 0.85:
                    reasons.append("Instagram handle high similarity")

            confidence = weighted_confidence(score, used)
            if confidence > 0:
                candidate = CandidateResult(author=author, confidence=confidence, reasons=reasons or ["Weak identity signal match"])
                existing = best_by_author.get(author.id)
                if existing is None or candidate.confidence > existing.confidence:
                    best_by_author[author.id] = candidate

        candidates = list(best_by_author.values())

        if not candidates:
            return IdentityResolveResponse(
                confidence=0.0,
                verification_required=True,
                reasons=["No matching identity candidates"],
                decision=ResolutionDecision.REJECT,
                fallback_reason="low_confidence",
                candidate_count=0,
                linked_platforms=[],
                matching_signals=[],
            )

        candidates.sort(key=lambda c: c.confidence, reverse=True)
        best = candidates[0]
        top_count = len([c for c in candidates if c.confidence >= 0.70])

        logger.info(
            "identity_resolution",
            extra={
                "best_author_id": best.author.id,
                "confidence": round(best.confidence, 4),
                "candidate_count": len(candidates),
                "top_candidate_count": top_count,
            },
        )

        top_candidates = [
            IdentityCandidate(id=c.author.id, name=c.author.full_name, confidence=round(c.confidence, 3))
            for c in candidates[:4]
        ]

        def platforms_for(author_id: str) -> list[str]:
            rows = [r for r in identity_rows if r.author_id == author_id]
            flags = {
                "Email": any(normalize_email(r.email) for r in rows),
                "WhatsApp": any(normalize_phone(r.whatsapp) for r in rows),
                "Instagram": any(normalize_handle(r.instagram) for r in rows),
                "Dashboard Profile": any(normalize_name(r.name_variant) for r in rows),
            }
            return [k for k, v in flags.items() if v]

        if top_count > 1:
            return IdentityResolveResponse(
                author=MatchedAuthor(id=best.author.id, name=best.author.full_name, email=best.author.email),
                confidence=round(best.confidence, 3),
                verification_required=True,
                reasons=best.reasons + ["Multiple plausible matches"],
                decision=ResolutionDecision.MANUAL_VERIFICATION,
                fallback_reason="multiple_matches",
                candidate_count=len(candidates),
                linked_platforms=platforms_for(best.author.id),
                matching_signals=best.reasons,
                candidates=top_candidates,
            )

        if best.confidence >= 0.90:
            decision = ResolutionDecision.AUTO_RESOLVE
            verification_required = False
        elif best.confidence >= 0.70:
            decision = ResolutionDecision.MANUAL_VERIFICATION
            verification_required = True
        else:
            decision = ResolutionDecision.REJECT
            verification_required = True

        author_payload = None if decision == ResolutionDecision.REJECT else MatchedAuthor(
            id=best.author.id,
            name=best.author.full_name,
            email=best.author.email,
        )

        return IdentityResolveResponse(
            author=author_payload,
            confidence=round(best.confidence, 3),
            verification_required=verification_required,
            reasons=best.reasons,
            decision=decision,
            fallback_reason="low_confidence" if decision == ResolutionDecision.REJECT else None,
            candidate_count=len(candidates),
            linked_platforms=platforms_for(best.author.id),
            matching_signals=best.reasons,
            candidates=top_candidates,
        )


identity_resolver = IdentityResolver()
