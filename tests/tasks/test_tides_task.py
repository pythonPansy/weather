from src.context import PipelineContext
from src.tasks.ingest.tides_api import TidesAPITask, normalise_tides_response


def _sample_tideturtle_payload():
    return {
        "distanceKm": 39.7,
        "place": {
            "slug": "salcombe-devon",
            "country": "united-kingdom",
            "region": "devon",
            "name": "Salcombe",
            "country_name": "United Kingdom",
            "region_name": "Devon",
            "href": "/united-kingdom/devon/salcombe-devon",
            "lat": 50.2368,
            "lon": -3.773,
        },
        "tides": {
            "license": "https://open-meteo.com/en/license",
            "data": {
                "datum": "MSL",
                "unit": "m",
                "timezone": "Europe/London",
                "source": "Predictions: Open-Meteo Marine",
                "extrema": [
                    {
                        "time": "2026-08-09T08:00:00.000Z",
                        "date": "2026-08-09",
                        "height": 1.35,
                        "isHigh": True,
                    },
                    {
                        "time": "2026-08-09T14:00:00.000Z",
                        "date": "2026-08-09",
                        "height": -2.09,
                        "isHigh": False,
                    },
                ],
            },
        },
    }


def test_normalise_tides_response_uses_uk_english_schema():
    normalised = normalise_tides_response(_sample_tideturtle_payload())

    assert "licence" in normalised
    assert "license" not in normalised
    assert normalised["distance_km"] == 39.7
    assert normalised["time_zone"] == "Europe/London"
    assert normalised["place"]["latitude"] == 50.2368
    assert normalised["place"]["longitude"] == -3.773
    assert normalised["extrema"][0] == {
        "time": "2026-08-09T08:00:00.000Z",
        "date": "2026-08-09",
        "height_m": 1.35,
        "is_high": True,
    }
    assert normalised["extrema"][1]["is_high"] is False
    assert normalised["extrema"][1]["height_m"] == -2.09


def test_tides_task_adds_tides_to_context(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = _sample_tideturtle_payload()
    mock_response.raise_for_status.return_value = None
    mock_get = mocker.patch(
        "src.tasks.ingest.tides_api.requests.get", return_value=mock_response
    )

    task = TidesAPITask(
        params={
            "latitude": 50.547,
            "longitude": -3.497,
        }
    )

    result = task.run(PipelineContext())

    assert result.tides is not None
    assert result.tides["place"]["name"] == "Salcombe"
    assert result.tides["extrema"][0]["is_high"] is True
    assert result.tides_call == {"latitude": 50.547, "longitude": -3.497}
    mock_get.assert_called_once_with(
        "https://tideturtle.com/api/v1/tides",
        params={"lat": 50.547, "lon": -3.497},
        timeout=30,
    )
