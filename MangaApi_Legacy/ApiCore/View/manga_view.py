from rest_framework import viewsets, filters as drf_filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from ApiCore.access_control import DRFDACPermission
from django.db.models import F
from django_filters.rest_framework import DjangoFilterBackend
from ApiCore.models.manga_models import manga, manga_alt_titulo, manga_cover, manga_autor, manga_tag
from ApiCore.Serializer.manga_serializer import (
    MangaSerializer, MangaAltTituloSerializer, MangaCoverSerializer, MangaAutorSerializer, MangaTagSerializer
)
from ApiCore.Filter.manga_filters import MangaFilter, MangaCoverFilter
from ApiCore.access_control import DRFDACPermission


from ApiCore.permissions.checkers import CanViewNSFW, IsModeratorOrAdmin

class MangaViewSet(viewsets.ModelViewSet):
    # queryset = manga.objects.all().select_related('demografia', 'estado', 'autor').prefetch_related('covers', 'tags__tag')
    serializer_class = MangaSerializer
    # Use DAC permission: read allowed to all, writes require DAC 'write' on the object
    # Also integrate Profile permissions
    permission_classes = [DRFDACPermission, CanViewNSFW]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_class = MangaFilter
    search_fields = ['titulo', 'sinopsis']
    ordering_fields = ['vistas', 'titulo', 'creado_en', 'actualizado_en']

    def get_serializer_class(self):
        if self.action in ['list', 'random']:
             from ApiCore.Serializer.manga_serializer import MangaCardSerializer
             return MangaCardSerializer
        return MangaSerializer

    def get_object(self):
        # Allow lookup by slug OR id
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs.get(lookup_url_kwarg)

        # Si el valor parece un entero, tratamos como ID (PK)
        # Si no, asumimos que es un slug
        if lookup_value and str(lookup_value).isdigit():
             self.lookup_field = 'pk'
        else:
             self.lookup_field = 'slug'

        return super().get_object()

    def get_queryset(self):
        qs = manga.objects.all().select_related('demografia', 'estado', 'autor').prefetch_related('covers', 'tags__tag')
        
        # Check NSFW access via Profile
        # logic: if user is not authenticated OR (auth and no profile) OR (auth+profile but no nsfw perm) -> hide erotic
        can_see_nsfw = False
        if self.request.user.is_authenticated and hasattr(self.request.user, 'userprofile'):
             can_see_nsfw = self.request.user.userprofile.can_view_nsfw
        
        if not can_see_nsfw:
            qs = qs.filter(erotico=False)
            
        return qs

    def perform_create(self, serializer):
        """
        1. Guarda el manga (serializer ya no toca B2).
        2. Inicializa carpetas en B2 si hay código.
        3. Si viene cover_image, delega la subida a CoverUploadService.
        """
        from ApiCore.services.cover_service import CoverUploadService, CoverUploadError

        cover_file = self.request.FILES.get('cover_image')
        instance = serializer.save()

        # Inicializar estructura de carpetas en B2
        if instance.codigo:
            try:
                from ApiCore.services.b2_service import B2Service
                B2Service().initialize_manga_folders(instance.codigo)
            except Exception as e:
                # No crítico: las carpetas son solo marcadores virtuales
                import logging
                logging.getLogger(__name__).warning(
                    "Failed to init B2 folders for %s: %s", instance.codigo, e
                )

        # Subida de cover (si vino en el request)
        if cover_file and instance.codigo:
            try:
                CoverUploadService().attach_cover(instance, cover_file)
            except CoverUploadError as exc:
                # El manga ya fue creado; no revertimos, pero registramos el error.
                import logging
                logging.getLogger(__name__).error(
                    "Cover upload failed after creating manga %s: %s", instance.codigo, exc
                )

    def perform_update(self, serializer):
        """
        1. Guarda los cambios del manga.
        2. Si viene cover_image, delega la subida a CoverUploadService
           (que también desactiva las covers previas automáticamente).
        """
        from ApiCore.services.cover_service import CoverUploadService, CoverUploadError

        cover_file = self.request.FILES.get('cover_image')
        instance = serializer.save()

        if cover_file and instance.codigo:
            try:
                CoverUploadService().attach_cover(instance, cover_file)
            except CoverUploadError as exc:
                import logging
                logging.getLogger(__name__).error(
                    "Cover upload failed during update of manga %s: %s", instance.codigo, exc
                )

    @action(detail=True, methods=['post'], url_path='increment-view', permission_classes=[AllowAny])
    def increment_view(self, request, pk=None):
        try:
            obj = self.get_object()
            manga.objects.filter(pk=obj.pk).update(vistas=F('vistas') + 1)
            obj.refresh_from_db(fields=['vistas'])
            return Response({ 'id': obj.pk, 'vistas': obj.vistas })
        except Exception as e:
            return Response({ 'detail': str(e) }, status=400)

    @action(detail=False, methods=['get'], url_path='random', pagination_class=None)
    def random(self, request):
        """Return 5 random items efficiently using ID-based selection."""
        qs = self.get_queryset()
        # If user is not authenticated, exclude erotic content
        if not request.user.is_authenticated:
            qs = qs.filter(erotico=False)
            
        import random
        from django.db.models import Max

        # Optimization: Avoid order_by('?') which is O(N)
        # Strategy: Get Max ID -> Generate Random IDs -> Fetch
        
        count = qs.count()
        if count == 0:
            return Response([])
            
        # For small datasets, random.sample is fine and better distributed
        if count < 1000:
            items = list(qs)
            if len(items) > 5:
                items = random.sample(items, 5)
            serializer = self.get_serializer(items, many=True)
            return Response(serializer.data)

        # For large datasets, use ID-based probing
        max_id = qs.aggregate(max_id=Max("id"))['max_id']
        if not max_id:
             return Response([])

        random_items = []
        visited_ids = set()
        required_count = 5
        attempts = 0
        max_attempts = 20 # Circuit breaker to prevent infinite loops
        
        while len(random_items) < required_count and attempts < max_attempts:
            pk = random.randint(1, max_id)
            if pk in visited_ids:
                attempts += 1
                continue
            visited_ids.add(pk)
            
            # Find the first item with ID >= pk (handling gaps)
            # Important: Apply the same filters (qs) to ensure we don't return restricted content
            obj = qs.filter(id__gte=pk).order_by('id').first()
            
            if obj:
                # Avoid duplicates in the result set
                if obj.id not in [x.id for x in random_items]:
                    random_items.append(obj)
            
            attempts += 1
            
        # If we didn't get enough (e.g. extremely sparse IDs or strict filters), simple fallback
        if len(random_items) < required_count:
            exclude_ids = [x.id for x in random_items]
            # Grab a few more to fill the gap
            needed = required_count - len(random_items)
            extras = list(qs.exclude(id__in=exclude_ids)[:needed])
            random_items.extend(extras)

        serializer = self.get_serializer(random_items, many=True)
        return Response(serializer.data)


class MangaAltTituloViewSet(viewsets.ModelViewSet):
    queryset = manga_alt_titulo.objects.select_related('manga').all()
    serializer_class = MangaAltTituloSerializer
    permission_classes = [DRFDACPermission]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_fields = ['manga']
    search_fields = ['titulo_alternativo']


class MangaCoverViewSet(viewsets.ModelViewSet):
    queryset = manga_cover.objects.select_related('manga').all()
    serializer_class = MangaCoverSerializer
    permission_classes = [DRFDACPermission]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_class = MangaCoverFilter
    search_fields = ['url_imagen']
    ordering_fields = ['id', 'manga__id']


class MangaAutorViewSet(viewsets.ModelViewSet):
    queryset = manga_autor.objects.select_related('manga', 'autor').all()
    serializer_class = MangaAutorSerializer
    permission_classes = [DRFDACPermission]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_fields = ['manga']
    search_fields = ['rol']


class MangaTagViewSet(viewsets.ModelViewSet):
    queryset = manga_tag.objects.select_related('manga', 'tag').all()
    serializer_class = MangaTagSerializer
    permission_classes = [DRFDACPermission]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_fields = ['manga']
