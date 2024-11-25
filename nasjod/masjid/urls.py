from django.urls import path, include

from .views import (MasjidViewSet, SuggestionMasjidModificationViewSet)

from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'masajid', MasjidViewSet, basename='masjid')
router.register(r'suggestions-modification-masjid', SuggestionMasjidModificationViewSet, basename='suggestion-modification-masjid')


urlpatterns = [
    path('', include(router.urls)),
]
