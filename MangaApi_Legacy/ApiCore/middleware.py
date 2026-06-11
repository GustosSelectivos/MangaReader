"""
Middleware para contar llamadas a la API
"""
import time
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin


class APICallCounterMiddleware(MiddlewareMixin):
    """
    Middleware que cuenta las llamadas a endpoints de la API
    Usa Django cache para almacenar contadores
    """
    
    def process_request(self, request):
        # Guardar tiempo de inicio
        request._start_time = time.time()
        
        # Solo contar rutas que empiecen con /api/
        if request.path.startswith('/api/'):
            # Contador global
            cache.set('api_total_calls', cache.get('api_total_calls', 0) + 1, timeout=None)
            
            # Contador por endpoint
            # SECURITY: Added timeout to prevent memory exhaustion (DoS) from random paths
            endpoint_key = f'api_endpoint_{request.path}_{request.method}'
            cache.set(endpoint_key, cache.get(endpoint_key, 0) + 1, timeout=86400) # 24h timeout
            
            # Contador por día (se resetea cada día)
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            daily_key = f'api_calls_daily_{today}'
            cache.set(daily_key, cache.get(daily_key, 0) + 1, timeout=86400)  # 24 horas
    
    def process_response(self, request, response):
        # Calcular tiempo de respuesta
        if hasattr(request, '_start_time'):
            response_time = time.time() - request._start_time
            
            # Guardar tiempo promedio de respuesta
            if request.path.startswith('/api/'):
                avg_key = 'api_avg_response_time'
                count_key = 'api_response_count'
                
                current_avg = cache.get(avg_key, 0)
                current_count = cache.get(count_key, 0)
                
                # Calcular nuevo promedio
                new_count = current_count + 1
                new_avg = ((current_avg * current_count) + response_time) / new_count
                
                cache.set(avg_key, new_avg, timeout=None)
                cache.set(count_key, new_count, timeout=None)
        
        return response


class DACAuditMiddleware(MiddlewareMixin):
    """Middleware that records access attempts and denials related to DAC.

    - Records request metadata on process_view
    - On process_response, updates the record with allowed/denied based on status code
    - Attempts to resolve the object via DRF view's `get_object()` when available
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        # store initial metadata on the request for later logging
        request._dac_audit = {
            'path': request.path,
            'method': request.method,
            'view_func': getattr(view_func, '__name__', str(view_func)),
            'view_instance': getattr(view_func, '__self__', None),
            'view_kwargs': view_kwargs.copy() if isinstance(view_kwargs, dict) else {},
            'resolved_object': None,
        }

        # best-effort: try to resolve object via DRF view's get_object()
        view_instance = request._dac_audit.get('view_instance')
        if view_instance is not None:
            try:
                get_obj = getattr(view_instance, 'get_object', None)
                if callable(get_obj):
                    obj = get_obj()
                    request._dac_audit['resolved_object'] = obj
            except Exception:
                # don't fail the request for audit resolution errors
                request._dac_audit['resolved_object'] = None

    def process_response(self, request, response):
        try:
            from .models import AuditLog
            from django.contrib.contenttypes.models import ContentType
        except Exception:
            return response

        meta = getattr(request, '_dac_audit', None)
        if not meta:
            return response

        user = getattr(request, 'user', None)
        obj = meta.get('resolved_object')
        ct = None
        obj_id = None
        if obj is not None:
            try:
                ct = ContentType.objects.get_for_model(obj.__class__)
                obj_id = str(getattr(obj, 'pk', getattr(obj, 'id', None)))
            except Exception:
                ct = None
                obj_id = None

        allowed = True if (response.status_code < 400 and response.status_code != 403) else False

        try:
            AuditLog.objects.create(
                user=(user if getattr(user, 'is_authenticated', False) else None),
                path=meta.get('path') or request.path,
                method=meta.get('method') or request.method,
                view_name=meta.get('view_func') or '',
                content_type=ct,
                object_id=obj_id,
                allowed=allowed,
                status_code=response.status_code,
                detail=''
            )
        except Exception:
            # swallow audit errors
            pass

        return response
