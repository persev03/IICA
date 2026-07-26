"""Proxy público y acotado para búsquedas manuales de lugares."""

from __future__ import annotations

from typing import Annotated, Protocol

from fastapi import APIRouter, Depends, HTTPException, status

from application.place_search import (
    NominatimPlaceSearch,
    PlaceCandidate,
    PlaceSearchUnavailable,
)
from presentation.http.schemas import PlaceSearchRequest, PlaceSearchResponse

router = APIRouter(prefix="/v1/places", tags=["places"])


class PlaceSearchService(Protocol):
    """Contrato mínimo para desacoplar el endpoint del proveedor concreto."""

    async def search(
        self, *, query: str, city_name: str
    ) -> list[PlaceCandidate]: ...


_place_search = NominatimPlaceSearch()


def get_place_search() -> PlaceSearchService:
    """Entrega el cliente compartido que aplica cache y límite global."""

    return _place_search


@router.post("/search", response_model=list[PlaceSearchResponse])
async def search_places(
    payload: PlaceSearchRequest,
    service: Annotated[PlaceSearchService, Depends(get_place_search)],
) -> list[PlaceSearchResponse]:
    """Busca hasta cinco coincidencias tras el envío explícito del formulario."""

    try:
        candidates = await service.search(
            query=payload.query,
            city_name=payload.city_name,
        )
    except PlaceSearchUnavailable as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    return [
        PlaceSearchResponse(
            id=candidate.id,
            name=candidate.name,
            display_name=candidate.display_name,
            latitude=candidate.latitude,
            longitude=candidate.longitude,
            category=candidate.category,
        )
        for candidate in candidates
    ]
