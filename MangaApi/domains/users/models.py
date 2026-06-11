"""
domains/users/models.py
=======================
Modelos SQLAlchemy para el dominio de usuarios.

NOTA IMPORTANTE sobre auth_user (tabla Django):
Django gestiona la tabla `auth_user` con su propio ORM. En FastAPI,
la mapeamos como read-only para consultas (login, perfil, etc.).
NO se crearán migraciones Alembic para auth_user.

Tablas:
  - auth_user     → tabla de Django (mapeada como lectura)
  - user_profiles → UserProfile de Django

Señal Django reemplazada: el UserProfile ya no se crea por signal post_save.
En FastAPI se crea explícitamente en el endpoint de registro.
"""

from datetime import datetime
from sqlalchemy import (
    BigInteger, Boolean, DateTime, ForeignKey,
    Integer, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class User(Base):
    """
    Mapeo de la tabla auth_user de Django.
    Solo lectura desde FastAPI; Django sigue siendo la fuente de verdad
    para autenticación (si se migra gradualmente con Strangler Fig).
    """
    __tablename__ = "auth_user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    password: Mapped[str] = mapped_column(String(128), nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    username: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    first_name: Mapped[str] = mapped_column(String(150), nullable=False, default="")
    last_name: Mapped[str] = mapped_column(String(150), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(254), nullable=False, default="")
    is_staff: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    date_joined: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    # ── Relaciones ────────────────────────────────────────────────────────────
    profile: Mapped["UserProfile | None"] = relationship(
        "UserProfile", back_populates="user", uselist=False, lazy="noload"
    )


class UserProfile(Base):
    """Tabla: user_profiles"""
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("auth_user.id"), nullable=False, unique=True
    )
    profile: Mapped[str] = mapped_column(
        String(20), nullable=False, default="home_only", index=True
    )
    profile_updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    banned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ban_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # ── Relación ──────────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="profile", lazy="noload")

    # ── Permisos de perfil (equivalente al Meta.permissions de Django) ────────
    # Estos permisos no se almacenan en BD separada; se derivan del campo 'profile'
    PROFILE_PERMISSIONS: dict[str, list[str]] = {
        "home_only": [],
        "premium": ["view_nsfw_content", "view_premium_content"],
        "moderator": ["view_nsfw_content", "view_premium_content", "moderate_comments",
                      "moderate_reports", "access_admin_panel", "view_analytics"],
        "admin": ["view_nsfw_content", "view_premium_content", "access_admin_panel",
                  "manage_users", "manage_manga", "manage_chapters",
                  "moderate_comments", "moderate_reports", "view_analytics"],
    }

    @property
    def can_view_nsfw(self) -> bool:
        return "view_nsfw_content" in self.PROFILE_PERMISSIONS.get(self.profile, [])

    @property
    def can_access_admin(self) -> bool:
        return "access_admin_panel" in self.PROFILE_PERMISSIONS.get(self.profile, [])

    @property
    def is_moderator_or_higher(self) -> bool:
        return self.profile in ("moderator", "admin")

    def has_permission(self, codename: str) -> bool:
        return codename in self.PROFILE_PERMISSIONS.get(self.profile, [])
