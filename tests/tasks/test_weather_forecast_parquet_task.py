import json

import pyarrow.parquet as pq
import pytest

from src.context import PipelineContext
from src.tasks.export.weather_forecast_parquet import (
    PARQUET_COLUMNS,
    WeatherForecastParquetTask,
)
from tests.helpers import print_parquet_table


def _sample_context():
    return PipelineContext(
        weather_forecast_call={"latitude": 45.0, "longitude": -73.0},
        weather_forecast={
            "cod": "200",
            "list": [{"main": {"temp": 288.15}}],
            "city": {"name": "Montreal"},
        },
    )


def test_writes_row_to_new_parquet_file(tmp_path):
    output_path = tmp_path / "weather_forecast.parquet"
    task = WeatherForecastParquetTask(params={"output_path": str(output_path)})

    result = task.run(_sample_context())

    table = pq.read_table(output_path)
    print_parquet_table(table)
    assert table.num_rows == 1
    assert table.column_names == list(PARQUET_COLUMNS)
    assert table.column("latitude")[0].as_py() == 45.0
    assert table.column("longitude")[0].as_py() == -73.0
    response = json.loads(table.column("response")[0].as_py())
    assert response == _sample_context().weather_forecast
    assert result.weather_forecast_parquet_path == str(output_path)
    assert result.weather_forecast == _sample_context().weather_forecast


def test_appends_second_row(tmp_path):
    output_path = tmp_path / "weather_forecast.parquet"
    task = WeatherForecastParquetTask(params={"output_path": str(output_path)})

    task.run(_sample_context())
    task.run(
        PipelineContext(
            weather_forecast_call={"latitude": 46.0, "longitude": -74.0},
            weather_forecast={"list": [{"main": {"temp": 290.0}}]},
        )
    )

    table = pq.read_table(output_path)
    print_parquet_table(table)
    assert table.num_rows == 2
    assert table.column("latitude")[1].as_py() == 46.0
    assert (
        json.loads(table.column("response")[1].as_py())["list"][0]["main"]["temp"]
        == 290.0
    )


def test_raises_when_forecast_missing(tmp_path):
    output_path = tmp_path / "weather_forecast.parquet"
    task = WeatherForecastParquetTask(params={"output_path": str(output_path)})

    with pytest.raises(KeyError, match="weather_forecast"):
        task.run(
            PipelineContext(
                weather_forecast_call={"latitude": 45.0, "longitude": -73.0},
            )
        )
