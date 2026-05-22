from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuthorIdentity(Base):
    __tablename__ = "author_identities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    author_id: Mapped[str] = mapped_column(String(36), ForeignKey("authors.id", ondelete="CASCADE"), index=True)
    name_variant: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    instagram: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    whatsapp: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    author = relationship("Author")
