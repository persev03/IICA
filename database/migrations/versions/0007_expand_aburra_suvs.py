"""Amplía IICA al Valle de Aburrá y a cuatro SUV híbridas verificadas.

Revision ID: 0007_expand_aburra_suvs
Revises: 0006_seed_bogota_hybrid_tax_2026
Create Date: 2026-07-25
"""

from datetime import date
from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision = "0007_expand_aburra_suvs"
down_revision = "0006_seed_bogota_hybrid_tax_2026"
branch_labels = None
depends_on = None

AREA_SOURCE = "https://www.metropol.gov.co/area/Paginas/somos/subdirecciones.aspx"
MOBILITY_SOURCE = (
    "https://www.medellin.gov.co/es/sala-de-prensa/noticias/"
    "el-lunes-2-de-febrero-inicia-la-nueva-rotacion-del-pico-y-placa-en-medellin/"
)
MOBILITY_SOURCE_SECOND_HALF = (
    "https://www.medellin.gov.co/es/sala-de-prensa/noticias/"
    "la-nueva-rotacion-del-pico-y-placa-en-medellin-comenzara-a-regir-"
    "a-partir-del-lunes-3-de-agosto/"
)
INFRA_SOURCE = "https://www.datos.gov.co/resource/qqm3-dw2u.json"

CITIES = [
    ("medellin", "Medellín", "203adf3c-5212-47d7-a58e-579749ed6a6a", 29),
    ("barbosa", "Barbosa", "7cd52b6f-8591-4de8-a59f-a8410543e11c", 0),
    ("bello", "Bello", "5661a09a-1fda-45be-a6a6-63836f7d22da", 2),
    ("caldas", "Caldas", "17fb0a97-e02c-423d-8c73-5e582190ce67", 0),
    ("copacabana", "Copacabana", "50b3b987-1583-4fb4-ada2-09d09f76c111", 0),
    ("envigado", "Envigado", "5bceef82-cb5f-4207-9a17-1902168a6d0d", 3),
    ("girardota", "Girardota", "b51ae97b-ce71-4185-87aa-2e9194244691", 0),
    ("itagui", "Itagüí", "535825aa-ae22-4433-8975-ce39362468db", 0),
    ("la-estrella", "La Estrella", "73a55b50-6dfa-4231-a840-e01f3e038dba", 0),
    ("sabaneta", "Sabaneta", "9e70b002-6e59-4c73-b788-d9fbb58c2473", 3),
]

BRANDS = [
    ("Ford", "ford", "f127beae-92cf-49df-a02f-dc05ee0e723c"),
    ("Chery", "chery", "ba944b66-3743-4f63-a9ea-f23ff592f154"),
    ("Kia", "kia", "1879b6ed-0850-44b7-8581-03ed59888d52"),
]

MODELS = [
    (
        "Ford",
        "Territory",
        "territory",
        "35ed1d71-a709-4546-b74e-2a9bbf3d9338",
        "f127beae-92cf-49df-a02f-dc05ee0e723c",
    ),
    (
        "Chery",
        "Tiggo 7 CSH",
        "tiggo-7-csh",
        "7a86fa15-64d7-4fc4-b8d6-749997fb6ad2",
        "ba944b66-3743-4f63-a9ea-f23ff592f154",
    ),
    (
        "Toyota",
        "Corolla Cross",
        "corolla-cross",
        "b19dbd88-659e-432a-b1e4-1984d0fe5a0f",
        "3c76b714-16a6-48eb-af91-f10064edfbab",
    ),
    (
        "Kia",
        "Sportage",
        "sportage",
        "64e6711a-2fef-436b-b448-87be2e265121",
        "1879b6ed-0850-44b7-8581-03ed59888d52",
    ),
]


def upgrade() -> None:
    op.alter_column(
        "vehicle_versions",
        "safety_score",
        existing_type=sa.Numeric(5, 2),
        nullable=True,
    )
    cities = sa.table(
        "cities",
        sa.column("id", sa.Uuid()),
        sa.column("country_code", sa.String()),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
    )
    brands = sa.table(
        "vehicle_brands",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("slug", sa.String()),
        sa.column("active", sa.Boolean()),
    )
    models = sa.table(
        "vehicle_models",
        sa.column("id", sa.Uuid()),
        sa.column("brand_id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("slug", sa.String()),
        sa.column("body_style", sa.String()),
    )
    op.bulk_insert(
        cities,
        [
            {"id": UUID(city_id), "country_code": "CO", "code": code, "name": name}
            for code, name, city_id, _ in CITIES
        ],
    )
    op.bulk_insert(
        brands,
        [
            {"id": UUID(brand_id), "name": name, "slug": slug, "active": True}
            for name, slug, brand_id in BRANDS
        ],
    )
    op.bulk_insert(
        models,
        [
            {
                "id": UUID(model_id),
                "brand_id": UUID(brand_id),
                "name": name,
                "slug": slug,
                "body_style": "suv",
            }
            for _, name, slug, model_id, brand_id in MODELS
        ],
    )
    _insert_vehicles()
    _insert_city_context()


def _insert_vehicles() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO vehicle_versions (
                id, model_id, trim, model_year, powertrain, seats,
                safety_score, warranty_months, list_price, currency_code, attributes
            ) VALUES
            (
                '374c54e0-6ee4-4ecf-b60b-aeb79e00726a',
                '35ed1d71-a709-4546-b74e-2a9bbf3d9338',
                'Trend 1.5L FHEV AT', 2026, 'hybrid', 5,
                NULL, 36, 139990000, 'COP',
                '{"market_as_of":"2026-07-25",
                  "source_url":"https://www.ford.com.co/suvs/territory/comparar-modelos/",
                  "technical_source_url":"https://www.ford.com.co/content/dam/Ford/website-assets/latam/co/nameplate/territory/2026/pdf/fco-ficha-tecnica-territory.pdf",
                  "safety_status":"no_equivalent_independent_ncap_result"}'::json
            ),
            (
                '13b70358-85ea-401b-b8fd-bbb5990d08dc',
                '7a86fa15-64d7-4fc4-b8d6-749997fb6ad2',
                'Super Hybrid CSH', 2026, 'plug_in_hybrid', 5,
                82, 96, 129990000, 'COP',
                '{"market_as_of":"2026-07-25",
                  "source_url":"https://www.chery.com.co/chery-tiggo-7-super-hibrida-csh/",
                  "safety_source_url":"https://www.euroncap.com/assessments/chery/tiggo%2B7/1222ra/",
                  "safety_metric":"adult_occupant_percentage"}'::json
            ),
            (
                'e559e39a-cf4a-44e3-852d-22edc122a3f9',
                'b19dbd88-659e-432a-b1e4-1984d0fe5a0f',
                'SEG 1.8 HEV 4x2 E-CVT', 2026, 'hybrid', 5,
                NULL, 60, 155200000, 'COP',
                '{"market_as_of":"2026-07-25",
                  "source_url":"https://www.toyota.com.co/vehiculos/hibridos/corolla-cross/version/seg-1-8-hev",
                  "safety_source_url":"https://www.euroncap.com/assessments/toyota/corolla%20cross/0994/",
                  "safety_status":"tested_powertrain_differs_from_colombian_version"}'::json
            ),
            (
                '2a6215ee-c962-4358-afd4-eaeb4fde5455',
                '64e6711a-2fef-436b-b448-87be2e265121',
                'Vibrant 1.6 Turbo HEV', 2027, 'hybrid', 5,
                90, 84, 149990000, 'COP',
                '{"market_as_of":"2026-07-25",
                  "source_url":"https://kia.com.co/nuestros-vehiculos/suv-sportage/especificaciones/vibrant-h%C3%ADbrida",
                  "safety_source_url":"https://www.latinncap.com/es/resultado/209/kia-sportage-%2B-6-airbags",
                  "safety_metric":"adult_occupant_percentage"}'::json
            )
            """
        )
    )


def _insert_city_context() -> None:
    for code, _, city_id, charging_points in CITIES:
        restriction_id = UUID(int=UUID(city_id).int ^ 0x11111111111111111111111111111111)
        infrastructure_id = UUID(int=UUID(city_id).int ^ 0x22222222222222222222222222222222)
        periods = (
            (date(2026, 2, 2), date(2026, 7, 31), MOBILITY_SOURCE, 0),
            (date(2026, 8, 1), date(2026, 12, 31), MOBILITY_SOURCE_SECOND_HALF, 1),
        )
        powertrains = (("hybrid", "híbridos", 0), ("plug_in_hybrid", "PHEV", 1))
        for effective_from, effective_to, source, period_index in periods:
            for powertrain, label, powertrain_index in powertrains:
                rule_id = UUID(
                    int=restriction_id.int
                    ^ ((period_index * 2 + powertrain_index) << 64)
                )
                op.execute(
                    sa.text(
                        """
                        INSERT INTO mobility_restrictions (
                            id, city_id, name, powertrain, restricted_days_per_month,
                            exemption, conditions, effective_from, effective_to,
                            source_url
                        ) VALUES (
                            :id, :city_id, :name, :powertrain, 0, true,
                            '{"runt_registration_required":"true"}'::json,
                            :effective_from, :effective_to, :source
                        )
                        """
                    ).bindparams(
                        id=rule_id,
                        city_id=UUID(city_id),
                        name=f"Exención metropolitana 2026 para {label} · {code}",
                        powertrain=powertrain,
                        effective_from=effective_from,
                        effective_to=effective_to,
                        source=source,
                    )
                )
        op.execute(
            sa.text(
                """
                INSERT INTO infrastructure_snapshots (
                    id, city_id, as_of, public_charging_points,
                    authorized_workshops, dealerships, source_url
                ) VALUES (:id, :city_id, '2025-07-29', :points, 0, 0, :source)
                """
            ).bindparams(
                id=infrastructure_id,
                city_id=UUID(city_id),
                points=charging_points,
                source=INFRA_SOURCE,
            )
        )


def downgrade() -> None:
    city_ids = [UUID(city_id) for _, _, city_id, _ in CITIES]
    model_ids = [UUID(model_id) for _, _, _, model_id, _ in MODELS]
    brand_ids = [UUID(brand_id) for _, _, brand_id in BRANDS]
    op.execute(
        sa.text("DELETE FROM infrastructure_snapshots WHERE city_id IN :ids").bindparams(
            sa.bindparam("ids", expanding=True, value=city_ids)
        )
    )
    op.execute(
        sa.text("DELETE FROM mobility_restrictions WHERE city_id IN :ids").bindparams(
            sa.bindparam("ids", expanding=True, value=city_ids)
        )
    )
    op.execute(
        sa.text("DELETE FROM vehicle_versions WHERE model_id IN :ids").bindparams(
            sa.bindparam("ids", expanding=True, value=model_ids)
        )
    )
    op.execute(
        sa.text("DELETE FROM vehicle_models WHERE id IN :ids").bindparams(
            sa.bindparam("ids", expanding=True, value=model_ids)
        )
    )
    op.execute(
        sa.text("DELETE FROM vehicle_brands WHERE id IN :ids").bindparams(
            sa.bindparam("ids", expanding=True, value=brand_ids)
        )
    )
    op.execute(
        sa.text("DELETE FROM cities WHERE id IN :ids").bindparams(
            sa.bindparam("ids", expanding=True, value=city_ids)
        )
    )
    op.alter_column(
        "vehicle_versions",
        "safety_score",
        existing_type=sa.Numeric(5, 2),
        nullable=False,
    )
