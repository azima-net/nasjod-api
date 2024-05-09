from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MasjidViewSet


router = DefaultRouter()
router.register(r'', MasjidViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
