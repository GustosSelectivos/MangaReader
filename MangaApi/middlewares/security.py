import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Inyecta cabeceras de seguridad modernas para prevenir:
    - MIME-Sniffing
    - Clickjacking
    - XSS secundario
    - Forzar HTTPS (HSTS)
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Prevenir MIME-Sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevenir Clickjacking (FastAPI no usa iframes)
        response.headers["X-Frame-Options"] = "DENY"
        
        # Forzar conexiones HTTPS en clientes (1 año)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Controlar qué información referer se envía
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
