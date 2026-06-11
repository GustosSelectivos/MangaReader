from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select, and_, or_, text

from core.security import pwd_context, create_access_token, create_refresh_token, _decode_token
from domains.dac.models import AccessGrant, DacPermission
from . import repository as repo


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def login(self, username: str, password: str) -> dict:
        user = await repo.get_user_by_username(self.db, username)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            # Ejecutar el hashing en un thread pool para no bloquear el Event Loop principal
            is_valid = await run_in_threadpool(pwd_context.verify, password, user.password)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciales inválidas.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        groups = await repo.get_user_groups(self.db, user.id)
        profile = user.profile.profile if user.profile else "home_only"

        token_data = {
            "user_id": user.id,
            "username": user.username,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "profile": profile,
            "groups": groups,
        }
        return {
            "access": create_access_token(token_data),
            "refresh": create_refresh_token({"user_id": user.id}),
        }

    async def refresh_token(self, refresh_token_str: str) -> dict:
        claims = _decode_token(refresh_token_str)
        user_id = claims.get("user_id")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido.")

        user = await repo.get_user_by_id(self.db, user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inactivo.")

        groups = await repo.get_user_groups(self.db, user.id)
        profile = user.profile.profile if user.profile else "home_only"

        new_access = create_access_token({
            "user_id": user.id,
            "username": user.username,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "profile": profile,
            "groups": groups,
        })
        return {"access": new_access}

    async def get_user_permissions(self, user_id: int) -> tuple[list[str], list[str]]:
        groups = await repo.get_user_groups(self.db, user_id)

        group_ids_result = await self.db.execute(
            text("SELECT id FROM auth_group WHERE name IN :names"),
            {"names": tuple(groups) if groups else ("__none__",)}
        )
        group_ids = [r[0] for r in group_ids_result.fetchall()]

        grants_q = await self.db.execute(
            select(DacPermission.codename)
            .join(AccessGrant, AccessGrant.permission_id == DacPermission.id)
            .where(
                and_(
                    or_(
                        AccessGrant.user_id == user_id,
                        AccessGrant.group_id.in_(group_ids) if group_ids else False,
                    ),
                    AccessGrant.object_id == "*",
                    AccessGrant.allow == True,  # noqa: E712
                )
            )
        )
        perms = sorted(set(row[0] for row in grants_q.fetchall()))
        return perms, groups


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_users(self, search: str | None = None):
        return await repo.list_users(self.db, search=search)

    async def update_profile(self, user_id: int, data: dict):
        profile = await repo.update_user_profile(self.db, user_id, data)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil de usuario no encontrado.",
            )
        return profile
