from rest_framework import serializers
from .models import Masjid


class MasjidSerializer(serializers.ModelSerializer):
    class Meta:
        model = Masjid
        fields = '__all__'
