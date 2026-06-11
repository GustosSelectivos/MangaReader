"""
core/database.py
================
Configura el engine async de SQLAlchemy 2.0 con asyncmy (MySQL).
Expone:
  - engine          → AsyncEngine (para Alembic y lifespan)
  - AsyncSessionLocal → fábrica de sesiones
  - get_db()        → Depends() que provee una AsyncSession por request

Decisión: Se usa `NullPool` en producción para no acumular conexiones
inactivas en entornos serverless (Railway). En desarrollo se usa
`AsyncAdaptedQueuePool` con pool_size configurable.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from core.config import settings


def _build_engine():
    kwargs: dict = {
        "echo": settings.DEBUG,
        "pool_pre_ping": True,   # Valida conexión antes de usarla (evita OperationalError)
    }
    # En producción sin estado (Railway/Heroku): NullPool evita fugas
    if settings.ENVIRONMENT == "production":
        kwargs["poolclass"] = NullPool
    else:
        kwargs["pool_size"] = 10
        kwargs["max_overflow"] = 20
        kwargs["pool_recycle"] = 3600  # Reciclar conexiones cada hora

    return create_async_engine(settings.database_url, **kwargs)


engine = _build_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,   # Evita lazy-load post-commit en contextos async
)


class Base(DeclarativeBase):
    """Base declarativa compartida por todos los modelos SQLAlchemy."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia FastAPI que provee una sesión de BD por request.

    Uso en router:
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
