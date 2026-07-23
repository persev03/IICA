"""Modelo de dominio del IICA.

Este módulo no conoce HTTP, bases de datos ni librerías de validación. Sus
objetos inmutables representan las entradas y la salida explicable del motor.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum


class VehicleUse(str, Enum):
    """Uso principal declarado por quien compra el vehículo."""

    URBAN = "urban"
    MIXED = "mixed"
    ROAD_TRIPS = "road_trips"
    WORK = "work"
    FAMILY = "family"


class Powertrain(str, Enum):
    """Tecnología de propulsión relevante para costos y restricciones."""

    GASOLINE = "gasoline"
    DIESEL = "diesel"
    HYBRID = "hybrid"
    PLUG_IN_HYBRID = "plug_in_hybrid"
    ELECTRIC = "electric"


class ChargingAccess(str, Enum):
    """Acceso habitual del comprador a carga eléctrica."""

    NONE = "none"
    PUBLIC = "public"
    HOME = "home"
    WORK = "work"


class Classification(str, Enum):
    """Clasificación de compra derivada del único resultado IICA."""

    EXCEPTIONAL = "Compra excepcional"
    EXCELLENT = "Excelente compra"
    VERY_GOOD = "Muy buena compra"
    GOOD = "Buena compra"
    ACCEPTABLE = "Aceptable"
    NOT_RECOMMENDED = "Poco recomendable para este perfil"


@dataclass(frozen=True)
class Money:
    """Importe monetario preciso y no negativo."""

    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        try:
            normalized_amount = Decimal(self.amount)
        except (InvalidOperation, ValueError, TypeError) as error:
            raise ValueError("amount debe ser un valor monetario válido.") from error

        if normalized_amount < 0:
            raise ValueError("amount no puede ser negativo.")
        if len(self.currency) != 3 or not self.currency.isalpha():
            raise ValueError("currency debe ser un código ISO-4217 de tres letras.")

        object.__setattr__(self, "amount", normalized_amount)
        object.__setattr__(self, "currency", self.currency.upper())


@dataclass(frozen=True)
class Score:
    """Puntuación IICA acotada entre 0 y 100."""

    value: Decimal

    def __post_init__(self) -> None:
        try:
            normalized_value = Decimal(self.value)
        except (InvalidOperation, ValueError, TypeError) as error:
            raise ValueError("value debe ser una puntuación válida.") from error

        if not Decimal(0) <= normalized_value <= Decimal(100):
            raise ValueError("La puntuación IICA debe estar entre 0 y 100.")
        object.__setattr__(self, "value", normalized_value.quantize(Decimal("0.01")))

    @property
    def classification(self) -> Classification:
        """Clasificación pública definida por el umbral de la puntuación."""

        if self.value >= 95:
            return Classification.EXCEPTIONAL
        if self.value >= 90:
            return Classification.EXCELLENT
        if self.value >= 80:
            return Classification.VERY_GOOD
        if self.value >= 70:
            return Classification.GOOD
        if self.value >= 60:
            return Classification.ACCEPTABLE
        return Classification.NOT_RECOMMENDED


@dataclass(frozen=True)
class BuyerProfile:
    """Información de la persona que cambia la conveniencia de compra."""

    country_code: str
    city_code: str
    budget: Money
    annual_kilometers: int
    ownership_years: int
    primary_use: VehicleUse
    household_size: int
    frequent_road_trips: bool
    charging_access: ChargingAccess

    def __post_init__(self) -> None:
        if len(self.country_code) != 2 or not self.country_code.isalpha():
            raise ValueError("country_code debe ser ISO-3166 alpha-2.")
        if not self.city_code.strip():
            raise ValueError("city_code es obligatorio.")
        if self.annual_kilometers < 0:
            raise ValueError("annual_kilometers no puede ser negativo.")
        if self.ownership_years < 1:
            raise ValueError("ownership_years debe ser al menos 1.")
        if self.household_size < 1:
            raise ValueError("household_size debe ser al menos 1.")
        object.__setattr__(self, "country_code", self.country_code.upper())
        object.__setattr__(self, "city_code", self.city_code.strip())


@dataclass(frozen=True)
class VehicleProfile:
    """Datos comparables de un vehículo y su versión concreta."""

    vehicle_id: str
    brand: str
    model: str
    trim: str
    model_year: int
    purchase_price: Money
    powertrain: Powertrain
    seats: int
    safety_score: Score
    warranty_months: int

    def __post_init__(self) -> None:
        required_values = {
            "vehicle_id": self.vehicle_id,
            "brand": self.brand,
            "model": self.model,
            "trim": self.trim,
        }
        if any(not value.strip() for value in required_values.values()):
            raise ValueError("vehicle_id, brand, model y trim son obligatorios.")
        if not 1886 <= self.model_year <= 2100:
            raise ValueError("model_year no es válido.")
        if self.seats < 1:
            raise ValueError("seats debe ser al menos 1.")
        if self.warranty_months < 0:
            raise ValueError("warranty_months no puede ser negativo.")


@dataclass(frozen=True)
class EnvironmentProfile:
    """Contexto normativo y de infraestructura vigente y versionado."""

    country_code: str
    city_code: str
    rules_version: str
    effective_on: str
    annual_vehicle_tax: Money
    purchase_incentive: Money
    mobility_restriction_days_per_month: int
    has_electric_exemption: bool
    public_charging_points: int

    def __post_init__(self) -> None:
        if len(self.country_code) != 2 or not self.country_code.isalpha():
            raise ValueError("country_code debe ser ISO-3166 alpha-2.")
        if not self.city_code.strip() or not self.rules_version.strip():
            raise ValueError("city_code y rules_version son obligatorios.")
        if not self.effective_on.strip():
            raise ValueError("effective_on es obligatorio.")
        if self.mobility_restriction_days_per_month < 0:
            raise ValueError("Las restricciones mensuales no pueden ser negativas.")
        if self.public_charging_points < 0:
            raise ValueError("public_charging_points no puede ser negativo.")
        object.__setattr__(self, "country_code", self.country_code.upper())
        object.__setattr__(self, "city_code", self.city_code.strip())


@dataclass(frozen=True)
class MarketProfile:
    """Señales de mercado asociadas a un vehículo, con fecha de corte."""

    as_of: str
    expected_annual_depreciation_percentage: Decimal
    liquidity_score: Score
    owner_satisfaction_score: Score

    def __post_init__(self) -> None:
        try:
            depreciation = Decimal(self.expected_annual_depreciation_percentage)
        except (InvalidOperation, ValueError, TypeError) as error:
            raise ValueError("La depreciación esperada debe ser válida.") from error
        if not Decimal(0) <= depreciation <= Decimal(100):
            raise ValueError("La depreciación anual debe estar entre 0 y 100.")
        if not self.as_of.strip():
            raise ValueError("as_of es obligatorio.")
        object.__setattr__(
            self,
            "expected_annual_depreciation_percentage",
            depreciation.quantize(Decimal("0.01")),
        )


@dataclass(frozen=True)
class EvaluationInput:
    """Entradas completas y reproducibles que acepta el motor IICA."""

    buyer: BuyerProfile
    vehicle: VehicleProfile
    environment: EnvironmentProfile
    market: MarketProfile
    engine_version: str

    def __post_init__(self) -> None:
        if self.buyer.country_code != self.environment.country_code:
            raise ValueError("El país del usuario y el entorno deben coincidir.")
        if self.buyer.city_code != self.environment.city_code:
            raise ValueError("La ciudad del usuario y el entorno deben coincidir.")
        if self.vehicle.purchase_price.currency != self.buyer.budget.currency:
            raise ValueError("El presupuesto y el precio deben usar la misma moneda.")
        if not self.engine_version.strip():
            raise ValueError("engine_version es obligatorio.")


@dataclass(frozen=True)
class Influence:
    """Factor verificable que afectó la puntuación final."""

    key: str
    direction: int
    summary: str

    def __post_init__(self) -> None:
        if not self.key.strip() or not self.summary.strip():
            raise ValueError("key y summary son obligatorios.")
        if self.direction not in {-1, 0, 1}:
            raise ValueError("direction debe ser -1, 0 o 1.")


@dataclass(frozen=True)
class EvaluationExplanation:
    """Explicación pública sin revelar subíndices internos."""

    strengths: Sequence[str]
    weaknesses: Sequence[str]
    influences: Sequence[Influence]
    recommendations: Sequence[str]

    def __post_init__(self) -> None:
        if not self.influences:
            raise ValueError("La explicación debe tener al menos una influencia.")
        entries = (*self.strengths, *self.weaknesses, *self.recommendations)
        if any(not item.strip() for item in entries):
            raise ValueError("La explicación no puede contener textos vacíos.")


@dataclass(frozen=True)
class EvaluationResult:
    """Salida única, explicable y reproducible del motor IICA."""

    score: Score
    explanation: EvaluationExplanation
    engine_version: str
    data_version: str

    def __post_init__(self) -> None:
        if not self.engine_version.strip() or not self.data_version.strip():
            raise ValueError("engine_version y data_version son obligatorios.")

    @property
    def classification(self) -> Classification:
        """Clasificación derivada únicamente de la puntuación IICA."""

        return self.score.classification
