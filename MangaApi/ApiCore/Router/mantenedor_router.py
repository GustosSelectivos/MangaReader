from rest_framework.routers import DefaultRouter
from ApiCore.View.mantenedor_view import AutoresViewSet, EstadosViewSet, DemografiaViewSet, TagsViewSet

router = DefaultRouter()
router.register(r'autores', AutoresViewSet, basename='autores')
router.register(r'estados', EstadosViewSet, basename='estados')
router.register(r'demografias', DemografiaViewSet, basename='demografias')
router.register(r'tags', TagsViewSet, basename='tags')
