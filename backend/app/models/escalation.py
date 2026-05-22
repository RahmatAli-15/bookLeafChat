from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Escalation(Base):
    __tablename__ = "escalations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    query_id: Mapped[str] = mapped_column(String(36), ForeignKey("query_logs.id", ondelete="CASCADE"), index=True)
    escalation_level: Mapped[int] = mapped_column(Integer, default=1)
    reason: Mapped[str] = mapped_column(Text)
    assigned_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    priority: Mapped[str] = mapped_column(String(64), default="medium")
    status: Mapped[str] = mapped_column(String(64), default="open")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    query_log = relationship("QueryLog", back_populates="escalations")
