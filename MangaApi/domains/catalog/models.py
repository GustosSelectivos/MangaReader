"""
domains/catalog/models.py
=========================
Modelos SQLAlchemy para las tablas de catálogo (mantenedores):
  - autores    → apicore_autores
  - estados    → apicore_estados
  - demografia → apicore_demografia
  - tags       → apicore_tags

IMPORTANTE: __tablename__ explícito en cada modelo para preservar
los datos existentes en MySQL. No se renombran tablas.
"""

import enum
from datetime import datetime
from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


# ── Enums ─────────────────────────────────────────────────────────────────────

class TipoAutorEnum(str, enum.Enum):
    mangaka = "mangaka"
    ilustrador = "ilustrador"
    guionista = "guionista"


# ── Modelos ───────────────────────────────────────────────────────────────────

class Autor(Base):
    """Tabla: apicore_autores"""
    __tablename__ = "apicore_autores"

    id: Mapped[int] = mapped_column("AUT_ID", primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column("AUT_NOMBRE", String(100), nullable=False)
    tipo_autor: Mapped[str] = mapped_column(
        "AUT_TIPO_AUTOR", String(20), nullable=False, default="mangaka"
    )
    foto: Mapped[str | None] = mapped_column("AUT_FOTO", String(255), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        "AUT_CREACION", DateTime, nullable=False, server_default=func.now()
    )
    vigente: Mapped[bool] = mapped_column("AUT_VIGENTE", Boolean, nullable=False, default=True)


class Estado(Base):
    """Tabla: apicore_estados"""
    __tablename__ = "apicore_estados"

    id: Mapped[int] = mapped_column("EST_ID", primary_key=True, autoincrement=True)
    descripcion: Mapped[str | None] = mapped_column("EST_DESCRIPCION", String(255), nullable=True)
    vigente: Mapped[bool] = mapped_column("EST_VIGENTE", Boolean, nullable=False, default=True)


class Demografia(Base):
    """Tabla: apicore_demografia"""
    __tablename__ = "apicore_demografia"

    id: Mapped[int] = mapped_column("DEM_ID", primary_key=True, autoincrement=True)
    descripcion: Mapped[str | None] = mapped_column("DEM_DESCRIPCION", String(255), nullable=True)
    color: Mapped[str | None] = mapped_column("DEM_COLOR", String(7), nullable=True)
    vigente: Mapped[bool] = mapped_column("DEM_VIGENTE", Boolean, nullable=False, default=True)


class Tag(Base):
    """Tabla: apicore_tags"""
    __tablename__ = "apicore_tags"

    id: Mapped[int] = mapped_column("TAG_ID", primary_key=True, autoincrement=True)
    descripcion: Mapped[str | None] = mapped_column("TAG_DESCRIPCION", String(255), nullable=True)
    vigente: Mapped[bool] = mapped_column("TAG_VIGENTE", Boolean, nullable=False, default=True)
