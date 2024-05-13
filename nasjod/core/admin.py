from django.contrib.gis import admin
from .models import Address

class AddressAdmin(admin.GISModelAdmin):
    # Setting the default map template
    # map_template = 'gis/admin/custom_osm.html'
    pass

admin.site.register(Address, AddressAdmin)
