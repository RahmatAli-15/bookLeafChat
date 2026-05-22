from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.query_log import QueryLog
from app.services.crud_service import CRUDService


query_log_service = CRUDService[QueryLog](QueryLog)


def log_query(db: Session, payload: dict) -> QueryLog:
    if "metadata" in payload:
        payload["meta"] = payload.pop("metadata")
    return query_log_service.create(db, payload)
