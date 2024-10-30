from django.contrib import admin
from django.contrib.gis import admin as geoadmin
from core.admin import export_to_csv
from .models import Masjid


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

admin.site.register(Masjid, MasjidAdmin)
