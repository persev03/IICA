"""Endpoint asistivo de IA moderna (Qwen local) para explicar resultados IICA."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from application.ai_assistant import (
    AssistantUnavailableError,
    explain_evaluation_with_qwen,
)
from application.evaluations import EvaluationDataError, evaluate_vehicles
from presentation.http.dependencies import DatabaseSession, optional_user_id
from presentation.http.schemas import (
    AiExplainRequest,
    AiExplainResponse,
)

router = APIRouter(prefix="/v1/ai", tags=["ai"])


@router.post("/evaluations/explain", response_model=AiExplainResponse)
def explain_evaluation(
    payload: AiExplainRequest,
    session: DatabaseSession,
    user_id: Annotated[str | None, Depends(optional_user_id)],
) -> AiExplainResponse:
    """Genera una explicación con IA local basada en un cálculo determinista vigente."""

    try:
        evaluation = evaluate_vehicles(
            payload.evaluation,
            session,
            user_id=None,
        )
    except EvaluationDataError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    try:
        return explain_evaluation_with_qwen(
            question=payload.question,
            evaluation=evaluation,
            city_code=payload.evaluation.city_code,
            session=session,
            user_id=user_id,
        )
    except AssistantUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
