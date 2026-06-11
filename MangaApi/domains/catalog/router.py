"""
domains/catalog/router.py
=========================
APIRouter para el catálogo de mantenedores.
Reemplaza: AutoresViewSet, EstadosViewSet, DemografiaViewSet, TagsViewSet (DRF).

Prefijos: /api/catalog/autores, /api/catalog/estados,
          /api/catalog/demografias, /api/catalog/tags
"""

from math import ceil
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_user
from core.pagination import paginate
from domains.dac.dependencies import require_dac_write
from .dependencies import get_catalog_service
from .services import CatalogService
from .schemas import (
    AutorCreate, AutorRead, AutorUpdate,
    DemografiaCreate, DemografiaRead, DemografiaUpdate,
    EstadoCreate, EstadoRead, EstadoUpdate,
    TagCreate, TagRead, TagUpdate,
)
from domains.mangas.schemas import PaginationMeta

router = APIRouter(prefix="/catalog", tags=["Catalog"])

# ── Autores ───────────────────────────────────────────────────────────────────

@router.get("/autores", response_model=dict)
async def list_autores(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
    search: str | None = Query(default=None),
    vigente: bool | None = Query(default=None),
    service: CatalogService = Depends(get_catalog_service),
):
    items, total = await service.get_autores(
        skip=(page - 1) * page_size, limit=page_size, search=search, vigente=vigente
    )
    return paginate([AutorRead.model_validate(i) for i in items], total, page, page_size)


@router.get("/autores/{autor_id}", response_model=AutorRead)
async def get_autor(autor_id: int, service: CatalogService = Depends(get_catalog_service)):
    obj = await service.get_autor(autor_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Autor no encontrado.")
    return obj


@router.post("/autores", response_model=AutorRead, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_dac_write("autor"))])
async def create_autor(data: AutorCreate, service: CatalogService = Depends(get_catalog_service)):
    return await service.create_autor(data.model_dump())


@router.patch("/autores/{autor_id}", response_model=AutorRead,
              dependencies=[Depends(require_dac_write("autor"))])
async def update_autor(autor_id: int, data: AutorUpdate, service: CatalogService = Depends(get_catalog_service)):
    obj = await service.update_autor(autor_id, data.model_dump(exclude_none=True))
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Autor no encontrado.")
    return obj


@router.delete("/autores/{autor_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_dac_write("autor"))])
async def delete_autor(autor_id: int, service: CatalogService = Depends(get_catalog_service)):
    if not await service.delete_autor(autor_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Autor no encontrado.")


# ── Estados ───────────────────────────────────────────────────────────────────

@router.get("/estados", response_model=list[EstadoRead])
async def list_estados(
    search: str | None = Query(default=None),
    service: CatalogService = Depends(get_catalog_service),
):
    items, _ = await service.get_estados(limit=500, search=search)
    return items


@router.get("/estados/{estado_id}", response_model=EstadoRead)
async def get_estado(estado_id: int, service: CatalogService = Depends(get_catalog_service)):
    obj = await service.get_estado(estado_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estado no encontrado.")
    return obj


@router.post("/estados", response_model=EstadoRead, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_dac_write("autor"))])
async def create_estado(data: EstadoCreate, service: CatalogService = Depends(get_catalog_service)):
    return await service.create_estado(data.model_dump())


@router.patch("/estados/{estado_id}", response_model=EstadoRead,
              dependencies=[Depends(require_dac_write("autor"))])
async def update_estado(estado_id: int, data: EstadoUpdate, service: CatalogService = Depends(get_catalog_service)):
    obj = await service.update_estado(estado_id, data.model_dump(exclude_none=True))
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estado no encontrado.")
    return obj


@router.delete("/estados/{estado_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_dac_write("autor"))])
async def delete_estado(estado_id: int, service: CatalogService = Depends(get_catalog_service)):
    if not await service.delete_estado(estado_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estado no encontrado.")


# ── Demografías ───────────────────────────────────────────────────────────────

@router.get("/demografias", response_model=list[DemografiaRead])
async def list_demografias(
    search: str | None = Query(default=None),
    service: CatalogService = Depends(get_catalog_service),
):
    items, _ = await service.get_demografias(limit=500, search=search)
    return items


@router.get("/demografias/{dem_id}", response_model=DemografiaRead)
async def get_demografia(dem_id: int, service: CatalogService = Depends(get_catalog_service)):
    obj = await service.get_demografia(dem_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demografía no encontrada.")
    return obj


@router.post("/demografias", response_model=DemografiaRead, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_dac_write("autor"))])
async def create_demografia(data: DemografiaCreate, service: CatalogService = Depends(get_catalog_service)):
    return await service.create_demografia(data.model_dump())


@router.patch("/demografias/{dem_id}", response_model=DemografiaRead,
              dependencies=[Depends(require_dac_write("autor"))])
async def update_demografia(dem_id: int, data: DemografiaUpdate, service: CatalogService = Depends(get_catalog_service)):
    obj = await service.update_demografia(dem_id, data.model_dump(exclude_none=True))
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demografía no encontrada.")
    return obj


@router.delete("/demografias/{dem_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_dac_write("autor"))])
async def delete_demografia(dem_id: int, service: CatalogService = Depends(get_catalog_service)):
    if not await service.delete_demografia(dem_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demografía no encontrada.")


# ── Tags ──────────────────────────────────────────────────────────────────────

@router.get("/tags", response_model=list[TagRead])
async def list_tags(
    search: str | None = Query(default=None),
    service: CatalogService = Depends(get_catalog_service),
):
    items, _ = await service.get_tags(limit=500, search=search)
    return items


@router.get("/tags/{tag_id}", response_model=TagRead)
async def get_tag(tag_id: int, service: CatalogService = Depends(get_catalog_service)):
    obj = await service.get_tag(tag_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag no encontrado.")
    return obj


@router.post("/tags", response_model=TagRead, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_dac_write("autor"))])
async def create_tag(data: TagCreate, service: CatalogService = Depends(get_catalog_service)):
    return await service.create_tag(data.model_dump())


@router.patch("/tags/{tag_id}", response_model=TagRead,
              dependencies=[Depends(require_dac_write("autor"))])
async def update_tag(tag_id: int, data: TagUpdate, service: CatalogService = Depends(get_catalog_service)):
    obj = await service.update_tag(tag_id, data.model_dump(exclude_none=True))
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag no encontrado.")
    return obj


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_dac_write("autor"))])
async def delete_tag(tag_id: int, service: CatalogService = Depends(get_catalog_service)):
    if not await service.delete_tag(tag_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag no encontrado.")
