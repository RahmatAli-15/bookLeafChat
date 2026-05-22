from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core_config import settings
from app.db.seed import seed_mock_data
from app.db.session import SessionLocal, check_database_health, create_tables
from app.routes.ai_classification import router as ai_classification_router
from app.routes.analytics import router as analytics_router
from app.routes.authors import router as authors_router
from app.routes.books import router as books_router
from app.routes.chat import router as chat_router
from app.routes.escalations import router as escalations_router
from app.routes.health import router as health_router
from app.routes.identity import router as identity_router
from app.routes.queries import router as queries_router
from app.utils.exceptions import DatabaseUnavailableError, MultipleRecordsFoundError, RecordNotFoundError
from app.utils.logging_config import configure_logging


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    create_tables()
    if SessionLocal is not None:
        db = SessionLocal()
        try:
            seed_mock_data(db)
        finally:
            db.close()

    db_health = check_database_health()
    if not db_health.get("ok"):
        raise RuntimeError(f"Startup database health check failed: {db_health}")

    yield


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
    allowed_origins = [origin.strip() for origin in settings.FRONTEND_ORIGIN.split(",") if origin.strip()]
    # Render preview/renamed frontends can change hostnames; keep CORS resilient for onrender domains.
    render_origin_regex = r"^https://([a-zA-Z0-9-]+\.)?onrender\.com$"

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins or ["http://localhost:5173"],
        allow_origin_regex=render_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(DatabaseUnavailableError)
    async def db_unavailable_handler(_, exc: DatabaseUnavailableError):
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(RecordNotFoundError)
    async def not_found_handler(_, exc: RecordNotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(MultipleRecordsFoundError)
    async def multiple_records_handler(_, exc: MultipleRecordsFoundError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    app.include_router(health_router, prefix=settings.API_PREFIX, tags=["Health"])
    app.include_router(chat_router, prefix=settings.API_PREFIX, tags=["Chat"])
    app.include_router(authors_router, prefix=settings.API_PREFIX, tags=["Authors"])
    app.include_router(books_router, prefix=settings.API_PREFIX, tags=["Books"])
    app.include_router(queries_router, prefix=settings.API_PREFIX, tags=["Queries"])
    app.include_router(ai_classification_router, prefix=settings.API_PREFIX, tags=["AI"])
    app.include_router(identity_router, prefix=settings.API_PREFIX, tags=["Identity"])
    app.include_router(analytics_router, prefix=settings.API_PREFIX, tags=["Analytics"])
    app.include_router(escalations_router, prefix=settings.API_PREFIX, tags=["Escalations"])

    return app


app = create_app()
