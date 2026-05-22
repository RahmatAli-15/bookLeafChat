from __future__ import annotations

import logging
import sys

from app.db.seed import seed_mock_data
from app.db.session import SessionLocal, check_database_health, create_tables
from app.utils.logging_config import configure_logging


def run() -> int:
    configure_logging()
    logger = logging.getLogger("app.db.seed_runner")

    health = check_database_health()
    if not health.get("ok"):
        logger.error("seed_runner_db_unhealthy", extra={"health": health})
        return 1

    if SessionLocal is None:
        logger.error("seed_runner_session_unavailable")
        return 1

    create_tables()

    db = SessionLocal()
    try:
        seed_mock_data(db)
        logger.info("seed_runner_completed")
        return 0
    except Exception:
        logger.exception("seed_runner_failed")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(run())

