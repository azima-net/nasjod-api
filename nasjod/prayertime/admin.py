from django.contrib import admin
from .models import PrayerTime, JumuahPrayerTime, EidPrayerTime, IqamaTime


@admin.register(PrayerTime)
class PrayerTimeAdmin(admin.ModelAdmin):
    list_display = ('date', 'hijri_date', 'fajr', 'dhuhr', 'asr', 'maghrib', 'isha', 'city')
    list_filter = ('masjids', 'date', 'location__city')
    search_fields = ('masjids__name', 'location__city')

    def city(self, obj):
        # Returns the city name from the related Address model
        return obj.location.city if obj.location else "No City"
    city.short_description = "City"

@admin.register(JumuahPrayerTime)
class JumuahPrayerTimeAdmin(admin.ModelAdmin):
    list_display = ('masjid', 'date', 'hijri_date', 'jumuah_time')
    list_filter = ('masjid', 'date')
    search_fields = ('masjid__name',)

@admin.register(EidPrayerTime)
class eidPrayerTimeAdmin(admin.ModelAdmin):
    list_display = ('date', 'hijri_date', 'eid_time')
    list_filter = ('masjids','date')

@admin.register(IqamaTime)
class IqamaTimeAdmin(admin.ModelAdmin):
    list_display = ('masjid', 'fajr_iqama', 'dhuhr_iqama', 'asr_iqama', 'maghrib_iqama', 'isha_iqama')
    list_filter = ('masjid',)
