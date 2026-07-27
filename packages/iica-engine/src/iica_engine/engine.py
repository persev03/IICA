"""Implementación determinista y explicable de referencia del IICA."""

from __future__ import annotations

from decimal import Decimal

from .models import (
    BuyerProfile,
    ChargingAccess,
    EvaluationExplanation,
    EvaluationInput,
    EvaluationResult,
    Influence,
    Powertrain,
    PreferenceCriterion,
    Score,
    VehicleUse,
)


class DeterministicIicaEngine:
    """Calcula una primera versión calibrable del IICA sin dependencias externas."""

    VERSION = "1.0.0"

    _PREFERENCE_MULTIPLIERS = (
        Decimal("2.00"),
        Decimal("1.70"),
        Decimal("1.45"),
        Decimal("1.25"),
        Decimal("1.10"),
        Decimal("0.95"),
        Decimal("0.80"),
        Decimal("0.70"),
    )

    def evaluate(self, evaluation_input: EvaluationInput) -> EvaluationResult:
        """Entrega una sola puntuación y sus razones más relevantes."""

        buyer = evaluation_input.buyer
        vehicle = evaluation_input.vehicle
        environment = evaluation_input.environment
        market = evaluation_input.market

        effective_cost = max(
            Decimal(0),
            vehicle.purchase_price.amount
            + environment.annual_vehicle_tax.amount
            - environment.purchase_incentive.amount,
        )
        budget_fit = self._budget_fit(
            effective_cost,
            buyer.budget.amount,
        )
        mobility_fit = self._mobility_fit(evaluation_input)
        infrastructure_fit = self._infrastructure_fit(evaluation_input)
        use_fit = self._use_fit(evaluation_input)
        warranty_fit = min(Decimal(100), Decimal(vehicle.warranty_months) * 2)
        efficiency_fit = self._efficiency_fit(evaluation_input)
        space_fit = self._space_fit(evaluation_input)
        technology_fit = self._technology_fit(evaluation_input)

        components = [
            (
                "presupuesto",
                budget_fit,
                Decimal(25),
                "El costo efectivo, incluidos impuestos e incentivos, se ajusta al presupuesto.",
                PreferenceCriterion.AFFORDABILITY,
            ),
            (
                "movilidad_local",
                mobility_fit,
                Decimal(15),
                (
                    "La versión cuenta con una exención de movilidad vigente en tu ciudad."
                    if environment.has_mobility_exemption
                    else "Las reglas de movilidad de tu ciudad afectan el uso diario."
                ),
                PreferenceCriterion.MOBILITY_EXEMPTION,
            ),
            (
                "uso",
                use_fit,
                Decimal("7.5"),
                "La tecnología debe ajustarse a tu patrón de uso.",
                None,
            ),
            (
                "infraestructura",
                infrastructure_fit,
                Decimal(5),
                "La infraestructura condiciona la conveniencia operativa.",
                PreferenceCriterion.TECHNOLOGY,
            ),
            (
                "garantia",
                warranty_fit,
                Decimal("2.5"),
                "La cobertura reduce incertidumbre en los primeros años.",
                PreferenceCriterion.RELIABILITY,
            ),
            (
                "rendimiento",
                efficiency_fit,
                Decimal(10),
                "La motorización favorece el rendimiento energético y el consumo esperado.",
                PreferenceCriterion.FUEL_EFFICIENCY,
            ),
            (
                "espacio",
                space_fit,
                Decimal(10),
                "La capacidad de pasajeros responde al tamaño de tu hogar.",
                PreferenceCriterion.INTERIOR_SPACE,
            ),
            (
                "tecnologia",
                technology_fit,
                Decimal(5),
                "La tecnología de propulsión aporta electrificación y eficiencia operativa.",
                PreferenceCriterion.TECHNOLOGY,
            ),
        ]
        if vehicle.safety_score is not None:
            components.append(
                (
                    "seguridad",
                    vehicle.safety_score.value,
                    Decimal(15),
                    "La seguridad de esta versión es relevante para tu decisión.",
                    PreferenceCriterion.SAFETY,
                )
            )
        if market.liquidity_score is not None:
            components.append(
                (
                    "mercado",
                    market.liquidity_score.value,
                    Decimal(10),
                    "La liquidez observada influye en una futura reventa.",
                    PreferenceCriterion.RESALE,
                )
            )
        if market.expected_annual_depreciation_percentage is not None:
            depreciation_fit = max(
                Decimal(0),
                Decimal(100)
                - market.expected_annual_depreciation_percentage * 4,
            )
            components.append(
                (
                    "depreciacion",
                    depreciation_fit,
                    Decimal(10),
                    "La depreciación observada afecta el costo total de propiedad.",
                    PreferenceCriterion.AFFORDABILITY,
                )
            )
        if market.owner_satisfaction_score is not None:
            components.append(
                (
                    "satisfaccion",
                    market.owner_satisfaction_score.value,
                    Decimal(10),
                    "La experiencia documentada de propietarios aporta evidencia práctica.",
                    PreferenceCriterion.RELIABILITY,
                )
            )
        weighted_components = [
            (
                key,
                value,
                weight * self._preference_multiplier(buyer, criterion),
                summary,
                criterion,
            )
            for key, value, weight, summary, criterion in components
        ]
        available_weight = sum(
            (weight for _, _, weight, _, _ in weighted_components), Decimal(0)
        )
        weighted_sum = sum(
            (
                value * weight / 100
                for _, value, weight, _, _ in weighted_components
            ),
            Decimal(0),
        )
        total = weighted_sum * Decimal(100) / available_weight
        influences = [
            Influence(
                key=key,
                direction=1 if value >= 70 else -1 if value < 50 else 0,
                summary=summary,
            )
            for key, value, _, summary, _ in sorted(
                weighted_components,
                key=lambda component: component[2] * abs(component[1] - 50),
                reverse=True,
            )[:3]
        ]
        strengths = [
            summary
            for _, value, _, summary, _ in weighted_components
            if value >= 70
        ][:3]
        weaknesses = [
            summary
            for _, value, _, summary, _ in weighted_components
            if value < 50
        ][:3]
        priority_insights = self._priority_insights(buyer, weighted_components)
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
                priority_insights=priority_insights,
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
        environment = evaluation_input.environment
        if environment.has_mobility_exemption:
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
    def _efficiency_fit(evaluation_input: EvaluationInput) -> Decimal:
        scores = {
            Powertrain.ELECTRIC: Decimal(100),
            Powertrain.PLUG_IN_HYBRID: Decimal(92),
            Powertrain.HYBRID: Decimal(86),
            Powertrain.DIESEL: Decimal(68),
            Powertrain.GASOLINE: Decimal(58),
        }
        score = scores[evaluation_input.vehicle.powertrain]
        if (
            evaluation_input.vehicle.powertrain == Powertrain.PLUG_IN_HYBRID
            and evaluation_input.buyer.charging_access == ChargingAccess.NONE
        ):
            return Decimal(74)
        return score

    @staticmethod
    def _space_fit(evaluation_input: EvaluationInput) -> Decimal:
        seats = evaluation_input.vehicle.seats
        household_size = evaluation_input.buyer.household_size
        if seats < household_size:
            return Decimal(20)
        spare_seats = seats - household_size
        return min(Decimal(100), Decimal(75 + spare_seats * 5))

    @staticmethod
    def _technology_fit(evaluation_input: EvaluationInput) -> Decimal:
        return {
            Powertrain.ELECTRIC: Decimal(100),
            Powertrain.PLUG_IN_HYBRID: Decimal(95),
            Powertrain.HYBRID: Decimal(85),
            Powertrain.DIESEL: Decimal(60),
            Powertrain.GASOLINE: Decimal(55),
        }[evaluation_input.vehicle.powertrain]

    def _preference_multiplier(
        self,
        buyer: BuyerProfile,
        criterion: PreferenceCriterion | None,
    ) -> Decimal:
        if criterion is None:
            return Decimal(1)
        rank = buyer.preference_order.index(criterion)
        return self._PREFERENCE_MULTIPLIERS[rank]

    @staticmethod
    def _priority_insights(
        buyer: BuyerProfile,
        components: list[
            tuple[
                str,
                Decimal,
                Decimal,
                str,
                PreferenceCriterion | None,
            ]
        ],
    ) -> list[str]:
        insights: list[str] = []
        for rank, criterion in enumerate(buyer.preference_order[:3], start=1):
            candidates = [
                component for component in components if component[4] == criterion
            ]
            if not candidates:
                continue
            _, value, _, summary, _ = max(candidates, key=lambda item: item[2])
            alignment = (
                "se alinea bien"
                if value >= 70
                else "se alinea parcialmente"
                if value >= 50
                else "no se alinea bien"
            )
            insights.append(f"Prioridad #{rank}: {alignment}. {summary}")
        return insights

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
