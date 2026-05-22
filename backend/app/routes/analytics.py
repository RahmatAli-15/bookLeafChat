from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.escalation import Escalation
from app.models.query_log import QueryLog
from app.utils.exceptions import DatabaseUnavailableError

router = APIRouter()


@router.get("/analytics/overview")
def analytics_overview(db: Session = Depends(get_db)) -> dict:
    try:
        total_queries = db.query(func.count(QueryLog.id)).scalar() or 0
        escalations = db.query(func.count(Escalation.id)).filter(Escalation.status != "resolved").scalar() or 0
        unresolved_cases = db.query(func.count(QueryLog.id)).filter(QueryLog.status != "resolved").scalar() or 0

        avg_conf = db.query(func.avg(QueryLog.meta["confidence"].as_float())).scalar()
        avg_confidence = float(avg_conf) if avg_conf is not None else 0.0

        recent_identity_rows = db.query(QueryLog).order_by(QueryLog.created_at.desc()).limit(500).all()
        auto_resolved = 0
        manually_verified = 0
        ambiguous_matches = 0
        for row in recent_identity_rows:
            meta = row.meta or {}
            identity = meta.get("identity_resolution") or {}
            decision = str(identity.get("decision") or "").upper()
            if decision == "AUTO_RESOLVE":
                auto_resolved += 1
            elif decision == "MANUAL_VERIFICATION":
                manually_verified += 1
            if int(identity.get("candidate_count") or 0) > 1:
                ambiguous_matches += 1

        health = {
            "ai_active": True,
            "db_connected": True,
            "rag_enabled": True,
            "escalation_monitoring_enabled": True,
            "query_normalizer_enabled": True,
            "identity_resolution_enabled": True,
        }
        return {
            "total_queries": int(total_queries),
            "escalations": int(escalations),
            "avg_confidence": round(avg_confidence * 100, 2),
            "unresolved_cases": int(unresolved_cases),
            "identity_analytics": {
                "resolved_automatically": auto_resolved,
                "manually_verified": manually_verified,
                "ambiguous_matches": ambiguous_matches,
            },
            "health": health,
        }
    except Exception as exc:
        raise DatabaseUnavailableError("Failed to fetch analytics overview") from exc


@router.get("/analytics/recent-queries")
def recent_queries(db: Session = Depends(get_db), limit: int = 20) -> dict:
    try:
        rows = (
            db.query(QueryLog)
            .order_by(QueryLog.created_at.desc())
            .limit(max(1, min(limit, 100)))
            .all()
        )
        items = []
        intents: Counter[str] = Counter()
        confidence_trend = []
        for row in rows:
            meta = row.meta or {}
            confidence = float(meta.get("confidence", 0.0))
            intents[row.intent or "UNKNOWN"] += 1
            confidence_trend.append(
                {
                    "query_id": row.id,
                    "confidence": round(confidence * 100, 2),
                    "created_at": row.created_at,
                }
            )
            items.append(
                {
                    "id": row.id,
                    "created_at": row.created_at,
                    "channel": row.channel,
                    "customer_email": row.customer_email,
                    "message": row.message,
                    "intent": row.intent or "UNKNOWN",
                    "status": row.status,
                    "confidence": round(confidence * 100, 2),
                    "escalated": bool(meta.get("escalated", False)),
                    "latency_ms": row.response_time_ms,
                    "language": str(meta.get("query_normalization", {}).get("language_detected") or "english").lower(),
                    "normalized_for_workflow": bool(meta.get("query_normalization", {}).get("normalized_for_workflow", False)),
                    "escalation_severity": str(meta.get("escalation_severity") or ""),
                }
            )

        top_intents = [{"intent": key, "count": count} for key, count in intents.most_common(6)]
        return {"items": items, "top_intents": top_intents, "confidence_trend": list(reversed(confidence_trend))}
    except Exception as exc:
        raise DatabaseUnavailableError("Failed to fetch recent queries") from exc
