"""Endpoints de consulta para catálogo y territorio IICA."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from infrastructure.persistence.models import (
    City,
    Country,
    TaxRule,
    VehicleBrand,
    VehicleModel,
    VehicleVersion,
)
from presentation.http.dependencies import DatabaseSession, require_admin_api_key
from presentation.http.schemas import (
    BrandResponse,
    CityResponse,
    CountryResponse,
    CreateBrandRequest,
    TaxRuleResponse,
    VehicleDetailResponse,
    VehicleSummaryResponse,
)

router = APIRouter(prefix="/v1", tags=["catalog"])


@router.get("/vehicle-brands", response_model=list[BrandResponse])
def list_vehicle_brands(session: DatabaseSession) -> list[VehicleBrand]:
    """Lista las marcas activas disponibles en el catálogo."""

    return list(session.scalars(select(VehicleBrand).order_by(VehicleBrand.name)))


@router.get("/tax-rules", response_model=list[TaxRuleResponse], tags=["rules"])
def list_tax_rules(session: DatabaseSession, country_code: str = "CO") -> list[TaxRule]:
    """Expone reglas tributarias vigentes para auditoría de la recomendación."""

    return list(
        session.scalars(
            select(TaxRule)
            .where(TaxRule.country_code == country_code.upper())
            .order_by(TaxRule.effective_from.desc())
        )
    )


@router.get("/countries", response_model=list[CountryResponse])
def list_countries(session: DatabaseSession) -> list[Country]:
    """Lista los países disponibles para construir un perfil IICA."""

    return list(session.scalars(select(Country).order_by(Country.name)))


@router.get("/countries/{country_code}/cities", response_model=list[CityResponse])
def list_cities(country_code: str, session: DatabaseSession) -> list[City]:
    """Lista ciudades configuradas para un país."""

    statement = (
        select(City)
        .where(City.country_code == country_code.upper())
        .order_by(City.name)
    )
    return list(session.scalars(statement))


@router.get("/vehicles", response_model=list[VehicleSummaryResponse])
def list_vehicles(
    session: DatabaseSession,
    limit: int = Query(default=20, ge=1, le=100),
    powertrain: str | None = Query(default=None),
) -> list[VehicleSummaryResponse]:
    """Lista versiones de vehículo comparables, con filtros acotados."""

    statement = (
        select(VehicleVersion, VehicleBrand.name, VehicleModel.name)
        .join(VehicleModel, VehicleVersion.model_id == VehicleModel.id)
        .join(VehicleBrand, VehicleModel.brand_id == VehicleBrand.id)
        .where(VehicleBrand.active.is_(True))
        .order_by(
            VehicleBrand.name, VehicleModel.name, VehicleVersion.model_year.desc()
        )
        .limit(limit)
    )
    if powertrain:
        statement = statement.where(VehicleVersion.powertrain == powertrain)

    return [
        VehicleSummaryResponse(
            id=version.id,
            brand=brand_name,
            model=model_name,
            trim=version.trim,
            model_year=version.model_year,
            powertrain=version.powertrain,
            list_price=version.list_price,
            currency_code=version.currency_code,
            safety_score=version.safety_score,
        )
        for version, brand_name, model_name in session.execute(statement)
    ]


@router.get("/vehicles/{vehicle_id}", response_model=VehicleDetailResponse)
def get_vehicle(vehicle_id: UUID, session: DatabaseSession) -> VehicleDetailResponse:
    """Obtiene la ficha normalizada de una versión concreta."""

    statement = (
        select(VehicleVersion, VehicleBrand.name, VehicleModel.name)
        .join(VehicleModel, VehicleVersion.model_id == VehicleModel.id)
        .join(VehicleBrand, VehicleModel.brand_id == VehicleBrand.id)
        .where(VehicleVersion.id == vehicle_id, VehicleBrand.active.is_(True))
    )
    row = session.execute(statement).one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado.",
        )

    version, brand_name, model_name = row
    return VehicleDetailResponse(
        id=version.id,
        brand=brand_name,
        model=model_name,
        trim=version.trim,
        model_year=version.model_year,
        powertrain=version.powertrain,
        list_price=version.list_price,
        currency_code=version.currency_code,
        safety_score=version.safety_score,
        seats=version.seats,
        warranty_months=version.warranty_months,
        attributes=version.attributes,
    )


@router.post(
    "/admin/vehicle-brands",
    response_model=BrandResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin_api_key)],
    tags=["admin"],
)
def create_vehicle_brand(
    payload: CreateBrandRequest, session: DatabaseSession
) -> VehicleBrand:
    """Crea una marca; la autorización final será delegada a Auth.js."""

    duplicate = session.scalar(
        select(VehicleBrand).where(VehicleBrand.slug == payload.slug)
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una marca con ese slug.",
        )

    brand = VehicleBrand(name=payload.name.strip(), slug=payload.slug)
    session.add(brand)
    session.commit()
    session.refresh(brand)
    return brand
