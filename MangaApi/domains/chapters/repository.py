"""
domains/chapters/repository.py
==============================
Queries async para el dominio de Chapters.
"""

from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Chapter
from domains.mangas.models import Manga


async def get_chapters(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 24,
    manga_param: str | None = None,
    search: str | None = None,
    ordering: str = "capitulo_numero",
) -> tuple[list[Chapter], int]:
    q = select(Chapter).options(selectinload(Chapter.manga))

    if manga_param:
        if manga_param.isdigit():
            q = q.where(Chapter.manga_id == int(manga_param))
        else:
            q = q.join(Manga).where(Manga.slug == manga_param)
    if search:
        q = q.where(Chapter.titulo.ilike(f"%{search}%"))

    _ORDER_MAP = {
        "capitulo_numero": Chapter.capitulo_numero,
        "-capitulo_numero": Chapter.capitulo_numero.desc(),
        "id": Chapter.id,
        "-id": Chapter.id.desc(),
    }
    order_col = _ORDER_MAP.get(ordering, Chapter.capitulo_numero)
    q = q.order_by(order_col)

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    skip = (page - 1) * page_size
    result = await db.execute(q.offset(skip).limit(page_size))
    return result.scalars().all(), total or 0


async def get_chapter(db: AsyncSession, chapter_id: int) -> Chapter | None:
    return await db.get(Chapter, chapter_id, options=[selectinload(Chapter.manga)])


async def create_chapter(db: AsyncSession, data: dict) -> Chapter:
    obj = Chapter(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def update_chapter(db: AsyncSession, chapter_id: int, data: dict) -> Chapter | None:
    obj = await db.get(Chapter, chapter_id)
    if not obj:
        return None
    for k, v in data.items():
        if v is not None:
            setattr(obj, k, v)
    await db.flush()
    await db.refresh(obj)
    return obj


async def delete_chapter(db: AsyncSession, chapter_id: int) -> bool:
    obj = await db.get(Chapter, chapter_id)
    if not obj:
        return False
    await db.delete(obj)
    return True


async def get_manga_for_chapter(db: AsyncSession, manga_id: int) -> Manga | None:
    """Verifica que el manga existe antes de disparar el worker."""
    return await db.get(Manga, manga_id)
