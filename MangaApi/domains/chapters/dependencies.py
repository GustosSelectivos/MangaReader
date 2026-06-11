from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from .services import ChapterService

async def get_chapter_service(db: AsyncSession = Depends(get_db)) -> ChapterService:
    return ChapterService(db)
