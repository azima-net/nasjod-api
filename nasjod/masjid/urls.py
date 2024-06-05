from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EidPrayerTimeViewSet, JumuahPrayerTimeViewSet, MasjidViewSet, PrayerTimeViewSet


router = DefaultRouter()
router.register(r'', MasjidViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('<uuid:masjid_uuid>/prayer_times/', PrayerTimeViewSet.as_view({'get': 'list', 'post': 'create'}), name='prayer-time-list'),
    path('<uuid:masjid_uuid>/prayer_times/<int:pk>/', PrayerTimeViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='prayer-time-detail'),
    path('<uuid:masjid_uuid>/jumuah_prayer_times/', JumuahPrayerTimeViewSet.as_view({'get': 'list', 'post': 'create'}), name='jumuah-prayer-time-list'),
    path('<uuid:masjid_uuid>/jumuah_prayer_times/<int:pk>/', JumuahPrayerTimeViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='jumuah-prayer-time-detail'),
    path('<uuid:masjid_uuid>/eid_prayer_times/', EidPrayerTimeViewSet.as_view({'get': 'list', 'post': 'create'}), name='eid-prayer-time-list'),
    path('<uuid:masjid_uuid>/eid_prayer_times/<int:pk>/', EidPrayerTimeViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='eid-prayer-time-detail'),
]
