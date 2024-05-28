from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.conf import settings

from .models import Masjid
from .serializers import MasjidSerializer
from .filters import MasjidFilter
from core.permissions import IsManagerOfMasjid


class MasjidViewSet(viewsets.ModelViewSet):
    queryset = Masjid.objects.all()
    serializer_class = MasjidSerializer
    filterset_class = MasjidFilter
    lookup_field = "uuid"
    
    def get_permissions(self):
        if self.action in ('create', 'destroy'):
            self.permission_classes = [IsAuthenticated, IsAdminUser]
        elif self.action in ('update', 'partial_update'):
            self.permission_classes = [IsAuthenticated, IsManagerOfMasjid]
        else:
            self.permission_classes = []

        return super().get_permissions()
