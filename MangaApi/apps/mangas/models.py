"""
apps.mangas — Dominio: mangas
=============================
Re-exporta los modelos definidos en ApiCore para ofrecer
una ruta de importación limpia por dominio.

Importación canónica para nuevo código:
    from apps.mangas.models import manga, manga_cover, manga_autor, manga_tag, manga_alt_titulo
"""
from ApiCore.models.manga_models import (
    manga,
    manga_alt_titulo,
    manga_cover,
    manga_autor,
    manga_tag,
)

__all__ = ['manga', 'manga_alt_titulo', 'manga_cover', 'manga_autor', 'manga_tag']
