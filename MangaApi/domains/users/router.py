"""
domains/users/router.py
=======================
APIRouter para usuarios y autenticación.

Reemplaza:
  - CurrentUserView        → GET /auth/me
  - CurrentUserPermissionsView → GET /auth/permissions
  - UsersListView          → GET /auth/users
  - JWT endpoints de simplejwt → POST /auth/token, POST /auth/token/refresh

NOTA: Este router no implementa registro de usuarios (POST /auth/register)
ya que la lógica de hashing de contraseñas de Django (PBKDF2) debe
ser replicada con cuidado. Se provee un endpoint de login que verifica
el hash de Django directamente usando passlib.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.concurrency import run_in_threadpool

from core.database import get_db
from core.security import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_optional_user,
    require_staff,
    pwd_context
)
from core.limiter import limiter
from .dependencies import get_auth_service, get_user_service
from .services import AuthService, UserService
from . import repository as repo
from .schemas import (
    TokenRefreshRequest,
    TokenRefreshResponse,
    TokenResponse,
    UserListItem,
    UserMeResponse,
    UserPermissionsResponse,
    UserProfileRead,
    UserProfileUpdate,
    UsersListResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth & Users"])


# ── Login (reemplaza simplejwt TokenObtainPairView) ───────────────────────────

@router.post("/token", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Login con username/password. Retorna access + refresh token.
    Verifica el hash PBKDF2 de Django (compatible con usuarios existentes).
    """
    return await auth_service.login(form_data.username, form_data.password)


@router.post("/token/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    payload: TokenRefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresca el access token usando el refresh token."""
    return await auth_service.refresh_token(payload.refresh)


from core.security import token_blacklist
import time

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Revoca el token actual guardando su 'jti' en una Blacklist en memoria.
    """
    jti = current_user.get("jti")
    exp = current_user.get("exp")
    
    if not jti or not exp:
        return {"msg": "Token inválido para revocación"}

    # Guardar en diccionario en memoria
    token_blacklist[jti] = exp
            
    return {"msg": "Sesión cerrada correctamente"}


# ── Me (GET /auth/me) ─────────────────────────────────────────────────────────

@router.get("/me", response_model=UserMeResponse)
async def get_me(
    current_user: dict | None = Depends(get_optional_user),
):
    """
    Equivale a CurrentUserView de DRF.
    Retorna datos del usuario autenticado o {authenticated: False}.
    """
    if not current_user:
        return UserMeResponse(authenticated=False)

    return UserMeResponse(
        authenticated=True,
        id=current_user.get("user_id"),
        username=current_user.get("username"),
        email=current_user.get("email"),
        is_staff=current_user.get("is_staff"),
        is_superuser=current_user.get("is_superuser"),
        groups=current_user.get("groups", []),
        profile=current_user.get("profile"),
    )


# ── Permissions (GET /auth/permissions) ──────────────────────────────────────

@router.get("/permissions", response_model=UserPermissionsResponse)
async def get_permissions(
    current_user: dict | None = Depends(get_optional_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Equivale a CurrentUserPermissionsView de DRF.
    Permisos globales del usuario basados en AccessGrant con object_id='*'.
    """
    if not current_user:
        return UserPermissionsResponse(authenticated=False)

    if current_user.get("is_superuser"):
        return UserPermissionsResponse(
            authenticated=True,
            permissions=["*"],
            groups=current_user.get("groups", []),
        )

    perms, groups = await auth_service.get_user_permissions(current_user["user_id"])

    return UserPermissionsResponse(
        authenticated=True,
        permissions=perms,
        groups=groups,
    )


# ── Users list (GET /auth/users) ──────────────────────────────────────────────

@router.get("/users", response_model=UsersListResponse,
            dependencies=[Depends(require_staff)])
async def list_users(
    q: str = Query(default=""),
    user_service: UserService = Depends(get_user_service),
):
    """Equivale a UsersListView de DRF. Solo staff/admin."""
    users = await user_service.list_users(search=q or None)
    items = [UserListItem.model_validate(u) for u in users]
    return UsersListResponse(count=len(items), results=items)


# ── User Profile (PATCH /auth/users/{user_id}/profile) ───────────────────────

@router.patch("/users/{user_id}/profile", response_model=UserProfileRead,
              dependencies=[Depends(require_staff)])
async def update_user_profile(
    user_id: int,
    data: UserProfileUpdate,
    user_service: UserService = Depends(get_user_service),
):
    """Actualiza el perfil de un usuario (solo staff/admin)."""
    profile = await user_service.update_profile(user_id, data.model_dump(exclude_none=True))
    return profile
