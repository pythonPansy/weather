6. Test-Driven Development (important part)
Example: test BEFORE implementation

tests/tasks/test_weather_task.py

from fish_pipeline.tasks.weather import WeatherAPITask

def test_weather_task_adds_weather_to_context(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"hourly": {"temperature_2m": [10, 11]}}
    mock_response.raise_for_status.return_value = None

    mocker.patch("requests.get", return_value=mock_response)

    task = WeatherAPITask(
        params={"latitude": 45.0, "longitude": -73.0}
    )

    context = {}
    result = task.run(context)

    assert "weather" in result
    assert result["weather"]["hourly"]["temperature_2m"] == [10, 11]


This teaches you:

Mocking external APIs

Testing behavior, not implementation

Isolation

Run tests:

pytest

7. YAML config example
tasks:
  - type: weather_api
    params:
      latitude: 45.123
      longitude: -73.456

8. Why this setup is ideal for learning

You’ll learn:

How to design interfaces

How to write testable code

How to structure a real project

How config drives behavior

How to evolve safely using tests

This is much better than jumping straight into frameworks.

Recommended learning path (next steps)

In order:

Add CSV export task

Add context object (typed wrapper)

Add custom exceptions

Add task dependencies

Add CLI (python -m fish_pipeline pipeline.yaml)

Add mypy typing

Add incremental runs

Next question for you

To guide the next step precisely:

Python version you’re using?

Do you want to write tests first together (true TDD)?

Should context stay a dict or become a class?

Are you comfortable with pytest already?

This is a very strong foundation — you’re setting yourself up well.