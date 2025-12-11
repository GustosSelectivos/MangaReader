"""
URL configuration for MangaApi project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from ApiCore.Router.mantenedor_router import router as mantenedor_router
from ApiCore.Router.manga_router import router as manga_router
from ApiCore.Router.chapter_router import router as chapter_router
from ApiCore.Router.dac_router import router as dac_router
from ApiCore.View.stats_view import APIStatsView, APIStatsResetView
from ApiCore.View.auth_view import CurrentUserView, UsersListView
from ApiCore.View.auth_view import CurrentUserPermissionsView

# Include each partial router so those files control their own endpoints
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/stats/', APIStatsView.as_view(), name='api_stats'),
    path('api/stats/reset/', APIStatsResetView.as_view(), name='api_stats_reset'),
    path('api/mantenedor/', include((mantenedor_router.urls, 'mantenedor'))),
    path('api/manga/', include((manga_router.urls, 'manga'))),
    path('api/chapters/', include((chapter_router.urls, 'chapter'))),
    path('api/dac/', include((dac_router.urls, 'dac'))),
    path('api/auth/user/', CurrentUserView.as_view(), name='current_user'),
    path('api/auth/users/', UsersListView.as_view(), name='users_list'),
    path('api/auth/permissions/', CurrentUserPermissionsView.as_view(), name='current_user_permissions'),
]
