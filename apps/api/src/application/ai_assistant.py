"""Asistente de IA moderna: explica resultados IICA sin alterar el score."""

from __future__ import annotations

from dataclasses import dataclass
from os import getenv

import httpx
from sqlalchemy.orm import Session

from infrastructure.persistence.models import AiAssistantRecord
from presentation.http.schemas import (
    AiExplainResponse,
    AiSourceResponse,
    EvaluationResponse,
)


class AssistantUnavailableError(RuntimeError):
    """Señala que el proveedor local de LLM no está disponible."""


@dataclass(frozen=True)
class OllamaConfig:
    model: str
    url: str
    timeout_seconds: float
    temperature: float


@dataclass(frozen=True)
class HuggingFaceConfig:
    api_key: str
    model: str
    url: str
    timeout_seconds: float
    temperature: float


def explain_evaluation_with_qwen(
    *,
    question: str,
    evaluation: EvaluationResponse,
    city_code: str,
    session: Session,
    user_id: str | None,
) -> AiExplainResponse:
    """Genera una explicación asistiva basada en evidencia del cálculo determinista."""

    config = _ollama_config()
    context = _build_context(evaluation)
    system_prompt = (
        "Eres un asistente del sistema IICA. "
        "Debes explicar resultados sin inventar datos y en español claro. "
        "Nunca alteres ni contradigas el score determinista. "
        "Si falta evidencia, dilo explícitamente. "
        "Enfatiza fortalezas, riesgos y recomendaciones accionables."
    )
    user_prompt = (
        f"Pregunta del usuario: {question}\n\n"
        "Contexto verificable del cálculo:\n"
        f"{context}\n\n"
        "Instrucciones de salida:\n"
        "1) Responde en 1-3 párrafos.\n"
        "2) Cita únicamente hechos presentes en el contexto.\n"
        "3) No prometas cambios automáticos en el score."
    )

    provider, model, answer = _call_best_available_chat(
        config=config,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        evaluation=evaluation,
    )
    sources = _extract_sources(evaluation)

    disclaimer = (
        "Respuesta asistiva generada por IA moderna con Qwen. "
        "No reemplaza el motor determinista ni modifica el score."
    )
    if provider == "deterministic-fallback":
        disclaimer = (
            "Respuesta de contingencia basada en reglas y evidencia del cálculo. "
            "Configura IICA_HF_API_KEY u Ollama para activar explicación generativa completa."
        )

    response = AiExplainResponse(
        answer=answer,
        disclaimer=disclaimer,
        model=model,
        sources=sources,
        evaluation=evaluation,
    )

    session.add(
        AiAssistantRecord(
            user_id=user_id,
            city_code=city_code,
            question=question,
            llm_provider=provider,
            llm_model=model,
            prompt_snapshot={
                "system": system_prompt,
                "user": user_prompt,
            },
            response_snapshot=response.model_dump(mode="json"),
        )
    )
    session.commit()

    return response


def _ollama_config() -> OllamaConfig:
    return OllamaConfig(
        model=getenv("IICA_OLLAMA_MODEL", "qwen2.5:7b-instruct"),
        url=getenv("IICA_OLLAMA_CHAT_URL", "http://localhost:11434/api/chat"),
        timeout_seconds=float(getenv("IICA_OLLAMA_TIMEOUT_SECONDS", "25")),
        temperature=float(getenv("IICA_OLLAMA_TEMPERATURE", "0.2")),
    )


def _call_ollama_chat(
    *,
    config: OllamaConfig,
    system_prompt: str,
    user_prompt: str,
) -> str:
    payload = {
        "model": config.model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "options": {"temperature": config.temperature},
    }

    try:
        with httpx.Client(timeout=config.timeout_seconds) as client:
            http_response = client.post(config.url, json=payload)
            http_response.raise_for_status()
    except httpx.HTTPError as error:
        raise AssistantUnavailableError(
            "No fue posible contactar al asistente local de IA (Ollama)."
        ) from error

    data = http_response.json()
    message = data.get("message", {})
    content = str(message.get("content", "")).strip()
    if not content:
        raise AssistantUnavailableError(
            "El asistente local respondió sin contenido utilizable."
        )
    return content


def _huggingface_config() -> HuggingFaceConfig | None:
    api_key = getenv("IICA_HF_API_KEY", "").strip()
    if not api_key:
        return None
    return HuggingFaceConfig(
        api_key=api_key,
        model=getenv("IICA_HF_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
        url=getenv(
            "IICA_HF_CHAT_URL",
            "https://router.huggingface.co/v1/chat/completions",
        ),
        timeout_seconds=float(getenv("IICA_HF_TIMEOUT_SECONDS", "25")),
        temperature=float(getenv("IICA_HF_TEMPERATURE", "0.2")),
    )


def _call_huggingface_chat(
    *,
    config: HuggingFaceConfig,
    system_prompt: str,
    user_prompt: str,
) -> str:
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": config.temperature,
        "max_tokens": 500,
    }
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=config.timeout_seconds) as client:
            http_response = client.post(config.url, json=payload, headers=headers)
            http_response.raise_for_status()
    except httpx.HTTPError as error:
        raise AssistantUnavailableError(
            "No fue posible contactar Hugging Face para el fallback de Qwen."
        ) from error

    data = http_response.json()
    choices = data.get("choices", [])
    if not isinstance(choices, list) or not choices:
        raise AssistantUnavailableError(
            "Hugging Face respondió sin opciones de contenido."
        )
    message = choices[0].get("message", {})
    content = str(message.get("content", "")).strip()
    if not content:
        raise AssistantUnavailableError(
            "Hugging Face respondió sin contenido utilizable."
        )
    return content


def _call_best_available_chat(
    *,
    config: OllamaConfig,
    system_prompt: str,
    user_prompt: str,
    evaluation: EvaluationResponse,
) -> tuple[str, str, str]:
    try:
        content = _call_ollama_chat(
            config=config,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        return ("ollama", config.model, content)
    except AssistantUnavailableError as ollama_error:
        hf_config = _huggingface_config()
        if hf_config is None:
            return (
                "deterministic-fallback",
                "iica-explainer-v1",
                _build_deterministic_fallback_answer(evaluation),
            )
        try:
            content = _call_huggingface_chat(
                config=hf_config,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            return ("huggingface", hf_config.model, content)
        except AssistantUnavailableError:
            return (
                "deterministic-fallback",
                "iica-explainer-v1",
                _build_deterministic_fallback_answer(evaluation),
            )


def _build_deterministic_fallback_answer(evaluation: EvaluationResponse) -> str:
    if not evaluation.results:
        return (
            "No hay resultados disponibles para explicar en este momento. "
            "Vuelve a ejecutar la comparación para generar evidencia."
        )

    top = evaluation.results[0]
    strengths = ", ".join(top.strengths[:2]) if top.strengths else "sin fortalezas destacadas"
    weaknesses = ", ".join(top.weaknesses[:2]) if top.weaknesses else "sin riesgos críticos"
    recommendation = (
        top.recommendations[0]
        if top.recommendations
        else "Compara con al menos una alternativa equivalente antes de decidir."
    )

    return (
        f"La mejor opción del cálculo actual es {top.name} con score {top.score} "
        f"y clasificación {top.classification}. Sus principales fortalezas son {strengths}, "
        f"mientras que los riesgos a revisar son {weaknesses}. "
        f"Recomendación principal: {recommendation}."
    )


def _build_context(evaluation: EvaluationResponse) -> str:
    lines: list[str] = [
        f"Ciudad evaluada: {evaluation.city}",
        f"Fecha de evaluación: {evaluation.evaluated_at}",
    ]
    for index, result in enumerate(evaluation.results[:3], start=1):
        lines.extend(
            [
                f"Vehículo {index}: {result.name}",
                f"Score: {result.score} ({result.classification})",
                "Fortalezas: " + ", ".join(result.strengths[:3]),
                "Riesgos: " + ", ".join(result.weaknesses[:3]),
                "Recomendaciones: " + ", ".join(result.recommendations[:3]),
            ]
        )
        if result.mobility_rule is not None:
            lines.append(
                "Regla de movilidad: "
                f"{result.mobility_rule.title}. Fuente: {result.mobility_rule.source_url}"
            )
    return "\n".join(lines)


def _extract_sources(evaluation: EvaluationResponse) -> list[AiSourceResponse]:
    sources: list[AiSourceResponse] = []
    for result in evaluation.results[:3]:
        if result.mobility_rule is None:
            continue
        sources.append(
            AiSourceResponse(
                title=f"Regla de movilidad aplicada a {result.name}",
                source_url=result.mobility_rule.source_url,
                evidence=result.mobility_rule.explanation,
            )
        )
    if not sources:
        sources.append(
            AiSourceResponse(
                title="Resultado determinista IICA",
                source_url=None,
                evidence="El análisis se basó en resultados reproducibles del motor IICA.",
            )
        )
    return sources
