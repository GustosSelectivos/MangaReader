"""
Vista para ver estadísticas de llamadas a la API
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from ApiCore.access_control import DRFDACPermission
from django.core.cache import cache
from datetime import datetime


class APIStatsView(APIView):
    """
    Endpoint para ver estadísticas de uso de la API
    GET /api/stats/ - Ver todas las estadísticas
    GET /api/stats/reset/ - Resetear contadores (requiere autenticación)
    """
    permission_classes = [DRFDACPermission]
    
    def get(self, request):
        # Obtener todos los contadores
        stats = {
            'total_calls': cache.get('api_total_calls', 0),
            'daily_calls': cache.get(f'api_calls_daily_{datetime.now().strftime("%Y-%m-%d")}', 0),
            'avg_response_time': round(cache.get('api_avg_response_time', 0), 3),
            'response_count': cache.get('api_response_count', 0),
            'endpoints': {}
        }
        
        # Obtener contadores por endpoint
        # Buscar todas las keys que empiecen con 'api_endpoint_'
        all_keys = cache.keys('api_endpoint_*') if hasattr(cache, 'keys') else []
        
        for key in all_keys:
            if isinstance(key, bytes):
                key = key.decode('utf-8')
            
            # Extraer path y método del key
            parts = key.replace('api_endpoint_', '').rsplit('_', 1)
            if len(parts) == 2:
                path, method = parts
                count = cache.get(key, 0)
                
                if path not in stats['endpoints']:
                    stats['endpoints'][path] = {}
                
                stats['endpoints'][path][method] = count
        
        # Ordenar endpoints por total de llamadas
        endpoint_totals = {}
        for path, methods in stats['endpoints'].items():
            total = sum(methods.values())
            endpoint_totals[path] = {
                'methods': methods,
                'total': total
            }
        
        # Ordenar por total descendente
        stats['endpoints_ranked'] = dict(
            sorted(endpoint_totals.items(), key=lambda x: x[1]['total'], reverse=True)
        )
        
        # Recomendaciones
        stats['recommendations'] = self.get_recommendations(stats)
        
        return Response(stats)


class APIStatsResetView(APIView):
    """
    Endpoint para resetear estadísticas (requiere autenticación)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Resetear contadores principales
        cache.delete('api_total_calls')
        cache.delete('api_avg_response_time')
        cache.delete('api_response_count')
        
        # Resetear contador diario
        today = datetime.now().strftime('%Y-%m-%d')
        cache.delete(f'api_calls_daily_{today}')
        
        # Resetear contadores por endpoint
        all_keys = cache.keys('api_endpoint_*') if hasattr(cache, 'keys') else []
        for key in all_keys:
            cache.delete(key)
        
        return Response({'message': 'Estadísticas reseteadas correctamente'})


def get_recommendations(stats):
    """
    Genera recomendaciones basadas en las estadísticas
    """
    recommendations = []
    
    # Tiempo de respuesta
    avg_time = stats.get('avg_response_time', 0)
    if avg_time > 1.0:
        recommendations.append({
            'type': 'performance',
            'level': 'warning',
            'message': f'Tiempo de respuesta promedio alto: {avg_time}s. Considera optimizar queries o agregar caché.'
        })
    elif avg_time > 0.5:
        recommendations.append({
            'type': 'performance',
            'level': 'info',
            'message': f'Tiempo de respuesta aceptable: {avg_time}s. Monitorea si aumenta.'
        })
    
    # Llamadas diarias
    daily = stats.get('daily_calls', 0)
    if daily > 10000:
        recommendations.append({
            'type': 'usage',
            'level': 'warning',
            'message': f'{daily} llamadas hoy. Alto tráfico, considera rate limiting.'
        })
    elif daily > 5000:
        recommendations.append({
            'type': 'usage',
            'level': 'info',
            'message': f'{daily} llamadas hoy. Tráfico moderado-alto.'
        })
    
    # Endpoints más usados
    endpoints_ranked = stats.get('endpoints_ranked', {})
    if endpoints_ranked:
        top_endpoint = list(endpoints_ranked.items())[0]
        path, data = top_endpoint
        total = data['total']
        
        recommendations.append({
            'type': 'optimization',
            'level': 'info',
            'message': f'Endpoint más usado: {path} con {total} llamadas. Prioriza su optimización.'
        })
    
    return recommendations


# Agregar función a la clase
APIStatsView.get_recommendations = staticmethod(get_recommendations)
