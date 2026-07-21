from django.db import models
from .policy.sensitivity import DataSensitivity

class SensitiveFieldMixin:
    def __init__(self, *args, sensitivity=DataSensitivity.INTERNAL, **kwargs):
        self.sensitivity = sensitivity
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()

        if hasattr(self, "sensitivity"):
            kwargs["sensitivity"] = self.sensitivity

        return name, path, args, kwargs
    
    def is_sensitive(self):
        return self.sensitivity in {
            DataSensitivity.SENSITIVE,
            DataSensitivity.HIGHLY_SENSITIVE,
        }

    def is_highly_sensitive(self):
        return self.sensitivity == DataSensitivity.HIGHLY_SENSITIVE

class SensitiveCharField(SensitiveFieldMixin, models.CharField):
    pass


class SensitiveTextField(SensitiveFieldMixin, models.TextField):
    pass


class SensitiveIntegerField(SensitiveFieldMixin, models.IntegerField):
    pass