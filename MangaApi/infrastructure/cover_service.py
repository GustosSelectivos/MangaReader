"""
infrastructure/cover_service.py
================================
CoverUploadService async.
Reemplaza ApiCore/services/cover_service.py (síncrono con transaction.atomic).

MEJORA: Usa aiobotocore (async) en lugar de boto3 (síncrono).
El servicio es llamado desde BackgroundTask, no desde el response path.
"""

import re
import logging
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure import b2_client

logger = logging.getLogger(__name__)

_SAFE_FILENAME_RE = re.compile(r"[^a-zA-Z0-9._-]")


class CoverUploadError(Exception):
    """Lanzada cuando la subida de cover a B2 falla."""
    pass


class CoverUploadService:
    """
    Servicio async de subida de portada.
    Equivale a CoverUploadService de Django pero sin @transaction.atomic
    (el control de transacciones lo hace el caller con AsyncSession).
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    def _sanitize_filename(self, name: str) -> str:
        return _SAFE_FILENAME_RE.sub("", name) or "cover"

    async def attach_cover(
        self,
        manga_id: int,
        codigo: str,
        cover_file: UploadFile,
    ) -> None:
        """
        Sube `cover_file` a B2 y registra la URL en `apicore_manga_cover`.

        Pasos:
          1. Leer bytes del archivo (validando content-type y tamaño)
          2. Subir a B2 async
          3. Desactivar covers 'main' previas
          4. Crear nuevo registro manga_cover

        Raises:
            CoverUploadError: si B2 falla o el archivo es inválido.
        """
        from domains.mangas.models import MangaCover
        from sqlalchemy import update

        # ── Validaciones de seguridad (recomendado en migration plan) ─────────
        ALLOWED_CONTENT_TYPES = {"image/webp", "image/jpeg", "image/png", "image/gif"}
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

        content_type = cover_file.content_type or "application/octet-stream"
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise CoverUploadError(
                f"Tipo de archivo no permitido: {content_type}. "
                f"Permitidos: {ALLOWED_CONTENT_TYPES}"
            )

        file_bytes = await cover_file.read()
        if len(file_bytes) > MAX_FILE_SIZE:
            raise CoverUploadError(
                f"Archivo demasiado grande: {len(file_bytes)} bytes. Máximo: {MAX_FILE_SIZE}."
            )

        filename = self._sanitize_filename(cover_file.filename or "cover.webp")

        # ── Subir a B2 ────────────────────────────────────────────────────────
        url = await b2_client.upload_cover(codigo, file_bytes, filename, content_type)
        if not url:
            raise CoverUploadError(
                f"B2 retornó None para manga '{codigo}'. Verifica credenciales y bucket."
            )

        # ── Desactivar covers previas ──────────────────────────────────────────
        await self.db.execute(
            update(MangaCover)
            .where(
                MangaCover.manga_id == manga_id,
                MangaCover.tipo_cover == "main",
                MangaCover.vigente == True,  # noqa: E712
            )
            .values(vigente=False)
        )

        # ── Crear nueva cover ─────────────────────────────────────────────────
        new_cover = MangaCover(
            manga_id=manga_id,
            url_imagen=url,
            tipo_cover="main",
            vigente=True,
        )
        self.db.add(new_cover)
        await self.db.flush()
        logger.info("Cover subida exitosamente para manga_id=%s: %s", manga_id, url)
