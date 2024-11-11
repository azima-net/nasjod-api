import phonenumbers
from hijri_converter import Gregorian

from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models.signals import m2m_changed, post_delete
from django.dispatch import receiver

from prayertime.models import PrayerTime
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
        # Only perform the uniqueness check if the address is not None
        if self.address is not None:
            if Masjid.objects.filter(address=self.address).exclude(id=self.id).exists():
                raise ValidationError("A Masjid with this address already exists.")

    def save(self, *args, **kwargs):
        # Save the masjid (this might update the address)
        self.clean()
        super().save(*args, **kwargs)

        # # If the address has a city, update the prayer times based on city changes
        # if self.address and self.address.city:
        #     # 1. Find mismatched PrayerTimes (old city)
        #     mismatched_prayer_times = PrayerTime.objects.filter(
        #         masjids=self
        #     ).exclude(location__city=self.address.city)

        #     # Bulk remove using `remove(*mismatched_prayer_times)`
        #     if mismatched_prayer_times:
        #         with transaction.atomic():
        #             self.prayertime_set.remove(*mismatched_prayer_times)

        #     # 2. Link the Masjid to PrayerTimes in the new city
        #     matching_prayer_times = PrayerTime.objects.filter(location__city__iexact=self.address.city)
        #     with transaction.atomic():
        #         self.prayertime_set.add(*matching_prayer_times)


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
