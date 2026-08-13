"""UK tide location seed data from WEATHER_APP_INTEGRATION_SPEC.md."""

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.weather.models import Location

SEED_LOCATIONS: list[dict[str, object]] = [
    {
        "id": "plym-uk-001",
        "name": "Plymouth",
        "region": "South Devon",
        "latitude": 50.3755,
        "longitude": -4.1427,
        "mhws": Decimal("4.80"),
        "mhwn": Decimal("3.50"),
        "admiralty_station_name": "Plymouth",
    },
    {
        "id": "salc-uk-002",
        "name": "Salcombe",
        "region": "South Devon",
        "latitude": 50.2378,
        "longitude": -3.7698,
        "mhws": Decimal("4.60"),
        "mhwn": Decimal("3.30"),
        "admiralty_station_name": "Salcombe",
    },
    {
        "id": "dart-uk-003",
        "name": "Dartmouth",
        "region": "South Devon",
        "latitude": 50.3521,
        "longitude": -3.5805,
        "mhws": Decimal("4.70"),
        "mhwn": Decimal("3.40"),
        "admiralty_station_name": "Dartmouth",
    },
    {
        "id": "torb-uk-004",
        "name": "Torbay",
        "region": "South Devon",
        "latitude": 50.4619,
        "longitude": -3.5253,
        "mhws": Decimal("4.50"),
        "mhwn": Decimal("3.20"),
        "admiralty_station_name": "Torquay",
    },
    {
        "id": "teig-uk-009",
        "name": "Teignmouth",
        "region": "South Devon",
        "latitude": 50.547,
        "longitude": -3.497,
        "mhws": Decimal("4.40"),
        "mhwn": Decimal("3.20"),
        "admiralty_station_name": "Teignmouth (Approaches)",
    },
    {
        "id": "mine-uk-003",
        "name": "Minehead",
        "region": "North Somerset",
        "latitude": 51.2036,
        "longitude": -3.4723,
        "mhws": Decimal("9.20"),
        "mhwn": Decimal("6.80"),
        "admiralty_station_name": "Minehead",
    },
    {
        "id": "blue-uk-010",
        "name": "Blue Anchor",
        "region": "West Somerset",
        "latitude": 51.164,
        "longitude": -3.384,
        "mhws": Decimal("9.00"),
        "mhwn": Decimal("6.60"),
        "admiralty_station_name": "Blue Anchor",
    },
    {
        "id": "lynm-uk-006",
        "name": "Lynmouth",
        "region": "North Devon",
        "latitude": 51.2289,
        "longitude": -3.8311,
        "mhws": Decimal("8.80"),
        "mhwn": Decimal("6.50"),
        "admiralty_station_name": "Lynmouth",
    },
    {
        "id": "ilfr-uk-007",
        "name": "Ilfracombe",
        "region": "North Devon",
        "latitude": 51.2089,
        "longitude": -4.1177,
        "mhws": Decimal("8.50"),
        "mhwn": Decimal("6.20"),
        "admiralty_station_name": "Ilfracombe",
    },
    {
        "id": "bide-uk-008",
        "name": "Bideford",
        "region": "North Devon",
        "latitude": 51.0167,
        "longitude": -4.2083,
        "mhws": Decimal("5.20"),
        "mhwn": Decimal("3.80"),
        "admiralty_station_name": "Bideford",
    },
]


async def seed_locations(session: AsyncSession) -> None:
    """Seed or update location catalogue."""
    for entry in SEED_LOCATIONS:
        location = await session.get(Location, entry["id"])
        if location is None:
            session.add(Location(**entry))
            continue

        location.name = str(entry["name"])
        location.region = str(entry["region"])
        location.latitude = float(entry["latitude"])
        location.longitude = float(entry["longitude"])
        location.mhws = entry["mhws"]  # type: ignore[assignment]
        location.mhwn = entry["mhwn"]  # type: ignore[assignment]
        if entry.get("admiralty_station_name"):
            location.admiralty_station_name = str(entry["admiralty_station_name"])

    await session.commit()
