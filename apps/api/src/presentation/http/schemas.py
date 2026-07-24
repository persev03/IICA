"""Esquemas Pydantic: frontera explícita entre HTTP y aplicación."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


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


class CreateCityRequest(BaseModel):
    country_code: str = Field(default="CO", min_length=2, max_length=2)
    code: str = Field(pattern=r"^[a-z0-9-]+$", min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=150)


class CreateVehicleRequest(BaseModel):
    brand_slug: str = Field(pattern=r"^[a-z0-9-]+$")
    model_name: str = Field(min_length=1, max_length=120)
    model_slug: str = Field(pattern=r"^[a-z0-9-]+$")
    body_style: str = Field(min_length=1, max_length=48)
    trim: str = Field(min_length=1, max_length=120)
    model_year: int = Field(ge=1886, le=2100)
    powertrain: str
    seats: int = Field(ge=1, le=100)
    safety_score: Decimal = Field(ge=0, le=100)
    warranty_months: int = Field(ge=0, le=240)
    list_price: Decimal = Field(gt=0)
    currency_code: str = Field(default="COP", min_length=3, max_length=3)
    market_as_of: date
    expected_annual_depreciation_percentage: Decimal | None = Field(
        default=None, ge=0, le=100
    )
    liquidity_score: Decimal | None = Field(default=None, ge=0, le=100)
    owner_satisfaction_score: Decimal | None = Field(default=None, ge=0, le=100)
    source_url: AnyHttpUrl


class CreateMobilityRestrictionRequest(BaseModel):
    city_code: str
    name: str = Field(min_length=1, max_length=160)
    powertrain: str | None = None
    restricted_days_per_month: int = Field(ge=0, le=31)
    exemption: bool = False
    effective_from: date
    effective_to: date | None = None
    source_url: AnyHttpUrl


class CreateInfrastructureSnapshotRequest(BaseModel):
    city_code: str
    as_of: date
    public_charging_points: int = Field(ge=0)
    authorized_workshops: int = Field(ge=0)
    dealerships: int = Field(ge=0)
    source_url: AnyHttpUrl


class CreateTaxRuleRequest(BaseModel):
    country_code: str = Field(default="CO", min_length=2, max_length=2)
    city_code: str | None = None
    name: str = Field(min_length=1, max_length=160)
    tax_kind: str = Field(min_length=1, max_length=48)
    rate_percentage: Decimal = Field(ge=0, le=100)
    effective_from: date
    effective_to: date | None = None
    source_url: AnyHttpUrl


class AdminRecordResponse(BaseModel):
    id: UUID
    status: str = "created"


class TaxRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    country_code: str
    city_id: UUID | None
    tax_kind: str
    rate_percentage: Decimal
    effective_from: str
    effective_to: str | None
    source_url: str


class EvaluationRequest(BaseModel):
    city_code: str = Field(min_length=1, max_length=64)
    budget: Decimal = Field(gt=0)
    annual_kilometers: int = Field(ge=0, le=200_000)
    ownership_years: int = Field(default=5, ge=1, le=30)
    primary_use: str
    household_size: int = Field(default=1, ge=1, le=20)
    frequent_road_trips: bool = False
    charging_access: str = "none"
    vehicle_ids: list[UUID] = Field(min_length=1, max_length=2)


class EvaluationInfluenceResponse(BaseModel):
    key: str
    direction: int
    summary: str


class EvaluatedVehicleResponse(BaseModel):
    id: UUID
    name: str
    score: Decimal
    classification: str
    strengths: list[str]
    weaknesses: list[str]
    influences: list[EvaluationInfluenceResponse]
    recommendations: list[str]
    engine_version: str
    data_version: str


class EvaluationResponse(BaseModel):
    city: str
    evaluated_at: str
    results: list[EvaluatedVehicleResponse]
