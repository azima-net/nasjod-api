from django.db import models
import uuid
from rest_framework_simplejwt.tokens import AccessToken


class APIKey(models.Model):
    identifier = models.CharField(max_length=255, unique=True, default=uuid.uuid4)
    app_name = models.CharField(max_length=255, default="app-default")  # New field for the app name
    key = models.TextField(blank=True, editable=False)  # The generated API key
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.key:  # Generate the key only if it doesn’t already exist
            token = AccessToken()
            token['app'] = self.app_name  # Use the app_name field for the claim
            self.key = str(token)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"API Key for {self.app_name} ({self.identifier})"
