# Forcing reload
import re
import logging
import uuid
import random
from slugify import slugify
from typing import Sequence
import time
from cachetools import TTLCache

from domains.mangas.interfaces import IMangaRepository
from domains.mangas.models import Manga
from domains.mangas.schemas import MangaDetail, MangaCard, MangaTagRead
from core.config import settings

logger = logging.getLogger(__name__)

_SLUG_SAFE_RE = re.compile(r"[^a-zA-Z0-9._-]")


def normalize_cover_url(url: str | None) -> str | None:
    if not url:
        return None
    cover_cdn = settings.CDN_COVER_BASE
    chapter_cdn = settings.CDN_CHAPTER_BASE

    if cover_cdn in url or chapter_cdn in url:
        return url

    path: str | None = None
    if "/file/MangaApi/" in url:
        path = url.split("/file/MangaApi/")[1]
    elif "/MangaApi/" in url:
        path = url.split("/MangaApi/")[1]

    if not path:
        return url

    if path.startswith("covers/"):
        return f"{cover_cdn}/file/MangaApi/{path}"
    elif path.startswith("chapters/"):
        return f"{chapter_cdn}/file/MangaApi/{path}"
    return url


def get_main_cover_url(manga: Manga) -> str | None:
    covers = manga.covers if manga.covers else []
    main = next((c for c in covers if c.vigente and c.tipo_cover == "main"), None)
    if not main:
        main = next((c for c in covers if c.vigente), None)
    if main:
        return normalize_cover_url(main.url_imagen)
    return None


class MangaService:
    """Orquestador de casos de uso para el dominio de Mangas."""
    _home_cache: dict = {}
    _home_cache_time: float = 0
    _HOME_TTL = 300  # 5 minutos
    _list_cache = TTLCache(maxsize=128, ttl=60)  # 1 minuto

    def __init__(self, repo: IMangaRepository):
        self.repo = repo

    async def get_mangas_list(self, **kwargs):
        """Obtiene la lista de mangas y la cantidad total con caché."""
        cache_key = frozenset(kwargs.items())
        if cache_key in self._list_cache:
            return self._list_cache[cache_key]

        result = await self.repo.get_mangas(**kwargs)
        self._list_cache[cache_key] = result
        return result

    async def get_manga_by_id(self, manga_id: int, can_see_nsfw: bool = False) -> Manga | None:
        return await self.repo.get_manga_by_id(manga_id, can_see_nsfw)

    async def get_manga_by_slug(self, slug: str, can_see_nsfw: bool = False) -> Manga | None:
        return await self.repo.get_manga_by_slug(slug, can_see_nsfw)

    async def generate_unique_slug(self, titulo: str, exclude_id: int | None = None) -> str:
        base_slug = slugify(titulo)
        slug = base_slug

        existing = await self.repo.get_manga_by_slug(slug, can_see_nsfw=True)
        if existing and (not exclude_id or existing.id != exclude_id):
            slug = f"{base_slug}-{str(uuid.uuid4())[:8]}"

        return slug

    async def create_manga(self, data: dict) -> Manga:
        mapped = {
            "titulo": data["titulo"],
            "sinopsis": data.get("sinopsis"),
            "estado_id": data["estado"],
            "demografia_id": data["demografia"],
            "tipo_serie": data.get("tipo_serie", "manga"),
            "autor_id": data["autor"],
            "fecha_lanzamiento": data.get("fecha_lanzamiento"),
            "vigente": data.get("vigente", True),
            "codigo": data.get("codigo"),
            "erotico": data.get("erotico", False),
        }
        mapped["slug"] = await self.generate_unique_slug(data["titulo"])
        return await self.repo.create_manga(mapped)

    async def update_manga(self, manga_id: int, data: dict) -> Manga | None:
        mapped: dict = {}
        fk_map = {"estado": "estado_id", "demografia": "demografia_id", "autor": "autor_id"}
        for k, v in data.items():
            if v is None:
                continue
            mapped[fk_map.get(k, k)] = v

        if "titulo" in mapped:
            mapped["slug"] = await self.generate_unique_slug(mapped["titulo"], exclude_id=manga_id)

        return await self.repo.update_manga(manga_id, mapped)

    async def increment_view_count(self, manga_id: int) -> int | None:
        return await self.repo.increment_view_count(manga_id)

    async def get_random_mangas(self, count: int = 5, can_see_nsfw: bool = False) -> list[Manga]:
        """Lógica de selección aleatoria (sampling vs probing)."""
        total = await self.repo.get_total_count(can_see_nsfw)
        if total == 0:
            return []

        if total < 100000:
            all_ids = await self.repo.get_all_ids(can_see_nsfw)
            sample_ids = random.sample(list(all_ids), min(count, len(all_ids)))
            return list(await self.repo.get_mangas_by_ids(sample_ids, can_see_nsfw))

        max_id = await self.repo.get_max_id(can_see_nsfw)
        if not max_id:
            return []

        selected_ids: set[int] = set()
        visited_ids: set[int] = set()
        attempts = 0
        max_attempts = 20

        while len(selected_ids) < count and attempts < max_attempts:
            pk = random.randint(1, max_id)
            if pk in visited_ids:
                attempts += 1
                continue
            visited_ids.add(pk)

            # Usar la query rápida que solo trae el ID
            manga_id = await self.repo.get_manga_id_gte(pk, can_see_nsfw)
            if manga_id and manga_id not in selected_ids:
                selected_ids.add(manga_id)
            attempts += 1

        selected: list[Manga] = []
        if selected_ids:
            # Traer todas las instancias y relaciones en una sola query optimizada
            mangas_result = await self.repo.get_mangas_by_ids(list(selected_ids), can_see_nsfw)
            selected.extend(list(mangas_result))

        if len(selected) < count:
            exclude_ids = {m.id for m in selected}
            needed = count - len(selected)
            extras = await self.repo.get_mangas_excluding_ids(exclude_ids, needed, can_see_nsfw)
            selected.extend(list(extras))

        return selected

    async def get_home_data(self) -> dict[str, Sequence[Manga]]:
        now = time.time()
        if self._home_cache and (now - MangaService._home_cache_time < MangaService._HOME_TTL):
            return self._home_cache
            
        data = await self.repo.get_home_data()
        MangaService._home_cache = data
        MangaService._home_cache_time = now
        return data

    # -- Pydantic Mappers --
    def to_detail(self, manga: Manga) -> MangaDetail:
        return MangaDetail(
            id=manga.id,
            slug=manga.slug,
            titulo=manga.titulo,
            sinopsis=manga.sinopsis,
            estado=manga.estado_id,
            estado_display=manga.estado.descripcion if manga.estado else None,
            demografia=manga.demografia_id,
            demografia_display=manga.demografia.descripcion if manga.demografia else None,
            dem_color=manga.demografia.color if manga.demografia else None,
            cover_url=get_main_cover_url(manga),
            autor=manga.autor_id,
            autor_display=manga.autor.nombre if manga.autor else None,
            fecha_lanzamiento=manga.fecha_lanzamiento,
            creado_en=manga.creado_en,
            actualizado_en=manga.actualizado_en,
            vigente=manga.vigente,
            vistas=manga.vistas,
            codigo=manga.codigo,
            tipo_serie=manga.tipo_serie,
            erotico=manga.erotico,
            tags=[
                MangaTagRead(
                    id=t.id,
                    manga=t.manga_id,
                    tag=t.tag_id,
                    tag_descripcion=t.tag.descripcion if t.tag else None,
                    vigente=t.vigente,
                )
                for t in manga.manga_tags
            ] if manga.manga_tags else [],
        )

    def to_card(self, manga: Manga) -> MangaCard:
        return MangaCard(
            id=manga.id,
            slug=manga.slug,
            titulo=manga.titulo,
            tipo_serie=manga.tipo_serie,
            cover_url=get_main_cover_url(manga),
            demografia=manga.demografia_id,
            demografia_display=manga.demografia.descripcion if manga.demografia else None,
            dem_color=manga.demografia.color if manga.demografia else None,
            estado_display=manga.estado.descripcion if manga.estado else None,
            vistas=manga.vistas,
            erotico=manga.erotico,
        )
