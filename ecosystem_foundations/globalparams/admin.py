from django.contrib import admin
from .models import GlobalParameter
from .forms import GlobalParameterAdminForm


@admin.register(GlobalParameter)
class GlobalParameterAdmin(admin.ModelAdmin):
    form = GlobalParameterAdminForm

    list_display = ["name", "type", "is_active"]
    list_filter = ["type", "is_active"]
    search_fields = ["name"]