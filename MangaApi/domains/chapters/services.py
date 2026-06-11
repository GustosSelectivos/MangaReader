import logging
import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import settings
from . import repository as repo

logger = logging.getLogger(__name__)

class ChapterService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_chapters(self, page: int, page_size: int, manga_id: int | None, search: str | None, ordering: str):
        return await repo.get_chapters(
            self.db, page=page, page_size=page_size,
            manga_id=manga_id, search=search, ordering=ordering
        )

    async def get_chapter(self, chapter_id: int):
        return await repo.get_chapter(self.db, chapter_id)

    async def create_chapter(self, data: dict):
        return await repo.create_chapter(self.db, data)

    async def update_chapter(self, chapter_id: int, data: dict):
        return await repo.update_chapter(self.db, chapter_id, data)

    async def delete_chapter(self, chapter_id: int):
        return await repo.delete_chapter(self.db, chapter_id)

    async def fetch_chapter(self, manga_id: int, chapter_num: int, url: str, series_code: str):
        manga_obj = await repo.get_manga_for_chapter(self.db, manga_id)
        if not manga_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Manga con ID {manga_id} no encontrado.",
            )

        worker_payload = {
            "url": url,
            "series_title": manga_obj.titulo,
            "chapter_number": chapter_num,
            "series_code": series_code,
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    f"{settings.WORKER_URL}/download",
                    json=worker_payload,
                    headers={"X-API-Key": settings.WORKER_API_KEY, "Content-Type": "application/json"},
                )
            if resp.status_code == 200:
                return resp.json()
            else:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Worker rechazó la tarea: {resp.text}",
                )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="El worker no respondió a tiempo.",
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"No se pudo conectar al worker: {exc}",
            )

    async def get_worker_status(self):
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(
                    f"{settings.WORKER_URL}/status",
                    headers={"X-API-Key": settings.WORKER_API_KEY},
                )
            if resp.status_code == 200:
                data = resp.json()
                data["status"] = "online"
                return data
            return {"status": "error", "error": f"Worker retornó {resp.status_code}"}
        except Exception:
            return {"status": "offline"}
