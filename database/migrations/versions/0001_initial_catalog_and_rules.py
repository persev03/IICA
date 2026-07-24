"""Crea catálogos de vehículos, territorio y reglas locales versionadas.

Revision ID: 0001_initial_catalog_and_rules
Revises:
Create Date: 2026-07-23
"""

import sqlalchemy as sa
from alembic import op

revision = "0001_initial_catalog_and_rules"
down_revision = None
branch_labels = None
depends_on = None

UUID = sa.Uuid()


def _audit_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "countries",
        sa.Column("code", sa.String(2), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("currency_code", sa.String(3), nullable=False),
        *_audit_columns(),
    )
    op.create_table(
        "regions",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("country_code", sa.String(2), sa.ForeignKey("countries.code", ondelete="RESTRICT"), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        *_audit_columns(),
        sa.UniqueConstraint("country_code", "code"),
    )
    op.create_table(
        "cities",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("country_code", sa.String(2), sa.ForeignKey("countries.code", ondelete="RESTRICT"), nullable=False),
        sa.Column("region_id", UUID, sa.ForeignKey("regions.id", ondelete="RESTRICT")),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        *_audit_columns(),
        sa.UniqueConstraint("country_code", "code"),
    )
    op.create_table(
        "vehicle_brands",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("name", sa.String(120), unique=True, nullable=False),
        sa.Column("slug", sa.String(140), unique=True, nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_audit_columns(),
    )
    op.create_table(
        "vehicle_models",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("brand_id", UUID, sa.ForeignKey("vehicle_brands.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(140), nullable=False),
        sa.Column("body_style", sa.String(48), nullable=False),
        *_audit_columns(),
        sa.UniqueConstraint("brand_id", "slug"),
    )
    op.create_table(
        "vehicle_versions",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("model_id", UUID, sa.ForeignKey("vehicle_models.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("trim", sa.String(120), nullable=False),
        sa.Column("model_year", sa.Integer(), nullable=False),
        sa.Column("powertrain", sa.String(32), nullable=False),
        sa.Column("seats", sa.Integer(), nullable=False),
        sa.Column("safety_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("warranty_months", sa.Integer(), nullable=False),
        sa.Column("list_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency_code", sa.String(3), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        *_audit_columns(),
        sa.UniqueConstraint("model_id", "model_year", "trim"),
        sa.CheckConstraint("model_year >= 1886", name="vehicle_version_model_year_valid"),
        sa.CheckConstraint("seats >= 1", name="vehicle_version_seats_valid"),
    )
    op.create_table(
        "tax_rules",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("country_code", sa.String(2), sa.ForeignKey("countries.code", ondelete="RESTRICT"), nullable=False),
        sa.Column("city_id", UUID, sa.ForeignKey("cities.id", ondelete="RESTRICT")),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("tax_kind", sa.String(48), nullable=False),
        sa.Column("rate_percentage", sa.Numeric(7, 4), nullable=False),
        sa.Column("conditions", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date()),
        sa.Column("source_url", sa.Text(), nullable=False),
        *_audit_columns(),
        sa.CheckConstraint("rate_percentage >= 0", name="tax_rule_rate_non_negative"),
    )
    op.create_table(
        "incentives",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("country_code", sa.String(2), sa.ForeignKey("countries.code", ondelete="RESTRICT"), nullable=False),
        sa.Column("city_id", UUID, sa.ForeignKey("cities.id", ondelete="RESTRICT")),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("incentive_kind", sa.String(64), nullable=False),
        sa.Column("powertrain", sa.String(32)),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency_code", sa.String(3), nullable=False),
        sa.Column("conditions", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date()),
        sa.Column("source_url", sa.Text(), nullable=False),
        *_audit_columns(),
        sa.CheckConstraint("amount >= 0", name="incentive_amount_non_negative"),
    )
    op.create_table(
        "mobility_restrictions",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("city_id", UUID, sa.ForeignKey("cities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("powertrain", sa.String(32)),
        sa.Column("restricted_days_per_month", sa.Integer(), nullable=False),
        sa.Column("exemption", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("conditions", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date()),
        sa.Column("source_url", sa.Text(), nullable=False),
        *_audit_columns(),
    )
    op.create_table(
        "infrastructure_snapshots",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("city_id", UUID, sa.ForeignKey("cities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("as_of", sa.Date(), nullable=False),
        sa.Column("public_charging_points", sa.Integer(), nullable=False),
        sa.Column("authorized_workshops", sa.Integer(), nullable=False),
        sa.Column("dealerships", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        *_audit_columns(),
        sa.UniqueConstraint("city_id", "as_of", "source_url"),
    )


def downgrade() -> None:
    op.drop_table("infrastructure_snapshots")
    op.drop_table("mobility_restrictions")
    op.drop_table("incentives")
    op.drop_table("tax_rules")
    op.drop_table("vehicle_versions")
    op.drop_table("vehicle_models")
    op.drop_table("vehicle_brands")
    op.drop_table("cities")
    op.drop_table("regions")
    op.drop_table("countries")
