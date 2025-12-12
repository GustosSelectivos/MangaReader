from rest_framework import viewsets, filters as drf_filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from ApiCore.access_control import DRFDACPermission
from django.db.models import F
from django_filters.rest_framework import DjangoFilterBackend
from ApiCore.Models.manga_models import manga, manga_alt_titulo, manga_cover, manga_autor, manga_tag
from ApiCore.Serializer.manga_serializer import (
    MangaSerializer, MangaAltTituloSerializer, MangaCoverSerializer, MangaAutorSerializer, MangaTagSerializer
)
from ApiCore.Filter.manga_filters import MangaFilter, MangaCoverFilter
from ApiCore.access_control import DRFDACPermission


class MangaViewSet(viewsets.ModelViewSet):
    queryset = manga.objects.all().prefetch_related('covers', 'demografia', 'estado', 'autor', 'tags__tag')
    serializer_class = MangaSerializer
    # Use DAC permission: read allowed to all, writes require DAC 'write' on the object
    permission_classes = [DRFDACPermission]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_class = MangaFilter
    search_fields = ['titulo', 'sinopsis']
    ordering_fields = ['vistas', 'titulo', 'creado_en', 'actualizado_en']

    def perform_create(self, serializer):
        instance = serializer.save()
        # Initialize B2 folders if code is present
        if instance.codigo:
            try:
                from ApiCore.services.b2_service import B2Service
                B2Service().initialize_manga_folders(instance.codigo)
            except Exception as e:
                print(f"Failed to init folders for {instance.codigo}: {e}")

    @action(detail=True, methods=['post'], url_path='increment-view')
    def increment_view(self, request, pk=None):
        try:
            obj = self.get_object()
            manga.objects.filter(pk=obj.pk).update(vistas=F('vistas') + 1)
            obj.refresh_from_db(fields=['vistas'])
            return Response({ 'id': obj.pk, 'vistas': obj.vistas })
        except Exception as e:
            return Response({ 'detail': str(e) }, status=400)


class MangaAltTituloViewSet(viewsets.ModelViewSet):
    queryset = manga_alt_titulo.objects.all()
    serializer_class = MangaAltTituloSerializer
    permission_classes = [DRFDACPermission]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_fields = ['manga']
    search_fields = ['titulo_alternativo']


class MangaCoverViewSet(viewsets.ModelViewSet):
    queryset = manga_cover.objects.all()
    serializer_class = MangaCoverSerializer
    permission_classes = [DRFDACPermission]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_class = MangaCoverFilter
    search_fields = ['url_imagen']
    ordering_fields = ['id', 'manga__id']


class MangaAutorViewSet(viewsets.ModelViewSet):
    queryset = manga_autor.objects.all()
    serializer_class = MangaAutorSerializer
    permission_classes = [DRFDACPermission]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_fields = ['manga']
    search_fields = ['rol']


class MangaTagViewSet(viewsets.ModelViewSet):
    queryset = manga_tag.objects.all()
    serializer_class = MangaTagSerializer
    permission_classes = [DRFDACPermission]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_fields = ['manga']
