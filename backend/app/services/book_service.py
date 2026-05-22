from __future__ import annotations

from app.models.book import Book
from app.services.crud_service import CRUDService


book_service = CRUDService[Book](Book)
