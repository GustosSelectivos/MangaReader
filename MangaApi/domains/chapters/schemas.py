"""
domains/chapters/schemas.py
============================
Schemas Pydantic v2 para el dominio de Chapters.

Reemplaza: ChapterSerializer (DRF).
La lógica de CDN (USE_CDN setting) se replica en el campo `pages`
usando un validator que normaliza las URLs al dominio CDN configurado.
"""

from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from core.config import settings


def _normalize_page_urls(pages: dict | None) -> dict | None:
    """
    Convierte URLs de Backblaze raw al CDN configurado.
    Equivale a la lógica get_pages() del ChapterSerializer de DRF.
    """
    if not pages or "images" not in pages:
        return {"images": []}

    images = pages.get("images", [])
    cdn_images = []
    for url in images:
        if isinstance(url, str) and "backblazeb2.com" in url:
            try:
                path = url.split("backblazeb2.com")[1]
                cdn_images.append(f"{settings.CDN_CHAPTER_BASE}{path}")
            except IndexError:
                cdn_images.append(url)
        else:
            cdn_images.append(url)
    return {"images": cdn_images}


# ── Schemas ───────────────────────────────────────────────────────────────────

class ChapterBase(BaseModel):
    manga: int = Field(..., description="FK a manga")
    capitulo_numero: Decimal = Field(..., ge=0, max_digits=6, decimal_places=2)
    titulo: str | None = Field(default=None, max_length=200)
    volumen_numero: Decimal | None = Field(default=None, ge=0, max_digits=6, decimal_places=2)


class ChapterCreate(ChapterBase):
    pages: dict | None = None


class ChapterUpdate(BaseModel):
    titulo: str | None = None
    volumen_numero: Decimal | None = None
    pages: dict | None = None


class ChapterDetail(BaseModel):
    """
    Equivale a ChapterSerializer de DRF.
    El campo `pages` se normaliza al CDN en el model_validator.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    manga: int
    manga_titulo: str | None = None
    capitulo_numero: Decimal
    titulo: str | None
    volumen_numero: Decimal | None
    pages: dict | None = None

    @model_validator(mode="after")
    def normalize_pages(self) -> "ChapterDetail":
        self.pages = _normalize_page_urls(self.pages)
        return self


# ── Worker Payloads ───────────────────────────────────────────────────────────

class ChapterFetchRequest(BaseModel):
    """
    Payload para POST /chapters/fetch.
    Equivale al cuerpo que procesaba chapter_view::fetch() en Django.
    """
    url: str = Field(..., description="URL de la fuente a scrapear")
    manga_id: int
    chapter_num: float = Field(default=1.0, ge=0)
    series_code: str | None = None


class ChapterFetchResponse(BaseModel):
    status: str
    worker_response: dict | None = None


class ChapterCompletedPayload(BaseModel):
    """Callback del worker cuando un capítulo fue subido exitosamente."""
    series_title: str
    chapter_number: float
    status: str


class WorkerStatusResponse(BaseModel):
    status: str
    error: str | None = None
