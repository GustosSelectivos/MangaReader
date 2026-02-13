from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db.models import Prefetch

from ApiCore.models.manga_models import manga, manga_cover
from ApiCore.Serializer.manga_serializer import MangaCardSerializer

class HomeViewSet(viewsets.ViewSet):
    """
    Endpoint consolidado para dashboard.
    GET /api/manga/home/
    Reduce 4 round-trips a 1 request.
    """
    permission_classes = [AllowAny]
    # Cache por 5 minutos dado que la home cambia poco
    @method_decorator(cache_page(60 * 5))
    def list(self, request):
        # Base query optimizada
        qs = manga.objects.filter(vigente=True).select_related('estado', 'demografia').prefetch_related(
            Prefetch('covers', queryset=manga_cover.objects.filter(vigente=True))
        )

        # 1. Populares (Top Views)
        populars = qs.order_by('-vistas')[:12]
        
        # 2. Trending (Simulado por creación reciente de caps o fecha)
        # Idealmente usaríamos una tabla de analitycs, por ahora: creados recientemente
        trending = qs.order_by('-creado_en')[:8]

        # 3. Latest Updates
        latest = qs.order_by('-actualizado_en')[:8]
        
        # 4. Most Viewed (Sidebar)
        most_viewed = qs.order_by('-vistas')[:30]

        data = {
            "populars": MangaCardSerializer(populars, many=True, context={'request': request}).data,
            "trending": MangaCardSerializer(trending, many=True, context={'request': request}).data,
            "latest": MangaCardSerializer(latest, many=True, context={'request': request}).data,
            "most_viewed": MangaCardSerializer(most_viewed, many=True, context={'request': request}).data
        }
        return Response(data)
