"""
domains/dac/schemas.py
======================
Schemas Pydantic v2 para el sistema DAC.

Reemplaza:
  - GroupSerializer     → ProfileRead, ProfileCreate
  - AccessGrantSerializer → AccessGrantRead, AccessGrantCreate
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# ── Permisos DAC ──────────────────────────────────────────────────────────────

class DacPermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    codename: str
    name: str


# ── AccessGrant ───────────────────────────────────────────────────────────────

class AccessGrantRead(BaseModel):
    """Equivale a AccessGrantSerializer de DRF."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    group_id: int | None
    content_type_id: int
    object_id: str
    permission_id: int
    permission: DacPermissionRead | None = None
    allow: bool
    created: datetime


class AccessGrantCreate(BaseModel):
    """Payload para crear/actualizar un AccessGrant (endpoint grant de ProfileViewSet)."""
    codename: str = Field(..., description="Codename del permiso (ej. 'write')")
    model: str = Field(..., description="Nombre del modelo (ej. 'manga', 'chapter')")
    object_id: str = Field(default="*", description="ID del objeto o '*' para global")


# ── Profiles (Grupos Django) ──────────────────────────────────────────────────

class ProfileUserItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str


class ProfileRead(BaseModel):
    """Equivale a GroupSerializer de DRF."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class ProfileCreate(BaseModel):
    name: str = Field(..., max_length=150)


# ── Add/Remove User ───────────────────────────────────────────────────────────

class AddUserRequest(BaseModel):
    user_id: int


class GrantRequest(BaseModel):
    codename: str
    model: str
    object_id: str = "*"


# ── Stats / Audit ─────────────────────────────────────────────────────────────

class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    path: str
    method: str
    view_name: str
    allowed: bool
    status_code: int | None
    detail: str
    created: datetime
