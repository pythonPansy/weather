"""Application configuration from environment variables."""

from functools import lru_cache

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SIGNUP_URL = "https://developer.admiralty.co.uk/product#product=uk-tidal-api"
OPENWEATHER_SIGNUP_URL = "https://home.openweathermap.org/api_keys"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite+aiosqlite:///./weather.db"
    port: int = 8001
    tide_data_source: str = "fixture"
    admiralty_api_key: SecretStr = SecretStr("")
    tide_forecast_days: int = 7
    tide_location_ids: str = ""
    weather_data_source: str = "fixture"
    openweather_api_key: SecretStr = SecretStr("")

    def tide_location_id_list(self) -> list[str]:
        """Optional comma-separated location IDs to ingest (empty = all)."""
        if not self.tide_location_ids.strip():
            return []
        return [
            item.strip() for item in self.tide_location_ids.split(",") if item.strip()
        ]

    @field_validator("tide_forecast_days")
    @classmethod
    def validate_forecast_days(cls, value: int) -> int:
        if not 1 <= value <= 7:
            raise ValueError(
                "TIDE_FORECAST_DAYS must be between 1 and 7 (Discovery tier)"
            )
        return value

    def require_admiralty_api_key(self) -> str:
        """Return the subscription key or raise with signup instructions."""
        key = self.admiralty_api_key.get_secret_value().strip()
        if not key:
            raise ValueError(
                "ADMIRALTY_API_KEY is required when "
                "TIDE_DATA_SOURCE=admiralty_discovery. "
                f"Subscribe free at {SIGNUP_URL}, copy the primary key to .env, "
                "and never commit that file."
            )
        return key

    def require_openweather_api_key(self) -> str:
        """Return the OpenWeatherMap key or raise with signup instructions."""
        key = self.openweather_api_key.get_secret_value().strip()
        if not key:
            raise ValueError(
                "OPENWEATHER_API_KEY is required when "
                "WEATHER_DATA_SOURCE=openweather. "
                f"Create a free key at {OPENWEATHER_SIGNUP_URL} "
                "and never commit that file."
            )
        return key


@lru_cache
def get_settings() -> Settings:
    return Settings()
