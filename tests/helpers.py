import json


def print_weather_response(weather: dict) -> None:
    print("\n--- OpenWeatherMap response (summary) ---")
    summary = {
        "name": weather.get("name"),
        "coord": weather.get("coord"),
        "main": weather.get("main"),
        "weather": weather.get("weather"),
        "wind": weather.get("wind"),
    }
    print(json.dumps(summary, indent=2))


def print_parquet_table(table) -> None:
    print("\n--- Parquet table ---")
    print(f"columns: {table.column_names}")
    print(f"rows: {table.num_rows}")
    for i in range(table.num_rows):
        row = {name: table.column(name)[i].as_py() for name in table.column_names}
        row["response"] = json.loads(row["response"])
        print(f"row {i}: {row}")
