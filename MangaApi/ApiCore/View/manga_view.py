from rest_framework import viewsets, filters as drf_filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import F
from django_filters.rest_framework import DjangoFilterBackend
from ApiCore.Models.manga_models import manga, manga_alt_titulo, manga_cover, manga_autor, manga_tag
from ApiCore.Serializer.manga_serializer import (
    MangaSerializer, MangaAltTituloSerializer, MangaCoverSerializer, MangaAutorSerializer, MangaTagSerializer
)
from ApiCore.Filter.manga_filters import MangaFilter, MangaCoverFilter


class MangaViewSet(viewsets.ModelViewSet):
    queryset = manga.objects.all()
    serializer_class = MangaSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_class = MangaFilter
    search_fields = ['titulo', 'sinopsis']
    ordering_fields = ['vistas', 'titulo', 'creado_en', 'actualizado_en']

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
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    search_fields = ['titulo_alternativo']


class MangaCoverViewSet(viewsets.ModelViewSet):
    queryset = manga_cover.objects.all()
    serializer_class = MangaCoverSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_class = MangaCoverFilter
    search_fields = ['url_imagen']
    ordering_fields = ['id', 'manga__id']


class MangaAutorViewSet(viewsets.ModelViewSet):
    queryset = manga_autor.objects.all()
    serializer_class = MangaAutorSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    search_fields = ['rol']


class MangaTagViewSet(viewsets.ModelViewSet):
    queryset = manga_tag.objects.all()
    serializer_class = MangaTagSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
