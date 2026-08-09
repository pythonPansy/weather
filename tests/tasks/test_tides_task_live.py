import pytest

from src.tasks.ingest.tides_api import TidesAPITask

pytestmark = pytest.mark.live_api


def test_tides_task_calls_tideturtle_api():
    task = TidesAPITask(
        params={
            "latitude": 50.547,
            "longitude": -3.497,
        }
    )

    result = task.run({})

    assert "tides" in result
    tides = result["tides"]
    assert "extrema" in tides
    assert isinstance(tides["extrema"], list)
    assert len(tides["extrema"]) > 0
    assert "is_high" in tides["extrema"][0]
    assert "height_m" in tides["extrema"][0]
    assert "licence" in tides
    assert "license" not in tides
