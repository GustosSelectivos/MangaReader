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
            endpoint_key = f'api_endpoint_{request.path}_{request.method}'
            cache.set(endpoint_key, cache.get(endpoint_key, 0) + 1, timeout=None)
            
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
