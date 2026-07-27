from uuid import uuid4

from presentation.http.schemas import EvaluationRequest


def test_evaluation_accepts_more_than_two_vehicles() -> None:
    vehicle_ids = [uuid4(), uuid4(), uuid4()]

    request = EvaluationRequest(
        city_code="medellin",
        budget="140000000",
        annual_kilometers=12000,
        ownership_years=5,
        primary_use="mixed",
        household_size=2,
        vehicle_ids=vehicle_ids,
    )

    assert request.vehicle_ids == vehicle_ids
