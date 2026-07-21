from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from .validators import validate_field_path

""" IMPLEMENT CACHING FOR THIS MODEL """
class ModelFieldLabel(models.Model):
    """
    Stores human-readable labels for model field paths.

    Example:
        model = KYCRecord
        field_path = "person__name"
        label = "Customer Name"
    """

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE
    )

    field_path = models.CharField(
        max_length=255,
        help_text="Django ORM path, e.g. 'person__name'"
    )

    label = models.CharField(max_length=255)

    description = models.TextField(blank=True)

    group = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional grouping for UI sections"
    )

    class Meta:
        unique_together = ("content_type", "field_path")

    def clean(self):
        model = self.content_type.model_class()

        if not model:
            raise ValidationError("Invalid content type")

        validate_field_path(model, self.field_path)

    def __str__(self):
        return f"{self.content_type} :: {self.field_path} → {self.label}"