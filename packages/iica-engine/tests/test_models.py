from decimal import Decimal
from unittest import TestCase

from iica_engine.models import (
    BuyerProfile,
    ChargingAccess,
    Classification,
    EnvironmentProfile,
    EvaluationInput,
    MarketProfile,
    Money,
    Powertrain,
    Score,
    VehicleProfile,
    VehicleUse,
)


class ScoreTests(TestCase):
    def test_classifies_all_public_thresholds(self) -> None:
        expectations = {
            "95": Classification.EXCEPTIONAL,
            "90": Classification.EXCELLENT,
            "80": Classification.VERY_GOOD,
            "70": Classification.GOOD,
            "60": Classification.ACCEPTABLE,
            "59.99": Classification.NOT_RECOMMENDED,
        }

        for value, classification in expectations.items():
            with self.subTest(value=value):
                self.assertEqual(Score(Decimal(value)).classification, classification)

    def test_rejects_a_score_outside_the_public_scale(self) -> None:
        with self.assertRaises(ValueError):
            Score(Decimal("100.01"))


class EvaluationInputTests(TestCase):
    def test_rejects_a_profile_from_a_different_city_than_its_environment(self) -> None:
        buyer = BuyerProfile(
            country_code="CO",
            city_code="bogota",
            budget=Money(Decimal("100000000"), "cop"),
            annual_kilometers=12000,
            ownership_years=5,
            primary_use=VehicleUse.MIXED,
            household_size=3,
            frequent_road_trips=True,
            charging_access=ChargingAccess.NONE,
        )
        vehicle = VehicleProfile(
            vehicle_id="vehicle-001",
            brand="IICA",
            model="Reference",
            trim="Base",
            model_year=2026,
            purchase_price=Money(Decimal("95000000"), "COP"),
            powertrain=Powertrain.HYBRID,
            seats=5,
            safety_score=Score(Decimal("88")),
            warranty_months=60,
        )
        environment = EnvironmentProfile(
            country_code="CO",
            city_code="medellin",
            rules_version="2026-01",
            effective_on="2026-01-01",
            annual_vehicle_tax=Money(Decimal("1000000"), "COP"),
            purchase_incentive=Money(Decimal("0"), "COP"),
            mobility_restriction_days_per_month=4,
            has_electric_exemption=True,
            public_charging_points=200,
        )
        market = MarketProfile(
            as_of="2026-01-01",
            expected_annual_depreciation_percentage=Decimal("12.5"),
            liquidity_score=Score(Decimal("80")),
            owner_satisfaction_score=Score(Decimal("85")),
        )

        with self.assertRaises(ValueError):
            EvaluationInput(
                buyer=buyer,
                vehicle=vehicle,
                environment=environment,
                market=market,
                engine_version="0.2.0",
            )
