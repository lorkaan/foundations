from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

from ..base.models import ActiveMixin, BaseItemType, BaseUuidPrimaryKeyModel, ConditionalMixin, RepeatableOrderedMixin, TimeAuditableMixin

class FormInstanceStatus(models.TextChoices):
    DRAFT = "D", "Draft"
    SUBMITTED = "S", "Submitted"
    LOCKED = "L", "Locked"

class FieldType(models.TextChoices):
        TEXT = "T", "Text"
        NUMBER = "N", "Number"
        DATE = "D", "Date"
        DATE_RANGE = "DR", "Date Range"
        ENUM = "E", "Enum"
        DYNAMIC = "S", "Dynamic Select"
        DATETIME = "DT", "DateTime"
        DATETIME_RANGE = "DTR", "DateTime Range"

# Create your models here.
class FormType(TimeAuditableMixin, ActiveMixin, BaseUuidPrimaryKeyModel):
    name = models.CharField(max_length=255, blank=False)
    description = models.TextField(blank=True)

    code = models.CharField(max_length=100)
    version = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        constraints = [
            # name must not be empty string
            models.CheckConstraint(
                condition=~models.Q(name=""),
                name="formtype_name_not_empty",
            ),

            # code + version must be unique
            models.UniqueConstraint(
                fields=["code", "version"],
                name="unique_formtype_code_version",
            ),
        ]

class FormSection(RepeatableOrderedMixin, BaseUuidPrimaryKeyModel):
    form_type = models.ForeignKey(FormType, on_delete=models.CASCADE, related_name="sections")

    class Meta(RepeatableOrderedMixin.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["form_type", "order"],
                name="unique_group_order_per_form"
            )
        ]

class FormGroup(RepeatableOrderedMixin, BaseUuidPrimaryKeyModel):
    form_section = models.ForeignKey(FormSection, on_delete=models.CASCADE, related_name="groups")

    class  Meta(RepeatableOrderedMixin.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["form_section", "order"],
                name="unique_group_order_per_section"
            )
        ]

class FormQuestion(ConditionalMixin, TimeAuditableMixin, BaseUuidPrimaryKeyModel):
    label = models.CharField(max_length=255)
    form_group = models.ForeignKey(
        FormGroup,
        related_name="questions",
        on_delete=models.CASCADE
    )

    field_type = models.CharField(max_length=3, choices=FieldType)

    code = models.CharField(max_length=100) # Useful just for identifying the question

    required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    # Flexible schema definition
    schema = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["order"]
        constraints = [
            # Prevent duplicate labels in same form
            models.UniqueConstraint(
                fields=["form_group", "label"],
                name="unique_question_label_per_group"
            ),

            # Prevent duplicate ordering collisions
            models.UniqueConstraint(
                fields=["form_group", "order"],
                name="unique_question_order_per_group"
            ),
            models.UniqueConstraint(
                fields=["form_group", "code"],
                name="unique_question_code_per_group"
            )
        ]

    def __str__(self):
        return f"{self.label} ({self.field_type})"

class FormInstance(TimeAuditableMixin, BaseUuidPrimaryKeyModel):
    form_type = models.ForeignKey(FormType, on_delete=models.CASCADE)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,   # Does this integrate with the custom auth model?
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    status = models.CharField(
        max_length=1,
        choices=FormInstanceStatus.choices,
        default=FormInstanceStatus.DRAFT
    )

    def __str__(self):
        return f"Instance {self.id} - {self.form_type.name}"

class FormAnswer(TimeAuditableMixin, BaseUuidPrimaryKeyModel):
    form_instance = models.ForeignKey(
        FormInstance,
        related_name="answers",
        on_delete=models.CASCADE
    )
    question = models.ForeignKey(FormQuestion, on_delete=models.CASCADE)

    # universal value store
    value = models.JSONField()

    class Meta:
        unique_together = ("form_instance", "question")

    def clean(self):
        if self.question.form_type_id != self.form_instance.form_type_id:
            raise ValidationError("Question does not belong to this form instance")

    def save(self, *args, **kwargs):
        self.full_clean()  # ensure clean() is always enforced
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.question.label} -> {self.value}"

"""
    The Mapping from Instance and Answers into a model data
"""
class FormMapping(TimeAuditableMixin, ActiveMixin, BaseUuidPrimaryKeyModel):
    form_type = models.ForeignKey(FormType, on_delete=models.CASCADE, related_name="mappings")
    config = models.JSONField()