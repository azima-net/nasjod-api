from django import forms
from django.db import models, transaction
from django.contrib import admin, messages
from django.contrib.gis import admin as geoadmin
from core.admin import export_to_csv
from .models import Masjid, SuggestionMasjidModification
from prayertime.models import IqamaTime, JumuahPrayerTime, PrayerTime


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
        ]
    actions = [export_to_csv]

admin.site.register(Masjid, MasjidAdmin)

@admin.register(SuggestionMasjidModification)
class SuggestionMasjidModificationAdmin(admin.ModelAdmin):
    list_display = (
        'uuid', 'name', 'size', 'telephone', 'is_active', 'parking', 'disabled_access',
        'ablution_room', 'woman_space', 'adult_courses', 'children_courses',
        'salat_al_eid', 'salat_al_janaza', 'iftar_ramadhan', 'itikef',
        'fajr_iqama', 'dhuhr_iqama', 'asr_iqama', 'maghrib_iqama', 'isha_iqama',
        'jumuah_time', 'first_timeslot_jumuah', 'eid_time', 'created_at', 'updated_at'
    )
    search_fields = [
        "uuid",
        "name",
        ]
    readonly_fields = ('uuid', 'created_at', 'updated_at')

    @admin.action(description="Accept Suggestion and Update Masjid")
    def accept_suggestion(self, request, queryset):
        for suggestion in queryset:
            try:
                masjid = suggestion.suggestion_masjid
                if not masjid:
                    self.message_user(
                        request,
                        f"Suggestion {suggestion.name} does not have a linked Masjid.",
                        messages.ERROR,
                    )
                    continue

                # Update Masjid fields
                masjid_fields = {
                    'name': suggestion.name,
                    'telephone': suggestion.telephone,
                    'size': suggestion.size,
                    'cover': suggestion.cover,
                    'parking': suggestion.parking,
                    'disabled_access': suggestion.disabled_access,
                    'ablution_room': suggestion.ablution_room,
                    'woman_space': suggestion.woman_space,
                    'adult_courses': suggestion.adult_courses,
                    'children_courses': suggestion.children_courses,
                    'salat_al_eid': suggestion.salat_al_eid,
                    'salat_al_janaza': suggestion.salat_al_janaza,
                    'iftar_ramadhan': suggestion.iftar_ramadhan,
                    'itikef': suggestion.itikef,
                }
                # Only update fields that are not empty
                for field, value in masjid_fields.items():
                    if value not in [None, '', False]:
                        setattr(masjid, field, value)
                masjid.save()

                # Update IqamaTime
                if suggestion.fajr_iqama or suggestion.dhuhr_iqama or suggestion.asr_iqama or suggestion.maghrib_iqama or suggestion.isha_iqama:
                    iqama_time, created = IqamaTime.objects.get_or_create(
                        masjid=masjid,
                    )
                    iqama_fields = {
                        'fajr_iqama': suggestion.fajr_iqama,
                        'dhuhr_iqama': suggestion.dhuhr_iqama,
                        'asr_iqama': suggestion.asr_iqama,
                        'maghrib_iqama': suggestion.maghrib_iqama,
                        'isha_iqama': suggestion.isha_iqama,
                    }
                    for field, value in iqama_fields.items():
                        if value is not None:
                            setattr(iqama_time, field, value)
                    iqama_time.save()

                # # Update JumuahPrayerTime
                if suggestion.jumuah_time or suggestion.first_timeslot_jumuah:
                    jumuah_prayer_time, created = JumuahPrayerTime.objects.get_or_create(
                        masjid=masjid,
                    )
                    if suggestion.jumuah_time:
                        jumuah_prayer_time.jumuah_time = suggestion.jumuah_time
                    if suggestion.first_timeslot_jumuah is not None:
                        jumuah_prayer_time.first_timeslot_jumuah = suggestion.first_timeslot_jumuah
                    jumuah_prayer_time.save()

                self.message_user(
                    request,
                    f"Successfully accepted suggestion for Masjid: {masjid.name} ",
                    messages.SUCCESS,
                )
            except Exception as e:
                self.message_user(
                    request,
                    f"Error processing suggestion {suggestion.name}: {e}",
                    messages.ERROR,
                )

    actions = ['accept_suggestion']

