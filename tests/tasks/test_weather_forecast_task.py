from src.context import PipelineContext
from src.tasks.ingest.weather_forecast_api import WeatherForecastAPITask


def _sample_forecast_payload():
    return {
        "cod": "200",
        "list": [
            {
                "dt": 1723204800,
                "main": {"temp": 288.15},
                "weather": [{"description": "clear sky"}],
            }
        ],
        "city": {"name": "Montreal"},
    }


def test_weather_forecast_task_adds_forecast_to_context(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = _sample_forecast_payload()
    mock_response.raise_for_status.return_value = None
    mock_get = mocker.patch(
        "src.tasks.ingest.weather_forecast_api.requests.get",
        return_value=mock_response,
    )

    task = WeatherForecastAPITask(
        params={
            "latitude": 45.0,
            "longitude": -73.0,
            "api_key": "test-key",
        }
    )

    result = task.run(PipelineContext())

    assert result.weather_forecast == _sample_forecast_payload()
    assert result.weather_forecast_call == {
        "latitude": 45.0,
        "longitude": -73.0,
    }
    mock_get.assert_called_once_with(
        "https://api.openweathermap.org/data/2.5/forecast",
        params={"lat": 45.0, "lon": -73.0, "appid": "test-key"},
        timeout=30,
    )
