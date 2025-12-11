from rest_framework import viewsets, filters as drf_filters
from rest_framework.permissions import AllowAny
from ApiCore.access_control import DRFDACPermission
from django_filters.rest_framework import DjangoFilterBackend
from ApiCore.Models.mantenedor_models import autores, estados, demografia, tags
from ApiCore.Serializer.mantenedor_serializer import (
    AutorSerializer, EstadoSerializer, DemografiaSerializer, TagSerializer
)
from ApiCore.Filter.mantenedor_filters import MantenedorFilter


class AutoresViewSet(viewsets.ModelViewSet):
    queryset = autores.objects.all()
    serializer_class = AutorSerializer
    permission_classes = [DRFDACPermission]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_class = MantenedorFilter
    search_fields = ['nombre']


class EstadosViewSet(viewsets.ModelViewSet):
    queryset = estados.objects.all()
    serializer_class = EstadoSerializer
    permission_classes = [DRFDACPermission]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    search_fields = ['descripcion']


class DemografiaViewSet(viewsets.ModelViewSet):
    queryset = demografia.objects.all()
    serializer_class = DemografiaSerializer
    permission_classes = [DRFDACPermission]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    search_fields = ['descripcion']


class TagsViewSet(viewsets.ModelViewSet):
    queryset = tags.objects.all()
    serializer_class = TagSerializer
    permission_classes = [DRFDACPermission]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    search_fields = ['descripcion']
