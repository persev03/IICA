from decimal import Decimal
from unittest import TestCase

from iica_engine.engine import DeterministicIicaEngine
from iica_engine.models import (
    BuyerProfile,
    ChargingAccess,
    EnvironmentProfile,
    EvaluationInput,
    MarketProfile,
    Money,
    Powertrain,
    Score,
    VehicleProfile,
    VehicleUse,
)


class DeterministicEngineTests(TestCase):
    def test_returns_one_reproducible_and_explained_score(self) -> None:
        evaluation_input = EvaluationInput(
            buyer=BuyerProfile(
                "CO",
                "bogota",
                Money(Decimal(95000000), "COP"),
                12000,
                5,
                VehicleUse.MIXED,
                3,
                True,
                ChargingAccess.HOME,
            ),
            vehicle=VehicleProfile(
                "v1",
                "Example",
                "Model",
                "Trim",
                2026,
                Money(Decimal(95000000), "COP"),
                Powertrain.HYBRID,
                5,
                Score(Decimal(88)),
                60,
            ),
            environment=EnvironmentProfile(
                "CO",
                "bogota",
                "rules-1",
                "2026-01-01",
                Money(Decimal(1000000), "COP"),
                Money(Decimal(0), "COP"),
                4,
                False,
                100,
            ),
            market=MarketProfile(
                "2026-01-01", Decimal("12.5"), Score(Decimal(80)), Score(Decimal(85))
            ),
            engine_version="0.6.0",
        )

        engine = DeterministicIicaEngine()
        result = engine.evaluate(evaluation_input)

        self.assertEqual(result.score.value, Decimal("79.72"))
        self.assertEqual(result.engine_version, "0.8.0")
        self.assertEqual(result.data_version, "rules-1:2026-01-01")
        self.assertEqual(len(result.explanation.influences), 3)

        incentivized_input = EvaluationInput(
            buyer=evaluation_input.buyer,
            vehicle=evaluation_input.vehicle,
            environment=EnvironmentProfile(
                "CO",
                "bogota",
                "rules-1-with-incentive",
                "2026-01-01",
                Money(Decimal(1000000), "COP"),
                Money(Decimal(2000000), "COP"),
                4,
                False,
                100,
            ),
            market=evaluation_input.market,
            engine_version="0.8.0",
        )
        incentivized = engine.evaluate(incentivized_input)
        self.assertGreater(incentivized.score.value, result.score.value)

    def test_renormalizes_weights_when_market_signals_are_unavailable(self) -> None:
        evaluation_input = EvaluationInput(
            buyer=BuyerProfile(
                "CO",
                "bogota",
                Money(Decimal(100000000), "COP"),
                12000,
                5,
                VehicleUse.MIXED,
                3,
                False,
                ChargingAccess.NONE,
            ),
            vehicle=VehicleProfile(
                "v2",
                "Verified",
                "Vehicle",
                "Base",
                2026,
                Money(Decimal(90000000), "COP"),
                Powertrain.GASOLINE,
                5,
                Score(Decimal(80)),
                36,
            ),
            environment=EnvironmentProfile(
                "CO",
                "bogota",
                "rules-2",
                "2026-07-24",
                Money(Decimal(0), "COP"),
                Money(Decimal(0), "COP"),
                10,
                False,
                0,
            ),
            market=MarketProfile("2026-07-24"),
            engine_version="0.7.0",
        )

        result = DeterministicIicaEngine().evaluate(evaluation_input)

        self.assertGreaterEqual(result.score.value, Decimal(0))
        self.assertLessEqual(result.score.value, Decimal(100))
        self.assertNotIn(
            "La liquidez observada influye en una futura reventa.",
            result.explanation.strengths,
        )
