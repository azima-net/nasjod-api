import phonenumbers
from hijri_converter import Gregorian

from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models.signals import m2m_changed, post_delete
from django.dispatch import receiver

from core.models import Address, ObjectBase
from core._helpers import image_path_upload



User = get_user_model()

class Masjid(ObjectBase):
    SIZE_CHOICES = (
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
    )

    name = models.CharField(max_length=255)
    address = models.OneToOneField(Address, related_name='address_masjid',
                                   on_delete=models.SET_NULL, null=True, blank=True)
    telephone = models.CharField(max_length=20, null=True, blank=True)
    photo = models.ImageField(null=True, blank=True, upload_to=image_path_upload)
    cover = models.ImageField(null=True, blank=True, upload_to=image_path_upload)
    size = models.CharField(max_length=1, choices=SIZE_CHOICES, default='M')

    # Boolean fields
    is_active = models.BooleanField(default=True)
    parking = models.BooleanField(default=False)
    disabled_access = models.BooleanField(default=False)
    ablution_room = models.BooleanField(default=False)
    woman_space = models.BooleanField(default=False)
    adult_courses = models.BooleanField(default=False)
    children_courses = models.BooleanField(default=False)
    salat_al_eid = models.BooleanField(default=False)
    salat_al_janaza = models.BooleanField(default=False)
    iftar_ramadhan = models.BooleanField(default=False)
    itikef = models.BooleanField(default=False)

    # Users
    managers = models.ManyToManyField(User, related_name='managed_masjids', blank=True)
    assistants = models.ManyToManyField(User, related_name='assisted_masjids', blank=True)
    mousallis = models.ManyToManyField(User, related_name='favorite_masjids', blank=True)
    imams = models.ManyToManyField(User, related_name='led_masjids', blank=True)

    # prayer times
    prayer_times = models.ForeignKey('Masjid', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name_plural = "Masajid"

    def __str__(self):
        return self.name
    
    def clean(self):
        super().clean()
        if Masjid.objects.filter(address=self.address).exclude(id=self.id).exists():
            raise ValidationError("A Masjid with this address already exists.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

@receiver(m2m_changed, sender=Masjid.managers.through)
@receiver(m2m_changed, sender=Masjid.assistants.through)
def validate_unique_roles(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action == 'post_add' or action == 'post_remove' or action == 'post_clear':
        managers = set(instance.managers.all())
        assistants = set(instance.assistants.all())

        if managers.intersection(assistants):
            raise ValidationError("A user cannot be both a manager and an assistant in the same masjid.")

@receiver(post_delete, sender=Masjid)
def delete_associated_address(sender, instance, **kwargs):
    if instance.address:
        instance.address.delete()


class BasePrayerTime(models.Model):
    date = models.DateField()
    hijri_date = models.CharField(max_length=50, editable=False, default="")

    class Meta:
        abstract = True
        ordering = ['date']

    def save(self, *args, **kwargs):
        self.hijri_date = str(Gregorian(self.date.year, self.date.month, self.date.day).to_hijri())
        super().save(*args, **kwargs)


class IqamaTime():
    masjid = models.ForeignKey('Masjid', on_delete=models.CASCADE)
    fajr_iqama = models.IntegerField(null=True, blank=True,)
    dhuhr_iqama = models.IntegerField(null=True, blank=True,)
    asr_iqama = models.IntegerField(null=True, blank=True,)
    maghrib_iqama = models.IntegerField(null=True, blank=True,)
    isha_iqama = models.IntegerField(null=True, blank=True,)


class PrayerTime(BasePrayerTime):
    fajr = models.TimeField()
    sunrise = models.TimeField()
    dhuhr = models.TimeField()
    asr = models.TimeField()
    maghrib = models.TimeField()
    isha = models.TimeField()

    masjids = models.ManyToManyField('Masjid', blank=True)
    place = models.CharField(max_length=255, null=True, blank=True)
    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.masjid.name} - {self.date}"


class JumuahPrayerTime(BasePrayerTime):
    masjid = models.ForeignKey('Masjid', on_delete=models.CASCADE)
    jumuah_time = models.TimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['masjid', 'date', 'jumuah_time'], name='unique_jumuah_time_per_day_per_masjid')
        ]

    def clean(self):
        if self.date.weekday() != 4:  # 4 represents Friday
            raise ValidationError("Jumuah prayer time can only be set on a Friday.")

    def __str__(self):
        return f"{self.masjid.name} - {self.date} - {self.jumuah_time}"


class EidPrayerTime(BasePrayerTime):
    masjid = models.ForeignKey('Masjid', on_delete=models.CASCADE)
    eid_time = models.TimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['masjid', 'date', 'eid_time'], name='unique_eid_time_per_day_per_masjid')
        ]

    def __str__(self):
        return f"{self.masjid.name} - {self.date} - {self.eid_time}"
