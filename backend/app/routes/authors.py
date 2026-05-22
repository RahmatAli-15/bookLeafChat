from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.entities import AuthorOut
from app.services.author_service import author_service

router = APIRouter()


@router.get("/authors", response_model=list[AuthorOut])
def list_authors(db: Session = Depends(get_db)) -> list[AuthorOut]:
    return author_service.list(db)
