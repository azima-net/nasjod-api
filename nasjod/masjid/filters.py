from django.db import models
from django_filters import rest_framework as filters
from .models import Masjid
from prayertime.models import IqamaTime, JumuahPrayerTime


class MasjidFilter(filters.FilterSet):
    # Assuming the address fields are on a related model you might need to use the related field lookup
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    street = filters.CharFilter(field_name='address__street', lookup_expr='icontains')
    city = filters.CharFilter(field_name='address__city', lookup_expr='icontains')
    state = filters.CharFilter(field_name='address__state', lookup_expr='icontains')
    zip_code = filters.CharFilter(field_name='address__zip_code', lookup_expr='icontains')
    country = filters.CharFilter(field_name='address__country', lookup_expr='icontains')
    are_infos_complete = filters.BooleanFilter(method='filter_are_infos_complete')


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
    
    def filter_are_infos_complete(self, queryset, name, value):
        """
        Custom filter for `are_infos_complete` using the instance property logic.
        """
        # Use the queryset's `filter` method and apply the same logic as the property
        queryset = queryset.annotate(
            has_iqama_time=models.Exists(
                IqamaTime.objects.filter(masjid=models.OuterRef('pk'))
            ),
            has_jumuah_prayer_time=models.Exists(
                JumuahPrayerTime.objects.filter(masjid=models.OuterRef('pk'))
            )
        )

        if value:
            return queryset.filter(
                name__isnull=False,
                name__gt="",
                address__isnull=False,
                cover__isnull=False,
                cover__gt="",
                size__isnull=False,
                has_iqama_time=True,
                has_jumuah_prayer_time=True,
            )
        else:
            return queryset.exclude(
                name__isnull=False,
                name__gt="",
                address__isnull=False,
                cover__isnull=False,
                cover__gt="",
                size__isnull=False,
                has_iqama_time=True,
                has_jumuah_prayer_time=True,
            )
