"""Mapeos de persistencia del catálogo y reglas locales IICA."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, JSON, Numeric, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base declarativa de todos los modelos que pertenecen a PostgreSQL."""


class Timestamped:
    """Auditoría mínima para datos editables desde administración."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Country(Timestamped, Base):
    __tablename__ = "countries"

    code: Mapped[str] = mapped_column(String(2), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)


class Region(Timestamped, Base):
    __tablename__ = "regions"
    __table_args__ = (UniqueConstraint("country_code", "code"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    country_code: Mapped[str] = mapped_column(ForeignKey("countries.code", ondelete="RESTRICT"), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)


class City(Timestamped, Base):
    __tablename__ = "cities"
    __table_args__ = (UniqueConstraint("country_code", "code"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    country_code: Mapped[str] = mapped_column(ForeignKey("countries.code", ondelete="RESTRICT"), nullable=False)
    region_id: Mapped[UUID | None] = mapped_column(ForeignKey("regions.id", ondelete="RESTRICT"), nullable=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)


class VehicleBrand(Timestamped, Base):
    __tablename__ = "vehicle_brands"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(140), unique=True, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class VehicleModel(Timestamped, Base):
    __tablename__ = "vehicle_models"
    __table_args__ = (UniqueConstraint("brand_id", "slug"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    brand_id: Mapped[UUID] = mapped_column(ForeignKey("vehicle_brands.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), nullable=False)
    body_style: Mapped[str] = mapped_column(String(48), nullable=False)


class VehicleVersion(Timestamped, Base):
    __tablename__ = "vehicle_versions"
    __table_args__ = (
        UniqueConstraint("model_id", "model_year", "trim"),
        CheckConstraint("model_year >= 1886", name="vehicle_version_model_year_valid"),
        CheckConstraint("seats >= 1", name="vehicle_version_seats_valid"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    model_id: Mapped[UUID] = mapped_column(ForeignKey("vehicle_models.id", ondelete="RESTRICT"), nullable=False)
    trim: Mapped[str] = mapped_column(String(120), nullable=False)
    model_year: Mapped[int] = mapped_column(nullable=False)
    powertrain: Mapped[str] = mapped_column(String(32), nullable=False)
    seats: Mapped[int] = mapped_column(nullable=False)
    safety_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    warranty_months: Mapped[int] = mapped_column(nullable=False)
    list_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    attributes: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)


class TaxRule(Timestamped, Base):
    __tablename__ = "tax_rules"
    __table_args__ = (CheckConstraint("rate_percentage >= 0", name="tax_rule_rate_non_negative"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    country_code: Mapped[str] = mapped_column(ForeignKey("countries.code", ondelete="RESTRICT"), nullable=False)
    city_id: Mapped[UUID | None] = mapped_column(ForeignKey("cities.id", ondelete="RESTRICT"), nullable=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    tax_kind: Mapped[str] = mapped_column(String(48), nullable=False)
    rate_percentage: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    conditions: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)


class Incentive(Timestamped, Base):
    __tablename__ = "incentives"
    __table_args__ = (CheckConstraint("amount >= 0", name="incentive_amount_non_negative"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    country_code: Mapped[str] = mapped_column(ForeignKey("countries.code", ondelete="RESTRICT"), nullable=False)
    city_id: Mapped[UUID | None] = mapped_column(ForeignKey("cities.id", ondelete="RESTRICT"), nullable=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    incentive_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    powertrain: Mapped[str | None] = mapped_column(String(32), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    conditions: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)


class MobilityRestriction(Timestamped, Base):
    __tablename__ = "mobility_restrictions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    city_id: Mapped[UUID] = mapped_column(ForeignKey("cities.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    powertrain: Mapped[str | None] = mapped_column(String(32), nullable=True)
    restricted_days_per_month: Mapped[int] = mapped_column(nullable=False)
    exemption: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    conditions: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)


class InfrastructureSnapshot(Timestamped, Base):
    __tablename__ = "infrastructure_snapshots"
    __table_args__ = (UniqueConstraint("city_id", "as_of", "source_url"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    city_id: Mapped[UUID] = mapped_column(ForeignKey("cities.id", ondelete="RESTRICT"), nullable=False)
    as_of: Mapped[date] = mapped_column(Date, nullable=False)
    public_charging_points: Mapped[int] = mapped_column(nullable=False)
    authorized_workshops: Mapped[int] = mapped_column(nullable=False)
    dealerships: Mapped[int] = mapped_column(nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
