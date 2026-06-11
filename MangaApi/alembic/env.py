"""
alembic/env.py
==============
Configuración del entorno de Alembic para modo async.

FLUJO DE ARRANQUE (primera vez sobre BD existente de Django):
  1. pip install -r requirements.txt
  2. alembic stamp head       ← Marca el estado actual como "migrado"
  3. alembic revision --autogenerate -m "init"  ← Solo para cambios futuros
  4. alembic upgrade head     ← Aplica cambios futuros

NO ejecutar 'alembic upgrade head' sin el stamp previo;
destruiría tablas existentes.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from core.config import settings
from core.database import Base

# Importar todos los modelos para que Alembic los detecte
import domains.catalog.models       # noqa: F401
import domains.mangas.models        # noqa: F401
import domains.chapters.models      # noqa: F401
import domains.users.models         # noqa: F401
import domains.dac.models           # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Tablas de Django que NO debe tocar Alembic
EXCLUDE_TABLES = {
    "auth_user",
    "auth_group",
    "auth_user_groups",
    "auth_user_user_permissions",
    "auth_group_permissions",
    "auth_permission",
    "django_content_type",
    "django_migrations",
    "django_session",
    "django_admin_log",
}


def include_object(object, name, type_, reflected, compare_to):
    """Excluye las tablas de Django del autogenerate."""
    if type_ == "table" and name in EXCLUDE_TABLES:
        return False
    return True


def run_migrations_offline() -> None:
    url = settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
