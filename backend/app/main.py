from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from http import HTTPStatus

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import api_router
from app.core.config import settings
from app.db.session import SessionLocal
from app.services.valhalla_client import ValhallaClient


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """App startup/shutdown lifecycle hooks for initializing shared clients."""

    yield


def create_app() -> FastAPI:
    """FastAPI application factory."""

    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.get("/health", status_code=HTTPStatus.OK)
    async def healthcheck() -> dict[str, object]:
        """Probe API, PostGIS connectivity, and Valhalla availability."""

        db_ok = await _check_database()
        valhalla_ok = await ValhallaClient().healthcheck()

        status_text = "ok" if db_ok and valhalla_ok else "degraded"
        return {
            "status": status_text,
            "dependencies": {"postgis": db_ok, "valhalla": valhalla_ok},
        }

    return app


async def _check_database() -> bool:
    """Validate that DB is reachable and PostGIS extension is available."""

    try:
        async with SessionLocal() as session:
            assert isinstance(session, AsyncSession)
            await session.execute(text("SELECT PostGIS_Version();"))
        return True
    except Exception:
        return False


app = create_app()
