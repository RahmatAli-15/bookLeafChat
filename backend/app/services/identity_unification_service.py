from __future__ import annotations

from app.schemas.identity import IdentityResolveRequest, IdentityResolveResponse, ResolutionDecision


class IdentityUnificationService:
    """SQLAlchemy-era placeholder identity resolver; extensible for future channel graph matching."""

    def resolve(self, payload: IdentityResolveRequest) -> IdentityResolveResponse:
        has_signal = any(
            [
                payload.email,
                payload.phone,
                payload.partial_name,
                payload.instagram_handle,
                payload.whatsapp_number,
            ]
        )

        if not has_signal:
            return IdentityResolveResponse(
                matched_profile=None,
                confidence_score=0.0,
                decision=ResolutionDecision.REJECT,
                matching_reasons=["No identity signals provided"],
                scoring_breakdown=[],
                fallback_reason="insufficient_identity_signals",
                platform_extensions={"next": ["identity graph", "cross-channel embeddings"]},
            )

        return IdentityResolveResponse(
            matched_profile=None,
            confidence_score=65.0,
            decision=ResolutionDecision.REJECT,
            matching_reasons=["Identity engine is running in safe fallback mode"],
            scoring_breakdown=[],
            fallback_reason="identity_resolution_not_configured",
            platform_extensions={"next": ["postgres identity tables", "fuzzy matcher", "embedding ranker"]},
        )


identity_unification_service = IdentityUnificationService()
