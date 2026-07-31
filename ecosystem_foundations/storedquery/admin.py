from django.contrib import admin

from .models import SavedQuery, SavedQueryPermission

# Register your models here.
admin.register(SavedQuery)
admin.register(SavedQueryPermission)