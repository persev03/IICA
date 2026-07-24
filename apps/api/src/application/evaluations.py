"""Construcción de entradas verificadas y ejecución del motor IICA."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from uuid import UUID

from iica_engine import (
    BuyerProfile,
    ChargingAccess,
    DeterministicIicaEngine,
    EnvironmentProfile,
    EvaluationInput,
    MarketProfile,
    Money,
    Powertrain,
    Score,
    VehicleProfile,
    VehicleUse,
)
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from infrastructure.persistence.models import (
    City,
    EvaluationRecord,
    Incentive,
    InfrastructureSnapshot,
    MobilityRestriction,
    TaxRule,
    VehicleBrand,
    VehicleModel,
    VehicleVersion,
)
from presentation.http.schemas import (
    EvaluatedVehicleResponse,
    EvaluationInfluenceResponse,
    EvaluationRequest,
    EvaluationResponse,
)


class EvaluationDataError(ValueError):
    """Indica que aún no existen datos verificables para calcular un IICA."""


def evaluate_vehicles(
    payload: EvaluationRequest,
    session: Session,
    *,
    user_id: str | None = None,
    today: date | None = None,
) -> EvaluationResponse:
    """Evalúa hasta dos versiones usando únicamente registros versionados."""

    evaluation_date = today or datetime.now(UTC).date()
    city = session.scalar(
        select(City).where(City.code == payload.city_code).limit(1)
    )
    if city is None:
        raise EvaluationDataError(
            f"La ciudad '{payload.city_code}' no está disponible en el catálogo."
        )

    infrastructure = session.scalar(
        select(InfrastructureSnapshot)
        .where(
            InfrastructureSnapshot.city_id == city.id,
            InfrastructureSnapshot.as_of <= evaluation_date,
        )
        .order_by(InfrastructureSnapshot.as_of.desc())
        .limit(1)
    )
    if infrastructure is None:
        raise EvaluationDataError(
            f"Falta una medición de infraestructura vigente para {city.name}."
        )

    rows = session.execute(
        select(VehicleVersion, VehicleBrand.name, VehicleModel.name)
        .join(VehicleModel, VehicleVersion.model_id == VehicleModel.id)
        .join(VehicleBrand, VehicleModel.brand_id == VehicleBrand.id)
        .where(
            VehicleVersion.id.in_(payload.vehicle_ids),
            VehicleBrand.active.is_(True),
        )
    ).all()
    rows_by_id = {version.id: (version, brand, model) for version, brand, model in rows}
    missing_ids = [
        str(vehicle_id) for vehicle_id in payload.vehicle_ids if vehicle_id not in rows_by_id
    ]
    if missing_ids:
        raise EvaluationDataError(
            "No se encontraron estas versiones de vehículo: " + ", ".join(missing_ids)
        )

    try:
        primary_use = VehicleUse(payload.primary_use)
        charging_access = ChargingAccess(payload.charging_access)
    except ValueError as error:
        raise EvaluationDataError(
            "El uso principal o el acceso a carga no tienen un valor válido."
        ) from error

    buyer = BuyerProfile(
        country_code=city.country_code,
        city_code=city.code,
        budget=Money(payload.budget, "COP"),
        annual_kilometers=payload.annual_kilometers,
        ownership_years=payload.ownership_years,
        primary_use=primary_use,
        household_size=payload.household_size,
        frequent_road_trips=payload.frequent_road_trips,
        charging_access=charging_access,
    )
    engine = DeterministicIicaEngine()
    results: list[EvaluatedVehicleResponse] = []

    for vehicle_id in payload.vehicle_ids:
        version, brand_name, model_name = rows_by_id[vehicle_id]
        result = _evaluate_one(
            session=session,
            engine=engine,
            buyer=buyer,
            city=city,
            infrastructure=infrastructure,
            version=version,
            brand_name=brand_name,
            model_name=model_name,
            evaluation_date=evaluation_date,
        )
        results.append(result)

    results.sort(key=lambda item: item.score, reverse=True)
    response = EvaluationResponse(
        city=city.name,
        evaluated_at=evaluation_date.isoformat(),
        results=results,
    )
    if user_id:
        session.add(
            EvaluationRecord(
                user_id=user_id,
                city_id=city.id,
                input_snapshot=payload.model_dump(mode="json"),
                result_snapshot=response.model_dump(mode="json"),
                engine_version=engine.VERSION,
                data_version=" | ".join(result.data_version for result in results),
            )
        )
        session.commit()
    return response


def _evaluate_one(
    *,
    session: Session,
    engine: DeterministicIicaEngine,
    buyer: BuyerProfile,
    city: City,
    infrastructure: InfrastructureSnapshot,
    version: VehicleVersion,
    brand_name: str,
    model_name: str,
    evaluation_date: date,
) -> EvaluatedVehicleResponse:
    try:
        powertrain = Powertrain(version.powertrain)
    except ValueError as error:
        raise EvaluationDataError(
            f"La motorización de {brand_name} {model_name} no es compatible con el motor."
        ) from error

    restriction = _active_restriction(
        session, city.id, powertrain.value, evaluation_date
    )
    if restriction is None:
        raise EvaluationDataError(
            f"Falta una regla de movilidad vigente para {brand_name} {model_name} "
            f"en {city.name}."
        )

    market = _market_profile(version, brand_name, model_name)
    tax_rate, tax_version = _active_tax_rate(
        session,
        city,
        powertrain.value,
        version.list_price,
        evaluation_date,
    )
    incentive, incentive_version = _active_incentive(
        session, city, powertrain.value, version.currency_code, evaluation_date
    )
    annual_tax = version.list_price * tax_rate / Decimal(100)

    vehicle = VehicleProfile(
        vehicle_id=str(version.id),
        brand=brand_name,
        model=model_name,
        trim=version.trim,
        model_year=version.model_year,
        purchase_price=Money(version.list_price, version.currency_code),
        powertrain=powertrain,
        seats=version.seats,
        safety_score=Score(version.safety_score),
        warranty_months=version.warranty_months,
    )
    environment = EnvironmentProfile(
        country_code=city.country_code,
        city_code=city.code,
        rules_version=(
            f"mobility:{restriction.id};tax:{tax_version};"
            f"incentive:{incentive_version};infra:{infrastructure.as_of}"
        ),
        effective_on=evaluation_date.isoformat(),
        annual_vehicle_tax=Money(annual_tax, version.currency_code),
        purchase_incentive=Money(incentive, version.currency_code),
        mobility_restriction_days_per_month=restriction.restricted_days_per_month,
        has_electric_exemption=(
            powertrain == Powertrain.ELECTRIC and restriction.exemption
        ),
        public_charging_points=infrastructure.public_charging_points,
    )
    output = engine.evaluate(
        EvaluationInput(
            buyer=buyer,
            vehicle=vehicle,
            environment=environment,
            market=market,
            engine_version=engine.VERSION,
        )
    )

    return EvaluatedVehicleResponse(
        id=version.id,
        name=f"{brand_name} {model_name} {version.trim} {version.model_year}",
        score=output.score.value,
        classification=output.classification.value,
        strengths=list(output.explanation.strengths),
        weaknesses=list(output.explanation.weaknesses),
        influences=[
            EvaluationInfluenceResponse(
                key=influence.key,
                direction=influence.direction,
                summary=influence.summary,
            )
            for influence in output.explanation.influences
        ],
        recommendations=list(output.explanation.recommendations),
        engine_version=output.engine_version,
        data_version=output.data_version,
    )


def _market_profile(
    version: VehicleVersion, brand_name: str, model_name: str
) -> MarketProfile:
    required = {"market_as_of"}
    missing = sorted(required.difference(version.attributes))
    if missing:
        raise EvaluationDataError(
            f"Faltan datos de mercado para {brand_name} {model_name}: "
            + ", ".join(missing)
        )
    try:
        return MarketProfile(
            as_of=str(version.attributes["market_as_of"]),
            expected_annual_depreciation_percentage=(
                Decimal(
                    str(
                        version.attributes[
                            "expected_annual_depreciation_percentage"
                        ]
                    )
                )
                if "expected_annual_depreciation_percentage" in version.attributes
                else None
            ),
            liquidity_score=(
                Score(Decimal(str(version.attributes["liquidity_score"])))
                if "liquidity_score" in version.attributes
                else None
            ),
            owner_satisfaction_score=(
                Score(
                    Decimal(str(version.attributes["owner_satisfaction_score"]))
                )
                if "owner_satisfaction_score" in version.attributes
                else None
            ),
        )
    except (InvalidOperation, ValueError) as error:
        raise EvaluationDataError(
            f"Los datos de mercado de {brand_name} {model_name} no son válidos."
        ) from error


def _active_restriction(
    session: Session, city_id: UUID, powertrain: str, evaluation_date: date
) -> MobilityRestriction | None:
    exact = session.scalar(
        select(MobilityRestriction)
        .where(
            MobilityRestriction.city_id == city_id,
            MobilityRestriction.powertrain == powertrain,
            MobilityRestriction.effective_from <= evaluation_date,
            or_(
                MobilityRestriction.effective_to.is_(None),
                MobilityRestriction.effective_to >= evaluation_date,
            ),
        )
        .order_by(MobilityRestriction.effective_from.desc())
        .limit(1)
    )
    if exact is not None:
        return exact
    return session.scalar(
        select(MobilityRestriction)
        .where(
            MobilityRestriction.city_id == city_id,
            MobilityRestriction.powertrain.is_(None),
            MobilityRestriction.effective_from <= evaluation_date,
            or_(
                MobilityRestriction.effective_to.is_(None),
                MobilityRestriction.effective_to >= evaluation_date,
            ),
        )
        .order_by(MobilityRestriction.effective_from.desc())
        .limit(1)
    )


def _active_tax_rate(
    session: Session,
    city: City,
    powertrain: str,
    vehicle_value: Decimal,
    evaluation_date: date,
) -> tuple[Decimal, str]:
    rules = session.scalars(
        select(TaxRule)
        .where(
            TaxRule.country_code == city.country_code,
            or_(TaxRule.city_id == city.id, TaxRule.city_id.is_(None)),
            TaxRule.effective_from <= evaluation_date,
            or_(TaxRule.effective_to.is_(None), TaxRule.effective_to >= evaluation_date),
        )
        .order_by(TaxRule.city_id.desc(), TaxRule.effective_from.desc())
    ).all()
    rule = next(
        (
            candidate
            for candidate in rules
            if _tax_rule_applies(candidate, powertrain, vehicle_value)
        ),
        None,
    )
    if rule is None:
        return Decimal(0), "none"
    discount = Decimal(str(rule.conditions.get("discount_percentage", 0)))
    effective_rate = rule.rate_percentage * (Decimal(100) - discount) / Decimal(100)
    return effective_rate, str(rule.id)


def _tax_rule_applies(
    rule: TaxRule, powertrain: str, vehicle_value: Decimal
) -> bool:
    configured_powertrain = rule.conditions.get("powertrain")
    if configured_powertrain and configured_powertrain != powertrain:
        return False
    minimum = rule.conditions.get("minimum_value")
    if minimum is not None and vehicle_value < Decimal(str(minimum)):
        return False
    maximum = rule.conditions.get("maximum_value")
    return not (maximum is not None and vehicle_value > Decimal(str(maximum)))


def _active_incentive(
    session: Session,
    city: City,
    powertrain: str,
    currency_code: str,
    evaluation_date: date,
) -> tuple[Decimal, str]:
    rules = session.scalars(
        select(Incentive).where(
            Incentive.country_code == city.country_code,
            or_(Incentive.city_id == city.id, Incentive.city_id.is_(None)),
            or_(Incentive.powertrain == powertrain, Incentive.powertrain.is_(None)),
            Incentive.currency_code == currency_code,
            Incentive.effective_from <= evaluation_date,
            or_(
                Incentive.effective_to.is_(None),
                Incentive.effective_to >= evaluation_date,
            ),
        )
    ).all()
    if not rules:
        return Decimal(0), "none"
    return sum((rule.amount for rule in rules), Decimal(0)), ",".join(
        str(rule.id) for rule in rules
    )
