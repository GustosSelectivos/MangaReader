from rest_framework.routers import DefaultRouter
from ApiCore.View.dac_view import ProfileViewSet, AccessGrantViewSet

router = DefaultRouter()
router.register(r'profiles', ProfileViewSet, basename='profiles')
router.register(r'grants', AccessGrantViewSet, basename='accessgrants')
