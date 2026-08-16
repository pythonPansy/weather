"""Add latest weather observation per location."""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0003_weather_observations"
down_revision: Union[str, None] = "0002_admiralty_station"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "weather_observations",
        sa.Column("location_id", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.String(length=255), nullable=True),
        sa.Column("wind_speed_mph", sa.Numeric(precision=5, scale=1), nullable=True),
        sa.Column("wind_direction", sa.String(length=8), nullable=True),
        sa.Column("temperature_c", sa.Numeric(precision=5, scale=1), nullable=True),
        sa.Column("conditions", sa.String(length=120), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["locations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("location_id"),
    )


def downgrade() -> None:
    op.drop_table("weather_observations")
