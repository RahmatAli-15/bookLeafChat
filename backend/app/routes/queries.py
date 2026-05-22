from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.entities import QueryLogCreate, QueryLogOut
from app.services.query_log_service import log_query

router = APIRouter()


@router.post("/queries/log", response_model=QueryLogOut)
def create_query_log(payload: QueryLogCreate, db: Session = Depends(get_db)) -> QueryLogOut:
    return log_query(db, payload.model_dump())
