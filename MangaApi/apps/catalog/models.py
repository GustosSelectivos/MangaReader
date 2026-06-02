"""
apps.catalog — Dominio: tablas de catálogo/mantenedor
=====================================================
Re-exporta los modelos definidos en ApiCore para ofrecer
una ruta de importación limpia por dominio.

Importación canónica para nuevo código:
    from apps.catalog.models import autores, estados, demografia, tags
"""
from ApiCore.models.mantenedor_models import autores, estados, demografia, tags

__all__ = ['autores', 'estados', 'demografia', 'tags']
