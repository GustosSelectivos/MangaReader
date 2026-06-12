"""
domains/chapters/router.py
===========================
APIRouter para chapters.

Reemplaza:
  - ChapterViewSet → CRUD + fetch + completed + worker_status

Mejora: El proxy al worker usa httpx async (reemplaza requests síncrono).
"""

import logging
import os
from fastapi import APIRouter, Depends, HTTPException, Query, status
from core.database import get_db
from core.pagination import paginate
from core.security import get_current_user
from domains.dac.dependencies import require_dac_write
from . import repository as repo
from .schemas import (
    ChapterCreate, ChapterDetail, ChapterUpdate,
    ChapterFetchRequest, ChapterFetchResponse,
    ChapterCompletedPayload, WorkerStatusResponse,
)
from .dependencies import get_chapter_service
from .services import ChapterService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chapters", tags=["Chapters"])


def _to_detail(chapter) -> ChapterDetail:
    return ChapterDetail(
        id=chapter.id,
        manga=chapter.manga_id,
        manga_titulo=chapter.manga.titulo if chapter.manga else None,
        capitulo_numero=chapter.capitulo_numero,
        titulo=chapter.titulo,
        volumen_numero=chapter.volumen_numero,
        pages=chapter.pages,
    )


# ── LIST ──────────────────────────────────────────────────────────────────────

@router.get("", response_model=dict)
async def list_chapters(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=1000),
    manga: str | None = Query(default=None),
    search: str | None = Query(default=None),
    ordering: str = Query(default="capitulo_numero"),
    service: ChapterService = Depends(get_chapter_service),
):
    items, total = await service.list_chapters(
        page=page, page_size=page_size,
        manga_param=manga, search=search, ordering=ordering
    )
    return paginate([_to_detail(c) for c in items], total, page, page_size)


# ── GET ───────────────────────────────────────────────────────────────────────

@router.get("/{chapter_id}", response_model=ChapterDetail)
async def get_chapter(chapter_id: int, service: ChapterService = Depends(get_chapter_service)):
    obj = await service.get_chapter(chapter_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Capítulo no encontrado.")
    return _to_detail(obj)


# ── CREATE ────────────────────────────────────────────────────────────────────

@router.post("", response_model=ChapterDetail, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_dac_write("chapter"))])
async def create_chapter(data: ChapterCreate, service: ChapterService = Depends(get_chapter_service)):
    obj_data = {
        "manga_id": data.manga,
        "capitulo_numero": data.capitulo_numero,
        "titulo": data.titulo,
        "volumen_numero": data.volumen_numero,
        "pages": data.pages,
    }
    obj = await service.create_chapter(obj_data)
    return _to_detail(obj)


# ── UPDATE ────────────────────────────────────────────────────────────────────

@router.patch("/{chapter_id}", response_model=ChapterDetail,
              dependencies=[Depends(require_dac_write("chapter"))])
async def update_chapter(
    chapter_id: int, data: ChapterUpdate, service: ChapterService = Depends(get_chapter_service)
):
    obj = await service.update_chapter(chapter_id, data.model_dump(exclude_none=True))
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Capítulo no encontrado.")
    return _to_detail(obj)


# ── DELETE ────────────────────────────────────────────────────────────────────

@router.delete("/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_dac_write("chapter"))])
async def delete_chapter(chapter_id: int, service: ChapterService = Depends(get_chapter_service)):
    if not await service.delete_chapter(chapter_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Capítulo no encontrado.")


# ── FETCH (trigger worker) ────────────────────────────────────────────────────

@router.post("/fetch", response_model=ChapterFetchResponse)
async def fetch_chapter(
    payload: ChapterFetchRequest,
    current_user: dict = Depends(get_current_user),
    service: ChapterService = Depends(get_chapter_service),
):
    """
    Equivale a ChapterViewSet.fetch() de Django.
    MEJORA: Usa httpx async en lugar de requests síncrono, orquestado desde la capa de servicios.
    """
    worker_response = await service.fetch_chapter(
        manga_id=payload.manga_id,
        chapter_num=int(payload.chapter_num),
        url=payload.url,
        series_code=payload.series_code,
    )
    return ChapterFetchResponse(status="Task Started", worker_response=worker_response)


# ── COMPLETED (callback del worker) ───────────────────────────────────────────

@router.post("/completed", response_model=dict)
async def chapter_completed(payload: ChapterCompletedPayload):
    """
    Equivale a ChapterViewSet.completed() de Django.
    Callback que el worker llama cuando un capítulo está disponible.
    """
    logger.info(
        "✅ Callback recibido: %s #%s - %s",
        payload.series_title, payload.chapter_number, payload.status
    )
    # TODO: actualizar Chapter.status en BD cuando se agregue ese campo
    return {"status": "acknowledged"}


# ── WORKER STATUS ──────────────────────────────────────────────────────────────

@router.get("/worker-status", response_model=WorkerStatusResponse)
async def worker_status(service: ChapterService = Depends(get_chapter_service)):
    """
    Equivale a ChapterViewSet.worker_status() de Django.
    MEJORA: Usa httpx async.
    """
    status_data = await service.get_worker_status()
    return WorkerStatusResponse(**status_data)
