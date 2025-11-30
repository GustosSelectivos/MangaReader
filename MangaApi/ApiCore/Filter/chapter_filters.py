from django_filters import rest_framework as filters
from ApiCore.Models.chapter_models import chapter


class ChapterFilter(filters.FilterSet):
    manga = filters.NumberFilter(field_name='manga__id')
    capitulo_min = filters.NumberFilter(field_name='capitulo_numero', lookup_expr='gte')
    capitulo_max = filters.NumberFilter(field_name='capitulo_numero', lookup_expr='lte')
    titulo = filters.CharFilter(field_name='titulo', lookup_expr='icontains')

    class Meta:
        model = chapter
        fields = ['manga', 'capitulo_min', 'capitulo_max', 'titulo']
