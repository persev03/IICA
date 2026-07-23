"""Configuración de sesión SQLAlchemy aislada de la capa de presentación."""

from collections.abc import Iterator
from os import getenv

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

_DATABASE_URL = getenv("DATABASE_URL", "postgresql+psycopg://iica:iica@localhost:5432/iica")

engine = create_engine(_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_session() -> Iterator[Session]:
    """Entrega una sesión transaccional para endpoints y casos de uso."""

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
