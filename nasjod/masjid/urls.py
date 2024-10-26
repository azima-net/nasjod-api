from django.urls import path, include

from .views import (MasjidViewSet)

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'', MasjidViewSet, basename='masjid')

urlpatterns = [
    path('', include(router.urls)),
]
