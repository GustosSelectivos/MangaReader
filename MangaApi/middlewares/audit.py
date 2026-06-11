"""
middlewares/audit.py
=====================
DACAuditMiddleware → BaseHTTPMiddleware + BackgroundTask.

MEJORA CRÍTICA vs Django:
  - Django: `process_view` llamaba `get_object()` ANTES de la vista
    (query a BD en cada request auditado → riesgo de DoS).
  - FastAPI: Solo registra path/method/status_code DESPUÉS del response.
    La escritura al log de auditoría es un BackgroundTask (no bloquea cliente).

El audit log ya no hace query a la BD en el request path;
se escribe de forma diferida en segundo plano.
"""

import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class DACAuditMiddleware(BaseHTTPMiddleware):
    """
    Registra cada request/response al AuditLog de forma asíncrona.

    Solo audita rutas /api/ para evitar ruido de health checks, docs, etc.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Solo auditar rutas /api/
        if not request.url.path.startswith("/api/"):
            return response

        # Extraer user_id del token (sin verificar firma para no duplicar lógica)
        user_id = self._extract_user_id(request)
        allowed = response.status_code < 400 and response.status_code != 403

        # Escribir audit log en background (no bloquea la respuesta)
        # Usamos add_task en el background directamente
        from starlette.background import BackgroundTask

        audit_task = BackgroundTask(
            _write_audit_log,
            user_id=user_id,
            path=request.url.path,
            method=request.method,
            view_name=self._get_route_name(request),
            allowed=allowed,
            status_code=response.status_code,
        )

        # Adjuntar background task a la respuesta
        if response.background:
            # Si ya hay background tasks, encadenar
            existing = response.background
            response.background = BackgroundTask(
                _run_tasks, existing, audit_task
            )
        else:
            response.background = audit_task

        return response

    def _extract_user_id(self, request: Request) -> int | None:
        """Extrae user_id del JWT sin verificar firma (best-effort para audit)."""
        try:
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return None
            token = auth[7:]
            # Decodificar sin verificar para audit (solo lectura de claims)
            from jose import jwt as jose_jwt
            claims = jose_jwt.get_unverified_claims(token)
            return claims.get("user_id")
        except Exception:
            return None

    def _get_route_name(self, request: Request) -> str:
        """Obtiene el nombre de la ruta registrada en FastAPI."""
        try:
            route = request.scope.get("route")
            return getattr(route, "name", "") or ""
        except Exception:
            return ""


async def _run_tasks(*tasks) -> None:
    """Ejecuta múltiples background tasks en secuencia."""
    for task in tasks:
        if callable(task.func):
            await task()


async def _write_audit_log(
    user_id: int | None,
    path: str,
    method: str,
    view_name: str,
    allowed: bool,
    status_code: int,
) -> None:
    """
    Escribe el AuditLog en BD. Se ejecuta como BackgroundTask.
    Usa su propia sesión independiente (no la del request).
    """
    try:
        from core.database import AsyncSessionLocal
        from domains.dac.repository import create_audit_log

        async with AsyncSessionLocal() as db:
            await create_audit_log(
                db=db,
                user_id=user_id,
                path=path,
                method=method,
                view_name=view_name,
                allowed=allowed,
                status_code=status_code,
            )
            await db.commit()
    except Exception as exc:
        # El audit log no debe crashear el sistema; solo loguear el error
        logger.error("Error escribiendo AuditLog para %s %s: %s", method, path, exc)
