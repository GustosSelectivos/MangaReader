from sqlalchemy.ext.asyncio import AsyncSession
from cachetools import TTLCache

from . import repository as repo

class CatalogService:
    # Caché estático de 1 hora para listas maestras.
    _cache = TTLCache(maxsize=128, ttl=3600)

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Autores ───────────────────────────────────────────────────────────────
    async def get_autores(self, **kwargs):
        # Autores can have many items, no cache or short cache. For now, no cache.
        return await repo.get_autores(self.db, **kwargs)

    async def get_autor(self, autor_id: int):
        return await repo.get_autor(self.db, autor_id)

    async def create_autor(self, data: dict):
        return await repo.create_autor(self.db, data)

    async def update_autor(self, autor_id: int, data: dict):
        return await repo.update_autor(self.db, autor_id, data)

    async def delete_autor(self, autor_id: int):
        return await repo.delete_autor(self.db, autor_id)

    # ── Estados ───────────────────────────────────────────────────────────────
    async def get_estados(self, **kwargs):
        cache_key = frozenset([("type", "estados")] + list(kwargs.items()))
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = await repo.get_estados(self.db, **kwargs)
        self._cache[cache_key] = result
        return result

    async def get_estado(self, estado_id: int):
        return await repo.get_estado(self.db, estado_id)

    async def create_estado(self, data: dict):
        self._cache.clear()
        return await repo.create_estado(self.db, data)

    async def update_estado(self, estado_id: int, data: dict):
        self._cache.clear()
        return await repo.update_estado(self.db, estado_id, data)

    async def delete_estado(self, estado_id: int):
        self._cache.clear()
        return await repo.delete_estado(self.db, estado_id)

    # ── Demografías ───────────────────────────────────────────────────────────
    async def get_demografias(self, **kwargs):
        cache_key = frozenset([("type", "demografias")] + list(kwargs.items()))
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = await repo.get_demografias(self.db, **kwargs)
        self._cache[cache_key] = result
        return result

    async def get_demografia(self, dem_id: int):
        return await repo.get_demografia(self.db, dem_id)

    async def create_demografia(self, data: dict):
        self._cache.clear()
        return await repo.create_demografia(self.db, data)

    async def update_demografia(self, dem_id: int, data: dict):
        self._cache.clear()
        return await repo.update_demografia(self.db, dem_id, data)

    async def delete_demografia(self, dem_id: int):
        self._cache.clear()
        return await repo.delete_demografia(self.db, dem_id)

    # ── Tags ──────────────────────────────────────────────────────────────────
    async def get_tags(self, **kwargs):
        cache_key = frozenset([("type", "tags")] + list(kwargs.items()))
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = await repo.get_tags(self.db, **kwargs)
        self._cache[cache_key] = result
        return result

    async def get_tag(self, tag_id: int):
        return await repo.get_tag(self.db, tag_id)

    async def create_tag(self, data: dict):
        self._cache.clear()
        return await repo.create_tag(self.db, data)

    async def update_tag(self, tag_id: int, data: dict):
        self._cache.clear()
        return await repo.update_tag(self.db, tag_id, data)

    async def delete_tag(self, tag_id: int):
        self._cache.clear()
        return await repo.delete_tag(self.db, tag_id)
