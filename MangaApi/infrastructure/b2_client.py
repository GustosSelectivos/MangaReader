"""
infrastructure/b2_client.py
============================
Cliente async para Backblaze B2 (compatible con S3).
Reemplaza b2_service.py (boto3 síncrono).

MEJORA CRÍTICA: El upload a B2 ya no bloquea el event loop de FastAPI.
aiobotocore es el wrapper async oficial de botocore.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import aiobotocore.session
from aiobotocore.session import get_session

from core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _get_s3_client():
    """Context manager que provee un cliente S3 async para una operación."""
    session = get_session()
    async with session.create_client(
        "s3",
        endpoint_url=settings.B2_ENDPOINT_URL,
        aws_access_key_id=settings.B2_KEY_ID,
        aws_secret_access_key=settings.B2_APPLICATION_KEY,
        region_name="us-east-005",
    ) as client:
        yield client


async def get_presigned_url(file_path: str, content_type: str = "image/webp") -> str | None:
    """
    Genera una URL pre-firmada para PUT (subida directa desde el cliente).
    Equivale a B2Service.get_presigned_url().
    """
    try:
        async with _get_s3_client() as s3:
            url = await s3.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": settings.B2_BUCKET_NAME,
                    "Key": file_path,
                    "ContentType": content_type,
                },
                ExpiresIn=3600,
            )
        return url
    except Exception as exc:
        logger.error("Error generando presigned URL para %s: %s", file_path, exc)
        return None


async def initialize_manga_folders(serie_code: str) -> bool:
    """
    Crea carpetas virtuales en B2 subiendo un archivo .keep vacío.
    Equivale a B2Service.initialize_manga_folders().
    """
    try:
        async with _get_s3_client() as s3:
            await s3.put_object(
                Bucket=settings.B2_BUCKET_NAME,
                Key=f"chapters/{serie_code}/.keep",
                Body=b"",
            )
            await s3.put_object(
                Bucket=settings.B2_BUCKET_NAME,
                Key=f"covers/{serie_code}/.keep",
                Body=b"",
            )
        return True
    except Exception as exc:
        logger.error("Error creando carpetas B2 para %s: %s", serie_code, exc)
        return False


async def upload_cover(serie_code: str, file_bytes: bytes, filename: str, content_type: str) -> str | None:
    """
    Sube una cover a B2 y retorna la URL del CDN.
    Equivale a B2Service.upload_cover().
    MEJORA: Async, no bloquea el event loop.
    """
    key = f"covers/{serie_code}/{filename}"
    try:
        async with _get_s3_client() as s3:
            await s3.put_object(
                Bucket=settings.B2_BUCKET_NAME,
                Key=key,
                Body=file_bytes,
                ContentType=content_type,
            )
        return f"{settings.CDN_COVER_BASE}/file/{settings.B2_BUCKET_NAME}/{key}"
    except Exception as exc:
        logger.error("Error subiendo cover %s para %s: %s", filename, serie_code, exc)
        return None


async def upload_chapter_page(
    serie_code: str,
    chapter_num: int,
    file_bytes: bytes,
    filename: str,
    content_type: str,
) -> str | None:
    """
    Sube una página de capítulo a B2.
    Equivale a B2Service.upload_chapter_page().
    """
    key = f"chapters/{serie_code}/{chapter_num}/{filename}"
    try:
        async with _get_s3_client() as s3:
            await s3.put_object(
                Bucket=settings.B2_BUCKET_NAME,
                Key=key,
                Body=file_bytes,
                ContentType=content_type,
            )
        return f"{settings.CDN_CHAPTER_BASE}/file/{settings.B2_BUCKET_NAME}/{key}"
    except Exception as exc:
        logger.error("Error subiendo página %s: %s", filename, exc)
        return None
