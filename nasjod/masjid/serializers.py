from datetime import date, timedelta

from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Masjid
from core.models import Address
from core.serializers import AddressSerializer
from prayertime.models import EidPrayerTime, IqamaTime, JumuahPrayerTime, PrayerTime
from prayertime.serializers import EidPrayerTimeSerializer, IqamaTimeMasjidSerializer, JumuahPrayerTimeSerializer, PrayerTimeMasjidSerializer


User = get_user_model()


class MasjidSerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    jumuah_prayer_times = JumuahPrayerTimeSerializer(many=True, read_only=True)
    eid_prayer_times = EidPrayerTimeSerializer(many=True, read_only=True)
    today_prayer_times = serializers.SerializerMethodField()
    iqamas = serializers.SerializerMethodField()
    jumuah_prayer_time_this_week = serializers.SerializerMethodField()

    class Meta:
        model = Masjid
        fields = [
            'uuid',
            'name',
            'is_active',
            'address',
            'telephone',
            'photo',
            'cover',
            'size',
            'parking',
            'disabled_access',
            'ablution_room',
            'woman_space',
            'adult_courses',
            'children_courses',
            'salat_al_eid',
            'salat_al_janaza',
            'iftar_ramadhan',
            'itikef',
            'jumuah_prayer_times',
            'eid_prayer_times',
            'today_prayer_times',
            'iqamas',
            'jumuah_prayer_time_this_week',
        ]
        read_only_fields = [
            'is_active',
        ]

    def get_today_prayer_times(self, obj):
        today = date.today()
        prayer_times = PrayerTime.objects.filter(masjids=obj, date=today)
        return PrayerTimeMasjidSerializer(prayer_times, many=True).data

    def get_iqamas(self, obj):
        iqama_times = IqamaTime.objects.filter(masjid__uuid=obj.uuid)
        return IqamaTimeMasjidSerializer(iqama_times, many=True).data

    def get_jumuah_prayer_time_this_week(self, obj):
        # today = date.today()
        # # Calculate the upcoming Friday
        # friday = today + timedelta((4 - today.weekday()) % 7)

        # Filter JumuahPrayerTime for this mosque and the calculated upcoming Friday
        jumuah_prayer_times = JumuahPrayerTime.objects.filter(masjid__uuid=obj.uuid)

        # Prepare the response data manually using the model method
        response_data = []
        for jumuah_prayer_time in jumuah_prayer_times:
            response_data.append({
                'date': jumuah_prayer_time.date,
                'jumuah_time': jumuah_prayer_time.get_jumuah_time(),
                'first_timeslot_jumuah': jumuah_prayer_time.first_timeslot_jumuah
            })

        return response_data

    def get_eid_prayer_time_this_week(self, obj):
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())  # Start of the week (Monday)
        end_of_week = start_of_week + timedelta(days=6)  # End of the week (Sunday)
        eid_prayer_times = EidPrayerTime.objects.filter(masjid__uuid=obj.uuid, date__range=[start_of_week, end_of_week])
        return EidPrayerTimeSerializer(eid_prayer_times, many=True).data

    def create(self, validated_data):
        address_data = validated_data.pop('address')
        # Check if an address with the same coordinates exists
        try:
            address = Address.objects.get(coordinates=address_data.get('coordinates'))
        except Address.DoesNotExist:
            # If not found, create a new address
            address = Address.objects.create(**address_data)

        # Now create the Masjid with the retrieved or newly created address
        masjid = Masjid.objects.create(address=address, is_active=False, **validated_data)
        
        # If the address has a city, update the prayer times based on city changes
        if masjid.address and masjid.address.city:
            # 2. Link the Masjid to PrayerTimes in the new city
            matching_prayer_times = PrayerTime.objects.filter(location__city__iexact=masjid.address.city)
            with transaction.atomic():
                self.prayertime_set.add(*matching_prayer_times)
        return masjid

    def update(self, instance, validated_data):
        address_data = validated_data.pop('address', None)
        if address_data:
            address = instance.address
            for attr, value in address_data.items():
                setattr(address, attr, value)
            address.save()

         # If the address has a city, update the prayer times based on city changes
        if instance.address and instance.address.city:
            # 1. Find mismatched PrayerTimes (old city)
            mismatched_prayer_times = PrayerTime.objects.filter(
                masjids=instance
            ).exclude(location__city=instance.address.city)

            # Bulk remove using `remove(*mismatched_prayer_times)`
            if mismatched_prayer_times:
                with transaction.atomic():
                    self.prayertime_set.remove(*mismatched_prayer_times)

            # 2. Link the Masjid to PrayerTimes in the new city
            matching_prayer_times = PrayerTime.objects.filter(location__city__iexact=instance.address.city)
            with transaction.atomic():
                instance.prayertime_set.add(*matching_prayer_times)
        return super().update(instance, validated_data)
