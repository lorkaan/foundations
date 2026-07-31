from django.contrib import admin

from .models import AutomationAction, AutomationActionRun, AutomationRule, AutomationRun, AutomationTrigger

# Register your models here.
admin.register(AutomationRule)
admin.register(AutomationTrigger)
admin.register(AutomationAction)
admin.register(AutomationRun)
admin.register(AutomationActionRun)