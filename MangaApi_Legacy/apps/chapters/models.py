"""
apps.chapters — Dominio: capítulos
===================================
Re-exporta los modelos definidos en ApiCore para ofrecer
una ruta de importación limpia por dominio.

Importación canónica para nuevo código:
    from apps.chapters.models import chapter
"""
from ApiCore.models.chapter_models import chapter

__all__ = ['chapter']
