from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from .services import AuthService, UserService

async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)

async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)
