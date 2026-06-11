"""
domains/mangas/schemas.py
=========================
Schemas Pydantic v2 para el dominio de Mangas.

Reemplaza:
  - MangaSerializer (DRF)      → MangaCreate, MangaUpdate, MangaDetail
  - MangaCardSerializer (DRF)  → MangaCard
  - MangaAltTituloSerializer   → MangaAltTituloRead, MangaAltTituloCreate
  - MangaCoverSerializer       → MangaCoverRead
  - MangaAutorSerializer       → MangaAutorRead
  - MangaTagSerializer         → MangaTagRead

Compatibilidad JSON: Los campos de respuesta mantienen los mismos nombres que
DRF para no romper el frontend Vue3. Las diferencias:
  - `tags` en MangaDetail incluye el tag_id + tag_descripcion (idéntico a DRF)
  - `cover_url` se calcula en el router (no en el schema, para evitar I/O en Pydantic)
"""

from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Any


# ── Schemas embebidos (para anidamiento en MangaDetail) ───────────────────────

class MangaTagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    manga: int           # FK manga_id
    manga_titulo: str | None = None
    tag: int             # FK tag_id
    tag_descripcion: str | None = None
    vigente: bool


class MangaCoverRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    manga: int
    manga_titulo: str | None = None
    url_imagen: str
    url_absoluta: str | None = None   # URL normalizada (CDN)
    tipo_cover: str
    vigente: bool


class MangaAltTituloRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    manga: int
    manga_titulo: str | None = None
    titulo_alternativo: str
    codigo_lenguaje: str
    vigente: bool


class MangaAutorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    manga: int
    manga_titulo: str | None = None
    autor: int
    autor_nombre: str | None = None
    rol: str
    vigente: bool


# ── MangaCard (listados / home) ───────────────────────────────────────────────

class MangaCard(BaseModel):
    """
    Schema ligero para listas y grids (home, librería).
    Equivale a MangaCardSerializer de DRF.
    Excluye: sinopsis, autores, fechas.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str | None
    titulo: str
    tipo_serie: str
    cover_url: str | None = None
    demografia: int | None
    demografia_display: str | None = None
    dem_color: str | None = None
    estado_display: str | None = None
    vistas: int
    erotico: bool


# ── MangaDetail (detalle completo) ────────────────────────────────────────────

class MangaDetail(BaseModel):
    """
    Schema completo. Equivale a MangaSerializer de DRF.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str | None
    titulo: str
    sinopsis: str | None
    estado: int
    estado_display: str | None = None
    demografia: int
    demografia_display: str | None = None
    dem_color: str | None = None
    cover_url: str | None = None
    autor: int
    autor_display: str | None = None
    fecha_lanzamiento: date | None
    creado_en: datetime
    actualizado_en: datetime
    vigente: bool
    vistas: int
    codigo: str | None
    tipo_serie: str
    erotico: bool
    tags: list[MangaTagRead] = []


# ── Create / Update ───────────────────────────────────────────────────────────

class MangaCreate(BaseModel):
    """Payload para POST /mangas/. Equivale a los campos escribibles de MangaSerializer."""
    titulo: str = Field(..., max_length=200)
    sinopsis: str | None = None
    estado: int = Field(..., description="FK a estado")
    demografia: int = Field(..., description="FK a demografia")
    tipo_serie: str = Field(
        default="manga",
        pattern="^(manga|manhwa|manhua|one shot|novel|doujinshi|comic)$"
    )
    autor: int = Field(..., description="FK a autores")
    fecha_lanzamiento: date | None = None
    vigente: bool = True
    codigo: str | None = Field(default=None, max_length=50)
    erotico: bool = False
    # cover_image se maneja como UploadFile separado en el endpoint (multipart)


class MangaUpdate(BaseModel):
    """Payload para PATCH /mangas/{id}/. Todos los campos son opcionales."""
    titulo: str | None = Field(default=None, max_length=200)
    sinopsis: str | None = None
    estado: int | None = None
    demografia: int | None = None
    tipo_serie: str | None = Field(
        default=None,
        pattern="^(manga|manhwa|manhua|one shot|novel|doujinshi|comic)$"
    )
    autor: int | None = None
    fecha_lanzamiento: date | None = None
    vigente: bool | None = None
    codigo: str | None = None
    erotico: bool | None = None


# ── AltTitulo Create ──────────────────────────────────────────────────────────

class MangaAltTituloCreate(BaseModel):
    manga: int
    titulo_alternativo: str = Field(..., max_length=200)
    codigo_lenguaje: str = Field(..., max_length=10)
    vigente: bool = True


# ── Cover Create ──────────────────────────────────────────────────────────────

class MangaCoverCreate(BaseModel):
    manga: int
    url_imagen: str = Field(..., max_length=255)
    tipo_cover: str = Field(default="main", pattern="^(main|thumbnail|banner|extra)$")
    vigente: bool = True


# ── MangaAutor Create ─────────────────────────────────────────────────────────

class MangaAutorCreate(BaseModel):
    manga: int
    autor: int
    rol: str = Field(default="author", pattern="^(author|illustrator|writer|editor)$")
    vigente: bool = True


# ── MangaTag Create ───────────────────────────────────────────────────────────

class MangaTagCreate(BaseModel):
    manga: int
    tag: int
    vigente: bool = True


# ── Paginación ────────────────────────────────────────────────────────────────

class PaginationMeta(BaseModel):
    count: int
    pages: int
    page: int
    page_size: int
    next: str | None = None
    previous: str | None = None


class MangaCardPage(BaseModel):
    """Respuesta paginada de MangaCard. Equivale al formato StandardResultsPagination de DRF."""
    pagination: PaginationMeta
    results: list[MangaCard]
