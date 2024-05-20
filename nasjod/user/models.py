from uuid import uuid4
from datetime import date

import phonenumbers

from django.conf import settings
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.exceptions import ValidationError

from core._helpers import image_path_upload
from core.models import Address, GDPR_compliance

class UserManager(BaseUserManager):
    def create_user(
        self,
        email,
        address=None,
        password=None,
        device_os=None,
        device_token=None,
        **extra_fields,
    ):
        """Create and save a new user"""
        if not email:
            raise ValueError("Email adresse is compulsory!")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        # for multiple dbs we use using=self._db
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a new superuser with all permissions."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        # Checks to ensure proper superuser flags
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        # Create user already setting superuser and staff flags
        user = self.create_user(email, password=password, **extra_fields)
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin, GDPR_compliance):
    """Custom user model that supports using email instead of username"""

    SEX = [
        ("Male", "male"),
        ("Female", "female"),
    ]
    username = models.CharField(default="", max_length=50, blank=True)
    identifier = models.CharField(default=uuid4, max_length=50, editable=False)
    email = models.EmailField(max_length=255, unique=True)
    sex = models.CharField(max_length=30, choices=SEX, null=True)
    birth_date = models.DateField(null=True)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    address = models.OneToOneField(Address, related_name='address_user',
                                   on_delete=models.SET_NULL, null=True, blank=True)
    photo = models.ImageField(null=True, blank=True, upload_to=image_path_upload)

    objects = UserManager()

    USERNAME_FIELD = "email"

    def clean(self):
        if not getattr(self, 'is_superuser', False):
            """Validate age is below 15 and phone number is correctly formatted."""
            # Validate age
            if settings.VALIDATE_AGE:
                today = date.today()
                age = today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
                if age < settings.MINIMUM_AGE_LIMIT:
                    raise ValidationError({'birth_date': 'Age must be below 15.'})

            # Validate phone number
            if self.phone_number:
                try:
                    phone_number_obj = phonenumbers.parse(self.phone_number, None)
                    if not phonenumbers.is_valid_number(phone_number_obj):
                        raise ValidationError({'phone_number': 'Invalid phone number.'})
                    self.phone_number = phonenumbers.format_number(phone_number_obj, phonenumbers.PhoneNumberFormat.E164)
                except phonenumbers.NumberParseException:
                    raise ValidationError({'phone_number': 'Invalid phone number format.'})


    def save(self, *args, **kwargs):
        """Override the save method to include validation."""
        self.clean()  # Validates the model before saving.
        super().save(*args, **kwargs)  # Call the super class's save method

    def __str__(self) -> str:
        return self.email
