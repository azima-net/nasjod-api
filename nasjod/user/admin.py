from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from core.admin import export_to_csv, activate_users, deactivate_users
from .filters import BirthYearFilter, UserCityFilter
from .models import UserContributor


User = get_user_model()

class UserAdmin(BaseUserAdmin):
    ordering = ["id"]
    list_display = ["email", "first_name", "last_name", "is_active", "is_staff"]
    fieldsets = (
        (None, {"fields": ("email", "password", "username")}),
        (("Personal Info"), {"fields": ("first_name", "last_name")}),
        (("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser")}),
        (("Important dates"), {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "first_name", "last_name",
                       "sex", "birth_date", "phone_number", "address", "photo"),
        }),
    )
    list_filter = ["sex", BirthYearFilter, UserCityFilter]

    actions = [export_to_csv, activate_users, deactivate_users]

admin.site.register(User, UserAdmin)

@admin.register(UserContributor)
class UserContributorAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'masjids', 'contribution_date', 'accept_to_display')
    list_filter = ('accept_to_display', 'contribution_date')
    search_fields = ('name', 'email', 'masjids')
    readonly_fields = ('contribution_date',)
    ordering = ('-contribution_date',)
