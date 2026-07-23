"""Esquemas Pydantic: frontera explícita entre HTTP y aplicación."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CountryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str = Field(min_length=2, max_length=2)
    name: str
    currency_code: str = Field(min_length=3, max_length=3)


class CityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    country_code: str
    code: str
    name: str


class VehicleSummaryResponse(BaseModel):
    id: UUID
    brand: str
    model: str
    trim: str
    model_year: int
    powertrain: str
    list_price: Decimal
    currency_code: str
    safety_score: Decimal


class VehicleDetailResponse(VehicleSummaryResponse):
    seats: int
    warranty_months: int
    attributes: dict[str, object]


class CreateBrandRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str = Field(pattern=r"^[a-z0-9-]+$", min_length=1, max_length=140)


class BrandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    active: bool
