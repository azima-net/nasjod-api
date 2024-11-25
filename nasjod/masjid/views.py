from core.throttling import CreateMasjidAnonThrottle
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

import logging

logger = logging.getLogger(__name__)

from .models import Masjid, SuggestionMasjidModification
from .serializers import (MasjidSerializer, SuggestionMasjidModificationSerializer)
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

class SuggestionMasjidModificationViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing SuggestionMasjidModification instances.
    """
    queryset = SuggestionMasjidModification.objects.all()
    serializer_class = SuggestionMasjidModificationSerializer

    def create(self, request, *args, **kwargs):
        # Log the request data
        print("Request Data: %s", request.data)

        # Proceed with the usual create logic
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)