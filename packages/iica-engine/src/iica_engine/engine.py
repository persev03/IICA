"""Implementación determinista y explicable de referencia del IICA."""

from __future__ import annotations

from decimal import Decimal

from .models import (
    ChargingAccess,
    EvaluationExplanation,
    EvaluationInput,
    EvaluationResult,
    Influence,
    Powertrain,
    Score,
    VehicleUse,
)


class DeterministicIicaEngine:
    """Calcula una primera versión calibrable del IICA sin dependencias externas."""

    VERSION = "0.6.0"

    def evaluate(self, evaluation_input: EvaluationInput) -> EvaluationResult:
        """Entrega una sola puntuación y sus razones más relevantes."""

        buyer = evaluation_input.buyer
        vehicle = evaluation_input.vehicle
        environment = evaluation_input.environment
        market = evaluation_input.market

        budget_fit = self._budget_fit(
            vehicle.purchase_price.amount,
            buyer.budget.amount,
        )
        mobility_fit = self._mobility_fit(evaluation_input)
        infrastructure_fit = self._infrastructure_fit(evaluation_input)
        use_fit = self._use_fit(evaluation_input)
        depreciation_fit = max(
            Decimal(0),
            Decimal(100) - market.expected_annual_depreciation_percentage * 4,
        )
        warranty_fit = min(Decimal(100), Decimal(vehicle.warranty_months) * 2)

        components = [
            (
                "presupuesto",
                budget_fit,
                Decimal(25),
                "El precio se ajusta al presupuesto declarado.",
            ),
            (
                "seguridad",
                vehicle.safety_score.value,
                Decimal(15),
                "La seguridad de esta versión es relevante para tu decisión.",
            ),
            (
                "movilidad_local",
                mobility_fit,
                Decimal(15),
                "Las reglas de movilidad de tu ciudad afectan el uso diario.",
            ),
            (
                "mercado",
                market.liquidity_score.value,
                Decimal(10),
                "La liquidez prevista influye en una futura reventa.",
            ),
            (
                "depreciacion",
                depreciation_fit,
                Decimal(10),
                "La depreciación esperada afecta el costo total de propiedad.",
            ),
            (
                "satisfaccion",
                market.owner_satisfaction_score.value,
                Decimal(10),
                "La experiencia de propietarios aporta evidencia práctica.",
            ),
            (
                "uso",
                use_fit,
                Decimal("7.5"),
                "La tecnología debe ajustarse a tu patrón de uso.",
            ),
            (
                "infraestructura",
                infrastructure_fit,
                Decimal(5),
                "La infraestructura condiciona la conveniencia operativa.",
            ),
            (
                "garantia",
                warranty_fit,
                Decimal("2.5"),
                "La cobertura reduce incertidumbre en los primeros años.",
            ),
        ]
        total = sum(
            (value * weight / 100 for _, value, weight, _ in components),
            Decimal(0),
        )
        influences = [
            Influence(
                key=key,
                direction=1 if value >= 70 else -1 if value < 50 else 0,
                summary=summary,
            )
            for key, value, _, summary in sorted(
                components,
                key=lambda component: abs(component[1] - 50),
                reverse=True,
            )[:3]
        ]
        strengths = [summary for _, value, _, summary in components if value >= 70][:3]
        weaknesses = [summary for _, value, _, summary in components if value < 50][:3]
        recommendations = self._recommendations(
            evaluation_input, budget_fit, infrastructure_fit
        )

        return EvaluationResult(
            score=Score(total),
            explanation=EvaluationExplanation(
                strengths=strengths,
                weaknesses=weaknesses,
                influences=influences,
                recommendations=recommendations,
            ),
            engine_version=self.VERSION,
            data_version=f"{environment.rules_version}:{market.as_of}",
        )

    @staticmethod
    def _budget_fit(price: Decimal, budget: Decimal) -> Decimal:
        if budget == 0:
            return Decimal(0)
        if price <= budget:
            return Decimal(100)
        excess = (price - budget) / budget * 100
        return max(Decimal(0), Decimal(100) - excess * 2)

    @staticmethod
    def _mobility_fit(evaluation_input: EvaluationInput) -> Decimal:
        vehicle = evaluation_input.vehicle
        environment = evaluation_input.environment
        if (
            vehicle.powertrain == Powertrain.ELECTRIC
            and environment.has_electric_exemption
        ):
            return Decimal(100)
        return max(
            Decimal(0),
            Decimal(100) - environment.mobility_restriction_days_per_month * 12,
        )

    @staticmethod
    def _infrastructure_fit(evaluation_input: EvaluationInput) -> Decimal:
        buyer = evaluation_input.buyer
        vehicle = evaluation_input.vehicle
        environment = evaluation_input.environment
        if vehicle.powertrain not in {Powertrain.ELECTRIC, Powertrain.PLUG_IN_HYBRID}:
            return Decimal(85)
        if buyer.charging_access in {ChargingAccess.HOME, ChargingAccess.WORK}:
            return Decimal(100)
        if environment.public_charging_points >= 100:
            return Decimal(70)
        return Decimal(25)

    @staticmethod
    def _use_fit(evaluation_input: EvaluationInput) -> Decimal:
        buyer = evaluation_input.buyer
        vehicle = evaluation_input.vehicle
        if (
            buyer.primary_use == VehicleUse.ROAD_TRIPS
            and vehicle.powertrain == Powertrain.ELECTRIC
        ):
            return (
                Decimal(65)
                if buyer.charging_access != ChargingAccess.NONE
                else Decimal(40)
            )
        if buyer.primary_use == VehicleUse.URBAN and vehicle.powertrain in {
            Powertrain.HYBRID,
            Powertrain.ELECTRIC,
        }:
            return Decimal(95)
        if (
            buyer.primary_use == VehicleUse.FAMILY
            and vehicle.seats < buyer.household_size
        ):
            return Decimal(20)
        return Decimal(80)

    @staticmethod
    def _recommendations(
        evaluation_input: EvaluationInput,
        budget_fit: Decimal,
        infrastructure_fit: Decimal,
    ) -> list[str]:
        recommendations: list[str] = []
        if budget_fit < 70:
            recommendations.append(
                "Considera una versión cuyo precio se ajuste mejor a tu presupuesto."
            )
        if infrastructure_fit < 50:
            recommendations.append(
                "Confirma opciones de carga antes de elegir esta tecnología."
            )
        if not recommendations:
            recommendations.append(
                "Compara esta versión con al menos una alternativa equivalente antes de decidir."
            )
        return recommendations
