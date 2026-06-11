"""
domains/catalog/repository.py
==============================
CRUD async para los modelos de catálogo usando AsyncSession.
Cada función recibe la sesión como parámetro (sin estado propio).
"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Autor, Estado, Demografia, Tag


# ── Autores ───────────────────────────────────────────────────────────────────

async def get_autores(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    vigente: bool | None = None,
) -> tuple[list[Autor], int]:
    q = select(Autor)
    if search:
        q = q.where(Autor.nombre.ilike(f"%{search}%"))
    if vigente is not None:
        q = q.where(Autor.vigente == vigente)
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    result = await db.execute(q.offset(skip).limit(limit))
    return result.scalars().all(), total or 0


async def get_autor(db: AsyncSession, autor_id: int) -> Autor | None:
    return await db.get(Autor, autor_id)


async def create_autor(db: AsyncSession, data: dict) -> Autor:
    obj = Autor(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def update_autor(db: AsyncSession, autor_id: int, data: dict) -> Autor | None:
    obj = await db.get(Autor, autor_id)
    if not obj:
        return None
    for k, v in data.items():
        if v is not None:
            setattr(obj, k, v)
    await db.flush()
    await db.refresh(obj)
    return obj


async def delete_autor(db: AsyncSession, autor_id: int) -> bool:
    obj = await db.get(Autor, autor_id)
    if not obj:
        return False
    await db.delete(obj)
    return True


# ── Estados ───────────────────────────────────────────────────────────────────

async def get_estados(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
) -> tuple[list[Estado], int]:
    q = select(Estado)
    if search:
        q = q.where(Estado.descripcion.ilike(f"%{search}%"))
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    result = await db.execute(q.offset(skip).limit(limit))
    return result.scalars().all(), total or 0


async def get_estado(db: AsyncSession, estado_id: int) -> Estado | None:
    return await db.get(Estado, estado_id)


async def create_estado(db: AsyncSession, data: dict) -> Estado:
    obj = Estado(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def update_estado(db: AsyncSession, estado_id: int, data: dict) -> Estado | None:
    obj = await db.get(Estado, estado_id)
    if not obj:
        return None
    for k, v in data.items():
        if v is not None:
            setattr(obj, k, v)
    await db.flush()
    await db.refresh(obj)
    return obj


async def delete_estado(db: AsyncSession, estado_id: int) -> bool:
    obj = await db.get(Estado, estado_id)
    if not obj:
        return False
    await db.delete(obj)
    return True


# ── Demografía ────────────────────────────────────────────────────────────────

async def get_demografias(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
) -> tuple[list[Demografia], int]:
    q = select(Demografia)
    if search:
        q = q.where(Demografia.descripcion.ilike(f"%{search}%"))
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    result = await db.execute(q.offset(skip).limit(limit))
    return result.scalars().all(), total or 0


async def get_demografia(db: AsyncSession, dem_id: int) -> Demografia | None:
    return await db.get(Demografia, dem_id)


async def create_demografia(db: AsyncSession, data: dict) -> Demografia:
    obj = Demografia(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def update_demografia(db: AsyncSession, dem_id: int, data: dict) -> Demografia | None:
    obj = await db.get(Demografia, dem_id)
    if not obj:
        return None
    for k, v in data.items():
        if v is not None:
            setattr(obj, k, v)
    await db.flush()
    await db.refresh(obj)
    return obj


async def delete_demografia(db: AsyncSession, dem_id: int) -> bool:
    obj = await db.get(Demografia, dem_id)
    if not obj:
        return False
    await db.delete(obj)
    return True


# ── Tags ──────────────────────────────────────────────────────────────────────

async def get_tags(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
) -> tuple[list[Tag], int]:
    q = select(Tag)
    if search:
        q = q.where(Tag.descripcion.ilike(f"%{search}%"))
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    result = await db.execute(q.offset(skip).limit(limit))
    return result.scalars().all(), total or 0


async def get_tag(db: AsyncSession, tag_id: int) -> Tag | None:
    return await db.get(Tag, tag_id)


async def create_tag(db: AsyncSession, data: dict) -> Tag:
    obj = Tag(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def update_tag(db: AsyncSession, tag_id: int, data: dict) -> Tag | None:
    obj = await db.get(Tag, tag_id)
    if not obj:
        return None
    for k, v in data.items():
        if v is not None:
            setattr(obj, k, v)
    await db.flush()
    await db.refresh(obj)
    return obj


async def delete_tag(db: AsyncSession, tag_id: int) -> bool:
    obj = await db.get(Tag, tag_id)
    if not obj:
        return False
    await db.delete(obj)
    return True
