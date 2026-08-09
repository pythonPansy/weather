from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any


@dataclass(frozen=True)
class PipelineContext:
    """Typed shared state passed between pipeline tasks."""

    weather: dict | None = None
    weather_call: dict | None = None
    tides: dict | None = None
    tides_call: dict | None = None
    parquet_path: str | None = None
    tides_parquet_path: str | None = None

    def with_values(self, **kwargs: Any) -> PipelineContext:
        """Return a new context with the given fields replaced."""
        return replace(self, **kwargs)

    def require(self, field: str) -> object:
        """Return a required field or raise KeyError with a task-oriented message."""
        if field not in self.__dataclass_fields__:
            raise KeyError(f"unknown context field '{field}'")

        value = getattr(self, field)
        if value is None:
            raise KeyError(f"context is missing '{field}'")
        return value
