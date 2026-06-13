import os

import pyarrow.parquet as pq
import pytest

from src.tasks.export.weather_parquet import WeatherParquetTask
from src.tasks.ingest.weather_api import WeatherAPITask
from tests.helpers import print_parquet_table, print_weather_response

pytestmark = pytest.mark.live_api


@pytest.mark.skipif(
    not os.environ.get("OPENWEATHER_API_KEY"),
    reason="OPENWEATHER_API_KEY not set",
)
def test_live_pipeline_writes_parquet(tmp_path):
    api_task = WeatherAPITask(
        params={
            "latitude": 45.0,
            "longitude": -73.0,
            "api_key": os.environ["OPENWEATHER_API_KEY"],
        }
    )
    output_path = tmp_path / "weather.parquet"
    parquet_task = WeatherParquetTask(params={"output_path": str(output_path)})

    context = api_task.run({})
    print_weather_response(context["weather"])
    parquet_task.run(context)

    table = pq.read_table(output_path)
    print_parquet_table(table)

    assert table.num_rows == 1
    assert "api_key" not in table.column_names
