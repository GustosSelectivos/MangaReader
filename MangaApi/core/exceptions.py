"""
core/exceptions.py
==================
Handlers de excepciones globales.
Reemplaza ApiCore/exceptions.py (custom_exception_handler de DRF).

Garantiza que TODOS los errores devuelvan el mismo formato JSON:
  { "status": "error", "code": int, "message": str, "errors": {...} }

Decisión: Se registran en main.py con app.add_exception_handler().
"""

import logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


def _error_response(status_code: int, message: str, errors: dict | None = None) -> JSONResponse:
    body: dict = {"status": "error", "code": status_code, "message": message}
    if errors:
        body["errors"] = errors
    return JSONResponse(status_code=status_code, content=body)


# ── Handlers individuales ─────────────────────────────────────────────────────

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Convierte HTTPException al formato estándar."""
    return _error_response(exc.status_code, str(exc.detail))


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Convierte errores de validación Pydantic (422) al formato estándar.
    Reemplaza los errores de validación de DRF Serializers.
    """
    errors: dict[str, list[str]] = {}
    for error in exc.errors():
        field = " → ".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.setdefault(field, []).append(error["msg"])

    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Error de validación en los datos de entrada.",
        errors=errors,
    )


async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """
    Captura errores de BD no manejados (ej. IntegrityError, OperationalError).
    Loguea el error real pero devuelve un mensaje genérico al cliente.
    """
    logger.error(
        "Error de base de datos en %s %s: %s",
        request.method,
        request.url.path,
        exc,
        exc_info=True,
    )
    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Error interno de base de datos. Por favor, intenta de nuevo.",
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Captura cualquier excepción no manejada → 500.
    Equivalente al `if response is None` del custom_exception_handler de DRF.
    """
    logger.error(
        "Excepción no manejada en %s %s: %s",
        request.method,
        request.url.path,
        exc,
        exc_info=True,
    )
    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Error interno del servidor.",
    )


# ── Registro centralizado ─────────────────────────────────────────────────────

def register_exception_handlers(app: FastAPI) -> None:
    """Registra todos los handlers en la app FastAPI. Llamar desde main.py."""
    app.add_exception_handler(HTTPException, http_exception_handler)          # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)         # type: ignore[arg-type]
