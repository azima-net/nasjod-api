from django_filters import rest_framework as filters
from .models import Masjid

class MasjidFilter(filters.FilterSet):
    # Assuming the address fields are on a related model you might need to use the related field lookup
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    street = filters.CharFilter(field_name='address__street', lookup_expr='icontains')
    city = filters.CharFilter(field_name='address__city', lookup_expr='icontains')
    state = filters.CharFilter(field_name='address__state', lookup_expr='icontains')
    zip_code = filters.CharFilter(field_name='address__zip_code', lookup_expr='icontains')
    country = filters.CharFilter(field_name='address__country', lookup_expr='icontains')

    class Meta:
        model = Masjid
        fields = {
            'size': ['exact'],
            'is_active': ['exact'],
            'parking': ['exact'],
            'disabled_access': ['exact'],
            'ablution_room': ['exact'],
            'woman_space': ['exact'],
            'adult_courses': ['exact'],
            'children_courses': ['exact'],
            'salat_al_eid': ['exact'],
            'salat_al_janaza': ['exact'],
            'iftar_ramadhan': ['exact'],
            'itikef': ['exact'],
        }
