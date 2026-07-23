"""Puertos del motor IICA.

Las aplicaciones dependen de esta interfaz y nunca de una implementación de
puntuación concreta. Esto permite calibrar o sustituir el algoritmo sin cambiar
los consumidores.
"""

from __future__ import annotations

from typing import Protocol

from .models import EvaluationInput, EvaluationResult


class IicaEngine(Protocol):
    """Contrato estable para cualquier implementación del motor IICA."""

    def evaluate(self, evaluation_input: EvaluationInput) -> EvaluationResult:
        """Calcula un único resultado IICA explicable y reproducible."""
