"""FastAPI application for tide, location, and current weather API."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from src.weather.db import Base, get_engine, get_session_factory
from src.weather.routes import api
from src.weather.services.ingest import run_tide_ingest
from src.weather.services.ingest_weather import run_weather_ingest
from src.weather.services.locations import seed_locations

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _daily_tide_ingest() -> None:
    await run_tide_ingest(force=True)


async def _hourly_weather_ingest() -> None:
    await run_weather_ingest(force=True)


async def _run_startup_ingest() -> None:
    """Fill the store if empty/stale. Idempotent when already fresh."""
    try:
        ingested = await run_tide_ingest()
        logger.info("Tide ingest complete: %s predictions stored", ingested)
    except Exception as exc:
        logger.warning("Tide ingest failed: %s", exc)

    try:
        weather_ingested = await run_weather_ingest()
        logger.info("Weather ingest complete: %s observations stored", weather_ingested)
    except Exception as exc:
        logger.warning("Weather ingest failed: %s", exc)


@asynccontextmanager
async def lifespan(
    _app: FastAPI, *, start_scheduler: bool = True
) -> AsyncIterator[None]:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with get_session_factory()() as session:
        await seed_locations(session)

    ingest_task: asyncio.Task[None] | None = None
    if start_scheduler:
        # Production: serve DB-backed APIs immediately; refresh in the background
        # so Render cold starts do not block (or 429) client tide/forecast reads.
        ingest_task = asyncio.create_task(_run_startup_ingest())
        scheduler.add_job(_daily_tide_ingest, "cron", hour=2, minute=0)
        scheduler.add_job(_hourly_weather_ingest, "cron", minute=0)
        scheduler.start()
    else:
        # Tests: await ingest so fixtures exist before the first request.
        await _run_startup_ingest()

    yield

    if ingest_task is not None and not ingest_task.done():
        ingest_task.cancel()
        try:
            await ingest_task
        except asyncio.CancelledError:
            pass
    if start_scheduler:
        scheduler.shutdown()


def create_app(*, start_scheduler: bool = True) -> FastAPI:
    @asynccontextmanager
    async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with lifespan(app, start_scheduler=start_scheduler) as state:
            yield state

    app = FastAPI(
        title="Weather App",
        version="0.1.0",
        lifespan=_lifespan,
    )
    app.include_router(api.router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
