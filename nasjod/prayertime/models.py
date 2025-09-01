from core._helpers import get_next_friday
from hijri_converter import Gregorian
from datetime import date, timedelta

from django.db import models
from django.core.exceptions import ValidationError

from core.models import Address


class BasePrayerTime(models.Model):
    date = models.DateField()
    hijri_date = models.CharField(max_length=50, editable=False, default="")

    class Meta:
        abstract = True
        ordering = ['date']

    def save(self, *args, **kwargs):
        self.hijri_date = str(Gregorian(self.date.year, self.date.month, self.date.day).to_hijri())
        super().save(*args, **kwargs)


class IqamaTime(BasePrayerTime):
    masjid = models.ForeignKey('masjid.Masjid', on_delete=models.CASCADE)
    fajr_iqama = models.IntegerField(null=True, blank=True,)
    dhuhr_iqama = models.IntegerField(null=True, blank=True,)
    asr_iqama = models.IntegerField(null=True, blank=True,)
    maghrib_iqama = models.IntegerField(null=True, blank=True,)
    isha_iqama = models.IntegerField(null=True, blank=True,)


class JumuahPrayerTime(BasePrayerTime):
    masjid = models.ForeignKey('masjid.Masjid', on_delete=models.CASCADE)
    jumuah_time = models.TimeField(null=True, blank=True,)
    first_timeslot_jumuah = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['masjid', 'date', 'jumuah_time'], name='unique_jumuah_time_per_day_per_masjid')
        ]
    
    def get_jumuah_time(self):
        """Returns the appropriate Jumuah time based on whether it's the first timeslot."""
        if self.first_timeslot_jumuah:
            # Get the corresponding Dhuhr prayer time for this date and masjid
            dhuhr_prayer_time = PrayerTime.objects.filter(date=get_next_friday(), masjids=self.masjid).first()
            if dhuhr_prayer_time:
                return dhuhr_prayer_time.dhuhr
            return None  # Return None if no Dhuhr time found
        return self.jumuah_time

    def clean(self):
        if not self.first_timeslot_jumuah and not self.jumuah_time:
            raise ValidationError("Jumuah time must be specified since its not in first time slot")
        if self.date.weekday() != 4:  # 4 represents Friday
            raise ValidationError("Jumuah prayer time can only be set on a Friday.")

    def __str__(self):
        return f"{self.masjid.name} - {get_next_friday()} - {self.jumuah_time}"


class BaseLocatedPrayerTime(BasePrayerTime):
    location = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    masjids = models.ManyToManyField('masjid.Masjid', blank=True)

    class Meta:
        abstract = True
        ordering = ['date']


class PrayerTime(BaseLocatedPrayerTime):
    fajr = models.TimeField()
    sunrise = models.TimeField()
    dhuhr = models.TimeField()
    asr = models.TimeField()
    maghrib = models.TimeField()
    isha = models.TimeField()

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.date}"


class EidPrayerTime(BaseLocatedPrayerTime):
    eid_time = models.TimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['date', 'eid_time'], name='unique_eid_time_per_day')
        ]

    def __str__(self):
        return f"{self.date} - {self.eid_time}"
