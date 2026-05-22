from __future__ import annotations

from app.schemas.identity import IdentityResolveRequest
from app.services.identity_unification_service import identity_unification_service


EXAMPLES = [
    IdentityResolveRequest(email="maya.richardson@bookleaf.ai"),
    IdentityResolveRequest(partial_name="anika sharm", instagram_handle="@anika.stories"),
    IdentityResolveRequest(phone="+1 604 555 0158", whatsapp_number="+1-604-555-0158"),
    IdentityResolveRequest(instagram_handle="@unknown_handle", partial_name="random person"),
]


if __name__ == "__main__":
    for example in EXAMPLES:
        result = identity_unification_service.resolve(example)
        print("input:", example.model_dump())
        print("decision:", result.decision.value)
        print("confidence:", result.confidence_score)
        print("reasons:", result.matching_reasons)
        print("breakdown:", [row.model_dump() for row in result.scoring_breakdown])
        print("profile:", result.matched_profile.model_dump() if result.matched_profile else None)
        print("fallback:", result.fallback_reason)
        print("---")
