"""Dependencias de HTTP compartidas por los routers."""

from __future__ import annotations

from os import getenv
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from infrastructure.persistence.session import get_session

DatabaseSession = Annotated[Session, Depends(get_session)]


def require_admin_api_key(
    x_admin_api_key: Annotated[str | None, Header()] = None,
) -> None:
    """Exige una clave explícita antes de mutar catálogos administrativos."""

    expected_key = getenv("IICA_ADMIN_API_KEY")
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La administración API no está configurada.",
        )
    if x_admin_api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clave de administración inválida.",
        )
