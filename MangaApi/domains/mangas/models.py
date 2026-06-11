"""
domains/mangas/models.py
========================
Modelos SQLAlchemy para el dominio de Mangas:
  - Manga           → apicore_manga
  - MangaAltTitulo  → apicore_manga_alt_titulo
  - MangaCover      → apicore_manga_cover
  - MangaAutor      → apicore_manga_autor
  - MangaTag        → apicore_manga_tag

Relaciones mapeadas para permitir joins eficientes con selectinload/joinedload.
La lógica de auto-slug (Django save()) se migra al service/repository.
"""

import enum
from datetime import date, datetime
from sqlalchemy import (
    BigInteger, Boolean, Date, DateTime, ForeignKey,
    Index, Numeric, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


# ── Enums ─────────────────────────────────────────────────────────────────────

class TipoSerieEnum(str, enum.Enum):
    manga = "manga"
    manhwa = "manhwa"
    manhua = "manhua"
    one_shot = "one shot"
    novel = "novel"
    doujinshi = "doujinshi"
    comic = "comic"


class TipoCoverEnum(str, enum.Enum):
    main = "main"
    thumbnail = "thumbnail"
    banner = "banner"
    extra = "extra"


class RolAutorEnum(str, enum.Enum):
    author = "author"
    illustrator = "illustrator"
    writer = "writer"
    editor = "editor"


# ── Modelos ───────────────────────────────────────────────────────────────────

class Manga(Base):
    """Tabla: apicore_manga"""
    __tablename__ = "apicore_manga"

    id: Mapped[int] = mapped_column("MNG_ID", BigInteger, primary_key=True, autoincrement=True)
    codigo: Mapped[str | None] = mapped_column("MNG_CODIGO", String(50), unique=True, nullable=True)
    titulo: Mapped[str] = mapped_column("MNG_TITULO", String(200), nullable=False)
    sinopsis: Mapped[str | None] = mapped_column("MNG_SINOPSIS", Text, nullable=True)
    estado_id: Mapped[int] = mapped_column("MNG_ESTADO_ID", ForeignKey("apicore_estados.EST_ID"), nullable=False)
    demografia_id: Mapped[int] = mapped_column("MNG_DEMOGRAFIA_ID", ForeignKey("apicore_demografia.DEM_ID"), nullable=False)
    tipo_serie: Mapped[str] = mapped_column("MNG_TIPO_SERIE", String(20), nullable=False, default="manga", index=True)
    autor_id: Mapped[int] = mapped_column("MNG_AUTOR_ID", ForeignKey("apicore_autores.AUT_ID"), nullable=False)
    fecha_lanzamiento: Mapped[date | None] = mapped_column("MNG_FECHA_LANZAMIENTO", Date, nullable=True)
    creado_en: Mapped[datetime] = mapped_column("MNG_CREACION", DateTime, nullable=False, server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column("MNG_ACTUALIZACION", DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    vigente: Mapped[bool] = mapped_column("MNG_VIGENTE", Boolean, nullable=False, default=True)
    vistas: Mapped[int] = mapped_column("MNG_VISTA", BigInteger, nullable=False, default=0)
    erotico: Mapped[bool] = mapped_column("MNG_EROTICO", Boolean, nullable=False, default=False)
    slug: Mapped[str | None] = mapped_column("MNG_SLUG", String(255), unique=True, nullable=True)

    # ── Relaciones ────────────────────────────────────────────────────────────
    estado: Mapped["Estado"] = relationship("Estado", lazy="noload")             # type: ignore[name-defined]
    demografia: Mapped["Demografia"] = relationship("Demografia", lazy="noload") # type: ignore[name-defined]
    autor: Mapped["Autor"] = relationship("Autor", lazy="noload")                # type: ignore[name-defined]
    covers: Mapped[list["MangaCover"]] = relationship("MangaCover", back_populates="manga", lazy="noload")
    alt_titulos: Mapped[list["MangaAltTitulo"]] = relationship("MangaAltTitulo", back_populates="manga", lazy="noload")
    manga_autores: Mapped[list["MangaAutor"]] = relationship("MangaAutor", back_populates="manga", lazy="noload")
    manga_tags: Mapped[list["MangaTag"]] = relationship("MangaTag", back_populates="manga", lazy="noload")


class MangaAltTitulo(Base):
    """Tabla: apicore_manga_alt_titulo"""
    __tablename__ = "apicore_manga_alt_titulo"

    id: Mapped[int] = mapped_column("MAT_ID", BigInteger, primary_key=True, autoincrement=True)
    manga_id: Mapped[int] = mapped_column("MAT_MANGA_ID", ForeignKey("apicore_manga.MNG_ID"), nullable=False)
    titulo_alternativo: Mapped[str] = mapped_column("MAT_TITULO_ALTERNATIVO", String(200), nullable=False)
    codigo_lenguaje: Mapped[str] = mapped_column("MAT_CODIGO_LENGUAJE", String(10), nullable=False)
    vigente: Mapped[bool] = mapped_column("MAT_VIGENTE", Boolean, nullable=False, default=True)

    manga: Mapped["Manga"] = relationship("Manga", back_populates="alt_titulos", lazy="noload")


class MangaCover(Base):
    """Tabla: apicore_manga_cover"""
    __tablename__ = "apicore_manga_cover"

    id: Mapped[int] = mapped_column("MCV_ID", BigInteger, primary_key=True, autoincrement=True)
    manga_id: Mapped[int] = mapped_column("MCV_MANGA_ID", ForeignKey("apicore_manga.MNG_ID"), nullable=False)
    url_imagen: Mapped[str] = mapped_column("MCV_URL_IMAGEN", String(255), nullable=False)
    tipo_cover: Mapped[str] = mapped_column("MCV_COVER_TIPO", String(20), nullable=False, default="main")
    vigente: Mapped[bool] = mapped_column("MCV_VIGENTE", Boolean, nullable=False, default=True)

    manga: Mapped["Manga"] = relationship("Manga", back_populates="covers", lazy="noload")


class MangaAutor(Base):
    """Tabla: apicore_manga_autor"""
    __tablename__ = "apicore_manga_autor"

    id: Mapped[int] = mapped_column("MAU_ID", BigInteger, primary_key=True, autoincrement=True)
    manga_id: Mapped[int] = mapped_column("MAU_MANGA_ID", ForeignKey("apicore_manga.MNG_ID"), nullable=False)
    autor_id: Mapped[int] = mapped_column("MAU_AUTOR_ID", ForeignKey("apicore_autores.AUT_ID"), nullable=False)
    rol: Mapped[str] = mapped_column("MAU_ROL", String(20), nullable=False, default="author")
    vigente: Mapped[bool] = mapped_column("MAU_VIGENTE", Boolean, nullable=False, default=True)

    manga: Mapped["Manga"] = relationship("Manga", back_populates="manga_autores", lazy="noload")
    autor: Mapped["Autor"] = relationship("Autor", lazy="noload")  # type: ignore[name-defined]


class MangaTag(Base):
    """Tabla: apicore_manga_tag"""
    __tablename__ = "apicore_manga_tag"

    id: Mapped[int] = mapped_column("MTG_ID", BigInteger, primary_key=True, autoincrement=True)
    manga_id: Mapped[int] = mapped_column("MTG_MANGA_ID", ForeignKey("apicore_manga.MNG_ID"), nullable=False)
    tag_id: Mapped[int] = mapped_column("MTG_TAG_ID", ForeignKey("apicore_tags.TAG_ID"), nullable=False)
    vigente: Mapped[bool] = mapped_column("MTG_VIGENTE", Boolean, nullable=False, default=True)

    manga: Mapped["Manga"] = relationship("Manga", back_populates="manga_tags", lazy="noload")
    tag: Mapped["Tag"] = relationship("Tag", lazy="noload")  # type: ignore[name-defined]
