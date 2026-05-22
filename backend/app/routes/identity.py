from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.query_log import QueryLog
from app.identity.resolver import identity_resolver
from app.schemas.identity import IdentityResolveRequest, IdentityResolveResponse

router = APIRouter()


@router.post("/identity/resolve", response_model=IdentityResolveResponse)
def resolve_identity(payload: IdentityResolveRequest, db: Session = Depends(get_db)) -> IdentityResolveResponse:
    return identity_resolver.resolve(db, payload)


@router.get("/identity/ambiguity-queue")
def ambiguity_queue(db: Session = Depends(get_db), limit: int = 30) -> dict:
    rows = (
        db.query(QueryLog)
        .order_by(QueryLog.created_at.desc())
        .limit(max(1, min(limit, 100)))
        .all()
    )
    items = []
    for row in rows:
        meta = row.meta or {}
        identity = meta.get("identity_resolution") or {}
        decision = str(identity.get("decision") or "")
        candidate_count = int(identity.get("candidate_count") or 0)
        if decision not in {"MANUAL_VERIFICATION", "REJECT"} and candidate_count <= 1:
            continue
        items.append(
            {
                "query_id": row.id,
                "created_at": row.created_at,
                "customer_email": row.customer_email,
                "review_status": "pending_review" if decision == "MANUAL_VERIFICATION" else "needs_manual_verification",
                "confidence": identity.get("confidence"),
                "candidate_count": candidate_count,
                "candidates": identity.get("candidates") or [],
                "reasons": identity.get("matching_signals") or identity.get("reasons") or [],
            }
        )
    return {"items": items}
