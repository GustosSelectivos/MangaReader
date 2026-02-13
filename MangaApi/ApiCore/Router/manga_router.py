from rest_framework.routers import DefaultRouter
from ApiCore.View.manga_view import (
    MangaViewSet, MangaAltTituloViewSet, MangaCoverViewSet, MangaAutorViewSet, MangaTagViewSet
)
from ApiCore.View.home_view import HomeViewSet

router = DefaultRouter()
router.register(r'mangas', MangaViewSet, basename='mangas')
router.register(r'home', HomeViewSet, basename='home')
router.register(r'manga-alt-titulos', MangaAltTituloViewSet, basename='manga-alt-titulos')
router.register(r'manga-covers', MangaCoverViewSet, basename='manga-covers')
router.register(r'manga-autores', MangaAutorViewSet, basename='manga-autores')
router.register(r'manga-tags', MangaTagViewSet, basename='manga-tags')
