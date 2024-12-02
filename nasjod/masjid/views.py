import json
import os
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from rest_framework.response import Response

from core.throttling import CreateMasjidAnonThrottle

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
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'suggestion_masjid__uuid']
    lookup_field = "uuid"
