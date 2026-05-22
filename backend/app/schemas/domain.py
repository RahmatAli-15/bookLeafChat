from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class BaseRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    created_at: datetime
    updated_at: datetime


class Author(BaseRecord):
    full_name: str
    email: EmailStr | None = None
    genre: str | None = None
    country: str | None = None
    active: bool = True


class AuthorIdentity(BaseRecord):
    author_id: str
    platform: str
    identity_value: str
    normalized_value: str
    verified: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class Book(BaseRecord):
    author_id: str
    title: str
    isbn: str | None = None
    publication_date: date | None = None
    status: str
    support_tier: str


class AddOnService(BaseRecord):
    book_id: str
    service_name: str
    service_type: str
    monthly_fee: Decimal
    status: str
    started_at: datetime
    ended_at: datetime | None = None


class QueryLog(BaseRecord):
    channel: str
    customer_name: str | None = None
    customer_email: EmailStr | None = None
    message: str
    intent: str | None = None
    status: str
    response_time_ms: int | None = None
    book_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Escalation(BaseRecord):
    query_id: str
    escalation_level: int
    reason: str
    assigned_to: str | None = None
    priority: str
    status: str
    resolved_at: datetime | None = None
