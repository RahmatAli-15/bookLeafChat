from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class QueryLog(Base):
    __tablename__ = "query_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    author_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("authors.id", ondelete="SET NULL"), nullable=True, index=True)
    book_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("books.id", ondelete="SET NULL"), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(64), default="web-chat")
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text)
    intent: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(64), default="open")
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    meta: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    author = relationship("Author", back_populates="query_logs")
    book = relationship("Book", back_populates="query_logs")
    escalations = relationship("Escalation", back_populates="query_log", cascade="all, delete-orphan")
