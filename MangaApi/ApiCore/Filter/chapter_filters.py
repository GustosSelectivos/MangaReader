from django_filters import rest_framework as filters
from ApiCore.models.chapter_models import chapter


class ChapterFilter(filters.FilterSet):
    manga = filters.CharFilter(method='filter_manga')

    def filter_manga(self, queryset, name, value):
        if str(value).isdigit():
            return queryset.filter(manga__id=value)
        return queryset.filter(manga__slug=value)

    capitulo_min = filters.NumberFilter(field_name='capitulo_numero', lookup_expr='gte')
    capitulo_max = filters.NumberFilter(field_name='capitulo_numero', lookup_expr='lte')
    titulo = filters.CharFilter(field_name='titulo', lookup_expr='icontains')
    # Filtros por atributos del Manga relacionado
    tipo_serie = filters.CharFilter(field_name='manga__tipo_serie', lookup_expr='iexact')
    demografia = filters.NumberFilter(field_name='manga__demografia__id')
    erotico = filters.BooleanFilter(field_name='manga__erotico')
    vigente = filters.BooleanFilter(field_name='manga__vigente')

    class Meta:
        model = chapter
        fields = ['manga', 'capitulo_min', 'capitulo_max', 'titulo', 'tipo_serie', 'demografia', 'erotico', 'vigente']
