from rest_framework import viewsets
from .models import Masjid
from .serializers import MasjidSerializer


class MasjidViewSet(viewsets.ModelViewSet):
    queryset = Masjid.objects.all()
    serializer_class = MasjidSerializer

