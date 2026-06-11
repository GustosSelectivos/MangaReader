from django_filters import rest_framework as filters
from ApiCore.models.mantenedor_models import autores


class MantenedorFilter(filters.FilterSet):
    nombre = filters.CharFilter(field_name='nombre', lookup_expr='icontains')

    class Meta:
        model = autores
        fields = ['id', 'nombre', 'vigente']
