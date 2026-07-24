"""Agrega Colombia como país base del catálogo.

Revision ID: 0003_seed_colombia
Revises: 0002_evaluation_history
Create Date: 2026-07-24
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_seed_colombia"
down_revision = "0002_evaluation_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    countries = sa.table(
        "countries",
        sa.column("code", sa.String(2)),
        sa.column("name", sa.String(100)),
        sa.column("currency_code", sa.String(3)),
    )
    op.bulk_insert(
        countries,
        [{"code": "CO", "name": "Colombia", "currency_code": "COP"}],
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM countries WHERE code = 'CO'"))
