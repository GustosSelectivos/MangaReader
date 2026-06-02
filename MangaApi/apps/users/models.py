"""
apps.users — Dominio: usuarios y perfiles
==========================================
Re-exporta los modelos definidos en ApiCore para ofrecer
una ruta de importación limpia por dominio.

Importación canónica para nuevo código:
    from apps.users.models import UserProfile
"""
from ApiCore.models.user_models import UserProfile

__all__ = ['UserProfile']
