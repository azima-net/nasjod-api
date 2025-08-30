import uuid

from django.db import models
from django.contrib.gis.db import models as geomodels


class Address(models.Model):
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    street = models.CharField(max_length=255, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    additional_info = models.CharField(max_length=255, blank=True, null=True)
    route_km_marker = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    coordinates = geomodels.PointField()
    
    def __str__(self):
        return f"{self.street}, {self.route_km_marker or ''}, {self.city}, {self.state}, {self.zip_code}, {self.country}"


class GDPR_compliance(models.Model):
    consent_given = models.BooleanField(default=False)
    is_subscribed_to_newsletter = models.BooleanField(default=False)
    is_subscribed_to_marketing_emails = models.BooleanField(default=False)
    is_subscribed_to_marketing_sms = models.BooleanField(default=False)
    is_subscribed_to_marketing_push_notification = models.BooleanField(default=False)
    consent_for_data_enrichment = models.BooleanField(default=False)
    consent_for_personalization = models.BooleanField(default=False)
    consent_for_third_party_sharing = models.BooleanField(default=False)

    class Meta:
        abstract = True

class ObjectBase(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
