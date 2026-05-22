from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Book(Base):
    __tablename__ = "books"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    author_id: Mapped[str] = mapped_column(String(36), ForeignKey("authors.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    isbn: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(64), default="published")
    royalty_status: Mapped[str] = mapped_column(String(64), default="pending")
    support_tier: Mapped[str] = mapped_column(String(64), default="standard")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    author = relationship("Author", back_populates="books")
    add_on_services = relationship("AddOnService", back_populates="book", cascade="all, delete-orphan")
    query_logs = relationship("QueryLog", back_populates="book")
