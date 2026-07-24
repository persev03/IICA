"""Agrega Bogotá como primera ciudad operativa.

Revision ID: 0004_seed_bogota
Revises: 0003_seed_colombia
Create Date: 2026-07-24
"""

from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision = "0004_seed_bogota"
down_revision = "0003_seed_colombia"
branch_labels = None
depends_on = None

BOGOTA_ID = UUID("8ee9da40-bc6d-4ea0-b4b6-94849908ab98")


def upgrade() -> None:
    cities = sa.table(
        "cities",
        sa.column("id", sa.Uuid()),
        sa.column("country_code", sa.String(2)),
        sa.column("code", sa.String(64)),
        sa.column("name", sa.String(150)),
    )
    op.bulk_insert(
        cities,
        [
            {
                "id": BOGOTA_ID,
                "country_code": "CO",
                "code": "bogota",
                "name": "Bogotá",
            }
        ],
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM cities WHERE id = :city_id").bindparams(
            city_id=BOGOTA_ID
        )
    )
