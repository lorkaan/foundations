from django.contrib import admin

from .models import Signal, SignalItemType

# Register your models here.
admin.register(Signal)
admin.register(SignalItemType)