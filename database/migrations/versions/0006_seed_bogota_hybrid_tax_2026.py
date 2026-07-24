"""Carga la regla tributaria verificable para híbridos nuevos en Bogotá.

Revision ID: 0006_seed_bogota_hybrid_tax_2026
Revises: 0005_seed_verified_yaris_catalog
Create Date: 2026-07-24
"""

from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision = "0006_seed_bogota_hybrid_tax_2026"
down_revision = "0005_seed_verified_yaris_catalog"
branch_labels = None
depends_on = None

RULE_ID = UUID("d52a9ec4-93a1-4b1f-a3c5-536e93db4326")
BOGOTA_ID = UUID("8ee9da40-bc6d-4ea0-b4b6-94849908ab98")
SOURCE = (
    "https://www.haciendabogota.gov.co/es/impuestos/"
    "impuesto-sobre-vehiculos-automotores"
)


def upgrade() -> None:
    op.execute(
        sa.text(
            f"""
            INSERT INTO tax_rules (
                id, country_code, city_id, name, tax_kind, rate_percentage,
                conditions, effective_from, effective_to, source_url
            ) VALUES (
                '{RULE_ID}', 'CO', '{BOGOTA_ID}',
                'Impuesto vehicular Bogotá 2026 · híbridos nuevos',
                'vehicle_ownership', 2.7,
                '{{"powertrain":"hybrid",
                   "minimum_value":"57349000.01",
                   "maximum_value":"129032000",
                   "discount_percentage":"40",
                   "discount_years":"5",
                   "new_vehicle_only":"true"}}'::json,
                '2026-01-01', '2026-12-31', '{SOURCE}'
            )
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM tax_rules WHERE id = :id").bindparams(id=RULE_ID)
    )
