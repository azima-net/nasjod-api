import phonenumbers

from django.db import models

from core.models import Address
from core._helpers import image_path_upload


class Masjid(models.Model):
    SIZE_CHOICES = (
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
    )

    name = models.CharField(max_length=255)
    address = models.OneToOneField(Address, related_name='address_masjid',
                                   on_delete=models.SET_NULL, null=True, blank=True)
    telephone = models.CharField(max_length=20)
    photo = models.ImageField(null=True, blank=True, upload_to=image_path_upload)
    cover = models.ImageField(null=True, blank=True, upload_to=image_path_upload)
    size = models.CharField(max_length=1, choices=SIZE_CHOICES, default='M')

    # Boolean fields
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

    class Meta:
        verbose_name_plural = "Masajid"

    def __str__(self):
        return self.name
