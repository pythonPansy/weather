import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_locations_returns_required_fields(client: AsyncClient) -> None:
    response = await client.get("/api/locations")
    assert response.status_code == 200
    locations = response.json()
    assert isinstance(locations, list)
    assert len(locations) >= 1

    required = {"id", "name", "region", "latitude", "longitude"}
    for location in locations:
        assert required.issubset(location.keys())
        assert isinstance(location["latitude"], float)
        assert isinstance(location["longitude"], float)


@pytest.mark.asyncio
async def test_locations_includes_plymouth(client: AsyncClient) -> None:
    response = await client.get("/api/locations")
    ids = {loc["id"] for loc in response.json()}
    assert "plym-uk-001" in ids
