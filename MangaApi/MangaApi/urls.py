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

from ApiCore.Router.mantenedor_router import router as mantenedor_router
from ApiCore.Router.manga_router import router as manga_router
from ApiCore.Router.chapter_router import router as chapter_router

# Include each partial router so those files control their own endpoints
urlpatterns = [
    path('admin/', admin.site.urls),
        path('api/mantenedor/', include((mantenedor_router.urls, 'mantenedor'))),
        path('api/manga/', include((manga_router.urls, 'manga'))),
        path('api/chapters/', include((chapter_router.urls, 'chapter'))),
]
