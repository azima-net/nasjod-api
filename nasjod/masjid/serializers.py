from datetime import date, timedelta

from django.db import IntegrityError
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Masjid, PrayerTime, JumuahPrayerTime, EidPrayerTime
from core.models import Address
from core.serializers import AddressSerializer


User = get_user_model()


class BasePrayerTimeSerializer(serializers.ModelSerializer):
    hijri_date = serializers.CharField(read_only=True)
    class Meta:
        abstract = True

    def create(self, validated_data):
        masjid_uuid = self.context['request'].parser_context['kwargs']['masjid_uuid']
        masjid = Masjid.objects.get(uuid=masjid_uuid)
        validated_data['masjid'] = masjid
        return super().create(validated_data)

    def update(self, instance, validated_data):
        masjid_uuid = self.context['request'].parser_context['kwargs']['masjid_uuid']
        masjid = Masjid.objects.get(uuid=masjid_uuid)
        validated_data['masjid'] = masjid
        return super().update(instance, validated_data)

class PrayerTimeSerializer(BasePrayerTimeSerializer):
    class Meta:
        model = PrayerTime
        exclude = ['masjid']
        read_only_fields = ['masjid']

class JumuahPrayerTimeSerializer(BasePrayerTimeSerializer):
    class Meta:
        model = JumuahPrayerTime
        exclude = ['masjid']

class EidPrayerTimeSerializer(BasePrayerTimeSerializer):
    class Meta:
        model = EidPrayerTime
        exclude = ['masjid']
    
class MasjidSerializer(serializers.ModelSerializer):
    managers = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=False)
    assistants = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=False)
    mousallis = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=False)
    imams = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=False)
    address = AddressSerializer()
    prayer_times = PrayerTimeSerializer(many=True, read_only=True)
    jumuah_prayer_times = JumuahPrayerTimeSerializer(many=True, read_only=True)
    eid_prayer_times = EidPrayerTimeSerializer(many=True, read_only=True)
    today_prayer_times = serializers.SerializerMethodField()
    jumuah_prayer_time_this_week = serializers.SerializerMethodField()

    class Meta:
        model = Masjid
        fields = [
            'uuid',
            'name',
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
            'imams',
            'managers',
            'assistants',
            'mousallis',
            'prayer_times',
            'jumuah_prayer_times',
            'eid_prayer_times',
            'today_prayer_times',
            'jumuah_prayer_time_this_week',
        ]

    def get_today_prayer_times(self, obj):
        today = date.today()
        prayer_times = PrayerTime.objects.filter(masjid=obj, date=today)
        return PrayerTimeSerializer(prayer_times, many=True).data

    def get_jumuah_prayer_time_this_week(self, obj):
        today = date.today()
        friday = today + timedelta((4 - today.weekday()) % 7)  # Calculate the upcoming Friday
        jumuah_prayer_times = JumuahPrayerTime.objects.filter(masjid=obj, date=friday)
        return JumuahPrayerTimeSerializer(jumuah_prayer_times, many=True).data

    def get_eid_prayer_time_this_week(self, obj):
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())  # Start of the week (Monday)
        end_of_week = start_of_week + timedelta(days=6)  # End of the week (Sunday)
        eid_prayer_times = EidPrayerTime.objects.filter(masjid=obj, date__range=[start_of_week, end_of_week])
        return EidPrayerTimeSerializer(eid_prayer_times, many=True).data

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
        return super().update(instance, validated_data)
