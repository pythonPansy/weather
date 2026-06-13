from src.tasks.ingest.callAPI import WeatherAPITask


def test_weather_task_adds_weather_to_context(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"main": {"temp": 10.5}}
    mock_response.raise_for_status.return_value = None
    mock_get = mocker.patch(
        "src.tasks.ingest.callAPI.requests.get", return_value=mock_response
    )

    task = WeatherAPITask(
        params={
            "latitude": 45.0,
            "longitude": -73.0,
            "api_key": "test-key",
        }
    )

    result = task.run({})

    assert "weather" in result
    assert result["weather"]["main"]["temp"] == 10.5
    mock_get.assert_called_once()
