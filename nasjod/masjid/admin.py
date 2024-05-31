from django import forms
from django.core.exceptions import ValidationError
from django.contrib import admin
from django.contrib.gis import admin as geoadmin
from django.contrib.gis.forms import fields as gis_fields, widgets as gis_widgets
from core.admin import export_to_csv
from .models import Masjid, PrayerTime, JumuahPrayerTime, EidPrayerTime
from core.models import Address


class MasjidAdminForm(forms.ModelForm):
    street = forms.CharField(required=False)
    city = forms.CharField(required=False)
    state = forms.CharField(required=False)
    zip_code = forms.CharField(required=False)
    country = forms.CharField(required=False)
    coordinates = gis_fields.PointField(widget=gis_widgets.OSMWidget(attrs={'map_width': 800, 'map_height': 500}), required=False)

    class Meta:
        model = Masjid
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(MasjidAdminForm, self).__init__(*args, **kwargs)
        address_instance = getattr(self.instance, 'address', None)
        if address_instance:
            self.fields['street'].initial = address_instance.street
            self.fields['city'].initial = address_instance.city
            self.fields['state'].initial = address_instance.state
            self.fields['zip_code'].initial = address_instance.zip_code
            self.fields['country'].initial = address_instance.country
            self.fields['coordinates'].initial = address_instance.coordinates

    def clean(self):
        cleaned_data = super().clean()
        managers = cleaned_data.get('managers')
        assistants = cleaned_data.get('assistants')

        if managers and assistants:
            if set(managers).intersection(set(assistants)):
                raise ValidationError("A user cannot be both a manager and an assistant in the same masjid.")

        return cleaned_data

    def save(self, commit=True):
        masjid = super(MasjidAdminForm, self).save(commit=False)
        if commit:
            masjid.save()
        
        address_data = {
            'street': self.cleaned_data['street'],
            'city': self.cleaned_data['city'],
            'state': self.cleaned_data['state'],
            'zip_code': self.cleaned_data['zip_code'],
            'country': self.cleaned_data['country'],
            'coordinates': self.cleaned_data['coordinates']
        }
        # Check if Masjid already has an address linked
        if hasattr(masjid, 'address') and masjid.address:
            address = masjid.address
            for key, value in address_data.items():
                setattr(address, key, value)
            address.save()
        else:
            # Create a new address and link it to Masjid
            address = Address.objects.create(**address_data)
            masjid.address = address
        
        if commit:
            masjid.save()

        return masjid


class MasjidAdmin(geoadmin.GISModelAdmin):
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
    form = MasjidAdminForm

admin.site.register(Masjid, MasjidAdmin)

@admin.register(PrayerTime)
class PrayerTimeAdmin(admin.ModelAdmin):
    list_display = ('masjid', 'date', 'fajr', 'dhuhr', 'asr', 'maghrib', 'isha')
    list_filter = ('masjid', 'date')
    search_fields = ('masjid__name',)

@admin.register(JumuahPrayerTime)
class JumuahPrayerTimeAdmin(admin.ModelAdmin):
    list_display = ('masjid', 'date', 'jumuah_time')
    list_filter = ('masjid', 'date')
    search_fields = ('masjid__name',)

@admin.register(EidPrayerTime)
class eidPrayerTimeAdmin(admin.ModelAdmin):
    list_display = ('masjid', 'date', 'eid_time')
    list_filter = ('masjid', 'date')
    search_fields = ('masjid__name',)
