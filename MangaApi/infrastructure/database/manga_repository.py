from typing import Sequence
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from domains.mangas.interfaces import IMangaRepository
from domains.mangas.models import Manga, MangaAltTitulo, MangaCover, MangaAutor, MangaTag
from domains.catalog.models import Estado, Demografia


class MangaRepository(IMangaRepository):
    """Implementación concreta de IMangaRepository usando SQLAlchemy."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _manga_base_query(self, can_see_nsfw: bool = False):
        q = (
            select(Manga)
            .options(
                joinedload(Manga.estado),
                joinedload(Manga.demografia),
                joinedload(Manga.autor),
                selectinload(Manga.covers),
                selectinload(Manga.manga_tags).joinedload(MangaTag.tag),
            )
        )
        if not can_see_nsfw:
            q = q.where(Manga.erotico == False)  # noqa: E712
        return q

    async def get_mangas(
        self,
        page: int = 1,
        page_size: int = 24,
        can_see_nsfw: bool = False,
        titulo: str | None = None,
        estado_desc: str | None = None,
        demografia_desc: str | None = None,
        tipo_serie: str | None = None,
        autor_id: int | None = None,
        fecha_from: str | None = None,
        fecha_to: str | None = None,
        vigente: bool | None = None,
        erotico: bool | None = None,
        ordering: str = "-creado_en",
        search: str | None = None,
    ) -> tuple[Sequence[Manga], int]:
        q = self._manga_base_query(can_see_nsfw)

        if titulo:
            q = q.where(Manga.titulo.ilike(f"%{titulo}%"))
        if estado_desc:
            q = q.join(Estado, Manga.estado_id == Estado.id).where(
                Estado.descripcion.ilike(f"%{estado_desc}%")
            )
        if demografia_desc:
            q = q.join(Demografia, Manga.demografia_id == Demografia.id).where(
                Demografia.descripcion.ilike(f"%{demografia_desc}%")
            )
        if tipo_serie:
            q = q.where(Manga.tipo_serie.ilike(tipo_serie))
        if autor_id:
            q = q.where(Manga.autor_id == autor_id)
        if fecha_from:
            q = q.where(Manga.fecha_lanzamiento >= fecha_from)
        if fecha_to:
            q = q.where(Manga.fecha_lanzamiento <= fecha_to)
        if vigente is not None:
            q = q.where(Manga.vigente == vigente)
        if erotico is not None and can_see_nsfw:
            q = q.where(Manga.erotico == erotico)

        if search:
            q = q.where(
                Manga.titulo.ilike(f"%{search}%") | Manga.sinopsis.ilike(f"%{search}%")
            )

        _ORDER_MAP = {
            "vistas": Manga.vistas,
            "-vistas": Manga.vistas.desc(),
            "titulo": Manga.titulo,
            "-titulo": Manga.titulo.desc(),
            "creado_en": Manga.creado_en,
            "-creado_en": Manga.creado_en.desc(),
            "actualizado_en": Manga.actualizado_en,
            "-actualizado_en": Manga.actualizado_en.desc(),
        }
        order_col = _ORDER_MAP.get(ordering, Manga.creado_en.desc())
        q = q.order_by(order_col)

        count_q = q.with_only_columns(func.count(Manga.id)).order_by(None)
        total = await self.db.scalar(count_q)
        skip = (page - 1) * page_size
        result = await self.db.execute(q.offset(skip).limit(page_size))
        return result.unique().scalars().all(), total or 0

    async def get_manga_by_id(self, manga_id: int, can_see_nsfw: bool = False) -> Manga | None:
        q = self._manga_base_query(can_see_nsfw).where(Manga.id == manga_id)
        result = await self.db.execute(q)
        return result.scalar_one_or_none()

    async def get_manga_by_slug(self, slug: str, can_see_nsfw: bool = False) -> Manga | None:
        q = self._manga_base_query(can_see_nsfw).where(Manga.slug == slug)
        result = await self.db.execute(q)
        return result.scalar_one_or_none()

    async def create_manga(self, data: dict) -> Manga:
        obj = Manga(**data)
        self.db.add(obj)
        await self.db.flush()
        return await self.get_manga_by_id(obj.id, can_see_nsfw=True)  # type: ignore

    async def update_manga(self, manga_id: int, data: dict) -> Manga | None:
        obj = await self.db.get(Manga, manga_id)
        if not obj:
            return None
        for k, v in data.items():
            if v is not None:
                setattr(obj, k, v)
        await self.db.flush()
        return await self.get_manga_by_id(manga_id, can_see_nsfw=True)

    async def increment_view_count(self, manga_id: int) -> int | None:
        await self.db.execute(
            update(Manga)
            .where(Manga.id == manga_id)
            .values(vistas=Manga.vistas + 1)
        )
        result = await self.db.execute(select(Manga.vistas).where(Manga.id == manga_id))
        return result.scalar_one_or_none()

    # -- Primitivas para lógica aleatoria --
    async def get_total_count(self, can_see_nsfw: bool = False) -> int:
        q = select(Manga.id)
        if not can_see_nsfw:
            q = q.where(Manga.erotico == False)
        return await self.db.scalar(select(func.count()).select_from(q.subquery())) or 0

    async def get_max_id(self, can_see_nsfw: bool = False) -> int | None:
        q = select(func.max(Manga.id))
        if not can_see_nsfw:
            q = q.where(Manga.erotico == False)
        return await self.db.scalar(q)

    async def get_all_ids(self, can_see_nsfw: bool = False) -> Sequence[int]:
        q = select(Manga.id)
        if not can_see_nsfw:
            q = q.where(Manga.erotico == False)
        result = await self.db.execute(q)
        return result.scalars().all()

    async def get_mangas_by_ids(self, ids: list[int], can_see_nsfw: bool = False) -> Sequence[Manga]:
        q = (
            select(Manga)
            .options(
                joinedload(Manga.estado),
                joinedload(Manga.demografia),
                joinedload(Manga.covers),
            )
            .where(Manga.id.in_(ids))
        )
        if not can_see_nsfw:
            q = q.where(Manga.erotico == False)
        result = await self.db.execute(q)
        return result.unique().scalars().all()

    async def get_manga_id_gte(self, pk: int, can_see_nsfw: bool = False) -> int | None:
        q = select(Manga.id)
        if not can_see_nsfw:
            q = q.where(Manga.erotico == False)
        q = q.where(Manga.id >= pk).order_by(Manga.id).limit(1)
        return await self.db.scalar(q)

    async def get_manga_gte_id(self, pk: int, can_see_nsfw: bool = False) -> Manga | None:
        q = self._manga_base_query(can_see_nsfw).where(Manga.id >= pk).order_by(Manga.id).limit(1)
        result = await self.db.execute(q)
        return result.scalar_one_or_none()

    async def get_mangas_excluding_ids(self, exclude_ids: set[int], limit: int, can_see_nsfw: bool = False) -> Sequence[Manga]:
        q = self._manga_base_query(can_see_nsfw).where(Manga.id.notin_(exclude_ids)).limit(limit)
        result = await self.db.execute(q)
        return result.scalars().all()

    # -- Home --
    async def get_home_data(self) -> dict[str, Sequence[Manga]]:
        base_q = (
            select(Manga)
            .options(
                joinedload(Manga.estado),
                joinedload(Manga.demografia),
                joinedload(Manga.covers),
            )
            .where(Manga.vigente == True, Manga.erotico == False)  # noqa: E712
        )

        populars = (await self.db.execute(base_q.order_by(Manga.vistas.desc()).limit(12))).unique().scalars().all()
        trending = (await self.db.execute(base_q.order_by(Manga.creado_en.desc()).limit(8))).unique().scalars().all()
        latest = (await self.db.execute(base_q.order_by(Manga.actualizado_en.desc()).limit(8))).unique().scalars().all()
        most_viewed = (await self.db.execute(base_q.order_by(Manga.vistas.desc()).limit(30))).unique().scalars().all()

        return {
            "populars": populars,
            "trending": trending,
            "latest": latest,
            "most_viewed": most_viewed,
        }

    async def get_manga_covers(self, manga_id: int) -> Sequence[MangaCover]:
        result = await self.db.execute(
            select(MangaCover).where(MangaCover.manga_id == manga_id)
        )
        return result.scalars().all()

    async def get_manga_alt_titulos(self, manga_id: int) -> Sequence[MangaAltTitulo]:
        result = await self.db.execute(
            select(MangaAltTitulo).where(MangaAltTitulo.manga_id == manga_id)
        )
        return result.scalars().all()
