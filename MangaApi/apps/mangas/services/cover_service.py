"""
apps.mangas.services.cover_service
====================================
Punto de importación canónico para la capa de servicios del dominio mangas.

Re-exporta CoverUploadService desde ApiCore para que el nuevo código
pueda importar por dominio sin tocar ApiCore directamente:

    from apps.mangas.services.cover_service import CoverUploadService, CoverUploadError
"""
from ApiCore.services.cover_service import CoverUploadService, CoverUploadError

__all__ = ['CoverUploadService', 'CoverUploadError']
