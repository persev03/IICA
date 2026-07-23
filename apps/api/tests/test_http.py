"""Pruebas de contrato que no requieren PostgreSQL."""

from os import environ
from unittest import TestCase

from fastapi.testclient import TestClient

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
