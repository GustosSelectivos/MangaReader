from rest_framework.routers import DefaultRouter
from ApiCore.View.chapter_view import ChapterViewSet

router = DefaultRouter()
router.register(r'', ChapterViewSet, basename='chapters')
