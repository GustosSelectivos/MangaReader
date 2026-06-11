"""
domains/users/repository.py
============================
Queries async para el dominio de usuarios.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import User, UserProfile


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    return await db.get(
        User, user_id,
        options=[selectinload(User.profile)]
    )


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(
        select(User)
        .options(selectinload(User.profile))
        .where(User.username == username)
    )
    return result.scalar_one_or_none()


async def list_users(
    db: AsyncSession,
    search: str | None = None,
    limit: int = 200,
) -> list[User]:
    q = select(User).order_by(User.username)
    if search:
        q = q.where(User.username.ilike(f"%{search}%"))
    result = await db.execute(q.limit(limit))
    return result.scalars().all()


async def get_or_create_user_profile(db: AsyncSession, user_id: int) -> UserProfile:
    """
    Reemplaza el signal post_save de Django.
    Se llama explícitamente en el endpoint de registro/creación de usuario.
    """
    profile = await db.scalar(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    if not profile:
        profile = UserProfile(user_id=user_id, profile="home_only")
        db.add(profile)
        await db.flush()
        await db.refresh(profile)
    return profile


async def update_user_profile(
    db: AsyncSession, user_id: int, data: dict
) -> UserProfile | None:
    profile = await db.scalar(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    if not profile:
        return None
    for k, v in data.items():
        if v is not None:
            setattr(profile, k, v)
    await db.flush()
    await db.refresh(profile)
    return profile


async def get_user_groups(db: AsyncSession, user_id: int) -> list[str]:
    """Retorna los nombres de grupos del usuario (tabla auth_user_groups + auth_group)."""
    from sqlalchemy import text
    result = await db.execute(
        text("""
            SELECT ag.name
            FROM auth_group ag
            JOIN auth_user_groups aug ON ag.id = aug.group_id
            WHERE aug.user_id = :user_id
        """),
        {"user_id": user_id}
    )
    return [row[0] for row in result.fetchall()]
