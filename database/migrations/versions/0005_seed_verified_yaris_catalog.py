"""Carga dos Toyota híbridos y contexto operativo verificable de Bogotá.

Revision ID: 0005_seed_verified_yaris_catalog
Revises: 0004_seed_bogota
Create Date: 2026-07-24
"""

from datetime import date
from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision = "0005_seed_verified_yaris_catalog"
down_revision = "0004_seed_bogota"
branch_labels = None
depends_on = None

BOGOTA_ID = UUID("8ee9da40-bc6d-4ea0-b4b6-94849908ab98")
TOYOTA_ID = UUID("3c76b714-16a6-48eb-af91-f10064edfbab")
YARIS_HB_MODEL_ID = UUID("19c3d47a-61d8-4f9e-b57d-4f451bd7af2c")
YARIS_CROSS_MODEL_ID = UUID("7f649989-fc95-44d0-8560-6fa58cdec3fb")
YARIS_HB_VERSION_ID = UUID("5d275224-bc85-4c54-8995-9bb5d068cf43")
YARIS_CROSS_VERSION_ID = UUID("6c7033e7-ddbc-45c1-9f92-324d5618fbac")
HYBRID_RESTRICTION_ID = UUID("bc265b2d-4e47-4c61-8b02-39934bbb609c")
INFRASTRUCTURE_ID = UUID("98a7ea4c-81b6-4c56-b3c2-d04c9712169c")

BOGOTA_HYBRID_EXEMPTION_URL = (
    "https://bogota.gov.co/mi-ciudad/movilidad/"
    "pico-y-placa-solidario-para-vehiculos-matriculados-fuera-bogota-2026"
)
BOGOTA_CHARGING_URL = (
    "https://bogota.gov.co/mi-ciudad/movilidad/"
    "terminal-transporte-bogota-carga-vehiculos-electricos-minutos-gratis"
)


def upgrade() -> None:
    brands = sa.table(
        "vehicle_brands",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String(120)),
        sa.column("slug", sa.String(140)),
        sa.column("active", sa.Boolean()),
    )
    models = sa.table(
        "vehicle_models",
        sa.column("id", sa.Uuid()),
        sa.column("brand_id", sa.Uuid()),
        sa.column("name", sa.String(120)),
        sa.column("slug", sa.String(140)),
        sa.column("body_style", sa.String(48)),
    )
    restrictions = sa.table(
        "mobility_restrictions",
        sa.column("id", sa.Uuid()),
        sa.column("city_id", sa.Uuid()),
        sa.column("name", sa.String(160)),
        sa.column("powertrain", sa.String(32)),
        sa.column("restricted_days_per_month", sa.Integer()),
        sa.column("exemption", sa.Boolean()),
        sa.column("effective_from", sa.Date()),
        sa.column("effective_to", sa.Date()),
        sa.column("source_url", sa.Text()),
    )
    infrastructure = sa.table(
        "infrastructure_snapshots",
        sa.column("id", sa.Uuid()),
        sa.column("city_id", sa.Uuid()),
        sa.column("as_of", sa.Date()),
        sa.column("public_charging_points", sa.Integer()),
        sa.column("authorized_workshops", sa.Integer()),
        sa.column("dealerships", sa.Integer()),
        sa.column("source_url", sa.Text()),
    )

    op.bulk_insert(
        brands,
        [{"id": TOYOTA_ID, "name": "Toyota", "slug": "toyota", "active": True}],
    )
    op.bulk_insert(
        models,
        [
            {
                "id": YARIS_HB_MODEL_ID,
                "brand_id": TOYOTA_ID,
                "name": "Yaris HB HEV",
                "slug": "yaris-hb-hev",
                "body_style": "hatchback",
            },
            {
                "id": YARIS_CROSS_MODEL_ID,
                "brand_id": TOYOTA_ID,
                "name": "Yaris Cross HEV",
                "slug": "yaris-cross-hev",
                "body_style": "suv",
            },
        ],
    )
    op.execute(
        sa.text(
            """
            INSERT INTO vehicle_versions (
                id, model_id, trim, model_year, powertrain, seats,
                safety_score, warranty_months, list_price, currency_code,
                attributes
            ) VALUES
            (
                '5d275224-bc85-4c54-8995-9bb5d068cf43',
                '19c3d47a-61d8-4f9e-b57d-4f451bd7af2c',
                'XL 1.5 HEV 4x2 E-CVT', 2027, 'hybrid', 5,
                66, 60, 89900000, 'COP',
                '{"market_as_of":"2026-07-24",
                  "source_url":"https://www.toyota.com.co/vehiculos/hibridos/yaris-hb",
                  "safety_source_url":"https://www.latinncap.com/es/resultado/207/toyota-yaris-sedan--hatchback-%2B-6-airbags",
                  "safety_metric":"adult_occupant_percentage"}'::json
            ),
            (
                '6c7033e7-ddbc-45c1-9f92-324d5618fbac',
                '7f649989-fc95-44d0-8560-6fa58cdec3fb',
                'XS 1.5 HEV 4x2 E-CVT', 2027, 'hybrid', 5,
                77, 60, 125900000, 'COP',
                '{"market_as_of":"2026-07-24",
                  "source_url":"https://www.toyota.com.co/vehiculos/hibridos/yaris-cross",
                  "safety_source_url":"https://www.latinncap.com/es/resultado/208/toyota-yaris-cross-%2B-6-airbags",
                  "safety_metric":"adult_occupant_percentage"}'::json
            )
            """
        )
    )
    op.bulk_insert(
        restrictions,
        [
            {
                "id": HYBRID_RESTRICTION_ID,
                "city_id": BOGOTA_ID,
                "name": "Exención de pico y placa para vehículos híbridos",
                "powertrain": "hybrid",
                "restricted_days_per_month": 0,
                "exemption": True,
                "effective_from": date(2026, 1, 1),
                "effective_to": date(2026, 12, 31),
                "source_url": BOGOTA_HYBRID_EXEMPTION_URL,
            }
        ],
    )
    op.bulk_insert(
        infrastructure,
        [
            {
                "id": INFRASTRUCTURE_ID,
                "city_id": BOGOTA_ID,
                "as_of": date(2026, 1, 13),
                "public_charging_points": 5,
                "authorized_workshops": 0,
                "dealerships": 0,
                "source_url": BOGOTA_CHARGING_URL,
            }
        ],
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM infrastructure_snapshots WHERE id = :record_id"
        ).bindparams(record_id=INFRASTRUCTURE_ID)
    )
    op.execute(
        sa.text(
            "DELETE FROM mobility_restrictions WHERE id = :record_id"
        ).bindparams(record_id=HYBRID_RESTRICTION_ID)
    )
    op.execute(
        sa.text(
            "DELETE FROM vehicle_versions WHERE id IN (:hb_id, :cross_id)"
        ).bindparams(hb_id=YARIS_HB_VERSION_ID, cross_id=YARIS_CROSS_VERSION_ID)
    )
    op.execute(
        sa.text(
            "DELETE FROM vehicle_models WHERE id IN (:hb_id, :cross_id)"
        ).bindparams(hb_id=YARIS_HB_MODEL_ID, cross_id=YARIS_CROSS_MODEL_ID)
    )
    op.execute(
        sa.text("DELETE FROM vehicle_brands WHERE id = :brand_id").bindparams(
            brand_id=TOYOTA_ID
        )
    )
