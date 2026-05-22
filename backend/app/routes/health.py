from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.db.session import check_database_health

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/db")
def db_health_check() -> JSONResponse:
    result = check_database_health()

    if result.get("ok"):
        return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ok", "database": result})

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR if result.get("error_type") == "connection_error" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content={"status": "error", "database": result})
