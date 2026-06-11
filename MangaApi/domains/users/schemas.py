"""
domains/users/schemas.py
========================
Schemas Pydantic v2 para el dominio de usuarios.

Reemplaza:
  - La respuesta de CurrentUserView (DRF) → UserMeResponse
  - La respuesta de CurrentUserPermissionsView → UserPermissionsResponse
  - La respuesta de UsersListView → UsersListResponse
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ── Usuario autenticado ───────────────────────────────────────────────────────

class UserMeResponse(BaseModel):
    """
    Equivale a la respuesta de GET /auth/me/ (CurrentUserView de DRF).
    Preserva el mismo JSON para compatibilidad con el frontend.
    """
    authenticated: bool
    id: int | None = None
    username: str | None = None
    email: str | None = None
    is_staff: bool | None = None
    is_superuser: bool | None = None
    groups: list[str] = []
    profile: str | None = None        # Nuevo: perfil del UserProfile


class UserPermissionsResponse(BaseModel):
    """
    Equivale a GET /auth/permissions/ (CurrentUserPermissionsView de DRF).
    """
    authenticated: bool
    permissions: list[str] = []
    groups: list[str] = []


class UserListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: str


class UsersListResponse(BaseModel):
    count: int
    results: list[UserListItem]


# ── UserProfile ───────────────────────────────────────────────────────────────

class UserProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    profile: str
    profile_updated_at: datetime
    banned: bool
    ban_reason: str


class UserProfileUpdate(BaseModel):
    """Actualizar perfil de usuario (solo admin/staff)."""
    profile: str | None = Field(
        default=None,
        pattern="^(home_only|premium|moderator|admin)$"
    )
    banned: bool | None = None
    ban_reason: str | None = None


# ── Tokens JWT ────────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    """Respuesta del endpoint de login (compatible con simplejwt)."""
    access: str
    refresh: str


class TokenRefreshRequest(BaseModel):
    refresh: str


class TokenRefreshResponse(BaseModel):
    access: str
