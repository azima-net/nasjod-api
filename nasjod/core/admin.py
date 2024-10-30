import csv

from django import forms
from django.contrib.gis import admin
from django.http import HttpResponse

from prayertime.models import EidPrayerTime, PrayerTime

from .models import Address
from masjid.models import Masjid

class AddressAdminForm(forms.ModelForm):
    linked_masjid = forms.ModelChoiceField(
        queryset=Masjid.objects.all(),
        required=False,
        label="Linked Masjid"
    )

    class Meta:
        model = Address
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-select the linked masjid if one exists
        if self.instance and self.instance.pk:
            self.fields['linked_masjid'].initial = Masjid.objects.filter(address=self.instance).first()

class AddressAdmin(admin.GISModelAdmin):
    form = AddressAdminForm
    list_display = ('city', 'state', 'street', 'coordinates', 'linked_masjid', 'linked_prayer_time', 'country')
    search_fields = ('city', 'state', 'country')
    actions = ['export_to_csv']

    def save_model(self, request, obj, form, change):
        # Save the address instance
        super().save_model(request, obj, form, change)
        # Get the selected masjid from the form
        linked_masjid = form.cleaned_data.get('linked_masjid')
        if linked_masjid:
            linked_masjid.address = obj  # Link the masjid to this address
            linked_masjid.save()
        else:
            # Unlink the address from any masjid if None is selected
            Masjid.objects.filter(address=obj).update(address=None)

    def linked_masjid(self, obj):
        # Returns the linked Masjid's name if it exists
        return obj.address_masjid.name if hasattr(obj, 'address_masjid') else "No linked Masjid"
    linked_masjid.short_description = "Linked Masjid"

    def linked_prayer_time(self, obj):
        # Check if there are any related PrayerTime or EidPrayerTime instances
        if PrayerTime.objects.filter(location=obj).exists() or EidPrayerTime.objects.filter(location=obj).exists():
            return "Prayer Time Linked"
        return "No Linked Prayer Time"
    linked_prayer_time.short_description = "Linked Prayer Time"

admin.site.register(Address, AddressAdmin)


@admin.action(description="Activate selected users")
def activate_users(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description="Deactivate selected users")
def deactivate_users(modeladmin, request, queryset):
    queryset.update(is_active=False)


def export_to_csv(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={opts.verbose_name}.csv'
    writer = csv.writer(response)

    fields = [field for field in opts.get_fields() if not field.many_to_many and not field.one_to_many]
    # Write a first row with header information
    writer.writerow([field.verbose_name for field in fields])

    # Write data rows
    for obj in queryset:
        data_row = []
        for field in fields:
            value = getattr(obj, field.name)
            if callable(value):
                value = value()
            data_row.append(value)
        writer.writerow(data_row)
    return response

export_to_csv.short_description = 'Export Selected to CSV'
