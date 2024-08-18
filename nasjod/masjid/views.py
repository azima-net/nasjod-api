from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.filters import OrderingFilter

from django.conf import settings

from .models import Masjid, PrayerTime, JumuahPrayerTime, EidPrayerTime
from .serializers import MasjidSerializer, PrayerTimeSerializer, JumuahPrayerTimeSerializer, EidPrayerTimeSerializer
from .filters import MasjidFilter
from core.permissions import IsManagerOfMasjid, IsAssistantOfMasjid, IsAdminOrManagerOrAssistant


class MasjidViewSet(viewsets.ModelViewSet):
    queryset = Masjid.objects.filter(is_active=True)
    serializer_class = MasjidSerializer
    filterset_class = MasjidFilter
    lookup_field = "uuid"
    ordering_fields = ['name', 'created_at', 'updated_at'] 
    
    def get_permissions(self):
        if self.action in ('create', 'destroy'):
            self.permission_classes = [IsAuthenticated, IsAdminUser]
        elif self.action in ('update', 'partial_update'):
            self.permission_classes = [IsAuthenticated, IsManagerOfMasjid]
        else:
            self.permission_classes = []
        return super().get_permissions()

class PrayerTimeViewSet(viewsets.ModelViewSet):
    serializer_class = PrayerTimeSerializer

    def get_queryset(self):
        return PrayerTime.objects.filter(masjid__uuid=self.kwargs['masjid_uuid'])
    
    def get_permissions(self):
        if self.action in ('create', 'destroy', 'update', 'partial_update'):
            self.permission_classes = [IsAuthenticated, IsAdminOrManagerOrAssistant]
        else:
            self.permission_classes = []
        return super().get_permissions()

class JumuahPrayerTimeViewSet(viewsets.ModelViewSet):
    serializer_class = JumuahPrayerTimeSerializer

    def get_queryset(self):
        return JumuahPrayerTime.objects.filter(masjid__uuid=self.kwargs['masjid_uuid'])

    def get_permissions(self):
        if self.action in ('create', 'destroy', 'update', 'partial_update'):
            self.permission_classes = [IsAuthenticated, IsAdminOrManagerOrAssistant]
        else:
            self.permission_classes = []
        return super().get_permissions()

class EidPrayerTimeViewSet(viewsets.ModelViewSet):
    serializer_class = EidPrayerTimeSerializer

    def get_queryset(self):
        return EidPrayerTime.objects.filter(masjid__uuid=self.kwargs['masjid_uuid'])
    def get_permissions(self):
        if self.action in ('create', 'destroy', 'update', 'partial_update'):
            self.permission_classes = [IsAuthenticated, IsAdminOrManagerOrAssistant]
        else:
            self.permission_classes = []
        return super().get_permissions()
