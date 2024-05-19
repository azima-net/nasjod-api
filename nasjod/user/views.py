from django.shortcuts import render

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import User
from .serializers import UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = "identifier"

    # def get_permissions(self):
    #     if self.action in ['create', 'update', 'partial_update', 'destroy']:
    #         self.permission_classes = [IsAuthenticated]
    #     else:
    #         self.permission_classes = [IsAuthenticated]
    #     return super().get_permissions()
