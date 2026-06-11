from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from .services import CatalogService

async def get_catalog_service(db: AsyncSession = Depends(get_db)) -> CatalogService:
    return CatalogService(db)
