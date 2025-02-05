from django.db import models
from django.db.models import Q, OuterRef, Subquery, Exists
from django_filters import rest_framework as filters
from .models import Masjid
from prayertime.models import PrayerTime, IqamaTime, JumuahPrayerTime


class MasjidFilter(filters.FilterSet):
    # Assuming the address fields are on a related model you might need to use the related field lookup
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    street = filters.CharFilter(field_name='address__street', lookup_expr='icontains')
    city = filters.CharFilter(field_name='address__city', lookup_expr='icontains')
    state = filters.CharFilter(field_name='address__state', lookup_expr='icontains')
    zip_code = filters.CharFilter(field_name='address__zip_code', lookup_expr='icontains')
    country = filters.CharFilter(field_name='address__country', lookup_expr='icontains')
    are_infos_complete = filters.BooleanFilter(method='filter_are_infos_complete')

    jumuah_time_from = filters.TimeFilter(method='filter_jumuah_time_from')

    def filter_jumuah_time_from(self, queryset, name, value):
        """
        Include Masjids that have at least one JumuahPrayerTime
        whose 'effective' Jumuah time >= `value`.

        - If first_timeslot_jumuah=False, we compare jumuah_time >= value
        - If first_timeslot_jumuah=True, we compare the Dhuhr time from
          PrayerTime (same date, same masjid) >= value
        """

        # Subquery to retrieve Dhuhr time from PrayerTime for the same date & masjid
        dhuhr_time_subq = PrayerTime.objects.filter(
            date=OuterRef('date'),
            masjids=OuterRef('masjid_id')
        ).values('dhuhr')[:1]

        # Subquery that finds all JumuahPrayerTime rows for each Masjid
        # that meet the "jumuah_time_from >= value" criterion
        jumuah_filter_subq = (
        JumuahPrayerTime.objects
        .annotate(dhuhr_time=Subquery(dhuhr_time_subq))
        # First filter by matching Masjid
        .filter(masjid=OuterRef('pk'))
        # Then handle the "either jumuah_time or Dhuhr >= value" logic
        .filter(
            Q(first_timeslot_jumuah=False, jumuah_time__gte=value) |
            Q(first_timeslot_jumuah=True,  dhuhr_time__gte=value)
        )
    )
        # Filter Masjids to those that have at least one matching Jumuah time
        return (
            queryset
            .filter(Exists(jumuah_filter_subq))
            .distinct()
        )

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
