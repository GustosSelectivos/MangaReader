"""
CoverUploadService
==================
Responsabilidad única: subir un archivo de portada a Backblaze B2
y registrar la URL resultante en la base de datos.

Mantiene al MangaSerializer limpio de lógica de I/O.
"""

import re
from django.db import transaction


class CoverUploadError(Exception):
    """
    Lanzada cuando la subida de cover a B2 falla.
    La view puede atraparla y decidir si revertir o responder con error parcial.
    """
    pass


class CoverUploadService:
    """
    Servicio de subida de portada.

    Uso típico (desde la view):
        service = CoverUploadService()
        cover = service.attach_cover(manga_instance, request.FILES['cover_image'])

    Genera:
        CoverUploadError si B2 devuelve None o lanza excepción interna.
    """

    # Caracteres permitidos en nombres de archivo
    _SAFE_FILENAME_RE = re.compile(r'[^a-zA-Z0-9._-]')

    def __init__(self):
        # Lazy-import para no romper entornos sin credenciales B2 en tests
        from ApiCore.services.b2_service import B2Service
        self._b2 = B2Service()

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _sanitize_filename(self, name: str) -> str:
        """Elimina caracteres peligrosos del nombre de archivo."""
        return self._SAFE_FILENAME_RE.sub('', name) or 'cover'

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    @transaction.atomic
    def attach_cover(self, manga_instance, cover_file):
        """
        Sube `cover_file` a B2 y crea/reemplaza el registro `manga_cover` principal.

        Pasos:
          1. Subir el archivo a B2  → URL
          2. Desactivar covers 'main' previas (vigente=False)
          3. Crear nuevo registro manga_cover con la URL recibida

        Returns:
            El nuevo objeto `manga_cover`.

        Raises:
            CoverUploadError: si B2 devuelve None o hay un error de red.
        """
        # Importación diferida: evita ciclo de imports si el servicio se usa en señales
        from ApiCore.models.manga_models import manga_cover

        filename = self._sanitize_filename(cover_file.name)

        try:
            url = self._b2.upload_cover(manga_instance.codigo, cover_file, filename)
        except Exception as exc:
            raise CoverUploadError(
                f"B2 upload failed for manga '{manga_instance.codigo}': {exc}"
            ) from exc

        if not url:
            raise CoverUploadError(
                f"B2 upload returned None for manga '{manga_instance.codigo}'. "
                "Verifica las credenciales y el bucket."
            )

        # Desactivar covers principales anteriores
        manga_cover.objects.filter(
            manga=manga_instance,
            tipo_cover='main',
            vigente=True,
        ).update(vigente=False)

        # Registrar nueva cover
        return manga_cover.objects.create(
            manga=manga_instance,
            url_imagen=url,
            tipo_cover='main',
            vigente=True,
        )
