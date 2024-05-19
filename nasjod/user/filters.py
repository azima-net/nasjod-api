from django.contrib import admin
from django.db.models.functions import ExtractYear

from core.filters import CityFilter


# Admin filters
class BirthYearFilter(admin.SimpleListFilter):
    title = "Birth Year"
    parameter_name = "birth_year"

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        years = (
            qs.annotate(year=ExtractYear("birth_date"))
            .values_list("year", flat=True)
            .distinct()
        )
        return [(year, year) for year in set(years)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(birth_date__year=self.value())

class UserCityFilter(CityFilter):
    address_field = "address__city"