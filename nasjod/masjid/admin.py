from django import forms
from django.db import models, transaction
from django.contrib import admin
from django.contrib.gis import admin as geoadmin
from core.admin import export_to_csv
from .models import Masjid
from prayertime.models import PrayerTime


class MasjidAdminForm(forms.ModelForm):
    prayer_times_location = forms.ChoiceField(required=False, label="Prayer Times Location")

    class Meta:
        model = Masjid
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Fetch distinct location combinations as tuples (country, state, city)
        location_combinations = PrayerTime.objects.values_list(
            'location__country', 'location__state', 'location__city'
        ).distinct()
        
        # Remove duplicates and format as "Country, State, City"
        unique_locations = sorted({f"{country}, {state}, {city}" for country, state, city in location_combinations})
        
        # Set the choices for the dropdown
        self.fields['prayer_times_location'].choices = [
            ('', 'Select Prayer Times Location')
        ] + [(location, location) for location in unique_locations]

        # Set default value based on existing linked PrayerTime
        if self.instance.pk:  # Check if the Masjid instance already exists
            linked_prayer_time = self.instance.prayertime_set.first()  # Get the first linked PrayerTime, if any
            if linked_prayer_time and linked_prayer_time.location:
                # Format the existing location as "Country, State, City"
                default_location = f"{linked_prayer_time.location.country}, {linked_prayer_time.location.state}, {linked_prayer_time.location.city}"
                self.fields['prayer_times_location'].initial = default_location

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Get the selected location string
        location = self.cleaned_data.get('prayer_times_location')
        
        if location:
            # Split the selected location into country, state, and city
            country, state, city = location.split(", ")
            
            # Link prayer times based on the selected location trio
            matching_prayer_times = PrayerTime.objects.filter(
                location__country=country,
                location__state=state,
                location__city=city
            )
            with transaction.atomic():
                instance.prayertime_set.set(matching_prayer_times)

        if commit:
            instance.save()
        return instance


class MasjidAdmin(geoadmin.GISModelAdmin):
    form = MasjidAdminForm
    list_display = [
        "uuid",
        "name",
        "telephone",
        "size",
        "parking",
        "disabled_access",
        "ablution_room",
        "woman_space",
        "adult_courses",
        "children_courses",
        "salat_al_eid",
        "salat_al_janaza",
        "iftar_ramadhan",
        "itikef",
        "is_active",
        "created_at",
        "updated_at",
    ]

    list_filter = [
        "size",
        "parking",
        "disabled_access",
        "ablution_room",
        "woman_space",
        "adult_courses",
        "children_courses",
        "salat_al_eid",
        "salat_al_janaza",
        "iftar_ramadhan",
        "itikef",
        "is_active",
        "created_at",
        "updated_at",
    ]
    search_fields = [
        "uuid",
        "name",
        "telephone",
        "address",
        ]
    actions = [export_to_csv]

admin.site.register(Masjid, MasjidAdmin)
