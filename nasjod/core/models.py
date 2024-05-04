from django.db import models
from django.contrib.gis.db import models as geomodels


class Address(models.Model):
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    country = models.CharField(max_length=100)
    coordinates = geomodels.PointField()

    def __str__(self):
        return f"{self.street}, {self.city}, {self.state}, {self.zip_code}, {self.country}"


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
