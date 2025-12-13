from rest_framework import viewsets, filters as drf_filters
from rest_framework.permissions import AllowAny
from ApiCore.access_control import DRFDACPermission
from django_filters.rest_framework import DjangoFilterBackend
from ApiCore.Models.chapter_models import chapter
from ApiCore.Serializer.chapter_serializer import ChapterSerializer
from ApiCore.Filter.chapter_filters import ChapterFilter


class ChapterViewSet(viewsets.ModelViewSet):
    queryset = chapter.objects.select_related('manga').all()
    serializer_class = ChapterSerializer
    permission_classes = [DRFDACPermission]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_class = ChapterFilter
    search_fields = ['titulo']
    ordering_fields = ['capitulo_numero', 'id']
    ordering = ['capitulo_numero']
