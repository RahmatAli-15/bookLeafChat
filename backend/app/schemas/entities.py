from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr


class AuthorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    full_name: str
    email: EmailStr
    genre: str | None = None
    country: str | None = None
    active: bool
    created_at: datetime


class BookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    author_id: str
    title: str
    isbn: str | None = None
    publication_date: date | None = None
    status: str
    royalty_status: str
    support_tier: str


class AddOnServiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    book_id: str
    service_name: str
    service_type: str
    monthly_fee: Decimal
    status: str


class QueryLogCreate(BaseModel):
    author_id: str | None = None
    book_id: str | None = None
    channel: str = "web-chat"
    customer_name: str | None = None
    customer_email: EmailStr | None = None
    message: str
    intent: str | None = None
    status: str = "open"
    response_time_ms: int | None = None
    metadata: dict = {}


class QueryLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    author_id: str | None
    book_id: str | None
    channel: str
    message: str
    intent: str | None
    status: str
    created_at: datetime
