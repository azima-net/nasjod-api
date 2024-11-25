from django.contrib.gis.geos import GEOSGeometry

from rest_framework import serializers
from .models import Address


class AddressSerializer(serializers.ModelSerializer):
    coordinates = serializers.SerializerMethodField()

    class Meta:
        model = Address
        fields = '__all__'

    def get_coordinates(self, obj):
        if obj.coordinates:
            return {
                "lat": obj.coordinates.y,  # Latitude
                "lng": obj.coordinates.x   # Longitude
            }
        return None
    
    def validate_coordinates(self, value):
        """
        Validate and convert the coordinates string to a GEOSGeometry object.
        """
        try:
            return GEOSGeometry(value)  # Convert to GEOSGeometry (Point)
        except Exception as e:
            raise serializers.ValidationError(f"Invalid coordinates: {e}")

    def to_internal_value(self, data):
        """
        Ensure coordinates are properly validated and included in the validated data.
        """
        internal_value = super().to_internal_value(data)
        if 'coordinates' in data:
            internal_value['coordinates'] = self.validate_coordinates(data['coordinates'])
        return internal_value