"""Pruebas del proxy de búsqueda manual de lugares."""

from __future__ import annotations

from unittest import IsolatedAsyncioTestCase, TestCase

import httpx
from fastapi.testclient import TestClient

from application.place_search import (
    NominatimPlaceSearch,
    PlaceCandidate,
    PlaceSearchUnavailable,
)
from presentation.http.main import app
from presentation.http.routers.places import get_place_search


class NominatimPlaceSearchTests(IsolatedAsyncioTestCase):
    async def test_finds_a_verified_local_place_missing_from_osm(self) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(200, json=[])

        search = NominatimPlaceSearch(
            endpoint="https://geocoder.example/search",
            transport=httpx.MockTransport(handler),
        )

        candidates = await search.search(
            query="Edificio SKY72",
            city_name="Medellín",
        )

        self.assertEqual(len(requests), 0)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].name, "Sky 72")
        self.assertEqual(candidates[0].latitude, 6.226866)
        self.assertEqual(candidates[0].longitude, -75.557377)
        self.assertIn("Carrera 28 #29-82", candidates[0].display_name)

    async def test_identifies_iica_and_caches_a_manual_search(self) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(
                200,
                json=[
                    {
                        "place_id": 123,
                        "name": "Parque de los Deseos",
                        "display_name": "Parque de los Deseos, Medellín, Colombia",
                        "lat": "6.2686",
                        "lon": "-75.5655",
                        "type": "park",
                    }
                ],
            )

        search = NominatimPlaceSearch(
            endpoint="https://geocoder.example/search",
            user_agent="IICA-test/1.0 (https://example.com/contact)",
            transport=httpx.MockTransport(handler),
        )

        first = await search.search(
            query="Parque de los Deseos",
            city_name="Medellín",
        )
        second = await search.search(
            query="  Parque de los Deseos ",
            city_name=" medellín ",
        )

        self.assertEqual(first, second)
        self.assertEqual(len(requests), 1)
        self.assertEqual(
            requests[0].headers["user-agent"],
            "IICA-test/1.0 (https://example.com/contact)",
        )
        self.assertEqual(
            requests[0].headers["referer"], "https://persev03.github.io/IICA/"
        )
        self.assertEqual(requests[0].url.params["format"], "jsonv2")
        self.assertEqual(requests[0].url.params["countrycodes"], "co")
        self.assertEqual(requests[0].url.params["limit"], "5")
        self.assertEqual(
            requests[0].url.params["q"],
            "Parque de los Deseos, Medellín, Colombia",
        )

    async def test_spaces_different_upstream_requests_by_at_least_1_05_seconds(
        self,
    ) -> None:
        requests: list[httpx.Request] = []
        now = [100.0]
        sleeps: list[float] = []

        def clock() -> float:
            return now[0]

        async def sleep(delay: float) -> None:
            sleeps.append(delay)
            now[0] += delay

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(200, json=[])

        search = NominatimPlaceSearch(
            endpoint="https://geocoder.example/search",
            transport=httpx.MockTransport(handler),
            clock=clock,
            sleep=sleep,
        )

        await search.search(query="Universidad", city_name="Medellín")
        await search.search(query="Hospital", city_name="Medellín")

        self.assertEqual(len(requests), 2)
        self.assertEqual(len(sleeps), 1)
        self.assertGreaterEqual(sleeps[0], 1.05)

    async def test_rejects_an_invalid_upstream_response(self) -> None:
        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"unexpected": True})

        search = NominatimPlaceSearch(
            endpoint="https://geocoder.example/search",
            transport=httpx.MockTransport(handler),
        )

        with self.assertRaisesRegex(
            PlaceSearchUnavailable,
            "respuesta inesperada",
        ):
            await search.search(query="Biblioteca", city_name="Medellín")


class _SuccessfulPlaceSearch:
    async def search(self, *, query: str, city_name: str) -> list[PlaceCandidate]:
        return [
            PlaceCandidate(
                id="456",
                name=query,
                display_name=f"{query}, {city_name}, Colombia",
                latitude=6.2442,
                longitude=-75.5812,
                category="amenity",
            )
        ]


class _UnavailablePlaceSearch:
    async def search(self, *, query: str, city_name: str) -> list[PlaceCandidate]:
        raise PlaceSearchUnavailable("Proveedor temporalmente no disponible.")


class PlaceSearchEndpointTests(TestCase):
    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_returns_the_public_place_contract(self) -> None:
        app.dependency_overrides[get_place_search] = _SuccessfulPlaceSearch
        client = TestClient(app)

        response = client.post(
            "/v1/places/search",
            json={"query": "Museo de Antioquia", "city_name": "Medellín"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {
                    "id": "456",
                    "name": "Museo de Antioquia",
                    "display_name": "Museo de Antioquia, Medellín, Colombia",
                    "latitude": 6.2442,
                    "longitude": -75.5812,
                    "category": "amenity",
                }
            ],
        )

    def test_exposes_a_clear_gateway_error(self) -> None:
        app.dependency_overrides[get_place_search] = _UnavailablePlaceSearch
        client = TestClient(app)

        response = client.post(
            "/v1/places/search",
            json={"query": "Museo de Antioquia", "city_name": "Medellín"},
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json(),
            {"detail": "Proveedor temporalmente no disponible."},
        )

    def test_rejects_blank_or_too_short_searches_without_calling_upstream(
        self,
    ) -> None:
        app.dependency_overrides[get_place_search] = _SuccessfulPlaceSearch
        client = TestClient(app)

        response = client.post(
            "/v1/places/search",
            json={"query": "   ", "city_name": "Medellín"},
        )

        self.assertEqual(response.status_code, 422)
