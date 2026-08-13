"""Add Admiralty station mapping columns to locations."""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0002_admiralty_station"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "locations",
        sa.Column("admiralty_station_id", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "locations",
        sa.Column("admiralty_station_name", sa.String(length=120), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("locations", "admiralty_station_name")
    op.drop_column("locations", "admiralty_station_id")
