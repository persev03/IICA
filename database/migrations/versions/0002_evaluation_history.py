"""Guarda cálculos autenticados como instantáneas reproducibles.

Revision ID: 0002_evaluation_history
Revises: 0001_initial_catalog_and_rules
Create Date: 2026-07-23
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_evaluation_history"
down_revision = "0001_initial_catalog_and_rules"
branch_labels = None
depends_on = None

UUID = sa.Uuid()


def upgrade() -> None:
    op.create_table(
        "evaluations",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column(
            "city_id",
            UUID,
            sa.ForeignKey("cities.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "evaluated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("input_snapshot", sa.JSON(), nullable=False),
        sa.Column("result_snapshot", sa.JSON(), nullable=False),
        sa.Column("engine_version", sa.String(32), nullable=False),
        sa.Column("data_version", sa.Text(), nullable=False),
    )
    op.create_index("ix_evaluations_user_id", "evaluations", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_evaluations_user_id", table_name="evaluations")
    op.drop_table("evaluations")
