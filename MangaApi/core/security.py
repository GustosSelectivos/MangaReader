"""
core/security.py
================
Manejo de JWT: creación y verificación de tokens.
Reemplaza djangorestframework_simplejwt.

Decisión de diseño:
- Se usa `python-jose` porque es la lib recomendada por FastAPI oficialmente.
- El SECRET_KEY viene de config.py (pydantic-settings), nunca hardcodeado.
- La función `get_current_user` es la dependencia principal de autenticación;
  devuelve un dict con los claims del token (no hace query a BD por performance).
- La función `get_current_user_from_db` es opcional y hace query si se necesitan
  datos del usuario (perfil, grupos, etc.).
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from passlib.context import CryptContext

from core.config import settings
from core.database import get_db

# Esquema de seguridad para Swagger UI (Bearer token)
bearer_scheme = HTTPBearer(auto_error=False)

# Contexto de contraseñas compatible con Django (PBKDF2)
pwd_context = CryptContext(schemes=["django_pbkdf2_sha256"], deprecated="auto")


# ── Creación de tokens ────────────────────────────────────────────────────────

def create_access_token(data: dict) -> str:
    """Crea un JWT de acceso con expiración."""
    payload = data.copy()
    expire = datetime.now(timezone.utc) + settings.access_token_expire
    payload.update({"exp": expire, "type": "access"})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Crea un JWT de refresco con expiración más larga."""
    payload = data.copy()
    expire = datetime.now(timezone.utc) + settings.refresh_token_expire
    payload.update({"exp": expire, "type": "refresh"})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# ── Verificación de tokens ────────────────────────────────────────────────────

def _decode_token(token: str) -> dict[str, Any]:
    """Decodifica y valida un JWT. Lanza HTTPException si es inválido."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido o expirado: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Dependencias FastAPI ──────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    """
    Dependencia que retorna los claims del JWT sin consultar la BD.
    Úsala cuando solo necesitas user_id, is_superuser, etc.

    Lanza 401 si no hay token o es inválido.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se proporcionó token de autenticación.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _decode_token(credentials.credentials)


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any] | None:
    """
    Como get_current_user pero NO lanza error si no hay token.
    Úsala en endpoints públicos que adaptan su respuesta si el usuario está auth.
    Ej: /mangas/ oculta contenido erotico si no hay token.
    """
    if credentials is None:
        return None
    try:
        return _decode_token(credentials.credentials)
    except HTTPException:
        return None


async def require_superuser(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Dependencia que exige que el usuario sea superusuario (is_superuser=True)."""
    if not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren privilegios de superusuario.",
        )
    return current_user


async def require_staff(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Dependencia que exige que el usuario sea staff (is_staff=True)."""
    if not current_user.get("is_staff") and not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren privilegios de staff.",
        )
    return current_user
