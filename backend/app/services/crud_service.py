from __future__ import annotations

from typing import Generic, TypeVar
from uuid import uuid4

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.utils.exceptions import DatabaseUnavailableError, MultipleRecordsFoundError, RecordNotFoundError

ModelT = TypeVar("ModelT")


class CRUDService(Generic[ModelT]):
    def __init__(self, model: type[ModelT]) -> None:
        self.model = model

    def list(self, db: Session, *, limit: int = 100) -> list[ModelT]:
        try:
            return db.query(self.model).limit(limit).all()
        except SQLAlchemyError as exc:
            raise DatabaseUnavailableError("Database query failed") from exc

    def get(self, db: Session, item_id: str) -> ModelT:
        try:
            items = db.query(self.model).filter(self.model.id == item_id).limit(2).all()
        except SQLAlchemyError as exc:
            raise DatabaseUnavailableError("Database query failed") from exc

        if not items:
            raise RecordNotFoundError(f"{self.model.__name__} not found: {item_id}")
        if len(items) > 1:
            raise MultipleRecordsFoundError(f"Duplicate {self.model.__name__} rows found for id={item_id}")
        return items[0]

    def create(self, db: Session, payload: dict) -> ModelT:
        if "id" not in payload:
            payload["id"] = str(uuid4())
        item = self.model(**payload)
        try:
            db.add(item)
            db.commit()
            db.refresh(item)
            return item
        except IntegrityError as exc:
            db.rollback()
            raise MultipleRecordsFoundError(f"Duplicate record for {self.model.__name__}") from exc
        except SQLAlchemyError as exc:
            db.rollback()
            raise DatabaseUnavailableError("Database write failed") from exc
