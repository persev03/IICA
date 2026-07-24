"""Pruebas de contrato que no requieren PostgreSQL."""

from datetime import date
from decimal import Decimal
from os import environ
from unittest import TestCase

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from infrastructure.persistence.models import (
    Base,
    City,
    Country,
    InfrastructureSnapshot,
    MobilityRestriction,
    VehicleBrand,
    VehicleModel,
    VehicleVersion,
)
from infrastructure.persistence.session import get_session
from presentation.http.main import app


class HealthEndpointTests(TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_endpoint_is_public(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_admin_mutation_rejects_requests_without_configuration(self) -> None:
        original_value = environ.pop("IICA_ADMIN_API_KEY", None)
        try:
            response = self.client.post(
                "/v1/admin/vehicle-brands",
                json={"name": "Example", "slug": "example"},
            )
        finally:
            if original_value is not None:
                environ["IICA_ADMIN_API_KEY"] = original_value

        self.assertEqual(response.status_code, 503)


class CatalogIntegrationTests(TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(bind=engine)

        with session_factory() as session:
            session.add(Country(code="CO", name="Colombia", currency_code="COP"))
            session.commit()

        def override_session():
            session = session_factory()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_session] = override_session
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_lists_countries_from_the_persistence_adapter(self) -> None:
        response = self.client.get("/v1/countries")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [{"code": "CO", "name": "Colombia", "currency_code": "COP"}],
        )


class EvaluationIntegrationTests(TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(bind=engine)

        with session_factory() as session:
            country = Country(code="CO", name="Colombia", currency_code="COP")
            city = City(country_code="CO", code="bogota", name="Bogotá")
            brand = VehicleBrand(name="Marca verificada", slug="marca-verificada")
            session.add_all([country, city, brand])
            session.flush()
            model = VehicleModel(
                brand_id=brand.id,
                name="Modelo",
                slug="modelo",
                body_style="suv",
            )
            session.add(model)
            session.flush()
            version = VehicleVersion(
                model_id=model.id,
                trim="Versión",
                model_year=2026,
                powertrain="gasoline",
                seats=5,
                safety_score=Decimal(90),
                warranty_months=60,
                list_price=Decimal(90_000_000),
                currency_code="COP",
                attributes={
                    "market_as_of": "2026-07-01",
                    "expected_annual_depreciation_percentage": "10",
                    "liquidity_score": "80",
                    "owner_satisfaction_score": "85",
                },
            )
            session.add_all(
                [
                    version,
                    InfrastructureSnapshot(
                        city_id=city.id,
                        as_of=date(2026, 7, 1),
                        public_charging_points=120,
                        authorized_workshops=20,
                        dealerships=10,
                        source_url="https://example.com/infrastructure",
                    ),
                    MobilityRestriction(
                        city_id=city.id,
                        name="Restricción vigente",
                        powertrain=None,
                        restricted_days_per_month=8,
                        exemption=False,
                        conditions={},
                        effective_from=date(2026, 1, 1),
                        effective_to=None,
                        source_url="https://example.com/mobility",
                    ),
                ]
            )
            session.commit()
            self.vehicle_id = str(version.id)

        def override_session():
            session = session_factory()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_session] = override_session
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_calculates_an_explained_result_from_versioned_data(self) -> None:
        response = self.client.post(
            "/v1/evaluations",
            json={
                "city_code": "bogota",
                "budget": "100000000",
                "annual_kilometers": 12000,
                "ownership_years": 5,
                "primary_use": "mixed",
                "household_size": 3,
                "frequent_road_trips": False,
                "charging_access": "none",
                "vehicle_ids": [self.vehicle_id],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["city"], "Bogotá")
        self.assertEqual(payload["results"][0]["score"], "74.35")
        self.assertEqual(payload["results"][0]["classification"], "Buena compra")
        self.assertTrue(payload["results"][0]["influences"])
