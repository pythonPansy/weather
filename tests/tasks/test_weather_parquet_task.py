import json

import pyarrow.parquet as pq

from src.tasks.export.weather_parquet import PARQUET_COLUMNS, WeatherParquetTask
from tests.helpers import print_parquet_table


def _sample_context():
    return {
        "weather_call": {"latitude": 45.0, "longitude": -73.0},
        "weather": {"main": {"temp": 10.5}, "name": "Montreal"},
    }


def test_writes_row_to_new_parquet_file(tmp_path):
    output_path = tmp_path / "weather.parquet"
    task = WeatherParquetTask(params={"output_path": str(output_path)})

    result = task.run(_sample_context())

    table = pq.read_table(output_path)
    print_parquet_table(table)
    assert table.num_rows == 1
    assert table.column_names == list(PARQUET_COLUMNS)
    assert table.column("latitude")[0].as_py() == 45.0
    assert table.column("longitude")[0].as_py() == -73.0
    response = json.loads(table.column("response")[0].as_py())
    assert response == _sample_context()["weather"]
    assert result["parquet_path"] == str(output_path)
    assert result["weather"] == _sample_context()["weather"]


def test_appends_second_row(tmp_path):
    output_path = tmp_path / "weather.parquet"
    task = WeatherParquetTask(params={"output_path": str(output_path)})

    task.run(_sample_context())
    task.run(
        {
            "weather_call": {"latitude": 46.0, "longitude": -74.0},
            "weather": {"main": {"temp": 12.0}},
        }
    )

    table = pq.read_table(output_path)
    print_parquet_table(table)
    assert table.num_rows == 2
    assert table.column("latitude")[1].as_py() == 46.0
    assert json.loads(table.column("response")[1].as_py())["main"]["temp"] == 12.0


def test_raises_when_weather_missing(tmp_path):
    output_path = tmp_path / "weather.parquet"
    task = WeatherParquetTask(params={"output_path": str(output_path)})

    try:
        task.run({"weather_call": {"latitude": 45.0, "longitude": -73.0}})
        raised = False
    except KeyError as exc:
        raised = True
        assert "weather" in str(exc)

    assert raised


def test_does_not_store_api_key(tmp_path):
    output_path = tmp_path / "weather.parquet"
    task = WeatherParquetTask(params={"output_path": str(output_path)})
    context = _sample_context()
    context["weather_call"]["api_key"] = "secret-should-not-persist"

    task.run(context)

    table = pq.read_table(output_path)
    assert set(table.column_names) == set(PARQUET_COLUMNS)
    assert "api_key" not in table.column_names
