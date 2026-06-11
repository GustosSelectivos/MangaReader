"""
apps.dac — Dominio: Discretionary Access Control
=================================================
Re-exporta los modelos definidos en ApiCore para ofrecer
una ruta de importación limpia por dominio.

Importación canónica para nuevo código:
    from apps.dac.models import Permission, AccessGrant, Owner, AuditLog
"""
from ApiCore.models.dac_models import Permission, AccessGrant, Owner, AuditLog

__all__ = ['Permission', 'AccessGrant', 'Owner', 'AuditLog']
