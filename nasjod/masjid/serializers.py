from rest_framework import serializers

from .models import Masjid
from core.models import Address
from core.serializers import AddressSerializer


class MasjidSerializer(serializers.ModelSerializer):
    address = AddressSerializer()

    class Meta:
        model = Masjid
        fields = '__all__'

    def create(self, validated_data):
        address_data = validated_data.pop('address')
        address = Address.objects.create(**address_data)
        masjid = Masjid.objects.create(address=address, **validated_data)
        return masjid
    
    def update(self, instance, validated_data):
        address_data = validated_data.pop('address', None)
        if address_data:
            address = instance.address
            for attr, value in address_data.items():
                setattr(address, attr, value)
            address.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance