from __future__ import annotations

from app.models.author import Author
from app.services.crud_service import CRUDService


author_service = CRUDService[Author](Author)
