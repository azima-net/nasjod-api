# users/permissions.py
from rest_framework.permissions import BasePermission
from masjid.models import Masjid


# General Role Check Permissions

class IsManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.managed_masjids.exists()


class IsAssistant(BasePermission):
    def has_permission(self, request, view):
        return request.user.assisted_masjids.exists()


class IsImam(BasePermission):
    def has_permission(self, request, view):
        return request.user.led_masjids.exists()


class IsMousalli(BasePermission):
    def has_permission(self, request, view):
        return request.user.attended_masjids.exists()


# Specific Masjid Check Permissions

class IsManagerOfMasjid(BasePermission):
    def has_permission(self, request, view):
        masjid_id = view.kwargs.get('pk') or view.kwargs.get('masjid_pk')
        if not masjid_id:
            return False
        try:
            masjid = Masjid.objects.get(pk=masjid_id)
            return request.user in masjid.managers.all()
        except Masjid.DoesNotExist:
            return False


class IsAssistantOfMasjid(BasePermission):
    def has_permission(self, request, view):
        masjid_id = view.kwargs.get('pk') or view.kwargs.get('masjid_pk')
        if not masjid_id:
            return False
        try:
            masjid = Masjid.objects.get(pk=masjid_id)
            return request.user in masjid.assistants.all()
        except Masjid.DoesNotExist:
            return False


class IsImamOfMasjid(BasePermission):
    def has_permission(self, request, view):
        masjid_id = view.kwargs.get('pk') or view.kwargs.get('masjid_pk')
        if not masjid_id:
            return False
        try:
            masjid = Masjid.objects.get(pk=masjid_id)
            return request.user in masjid.imams.all()
        except Masjid.DoesNotExist:
            return False


class IsMousalliOfMasjid(BasePermission):
    def has_permission(self, request, view):
        masjid_id = view.kwargs.get('pk') or view.kwargs.get('masjid_pk')
        if not masjid_id:
            return False
        try:
            masjid = Masjid.objects.get(pk=masjid_id)
            return request.user in masjid.mousallis.all()
        except Masjid.DoesNotExist:
            return False
