from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.escalation import Escalation
from app.models.query_log import QueryLog
from app.utils.exceptions import DatabaseUnavailableError

router = APIRouter()


@router.get("/escalations")
def list_escalations(db: Session = Depends(get_db), limit: int = 30) -> dict:
    try:
        rows = (
            db.query(Escalation, QueryLog)
            .join(QueryLog, QueryLog.id == Escalation.query_id)
            .order_by(Escalation.created_at.desc())
            .limit(max(1, min(limit, 100)))
            .all()
        )
        items = []
        for esc, query in rows:
            meta = query.meta or {}
            items.append(
                {
                    "id": esc.id,
                    "query_id": esc.query_id,
                    "reason": esc.reason,
                    "status": esc.status,
                    "priority": esc.priority,
                    "assigned_to": esc.assigned_to,
                    "created_at": esc.created_at,
                    "customer_email": query.customer_email,
                    "intent": query.intent,
                    "message": query.message,
                    "confidence": round(float(meta.get("confidence", 0.0)) * 100, 2),
                    "escalation_severity": str(meta.get("escalation_severity") or "Escalated"),
                }
            )
        return {"items": items}
    except Exception as exc:
        raise DatabaseUnavailableError("Failed to fetch escalations") from exc
