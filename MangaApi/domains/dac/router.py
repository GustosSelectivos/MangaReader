"""
domains/dac/router.py
======================
APIRouter para el sistema DAC (perfiles y grants).

Reemplaza:
  - ProfileViewSet → CRUD de grupos + add-user, remove-user, grant, grants
  - AccessGrantViewSet → lectura de grants
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from core.database import get_db
from core.security import get_current_user, require_staff
from .models import AccessGrant, AuthGroup, DacPermission
from .repository import grant_permission_to_group, get_content_type_id
from .schemas import (
    AccessGrantCreate, AccessGrantRead,
    AddUserRequest, AuditLogRead,
    DacPermissionRead, GrantRequest,
    ProfileCreate, ProfileRead,
)
from domains.dac.dependencies import MODEL_CONTENT_TYPE_MAP

router = APIRouter(prefix="/dac", tags=["DAC - Access Control"])


# ── Profiles (Grupos) ─────────────────────────────────────────────────────────

@router.get("/profiles", response_model=list[ProfileRead])
async def list_profiles(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    result = await db.execute(select(AuthGroup).order_by(AuthGroup.name))
    return result.scalars().all()


@router.post("/profiles", response_model=ProfileRead, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_staff)])
async def create_profile(data: ProfileCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.scalar(select(AuthGroup).where(AuthGroup.name == data.name))
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El perfil ya existe.")
    group = AuthGroup(name=data.name)
    db.add(group)
    await db.flush()
    await db.refresh(group)
    return group


@router.get("/profiles/{group_id}", response_model=ProfileRead)
async def get_profile(group_id: int, db: AsyncSession = Depends(get_db)):
    obj = await db.get(AuthGroup, group_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil no encontrado.")
    return obj


@router.delete("/profiles/{group_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_staff)])
async def delete_profile(group_id: int, db: AsyncSession = Depends(get_db)):
    obj = await db.get(AuthGroup, group_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil no encontrado.")
    await db.delete(obj)


@router.post("/profiles/{group_id}/add-user", response_model=dict,
             dependencies=[Depends(require_staff)])
async def add_user_to_profile(
    group_id: int,
    data: AddUserRequest,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        text("INSERT IGNORE INTO auth_user_groups (user_id, group_id) VALUES (:uid, :gid)"),
        {"uid": data.user_id, "gid": group_id},
    )
    return {"detail": "user added"}


@router.post("/profiles/{group_id}/remove-user", response_model=dict,
             dependencies=[Depends(require_staff)])
async def remove_user_from_profile(
    group_id: int,
    data: AddUserRequest,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        text("DELETE FROM auth_user_groups WHERE user_id = :uid AND group_id = :gid"),
        {"uid": data.user_id, "gid": group_id},
    )
    return {"detail": "user removed"}


@router.post("/profiles/{group_id}/grant", response_model=AccessGrantRead,
             dependencies=[Depends(require_staff)])
async def grant_to_profile(
    group_id: int,
    data: GrantRequest,
    db: AsyncSession = Depends(get_db),
):
    """Equivale a ProfileViewSet.grant() de DRF."""
    model_key = data.model.lower()
    mapping = {
        "manga": ("apicore", "manga"),
        "chapter": ("apicore", "chapter"),
        "autor": ("apicore", "autores"),
    }.get(model_key)

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Modelo desconocido: {model_key}",
        )

    ct_id = await get_content_type_id(db, mapping[0], mapping[1])
    if not ct_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ContentType no encontrado para {model_key}.",
        )

    grant = await grant_permission_to_group(
        db=db,
        group_id=group_id,
        content_type_id=ct_id,
        object_id=data.object_id,
        codename=data.codename,
    )
    return AccessGrantRead.model_validate(grant)


@router.get("/profiles/{group_id}/grants", response_model=list[AccessGrantRead],
            dependencies=[Depends(require_staff)])
async def get_profile_grants(group_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(AccessGrant)
        .options(selectinload(AccessGrant.permission))
        .where(AccessGrant.group_id == group_id)
    )
    return [AccessGrantRead.model_validate(g) for g in result.scalars().all()]


# ── AccessGrants (lectura) ────────────────────────────────────────────────────

@router.get("/grants", response_model=list[AccessGrantRead],
            dependencies=[Depends(require_staff)])
async def list_grants(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=100, le=500),
):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(AccessGrant)
        .options(selectinload(AccessGrant.permission))
        .limit(limit)
    )
    return [AccessGrantRead.model_validate(g) for g in result.scalars().all()]
