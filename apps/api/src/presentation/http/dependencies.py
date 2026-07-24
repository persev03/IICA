"""Dependencias de HTTP compartidas por los routers."""

from __future__ import annotations

from os import getenv
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from infrastructure.persistence.session import get_session

DatabaseSession = Annotated[Session, Depends(get_session)]
optional_bearer = HTTPBearer(auto_error=False)


def optional_user_id(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(optional_bearer)
    ] = None,
) -> str | None:
    """Devuelve el usuario verificado cuando la solicitud incluye una sesión."""

    if credentials is None:
        return None
    claims = _decode_supabase_token(credentials.credentials)
    subject = str(claims.get("sub", "")).strip()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesión no identifica a una persona.",
        )
    return subject


def require_admin_api_key(
    x_admin_api_key: Annotated[str | None, Header()] = None,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(optional_bearer)
    ] = None,
) -> None:
    """Exige un rol de Supabase o la clave local antes de mutar catálogos."""

    supabase_url = getenv("SUPABASE_URL", "").rstrip("/")
    if supabase_url:
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inicia sesión para administrar IICA.",
            )
        claims = _decode_supabase_token(credentials.credentials)

        raw_app_metadata = claims.get("app_metadata", {})
        app_metadata = (
            raw_app_metadata if isinstance(raw_app_metadata, dict) else {}
        )
        configured_emails = {
            email.strip().lower()
            for email in getenv("SUPABASE_ADMIN_EMAILS", "").split(",")
            if email.strip()
        }
        email = str(claims.get("email", "")).lower()
        if app_metadata.get("role") != "admin" and email not in configured_emails:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tu cuenta no tiene el rol administrador.",
            )
        return

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


def _decode_supabase_token(token: str) -> dict[str, object]:
    supabase_url = getenv("SUPABASE_URL", "").rstrip("/")
    if not supabase_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La autenticación de usuarios no está configurada.",
        )
    try:
        signing_key = jwt.PyJWKClient(
            f"{supabase_url}/auth/v1/.well-known/jwks.json"
        ).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256"],
            audience="authenticated",
            issuer=f"{supabase_url}/auth/v1",
        )
    except jwt.PyJWTError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesión no es válida.",
        ) from error
    return dict(claims)
