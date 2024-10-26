from django.urls import path
from .views import (IqamaTimeViewSet, PrayerTimeViewSet, JumuahPrayerTimeViewSet, EidPrayerTimeViewSet)

urlpatterns = [
    # Prayer Times
    path('prayer-times/', PrayerTimeViewSet.as_view({'get': 'list', 'post': 'create'}), name='prayer-time-list'),
    path('prayer-times/<int:pk>/', PrayerTimeViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='prayer-time-detail'),

    # Jumuah Prayer Times (remains with masjid_uuid)
    path('jumuah-prayer-times/', JumuahPrayerTimeViewSet.as_view({'get': 'list', 'post': 'create'}), name='jumuah-prayer-time-list'),
    path('jumuah-prayer-times/<int:pk>/', JumuahPrayerTimeViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='jumuah-prayer-time-detail'),
    
    # Iqama
    path('iqamas/', IqamaTimeViewSet.as_view({'get': 'list', 'post': 'create'}), name='iqamas-list'),
    path('iqamas/<int:pk>/', IqamaTimeViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='iqamas-detail'),

    # Eid Prayer Times (remains with masjid_uuid)
    path('eid-prayer-times/', EidPrayerTimeViewSet.as_view({'get': 'list', 'post': 'create'}), name='eid-prayer-time-list'),
    path('eid-prayer-times/<int:pk>/', EidPrayerTimeViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='eid-prayer-time-detail'),
]
