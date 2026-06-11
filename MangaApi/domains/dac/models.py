"""
domains/dac/models.py
=====================
Modelos SQLAlchemy para el sistema DAC (Discretionary Access Control):
  - DacPermission → apicore_permission
  - AccessGrant   → apicore_accessgrant
  - Owner         → apicore_owner
  - AuditLog      → apicore_auditlog

El ContentType de Django (django_content_type) se reemplaza por un
campo simple `model_name` (string) ya que FastAPI no tiene contenttypes.
Mapeamos el content_type_id al nombre del modelo para mantener compatibilidad.
"""

from datetime import datetime
from sqlalchemy import (
    BigInteger, Boolean, DateTime, ForeignKey,
    Integer, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class DacPermission(Base):
    """
    Tabla: apicore_permission
    Tipo de permiso (ej. 'read', 'write', 'delete').
    """
    __tablename__ = "apicore_permission"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codename: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, default="")

    grants: Mapped[list["AccessGrant"]] = relationship("AccessGrant", back_populates="permission", lazy="noload")


class AccessGrant(Base):
    """
    Tabla: apicore_accessgrant
    Concede/deniega un permiso a un usuario o grupo sobre un objeto.

    Nota: content_type_id referencia django_content_type. Se mantiene el
    campo para no romper datos existentes, pero la lógica DAC de FastAPI
    usa content_type_id directamente sin depender del ORM de contenttypes.
    """
    __tablename__ = "apicore_accessgrant"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("auth_user.id"), nullable=True
    )
    group_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("auth_group.id"), nullable=True
    )
    content_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("django_content_type.id"), nullable=False
    )
    object_id: Mapped[str] = mapped_column(String(255), nullable=False)
    permission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("apicore_permission.id"), nullable=False
    )
    allow: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    permission: Mapped["DacPermission"] = relationship("DacPermission", back_populates="grants", lazy="noload")


class Owner(Base):
    """
    Tabla: apicore_owner
    Registro explícito de propietario de un objeto.
    """
    __tablename__ = "apicore_owner"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("auth_user.id"), nullable=False
    )
    content_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("django_content_type.id"), nullable=False
    )
    object_id: Mapped[str] = mapped_column(String(255), nullable=False)


class AuditLog(Base):
    """
    Tabla: apicore_auditlog
    Log de auditoría de accesos DAC.

    MEJORA vs Django: Ya no se escribe sincrónicamente en process_response().
    FastAPI lo escribe como BackgroundTask (no bloquea la respuesta al cliente).
    """
    __tablename__ = "apicore_auditlog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("auth_user.id"), nullable=True
    )
    path: Mapped[str] = mapped_column(String(1024), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    view_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    content_type_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("django_content_type.id"), nullable=True
    )
    object_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), index=True
    )


class DjangoContentType(Base):
    """
    Tabla: django_content_type
    Mapeada como lectura para consultas de DAC que necesiten content_type_id.
    NO se modifica desde FastAPI.
    """
    __tablename__ = "django_content_type"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    app_label: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)


class AuthGroup(Base):
    """
    Tabla: auth_group (grupos de Django, para AccessGrant.group_id)
    Mapeada como lectura.
    """
    __tablename__ = "auth_group"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
