import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_tides_returns_valid_shape(client: AsyncClient) -> None:
    response = await client.get(
        "/api/tides/plym-uk-001",
        params={
            "start": "2026-08-11T00:00:00Z",
            "end": "2026-08-18T23:59:59Z",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "tides" in data
    assert isinstance(data["tides"], list)

    allowed_phases = {"spring", "neap", "medium", None}
    for tide in data["tides"]:
        assert {"time", "type", "height", "phase"}.issubset(tide.keys())
        assert tide["type"] in {"high", "low"}
        assert tide["height"] > 0
        assert tide["phase"] in allowed_phases


@pytest.mark.asyncio
async def test_tides_unknown_location_returns_404(client: AsyncClient) -> None:
    response = await client.get(
        "/api/tides/unknown-id",
        params={
            "start": "2026-08-11T00:00:00Z",
            "end": "2026-08-18T00:00:00Z",
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_tides_invalid_date_returns_400(client: AsyncClient) -> None:
    response = await client.get(
        "/api/tides/plym-uk-001",
        params={"start": "not-a-date", "end": "2026-08-18T00:00:00Z"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_tides_start_after_end_returns_400(client: AsyncClient) -> None:
    response = await client.get(
        "/api/tides/plym-uk-001",
        params={
            "start": "2026-08-20T00:00:00Z",
            "end": "2026-08-11T00:00:00Z",
        },
    )
    assert response.status_code == 400
