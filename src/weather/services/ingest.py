"""Tide data ingestion — fixture mode, Admiralty Discovery, and scheduled refresh."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.weather.config import get_settings
from src.weather.db import get_session_factory
from src.weather.models import Location, TidePrediction
from src.weather.services.admiralty_client import AdmiraltyClient
from src.weather.services.phase import classify_high_tide_phase, classify_low_tide_phase

logger = logging.getLogger(__name__)


def _fixture_high_height(mhws: Decimal, mhwn: Decimal, day_offset: int) -> Decimal:
    """Generate a high tide height that cycles through spring/neap/medium."""
    cycle = day_offset % 14
    if cycle < 5:
        return mhws + Decimal("0.20")
    if cycle < 10:
        return mhwn - Decimal("0.30")
    return (mhws + mhwn) / 2


def _fixture_low_height(high: Decimal, mhwn: Decimal) -> Decimal:
    return max(Decimal("0.50"), mhwn - (high - mhwn) * Decimal("0.60"))


async def ingest_fixture_tides(
    session: AsyncSession, *, days_ahead: int | None = None
) -> int:
    """Generate deterministic fixture tide predictions for all locations."""
    settings = get_settings()
    horizon_days = days_ahead if days_ahead is not None else settings.tide_forecast_days
    now = datetime.now(tz=UTC).replace(minute=0, second=0, microsecond=0)
    end = now + timedelta(days=horizon_days)

    result = await session.execute(select(Location))
    locations = result.scalars().all()
    settings = get_settings()
    allowed_ids = settings.tide_location_id_list()
    if allowed_ids:
        locations = [loc for loc in locations if loc.id in allowed_ids]

    total = 0

    for location in locations:
        await session.execute(
            delete(TidePrediction).where(
                TidePrediction.location_id == location.id,
                TidePrediction.prediction_time >= now,
                TidePrediction.prediction_time <= end,
            )
        )

        day = now.date()
        end_date = end.date()
        day_offset = 0
        current_phase: str | None = None

        tide_slots = ((5, "high"), (11, "low"), (17, "high"), (23, "low"))
        while day <= end_date:
            for hour, tide_type in tide_slots:
                prediction_time = datetime(
                    day.year, day.month, day.day, hour, 0, tzinfo=UTC
                )
                if prediction_time < now or prediction_time > end:
                    continue

                if tide_type == "high":
                    height = _fixture_high_height(
                        location.mhws, location.mhwn, day_offset
                    )
                    current_phase = classify_high_tide_phase(
                        height, location.mhws, location.mhwn
                    )
                else:
                    high = _fixture_high_height(
                        location.mhws, location.mhwn, day_offset
                    )
                    height = _fixture_low_height(high, location.mhwn)
                    current_phase = classify_low_tide_phase(current_phase)

                session.add(
                    TidePrediction(
                        location_id=location.id,
                        prediction_time=prediction_time,
                        tide_type=tide_type,
                        height_metres=height,
                        tide_phase=current_phase,
                    )
                )
                total += 1

            day += timedelta(days=1)
            day_offset += 1

    await session.commit()
    return total


async def _resolve_station_id(
    client: AdmiraltyClient, location: Location
) -> str | None:
    if location.admiralty_station_id:
        return location.admiralty_station_id
    if not location.admiralty_station_name:
        logger.warning(
            "Location %s has no Admiralty station mapping; skipping",
            location.id,
        )
        return None

    station_id = await client.resolve_station_id(location.admiralty_station_name)
    if station_id:
        location.admiralty_station_id = station_id
    return station_id


async def ingest_admiralty_tides(session: AsyncSession) -> int:
    """Fetch tide events from Admiralty Discovery for all mapped locations."""
    settings = get_settings()
    api_key = settings.require_admiralty_api_key()
    client = AdmiraltyClient(api_key)
    total = 0

    try:
        result = await session.execute(select(Location))
        locations = result.scalars().all()
        allowed_ids = settings.tide_location_id_list()
        if allowed_ids:
            locations = [loc for loc in locations if loc.id in allowed_ids]
            missing = set(allowed_ids) - {loc.id for loc in locations}
            for location_id in sorted(missing):
                logger.warning("TIDE_LOCATION_IDS entry not found: %s", location_id)
        now = datetime.now(tz=UTC)
        end = now + timedelta(days=settings.tide_forecast_days)

        for location in locations:
            station_id = await _resolve_station_id(client, location)
            if not station_id:
                continue

            events = await client.get_tidal_events(
                station_id,
                duration_days=settings.tide_forecast_days,
            )

            await session.execute(
                delete(TidePrediction).where(
                    TidePrediction.location_id == location.id,
                    TidePrediction.prediction_time >= now,
                    TidePrediction.prediction_time <= end,
                )
            )

            current_phase: str | None = None
            for event in events:
                height = Decimal(str(round(event.height_metres, 2)))
                if event.event_type == "high":
                    current_phase = classify_high_tide_phase(
                        height, location.mhws, location.mhwn
                    )
                else:
                    current_phase = classify_low_tide_phase(current_phase)

                session.add(
                    TidePrediction(
                        location_id=location.id,
                        prediction_time=event.event_time,
                        tide_type=event.event_type,
                        height_metres=height,
                        tide_phase=current_phase,
                    )
                )
                total += 1

        await session.commit()
    finally:
        await client.close()

    return total


async def run_tide_ingest() -> int:
    """Run tide ingestion according to configured data source."""
    settings = get_settings()
    factory = get_session_factory()

    async with factory() as session:
        source = settings.tide_data_source.lower()
        if source == "fixture":
            return await ingest_fixture_tides(session)
        if source in {"admiralty", "admiralty_discovery", "discovery"}:
            return await ingest_admiralty_tides(session)
        raise ValueError(
            f"Unknown TIDE_DATA_SOURCE={settings.tide_data_source!r}. "
            "Use fixture or admiralty_discovery."
        )


def run_tide_ingest_sync() -> int:
    """Synchronous entry point for the YAML task runner."""
    return asyncio.run(run_tide_ingest())
