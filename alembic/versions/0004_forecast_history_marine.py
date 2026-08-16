"""Forecast timesteps, observation history, and richer marine fields."""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0004_forecast_history_marine"
down_revision: Union[str, None] = "0003_weather_observations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("weather_observations") as batch_op:
        batch_op.add_column(
            sa.Column("pressure_hpa", sa.Numeric(precision=6, scale=1), nullable=True)
        )
        batch_op.add_column(
            sa.Column("cloud_cover_pct", sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("humidity_pct", sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("moon_phase", sa.String(length=32), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "swell_height_m", sa.Numeric(precision=5, scale=2), nullable=True
            )
        )
        batch_op.add_column(
            sa.Column(
                "swell_period_s", sa.Numeric(precision=5, scale=1), nullable=True
            )
        )
        batch_op.add_column(
            sa.Column("swell_direction", sa.String(length=8), nullable=True)
        )

    op.create_table(
        "weather_observation_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("location_id", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.String(length=255), nullable=True),
        sa.Column("wind_speed_mph", sa.Numeric(precision=5, scale=1), nullable=True),
        sa.Column("wind_direction", sa.String(length=8), nullable=True),
        sa.Column("temperature_c", sa.Numeric(precision=5, scale=1), nullable=True),
        sa.Column("conditions", sa.String(length=120), nullable=True),
        sa.Column("pressure_hpa", sa.Numeric(precision=6, scale=1), nullable=True),
        sa.Column("cloud_cover_pct", sa.Integer(), nullable=True),
        sa.Column("humidity_pct", sa.Integer(), nullable=True),
        sa.Column("moon_phase", sa.String(length=32), nullable=True),
        sa.Column("swell_height_m", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("swell_period_s", sa.Numeric(precision=5, scale=1), nullable=True),
        sa.Column("swell_direction", sa.String(length=8), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["locations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_weather_observation_history_location_observed",
        "weather_observation_history",
        ["location_id", "observed_at"],
    )

    op.create_table(
        "weather_forecasts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("location_id", sa.String(length=64), nullable=False),
        sa.Column("forecast_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("summary", sa.String(length=255), nullable=True),
        sa.Column("wind_speed_mph", sa.Numeric(precision=5, scale=1), nullable=True),
        sa.Column("wind_direction", sa.String(length=8), nullable=True),
        sa.Column("temperature_c", sa.Numeric(precision=5, scale=1), nullable=True),
        sa.Column("conditions", sa.String(length=120), nullable=True),
        sa.Column("pressure_hpa", sa.Numeric(precision=6, scale=1), nullable=True),
        sa.Column("cloud_cover_pct", sa.Integer(), nullable=True),
        sa.Column("humidity_pct", sa.Integer(), nullable=True),
        sa.Column("moon_phase", sa.String(length=32), nullable=True),
        sa.Column("swell_height_m", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("swell_period_s", sa.Numeric(precision=5, scale=1), nullable=True),
        sa.Column("swell_direction", sa.String(length=8), nullable=True),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["locations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "location_id",
            "forecast_at",
            name="uq_weather_forecasts_location_forecast_at",
        ),
    )
    op.create_index(
        "ix_weather_forecasts_location_forecast_at",
        "weather_forecasts",
        ["location_id", "forecast_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_weather_forecasts_location_forecast_at", table_name="weather_forecasts"
    )
    op.drop_table("weather_forecasts")
    op.drop_index(
        "ix_weather_observation_history_location_observed",
        table_name="weather_observation_history",
    )
    op.drop_table("weather_observation_history")
    with op.batch_alter_table("weather_observations") as batch_op:
        batch_op.drop_column("swell_direction")
        batch_op.drop_column("swell_period_s")
        batch_op.drop_column("swell_height_m")
        batch_op.drop_column("moon_phase")
        batch_op.drop_column("humidity_pct")
        batch_op.drop_column("cloud_cover_pct")
        batch_op.drop_column("pressure_hpa")
