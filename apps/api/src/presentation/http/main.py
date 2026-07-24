"""Punto de entrada HTTP de IICA."""

from os import getenv
from re import split

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from presentation.http.routers.catalog import router as catalog_router
from presentation.http.routers.evaluations import router as evaluations_router

app = FastAPI(
    title="IICA API",
    version="0.4.0",
    description="API del Índice Inteligente de Compra de Automóviles.",
)
allowed_origins = [
    origin.strip()
    for origin in split(
        r"[,;]",
        getenv(
            "IICA_ALLOWED_ORIGINS",
            "http://localhost:3000,http://localhost:3001",
        ),
    )
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Admin-API-Key"],
)
app.include_router(catalog_router)
app.include_router(evaluations_router)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Indica que el proceso HTTP está disponible."""
    return {"status": "ok"}
