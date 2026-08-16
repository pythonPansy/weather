from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.weather.config import get_settings
from src.weather.db import Base, get_session, reset_db_state
from src.weather.main import create_app
from src.weather.services.ingest import ingest_fixture_tides
from src.weather.services.ingest_weather import ingest_fixture_weather
from src.weather.services.locations import seed_locations


@pytest.fixture
async def client(monkeypatch: pytest.MonkeyPatch) -> AsyncGenerator[AsyncClient, None]:
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("TIDE_DATA_SOURCE", "fixture")
    monkeypatch.setenv("WEATHER_DATA_SOURCE", "fixture")
    get_settings.cache_clear()
    reset_db_state()

    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        await seed_locations(session)
        await ingest_fixture_tides(session)
        await ingest_fixture_weather(session)

    app = create_app(start_scheduler=False)

    async def override_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    await engine.dispose()
    get_settings.cache_clear()
    reset_db_state()
