from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.workflows.query_orchestrator import query_orchestrator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    logger.info("chat_endpoint_received", extra={"channel": payload.channel})
    return query_orchestrator.process(db, payload)
