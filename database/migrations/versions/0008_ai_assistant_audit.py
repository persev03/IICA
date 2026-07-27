"""Registra interacciones del asistente de IA local.

Revision ID: 0008_ai_assistant_audit
Revises: 0007_expand_aburra_suvs
Create Date: 2026-07-27
"""

import sqlalchemy as sa
from alembic import op

revision = "0008_ai_assistant_audit"
down_revision = "0007_expand_aburra_suvs"
branch_labels = None
depends_on = None

UUID = sa.Uuid()


def upgrade() -> None:
    op.create_table(
        "ai_assistant_records",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("user_id", sa.String(128), nullable=True),
        sa.Column("city_code", sa.String(64), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("llm_provider", sa.String(32), nullable=False),
        sa.Column("llm_model", sa.String(120), nullable=False),
        sa.Column("prompt_snapshot", sa.JSON(), nullable=False),
        sa.Column("response_snapshot", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_ai_assistant_records_user_id",
        "ai_assistant_records",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_ai_assistant_records_user_id", table_name="ai_assistant_records")
    op.drop_table("ai_assistant_records")
