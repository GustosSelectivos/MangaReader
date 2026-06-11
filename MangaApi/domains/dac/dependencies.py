"""
domains/dac/dependencies.py
============================
Dependencias FastAPI para el sistema DAC.

Reemplaza:
  - DRFDACPermission (clase de permisos DRF)
  - CanViewNSFW, IsModeratorOrAdmin, CanAccessAdminPanel (checkers.py)

Uso en routers:
    @router.put("/{manga_id}")
    async def update_manga(
        ...,
        _: None = Depends(dac_write_required("manga", get_manga_id)),
    ):

Decisión: Las dependencias reciben el token ya decodificado y hacen la
consulta DAC solo en endpoints que modifican datos (POST, PUT, PATCH, DELETE).
Los endpoints GET no requieren DAC (como en DRFDACPermission.has_permission).
"""

import logging
from typing import Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_user, get_optional_user
from .repository import has_permission, get_content_type_id

logger = logging.getLogger(__name__)

# Mapeo de nombre de dominio → (app_label, model_name) para buscar content_type_id
MODEL_CONTENT_TYPE_MAP: dict[str, tuple[str, str]] = {
    "manga":   ("apicore", "manga"),
    "chapter": ("apicore", "chapter"),
    "autor":   ("apicore", "autores"),
}


# ── Fábrica de dependencias DAC ───────────────────────────────────────────────

def require_dac_write(model_name: str):
    """
    Genera una dependencia que verifica el permiso 'write' del usuario sobre
    el modelo indicado (con object_id='*' → acceso global al modelo).

    Equivale a DRFDACPermission.has_object_permission con codename='write'.
    """
    async def _check(
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user),
    ) -> None:
        user_id: int = current_user["user_id"]
        is_superuser: bool = current_user.get("is_superuser", False)

        if is_superuser:
            return  # Fast-path: superusuarios siempre pasan

        mapping = MODEL_CONTENT_TYPE_MAP.get(model_name)
        if not mapping:
            logger.error("Modelo DAC desconocido: %s", model_name)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Configuración DAC incorrecta para modelo '{model_name}'.",
            )

        app_label, model_str = mapping
        ct_id = await get_content_type_id(db, app_label, model_str)
        if ct_id is None:
            logger.warning("ContentType no encontrado para %s.%s", app_label, model_str)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No se pudo verificar permisos. Contacta al administrador.",
            )

        allowed = await has_permission(
            db=db,
            user_id=user_id,
            is_superuser=is_superuser,
            content_type_id=ct_id,
            object_id="*",
            codename="write",
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para modificar este recurso.",
            )

    return _check


# ── Dependencias de perfil (reemplazan checkers.py) ──────────────────────────

async def require_nsfw_access(
    current_user: dict | None = Depends(get_optional_user),
) -> bool:
    """
    Retorna True si el usuario puede ver contenido NSFW.
    No lanza excepción; el router filtra en el queryset.
    Equivale a CanViewNSFW.has_object_permission de Django.
    """
    if not current_user:
        return False
    # El perfil se incluye en el JWT al momento del login
    profile = current_user.get("profile", "home_only")
    nsfw_profiles = {"premium", "moderator", "admin"}
    return profile in nsfw_profiles


async def require_moderator_or_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Equivale a IsModeratorOrAdmin de checkers.py."""
    profile = current_user.get("profile", "home_only")
    if profile not in ("moderator", "admin") and not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere perfil moderador o administrador.",
        )
    return current_user


async def require_admin_panel_access(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Equivale a CanAccessAdminPanel de checkers.py."""
    profile = current_user.get("profile", "home_only")
    if profile not in ("moderator", "admin") and not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere acceso al panel de administración.",
        )
    return current_user
