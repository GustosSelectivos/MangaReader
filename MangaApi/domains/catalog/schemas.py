"""
domains/catalog/schemas.py
==========================
Schemas Pydantic v2 para el dominio de catálogo.
Reemplaza: AutorSerializer, EstadoSerializer, DemografiaSerializer, TagSerializer (DRF).
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# ── Autores ───────────────────────────────────────────────────────────────────

class AutorBase(BaseModel):
    nombre: str = Field(..., max_length=100)
    tipo_autor: str = Field(default="mangaka", pattern="^(mangaka|ilustrador|guionista)$")
    foto: str | None = Field(default=None, max_length=255)
    vigente: bool = True


class AutorCreate(AutorBase):
    pass


class AutorUpdate(BaseModel):
    nombre: str | None = Field(default=None, max_length=100)
    tipo_autor: str | None = Field(default=None, pattern="^(mangaka|ilustrador|guionista)$")
    foto: str | None = None
    vigente: bool | None = None


class AutorRead(AutorBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    creado_en: datetime


# ── Estados ───────────────────────────────────────────────────────────────────

class EstadoBase(BaseModel):
    descripcion: str | None = Field(default=None, max_length=255)
    vigente: bool = True


class EstadoCreate(EstadoBase):
    pass


class EstadoUpdate(BaseModel):
    descripcion: str | None = None
    vigente: bool | None = None


class EstadoRead(EstadoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ── Demografía ────────────────────────────────────────────────────────────────

class DemografiaBase(BaseModel):
    descripcion: str | None = Field(default=None, max_length=255)
    color: str | None = Field(default=None, max_length=7, pattern=r"^#[0-9A-Fa-f]{6}$")
    vigente: bool = True


class DemografiaCreate(DemografiaBase):
    pass


class DemografiaUpdate(BaseModel):
    descripcion: str | None = None
    color: str | None = None
    vigente: bool | None = None


class DemografiaRead(DemografiaBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ── Tags ──────────────────────────────────────────────────────────────────────

class TagBase(BaseModel):
    descripcion: str | None = Field(default=None, max_length=255)
    vigente: bool = True


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    descripcion: str | None = None
    vigente: bool | None = None


class TagRead(TagBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
