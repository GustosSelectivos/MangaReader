import logging
import time
from datetime import datetime
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Configurar el logger
logger = logging.getLogger("api.requests")
logger.setLevel(logging.INFO)

# Si queremos que se vea con un formato específico, le añadimos un handler
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(message)s", 
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware para registrar todas las peticiones HTTP y sus respuestas.
    Muestra:
    - IP del cliente
    - Método y URL
    - Status Code
    - Tiempo de procesamiento (ms)
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        
        # Obtener IP del cliente (Remote Address)
        client_ip = request.client.host if request.client else "Unknown"
        # Si está detrás de un proxy (ej. Cloudflare/Nginx), intentar obtener de los headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0]

        # Procesar la petición
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise e
        finally:
            process_time = (time.time() - start_time) * 1000  # En milisegundos
            
            # Formatear el log
            log_message = (
                f"{client_ip} - "
                f"\"{request.method} {request.url.path}{'?' + request.url.query if request.url.query else ''}\" "
                f"{status_code} "
                f"| Tiempo: {process_time:.2f}ms"
            )
            
            if status_code >= 400:
                logger.warning(log_message)
            else:
                logger.info(log_message)

        return response
