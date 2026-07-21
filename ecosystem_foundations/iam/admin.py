from django.contrib import admin

from .flags import PermissionFlag

from .models import RoleFieldPermission, UserFieldPermission


# -----------------------------
# Helper for flag display
# -----------------------------
def format_flags(obj):
    flags = []

    if obj.permission & PermissionFlag.VIEW:  # VIEW
        flags.append("V")
    if obj.permission & PermissionFlag.EDIT:  # EDIT
        flags.append("E")
    if obj.permission & PermissionFlag.ADD:  # ADD
        flags.append("A")
    if obj.permission & PermissionFlag.DELETE:  # DELETE
        flags.append("D")

    return "".join(flags)


# -----------------------------
# Role-based permissions
# -----------------------------
@admin.register(RoleFieldPermission)
class RoleFieldPermissionAdmin(admin.ModelAdmin):

    list_display = (
        "role",
        "content_type",
        "field_name",
        "permission",
        "flags",
    )

    list_filter = (
        "role",
        "content_type",
    )

    search_fields = (
        "field_name",
    )

    autocomplete_fields = ("role", "content_type")

    def flags(self, obj):
        return format_flags(obj)

    flags.short_description = "Flags"


# -----------------------------
# User overrides
# -----------------------------
@admin.register(UserFieldPermission)
class UserFieldPermissionAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "content_type",
        "field_name",
        "permission",
        "flags",
    )

    list_filter = (
        "content_type",
    )

    search_fields = (
        "user__username",
        "field_name",
    )

    autocomplete_fields = ("user", "content_type")

    def flags(self, obj):
        return format_flags(obj)

    flags.short_description = "Flags"