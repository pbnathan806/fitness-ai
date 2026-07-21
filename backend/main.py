import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError

from database.session import check_database_connection, dispose_engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        await check_database_connection()
    except (SQLAlchemyError, OSError) as exc:
        logger.warning("Database could not be reached at startup: %s", exc)

    yield
    await dispose_engine()


app = FastAPI(title="Fitness AI Platform", lifespan=lifespan)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    try:
        await check_database_connection()
    except (SQLAlchemyError, OSError):
        return {"status": "error", "database": "unreachable"}

    return {"status": "ok", "database": "connected"}
