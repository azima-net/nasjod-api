from django.shortcuts import render

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import User, UserContributor
from .serializers import UserContributorSerializer, UserSerializer
from authentification.authentication import AppTokenAuthentication
from core.permissions import FrontendAppPermission

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = "identifier"
    permission_classes = [IsAdminUser]

    def get_permissions(self):
        if self.action in ('list', ):
            self.permission_classes = [IsAuthenticated, IsAdminUser]
        elif self.action in ('update', 'partial_update', 'destroy'):
            self.permission_classes = [IsAuthenticated, ]
        else:
            self.permission_classes = []
        return super().get_permissions()


class UserContributorViewset(viewsets.ModelViewSet):
    queryset = UserContributor.objects.all()
    serializer_class = UserContributorSerializer
    authentication_classes = [AppTokenAuthentication]
    permission_classes = [FrontendAppPermission]

    def get_queryset(self):
        # Filter the queryset to include only instances where `accept_to_display` is True
        return super().get_queryset().filter(accept_to_display=True)
