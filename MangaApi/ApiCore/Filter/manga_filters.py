from django_filters import rest_framework as filters
from ApiCore.Models.manga_models import manga, manga_cover


class MangaFilter(filters.FilterSet):
    titulo = filters.CharFilter(field_name='titulo', lookup_expr='icontains')
    # Permitir filtrar por nombre de estado/demografia (case insensitive)
    estado = filters.CharFilter(field_name='estado__descripcion', lookup_expr='icontains')
    demografia = filters.CharFilter(field_name='demografia__descripcion', lookup_expr='icontains')
    # Alias 'type' para 'tipo_serie'
    type = filters.CharFilter(field_name='tipo_serie', lookup_expr='iexact')
    
    autor = filters.NumberFilter(field_name='autor__id')
    fecha_from = filters.DateFilter(field_name='fecha_lanzamiento', lookup_expr='gte')
    fecha_to = filters.DateFilter(field_name='fecha_lanzamiento', lookup_expr='lte')
    vigente = filters.BooleanFilter(field_name='vigente')
    erotico = filters.BooleanFilter(field_name='erotico')

    class Meta:
        model = manga
        fields = ['titulo', 'estado', 'demografia', 'autor', 'fecha_from', 'fecha_to', 'vigente', 'erotico', 'type']


class MangaCoverFilter(filters.FilterSet):
    manga = filters.NumberFilter(field_name='manga__id')
    tipo_cover = filters.CharFilter(field_name='tipo_cover', lookup_expr='iexact')
    vigente = filters.BooleanFilter(field_name='vigente')

    class Meta:
        model = manga_cover
        fields = ['manga', 'tipo_cover', 'vigente']
