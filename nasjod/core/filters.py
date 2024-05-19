from django.contrib import admin


# Admin filters

class CityFilter(admin.SimpleListFilter):
    title = "City"
    parameter_name = "city"

    def lookups(self, request, model_admin):
        if self.address_field:
            qs = model_admin.get_queryset(request)
            cities = qs.values_list(self.address_field, flat=True).distinct()
            return [(city, city) for city in set(cities)]
        else:
            return []

    def queryset(self, request, queryset):
        if self.address_field and self.value():
            return queryset.filter(**{self.address_field: self.value()})