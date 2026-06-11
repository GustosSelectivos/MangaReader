"""
domains/mangas/router.py
========================
APIRouter principal de mangas.

Decisión: Los endpoints de escritura usan Depends(require_dac_write("manga")).
Los endpoints de lectura son públicos, pero filtran NSFW según el perfil.
La lógica de negocio reside en MangaService (Clean Architecture).
"""

import logging
from math import ceil
from typing import Optional

from fastapi import (
    APIRouter, BackgroundTasks, Depends, File, Form,
    HTTPException, Query, UploadFile, status,
)

from core.security import get_current_user, get_optional_user
from domains.dac.dependencies import require_dac_write, require_nsfw_access
from domains.mangas.services import MangaService
from domains.mangas.dependencies import get_manga_service

from .schemas import (
    MangaAltTituloCreate, MangaAltTituloRead,
    MangaAutorCreate, MangaAutorRead,
    MangaCard, MangaCardPage, MangaCoverCreate, MangaCoverRead,
    MangaCreate, MangaDetail,
    MangaTagCreate, MangaTagRead,
    MangaUpdate, PaginationMeta,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mangas", tags=["Mangas"])


# ── LIST + CREATE ─────────────────────────────────────────────────────────────

@router.get("", response_model=MangaCardPage)
async def list_mangas(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
    ordering: str = Query(default="-creado_en"),
    search: str | None = Query(default=None),
    titulo: str | None = Query(default=None),
    estado: str | None = Query(default=None),
    demografia: str | None = Query(default=None),
    type: str | None = Query(default=None),
    autor: int | None = Query(default=None),
    vigente: bool | None = Query(default=None),
    can_see_nsfw: bool = Depends(require_nsfw_access),
    service: MangaService = Depends(get_manga_service),
):
    items, total = await service.get_mangas_list(
        page=page,
        page_size=page_size,
        can_see_nsfw=can_see_nsfw,
        titulo=titulo,
        estado_desc=estado,
        demografia_desc=demografia,
        tipo_serie=type,
        autor_id=autor,
        vigente=vigente,
        ordering=ordering,
        search=search,
    )
    pages = ceil(total / page_size) if page_size else 1
    return MangaCardPage(
        pagination=PaginationMeta(count=total, pages=pages, page=page, page_size=page_size),
        results=[service.to_card(m) for m in items],
    )


@router.post("", response_model=MangaDetail, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_dac_write("manga"))])
async def create_manga(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    service: MangaService = Depends(get_manga_service),
    # Campos del manga como Form (para soportar multipart con cover_image)
    titulo: str = Form(...),
    sinopsis: str | None = Form(default=None),
    estado: int = Form(...),
    demografia: int = Form(...),
    tipo_serie: str = Form(default="manga"),
    autor: int = Form(...),
    fecha_lanzamiento: str | None = Form(default=None),
    vigente: bool = Form(default=True),
    codigo: str | None = Form(default=None),
    erotico: bool = Form(default=False),
    cover_image: UploadFile | None = File(default=None),
):
    data = {
        "titulo": titulo, "sinopsis": sinopsis, "estado": estado,
        "demografia": demografia, "tipo_serie": tipo_serie, "autor": autor,
        "fecha_lanzamiento": fecha_lanzamiento, "vigente": vigente,
        "codigo": codigo, "erotico": erotico,
    }
    manga_obj = await service.create_manga(data)

    # B2: inicializar carpetas y subir cover (BackgroundTask para no bloquear)
    if manga_obj.codigo:
        background_tasks.add_task(_init_b2_folders_bg, manga_obj.codigo)

    if cover_image and manga_obj.codigo:
        background_tasks.add_task(
            _upload_cover_bg, manga_obj.id, manga_obj.codigo, cover_image
        )

    return service.to_detail(manga_obj)


# ── RANDOM ────────────────────────────────────────────────────────────────────

@router.get("/random", response_model=list[MangaCard])
async def random_mangas(
    can_see_nsfw: bool = Depends(require_nsfw_access),
    service: MangaService = Depends(get_manga_service),
):
    """
    Equivale al action 'random' del MangaViewSet.
    """
    items = await service.get_random_mangas(count=5, can_see_nsfw=can_see_nsfw)
    return [service.to_card(m) for m in items]


# ── GET BY ID OR SLUG ─────────────────────────────────────────────────────────


@router.get("/{lookup}", response_model=MangaDetail)
async def get_manga(
    lookup: str,
    can_see_nsfw: bool = Depends(require_nsfw_access),
    service: MangaService = Depends(get_manga_service),
):
    """
    Lookup por ID numérico o por slug.
    """
    manga_obj = None
    if lookup.isdigit():
        manga_obj = await service.get_manga_by_id(int(lookup), can_see_nsfw)
    else:
        manga_obj = await service.get_manga_by_slug(lookup, can_see_nsfw)

    if not manga_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manga no encontrado.")
    return service.to_detail(manga_obj)


# ── UPDATE ─────────────────────────────────────────────────────────────────────

@router.patch("/{manga_id}", response_model=MangaDetail,
              dependencies=[Depends(require_dac_write("manga"))])
async def update_manga(
    manga_id: int,
    background_tasks: BackgroundTasks,
    service: MangaService = Depends(get_manga_service),
    titulo: str | None = Form(default=None),
    sinopsis: str | None = Form(default=None),
    estado: int | None = Form(default=None),
    demografia: int | None = Form(default=None),
    tipo_serie: str | None = Form(default=None),
    autor: int | None = Form(default=None),
    vigente: bool | None = Form(default=None),
    codigo: str | None = Form(default=None),
    erotico: bool | None = Form(default=None),
    cover_image: UploadFile | None = File(default=None),
):
    data = {k: v for k, v in {
        "titulo": titulo, "sinopsis": sinopsis, "estado": estado,
        "demografia": demografia, "tipo_serie": tipo_serie, "autor": autor,
        "vigente": vigente, "codigo": codigo, "erotico": erotico,
    }.items() if v is not None}

    manga_obj = await service.update_manga(manga_id, data)
    if not manga_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manga no encontrado.")

    if cover_image and manga_obj.codigo:
        background_tasks.add_task(
            _upload_cover_bg, manga_obj.id, manga_obj.codigo, cover_image
        )

    return service.to_detail(manga_obj)


# ── INCREMENT VIEW ─────────────────────────────────────────────────────────────

@router.post("/{manga_id}/increment-view", response_model=dict)
async def increment_view(manga_id: int, service: MangaService = Depends(get_manga_service)):
    new_vistas = await service.increment_view_count(manga_id)
    if new_vistas is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manga no encontrado.")
    return {"id": manga_id, "vistas": new_vistas}


# ── HOME ──────────────────────────────────────────────────────────────────────

home_router = APIRouter(prefix="/home", tags=["Home"])


@home_router.get("", response_model=dict)
async def get_home(service: MangaService = Depends(get_manga_service)):
    data = await service.get_home_data()
    return {
        "populars": [service.to_card(m) for m in data["populars"]],
        "trending": [service.to_card(m) for m in data["trending"]],
        "latest": [service.to_card(m) for m in data["latest"]],
        "most_viewed": [service.to_card(m) for m in data["most_viewed"]],
    }


# ── B2 PRESIGNED URL ─────────────────────────────────────────────────────────

b2_router = APIRouter(prefix="/b2", tags=["B2 Storage"])


@b2_router.post("/sign", response_model=dict,
                dependencies=[Depends(get_current_user)])
async def get_presigned_url(
    file_path: str = Form(...),
    content_type: str = Form(default="image/webp"),
):
    from infrastructure.b2_client import get_presigned_url as _get_url
    url = await _get_url(file_path, content_type)
    if not url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo generar la URL pre-firmada.",
        )
    return {"url": url}


# ── Background tasks (B2 async) ───────────────────────────────────────────────

async def _init_b2_folders_bg(codigo: str) -> None:
    try:
        from infrastructure.b2_client import initialize_manga_folders
        await initialize_manga_folders(codigo)
    except Exception as exc:
        logger.warning("Failed to init B2 folders for %s: %s", codigo, exc)


async def _upload_cover_bg(manga_id: int, codigo: str, cover_file: UploadFile) -> None:
    try:
        from infrastructure.cover_service import CoverUploadService, CoverUploadError
        from core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            service = CoverUploadService(db)
            await service.attach_cover(manga_id, codigo, cover_file)
            await db.commit()
    except Exception as exc:
        logger.error("Cover upload failed for manga %s: %s", codigo, exc)
