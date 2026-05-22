from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.query_log_service import log_query as persist_query_log
from app.utils.exceptions import DatabaseUnavailableError


def log_query(
    *,
    message: str,
    channel: str = "web-chat",
    customer_name: str | None = None,
    customer_email: str | None = None,
    intent: str | None = None,
    status: str = "open",
    response_time_ms: int | None = None,
    book_id: str | None = None,
    author_id: str | None = None,
    metadata: dict | None = None,
):
    if SessionLocal is None:
        raise DatabaseUnavailableError("DATABASE_URL is not configured")

    db: Session = SessionLocal()
    try:
        return persist_query_log(
            db,
            {
                "author_id": author_id,
                "book_id": book_id,
                "channel": channel,
                "customer_name": customer_name,
                "customer_email": customer_email,
                "message": message,
                "intent": intent,
                "status": status,
                "response_time_ms": response_time_ms,
                "metadata": metadata or {},
            },
        )
    finally:
        db.close()
