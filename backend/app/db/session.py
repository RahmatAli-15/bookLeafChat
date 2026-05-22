from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core_config import settings
from app.db.base import Base
from app.utils.exceptions import DatabaseUnavailableError

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True) if settings.DATABASE_URL else None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session) if engine else None


def get_db():
    if SessionLocal is None:
        raise DatabaseUnavailableError("DATABASE_URL is not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    if engine is None:
        raise DatabaseUnavailableError("DATABASE_URL is not configured")
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def check_database_health() -> dict:
    if engine is None:
        return {"ok": False, "error_type": "configuration_error", "message": "DATABASE_URL is not configured"}

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"ok": True, "message": "Database connection successful"}
    except Exception as exc:
        return {
            "ok": False,
            "error_type": "connection_error",
            "message": "Database connection failed",
            "details": str(exc),
        }
