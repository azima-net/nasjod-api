from django.contrib import admin
from django.utils.html import format_html
from .models import APIKey

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'app_name', 'created_at')
    fields = ('app_name', 'key', 'created_at', 'identifier')
    readonly_fields = ('key', 'created_at', 'identifier')

    def save_model(self, request, obj, form, change):
        """
        Save the model and display the generated key only during creation.
        """
        if not obj.pk:  # Object is being created
            super().save_model(request, obj, form, change)
            # Display the generated API key
            self.message_user(
                request,
                format_html(
                    f"<strong>API Key generated:</strong> <pre>{obj.key}</pre>"
                )
            )
        else:
            super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        """
        Make the `key` field readonly after creation.
        """
        if obj:  # For existing objects, make `key` read-only
            return self.readonly_fields + ('key',)
        return self.readonly_fields
