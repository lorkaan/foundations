from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, UserRole
from .forms import UserAdminForm


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserAdminForm

    list_display = (
        "username",
        "email",
        "role",
        "is_staff",
        "is_superuser",
        "is_active",
    )

    list_filter = (
        "role",
        "is_staff",
        "is_superuser",
        "is_active",
    )

    fieldsets = (
        (None, {"fields": ("username", "password")}),

        ("Personal Info", {
            "fields": ("full_name", "email")
        }),

        ("Access", {
            "fields": (
                "role",
                "is_active",
                "is_staff",
                "is_superuser",
            )
        }),

        ("Groups & Permissions", {
            "fields": ("groups", "user_permissions")
        }),

        ("Important Dates", {
            "fields": ("date_joined",)
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username",
                "password1",
                "password2",
                "role",
                "is_active",
                "is_staff",
                "is_superuser",
            ),
        }),
    )

    search_fields = ("username", "email")
    ordering = ("username",)
    filter_horizontal = ("groups", "user_permissions")

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("key", "label", "is_system")
    search_fields = ("key", "label")
    list_filter = ("is_system",)