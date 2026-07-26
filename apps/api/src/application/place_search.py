"""Búsqueda acotada de lugares mediante un proveedor Nominatim compatible."""

from __future__ import annotations

import asyncio
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from os import getenv
from time import monotonic
from typing import Any

import httpx

DEFAULT_GEOCODER_URL = "https://nominatim.openstreetmap.org/search"
DEFAULT_USER_AGENT = (
    "IICA/0.1 "
    "(https://github.com/persev03/IICA; https://persev03.github.io/IICA/)"
)
DEFAULT_REFERER = "https://persev03.github.io/IICA/"


class PlaceSearchUnavailable(RuntimeError):
    """Indica que el proveedor de geocodificación no pudo responder."""


@dataclass(frozen=True, slots=True)
class PlaceCandidate:
    """Lugar normalizado que la interfaz puede mostrar y seleccionar."""

    id: str
    name: str
    display_name: str
    latitude: float
    longitude: float
    category: str


@dataclass(frozen=True, slots=True)
class _CacheEntry:
    expires_at: float
    candidates: tuple[PlaceCandidate, ...]


class NominatimPlaceSearch:
    """Cliente Nominatim con cache y un máximo global de una consulta por segundo."""

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        user_agent: str | None = None,
        cache_ttl_seconds: float = 86_400,
        cache_max_entries: int = 256,
        min_interval_seconds: float = 1.05,
        transport: httpx.AsyncBaseTransport | None = None,
        clock: Callable[[], float] = monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._endpoint = (
            endpoint
            or getenv("IICA_GEOCODER_URL")
            or DEFAULT_GEOCODER_URL
        )
        self._user_agent = (
            user_agent
            or getenv("IICA_GEOCODER_USER_AGENT")
            or DEFAULT_USER_AGENT
        )
        self._cache_ttl_seconds = cache_ttl_seconds
        self._cache_max_entries = cache_max_entries
        self._min_interval_seconds = min_interval_seconds
        self._transport = transport
        self._clock = clock
        self._sleep = sleep
        self._cache: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._upstream_lock = asyncio.Lock()
        self._last_upstream_started: float | None = None

    async def search(
        self, *, query: str, city_name: str
    ) -> list[PlaceCandidate]:
        """Busca lugares solo a partir de una solicitud explícita del usuario."""

        normalized_query = " ".join(query.split())
        normalized_city = " ".join(city_name.split())
        cache_key = f"{normalized_query.casefold()}::{normalized_city.casefold()}"
        cached = self._cached(cache_key)
        if cached is not None:
            return list(cached)

        async with self._upstream_lock:
            cached = self._cached(cache_key)
            if cached is not None:
                return list(cached)

            await self._respect_rate_limit()
            candidates = await self._request_upstream(
                query=normalized_query,
                city_name=normalized_city,
            )
            self._remember(cache_key, candidates)
            return list(candidates)

    def _cached(self, cache_key: str) -> tuple[PlaceCandidate, ...] | None:
        entry = self._cache.get(cache_key)
        if entry is None:
            return None
        if entry.expires_at <= self._clock():
            del self._cache[cache_key]
            return None
        self._cache.move_to_end(cache_key)
        return entry.candidates

    def _remember(
        self, cache_key: str, candidates: list[PlaceCandidate]
    ) -> None:
        self._cache[cache_key] = _CacheEntry(
            expires_at=self._clock() + self._cache_ttl_seconds,
            candidates=tuple(candidates),
        )
        self._cache.move_to_end(cache_key)
        while len(self._cache) > self._cache_max_entries:
            self._cache.popitem(last=False)

    async def _respect_rate_limit(self) -> None:
        now = self._clock()
        if self._last_upstream_started is not None:
            elapsed = now - self._last_upstream_started
            remaining = self._min_interval_seconds - elapsed
            if remaining > 0:
                await self._sleep(remaining)
        self._last_upstream_started = self._clock()

    async def _request_upstream(
        self, *, query: str, city_name: str
    ) -> list[PlaceCandidate]:
        headers = {
            "Accept": "application/json",
            "Accept-Language": "es",
            "Referer": DEFAULT_REFERER,
            "User-Agent": self._user_agent,
        }
        params = {
            "q": f"{query}, {city_name}, Colombia",
            "format": "jsonv2",
            "addressdetails": "1",
            "countrycodes": "co",
            "limit": "5",
        }
        try:
            async with httpx.AsyncClient(
                headers=headers,
                timeout=httpx.Timeout(8.0),
                transport=self._transport,
            ) as client:
                response = await client.get(self._endpoint, params=params)
                response.raise_for_status()
                payload: Any = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise PlaceSearchUnavailable(
                "El buscador de lugares no está disponible en este momento."
            ) from error

        if not isinstance(payload, list):
            raise PlaceSearchUnavailable(
                "El buscador de lugares devolvió una respuesta inesperada."
            )
        return self._normalize_candidates(payload)

    @staticmethod
    def _normalize_candidates(payload: list[Any]) -> list[PlaceCandidate]:
        candidates: list[PlaceCandidate] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            try:
                latitude = float(item["lat"])
                longitude = float(item["lon"])
            except (KeyError, TypeError, ValueError):
                continue

            display_name = str(item.get("display_name", "")).strip()
            if not display_name:
                continue
            raw_name = str(item.get("name", "")).strip()
            name = raw_name or display_name.split(",", maxsplit=1)[0].strip()
            raw_category = item.get("type") or item.get("category") or "place"
            category = str(raw_category).strip() or "place"
            raw_id = item.get("place_id") or f"{latitude:.7f},{longitude:.7f}"
            candidates.append(
                PlaceCandidate(
                    id=str(raw_id),
                    name=name,
                    display_name=display_name,
                    latitude=latitude,
                    longitude=longitude,
                    category=category,
                )
            )
        return candidates
