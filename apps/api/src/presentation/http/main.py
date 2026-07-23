"""Punto de entrada HTTP de IICA.

Los endpoints de negocio se añadirán cuando el modelo de dominio y la
persistencia estén definidos. Mantener este módulo en presentation evita que
FastAPI atraviese los límites del dominio.
"""

from fastapi import FastAPI

app = FastAPI(title="IICA API", version="0.1.0")


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Indica que el proceso HTTP está disponible."""
    return {"status": "ok"}
