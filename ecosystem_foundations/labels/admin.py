from django.contrib import admin
from .models import ModelFieldLabel


@admin.register(ModelFieldLabel)
class ModelFieldLabelAdmin(admin.ModelAdmin):
    list_display = ("content_type", "field_path", "label", "group")
    search_fields = ("field_path", "label")