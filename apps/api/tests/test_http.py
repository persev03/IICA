"""Pruebas de contrato que no requieren PostgreSQL."""

from os import environ
from unittest import TestCase

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from infrastructure.persistence.models import Base, Country
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
