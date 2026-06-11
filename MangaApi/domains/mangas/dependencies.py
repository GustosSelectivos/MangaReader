from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from domains.mangas.interfaces import IMangaRepository
from infrastructure.database.manga_repository import MangaRepository
from domains.mangas.services import MangaService


def get_manga_repository(db: AsyncSession = Depends(get_db)) -> IMangaRepository:
    """Provee la implementación concreta del repositorio."""
    return MangaRepository(db)


def get_manga_service(repo: IMangaRepository = Depends(get_manga_repository)) -> MangaService:
    """Provee el servicio orquestador con el repositorio inyectado."""
    return MangaService(repo)
