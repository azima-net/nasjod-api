from core.throttling import CreateMasjidAnonThrottle
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser


from .models import Masjid
from .serializers import (MasjidSerializer)
from .filters import MasjidFilter
from core.permissions import IsManagerOfMasjid


class MasjidViewSet(viewsets.ModelViewSet):
    queryset = Masjid.objects.all()
    serializer_class = MasjidSerializer
    filterset_class = MasjidFilter
    lookup_field = "uuid"
    ordering_fields = ['name', 'created_at', 'updated_at'] 
    
    def get_permissions(self):
        if self.action in ('destroy',):
            self.permission_classes = [IsAuthenticated, IsAdminUser]
        elif self.action in ('update',):
            self.permission_classes = [IsAuthenticated, IsManagerOfMasjid]
        else:
            self.permission_classes = []
        return super().get_permissions()

    def get_throttles(self):
        if self.action == 'create':
            return [CreateMasjidAnonThrottle()]
        return super().get_throttles()
