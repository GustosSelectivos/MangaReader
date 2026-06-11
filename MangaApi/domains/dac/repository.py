"""
domains/dac/repository.py
=========================
Lógica DAC async.

Migra y CORRIGE access_control.py de Django:
  - has_permission() → async, sin except: pass silenciadores
  - Acceso a BD a través de AsyncSession (no ContentType de Django)
  - Levanta excepciones explícitas en lugar de silenciarlas

Compatibilidad: Mantiene la misma lógica de precedencia:
  superusuario > owner > deny explícito > allow explícito > deny por defecto
"""

import logging
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AccessGrant, AuditLog, DacPermission, Owner, DjangoContentType

logger = logging.getLogger(__name__)


# ── Lookup de ContentType (equivalente a ContentType.objects.get_for_model) ───

async def get_content_type_id(
    db: AsyncSession, app_label: str, model_name: str
) -> int | None:
    """Devuelve el ID del content type dado app_label y nombre de modelo."""
    result = await db.execute(
        select(DjangoContentType).where(
            and_(
                DjangoContentType.app_label == app_label,
                DjangoContentType.model == model_name,
            )
        )
    )
    ct = result.scalar_one_or_none()
    return ct.id if ct else None


# ── has_permission (CORREGIDO: sin except: pass) ──────────────────────────────

async def has_permission(
    db: AsyncSession,
    user_id: int,
    is_superuser: bool,
    content_type_id: int,
    object_id: str,
    codename: str,
    user_group_ids: list[int] | None = None,
) -> bool:
    """
    Comprueba si el usuario tiene `codename` sobre el objeto especificado.

    Precedencia (igual que access_control.py de Django):
    1. Superusuario → True siempre
    2. Owner explícito → True
    3. AccessGrant de usuario con allow=False → False (DENY explícito)
    4. AccessGrant de usuario con allow=True → True
    5. AccessGrant de grupo con allow=False → False
    6. AccessGrant de grupo con allow=True → True
    7. Default → False

    MEJORA: Ya no silencia excepciones con except: pass.
    Si la BD falla, la excepción se propaga y el caller decide.
    """
    if is_superuser:
        return True

    # ── 1. Owner check ────────────────────────────────────────────────────────
    owner_q = await db.execute(
        select(Owner).where(
            and_(
                Owner.user_id == user_id,
                Owner.content_type_id == content_type_id,
                Owner.object_id == str(object_id),
            )
        )
    )
    if owner_q.scalar_one_or_none():
        return True

    # ── 2. Buscar permiso por codename ────────────────────────────────────────
    perm_q = await db.execute(
        select(DacPermission).where(DacPermission.codename == codename)
    )
    perm = perm_q.scalar_one_or_none()
    if not perm:
        return False  # El permiso ni existe → deny

    obj_ids = [str(object_id), "*"]

    # ── 3. User grants ────────────────────────────────────────────────────────
    user_grants_q = await db.execute(
        select(AccessGrant).where(
            and_(
                AccessGrant.user_id == user_id,
                AccessGrant.content_type_id == content_type_id,
                AccessGrant.object_id.in_(obj_ids),
                AccessGrant.permission_id == perm.id,
            )
        )
    )
    user_grants = user_grants_q.scalars().all()

    if any(not g.allow for g in user_grants):
        return False  # Deny explícito tiene precedencia
    if any(g.allow for g in user_grants):
        return True

    # ── 4. Group grants ───────────────────────────────────────────────────────
    if user_group_ids:
        group_grants_q = await db.execute(
            select(AccessGrant).where(
                and_(
                    AccessGrant.group_id.in_(user_group_ids),
                    AccessGrant.content_type_id == content_type_id,
                    AccessGrant.object_id.in_(obj_ids),
                    AccessGrant.permission_id == perm.id,
                )
            )
        )
        group_grants = group_grants_q.scalars().all()
        if any(not g.allow for g in group_grants):
            return False
        if any(g.allow for g in group_grants):
            return True

    return False  # Default: deny


# ── Audit Log (escritura async, se llama desde BackgroundTask) ────────────────

async def create_audit_log(
    db: AsyncSession,
    user_id: int | None,
    path: str,
    method: str,
    view_name: str,
    allowed: bool,
    status_code: int | None,
    content_type_id: int | None = None,
    object_id: str | None = None,
    detail: str = "",
) -> None:
    """
    Crea un registro de auditoría.
    MEJORA: Se llama desde BackgroundTask → no bloquea la respuesta HTTP.
    """
    log = AuditLog(
        user_id=user_id,
        path=path,
        method=method,
        view_name=view_name,
        allowed=allowed,
        status_code=status_code,
        content_type_id=content_type_id,
        object_id=object_id,
        detail=detail,
    )
    db.add(log)
    # No se hace commit aquí; el caller debe manejarlo (BackgroundTask con su propia sesión)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def get_or_create_permission(db: AsyncSession, codename: str) -> DacPermission:
    perm_q = await db.execute(
        select(DacPermission).where(DacPermission.codename == codename)
    )
    perm = perm_q.scalar_one_or_none()
    if not perm:
        perm = DacPermission(codename=codename, name=codename)
        db.add(perm)
        await db.flush()
        await db.refresh(perm)
    return perm


async def grant_permission_to_group(
    db: AsyncSession,
    group_id: int,
    content_type_id: int,
    object_id: str,
    codename: str,
    allow: bool = True,
) -> AccessGrant:
    perm = await get_or_create_permission(db, codename)

    # Buscar grant existente
    existing_q = await db.execute(
        select(AccessGrant).where(
            and_(
                AccessGrant.group_id == group_id,
                AccessGrant.content_type_id == content_type_id,
                AccessGrant.object_id == object_id,
                AccessGrant.permission_id == perm.id,
            )
        )
    )
    existing = existing_q.scalar_one_or_none()
    if existing:
        if existing.allow != allow:
            existing.allow = allow
            await db.flush()
        return existing

    grant = AccessGrant(
        group_id=group_id,
        content_type_id=content_type_id,
        object_id=object_id,
        permission_id=perm.id,
        allow=allow,
    )
    db.add(grant)
    await db.flush()
    await db.refresh(grant)
    return grant
