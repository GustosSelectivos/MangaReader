"""
domains/chapters/models.py
==========================
Modelos SQLAlchemy para el dominio de Chapters:
  - Chapter → apicore_chapter

El campo `pages` es JSON (dict/list) que almacena las URLs de las páginas.
En SQLAlchemy 2.0 se mapea con el tipo JSON.
"""

from decimal import Decimal
from sqlalchemy import BigInteger, ForeignKey, Index, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Chapter(Base):
    """Tabla: apicore_chapter"""
    __tablename__ = "apicore_chapter"

    id: Mapped[int] = mapped_column("CHR_ID", BigInteger, primary_key=True, autoincrement=True)
    manga_id: Mapped[int] = mapped_column(
        "CHR_MANGA_ID", ForeignKey("apicore_manga.MNG_ID"), nullable=False
    )
    capitulo_numero: Mapped[Decimal] = mapped_column(
        "CHR_CAPITULO_NUMERO", Numeric(precision=6, scale=2), nullable=False
    )
    titulo: Mapped[str | None] = mapped_column("CHR_TITULO", String(200), nullable=True)
    volumen_numero: Mapped[Decimal | None] = mapped_column(
        "CHR_VOLUMEN_NUMERO", Numeric(precision=6, scale=2), nullable=True
    )
    pages: Mapped[dict | None] = mapped_column("CHR_PAGES", JSON, nullable=True)

    # ── Relación ──────────────────────────────────────────────────────────────
    manga: Mapped["Manga"] = relationship("Manga", lazy="noload")  # type: ignore[name-defined]

    # ── Índice compuesto (replica el de Django) ───────────────────────────────
    __table_args__ = (
        Index("chapter_manga_num_idx", "CHR_MANGA_ID", "CHR_CAPITULO_NUMERO"),
    )
