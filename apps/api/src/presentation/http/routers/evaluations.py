"""Endpoint público para cálculos IICA reproducibles."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from application.evaluations import EvaluationDataError, evaluate_vehicles
from infrastructure.persistence.models import EvaluationRecord
from presentation.http.dependencies import DatabaseSession, optional_user_id
from presentation.http.schemas import EvaluationRequest, EvaluationResponse

router = APIRouter(prefix="/v1", tags=["evaluations"])


@router.post("/evaluations", response_model=EvaluationResponse)
def create_evaluation(
    payload: EvaluationRequest,
    session: DatabaseSession,
    user_id: Annotated[str | None, Depends(optional_user_id)],
) -> EvaluationResponse:
    """Calcula resultados solo cuando todos los datos requeridos están vigentes."""

    try:
        return evaluate_vehicles(payload, session, user_id=user_id)
    except EvaluationDataError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error


@router.get("/me/evaluations", response_model=list[EvaluationResponse])
def list_my_evaluations(
    session: DatabaseSession,
    user_id: Annotated[str | None, Depends(optional_user_id)],
) -> list[EvaluationResponse]:
    """Recupera el historial reproducible de la sesión autenticada."""

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inicia sesión para consultar tu historial.",
        )
    records = session.scalars(
        select(EvaluationRecord)
        .where(EvaluationRecord.user_id == user_id)
        .order_by(EvaluationRecord.evaluated_at.desc())
        .limit(20)
    )
    return [
        EvaluationResponse.model_validate(record.result_snapshot) for record in records
    ]
