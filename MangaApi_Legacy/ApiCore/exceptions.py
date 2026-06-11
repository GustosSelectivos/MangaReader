from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Manejador global de excepciones para estandarizar respuestas JSON.
    Convierte errores 500 y otros en un formato {status, message, code}.
    """
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Si response es None, es una excepción no manejada por DRF (Ej: 500 Server Error, DB Error)
    if response is None:
        logger.error(f"Error no manejado en {context['view'].__class__.__name__}: {str(exc)}", exc_info=True)
        return Response({
            "status": "error",
            "message": "Error interno del servidor.",
            "detail": str(exc), # Ocultar en producción si se desea
            "code": 500
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Si DRF ya manejó el error (404, 403, 400), estandarizamos el formato
    # Normalmente DRF devuelve {"detail": "..."} o {"field": ["error"]}
    
    custom_data = {
        "status": "error",
        "code": response.status_code
    }

    # Intentar extraer mensaje legible
    if "detail" in response.data:
        custom_data["message"] = response.data["detail"]
    else:
        # Errores de validación de campos
        custom_data["message"] = "Error de validación"
        custom_data["errors"] = response.data

    response.data = custom_data
    return response
