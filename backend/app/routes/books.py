from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.entities import BookOut
from app.services.book_service import book_service

router = APIRouter()


@router.get("/books", response_model=list[BookOut])
def list_books(db: Session = Depends(get_db)) -> list[BookOut]:
    return book_service.list(db)


@router.get("/books/{book_id}", response_model=BookOut)
def get_book(book_id: str, db: Session = Depends(get_db)) -> BookOut:
    return book_service.get(db, book_id)
