from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

from ..base.models import ActiveMixin, BaseItemType, BaseUuidPrimaryKeyModel, ConditionalMixin, MetadataMixin, RepeatableOrderedMixin, TimeAuditableMixin

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

class FormSection(BaseItemType, MetadataMixin, BaseUuidPrimaryKeyModel):
    form_type = models.ForeignKey(FormType, on_delete=models.CASCADE, related_name="sections")

    description = models.TextField(blank=True)

    order = models.PositiveIntegerField(
        default=0
    )

    class Meta(BaseItemType.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["form_type", "code"],
                name="unique_section_code_per_form_type"
            ),
            models.UniqueConstraint(
                fields=["form_type", "order"],
                name="unique_section_order_per_form_type"
            )
        ]

class FormGroup(RepeatableOrderedMixin, BaseUuidPrimaryKeyModel):
    form_section = models.ForeignKey(FormSection, on_delete=models.CASCADE, related_name="groups")

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children"
    )

    def clean(self):
        super().clean()

        if self.parent:
            if self.parent.form_section_id != self.form_section_id:
                raise ValidationError(
                    "Parent group must belong to the same form section"
                )
        # Prevent self-reference
        if self.parent_id and self.parent_id == self.id:
            raise ValidationError("A group cannot be its own parent.")

        # Prevent circular references
        visited = set()
        current = self.parent

        while current:
            if current.id == self.id:
                raise ValidationError("Circular parent relationship detected.")

            if current.id in visited:
                break  # safety guard (shouldn't normally happen)

            visited.add(current.id)
            current = current.parent

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class  Meta(RepeatableOrderedMixin.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["form_section", "parent", "order"],
                name="unique_group_order_per_parent"
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

class FormGroupInstance(TimeAuditableMixin, BaseUuidPrimaryKeyModel):
    form_instance = models.ForeignKey(
        FormInstance,
        on_delete=models.CASCADE,
        related_name="group_instances"
    )

    group = models.ForeignKey(
        FormGroup,
        on_delete=models.CASCADE,
        related_name="instances"
    )

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children"
    )

    def clean(self):
        # --- 1. Parent must belong to same FormInstance ---
        if self.parent:
            if self.parent.form_instance_id != self.form_instance_id:
                raise ValidationError(
                    "Parent instance must belong to the same form instance."
                )

        # --- 2. Prevent self-reference ---
        if self.parent_id and self.parent_id == self.id:
            raise ValidationError("A group instance cannot be its own parent.")

        # --- 3. Enforce structural consistency with FormGroup ---
        if self.parent:
            expected_parent_group = self.group.parent_id  # assumes FormGroup has parent

            if expected_parent_group != self.parent.group_id:
                raise ValidationError(
                    "Parent instance does not match the group hierarchy."
                )

        # --- 4. Prevent circular references ---
        visited = set()
        current = self.parent

        while current:
            if current.id == self.id:
                raise ValidationError("Circular parent relationship detected.")

            if current.id in visited:
                break  # safety guard

            visited.add(current.id)
            current = current.parent

        # --- 5. Ensure same FormType (extra safety) ---
        if self.group.form_section.form_type_id != self.form_instance.form_type_id:
            raise ValidationError(
                "Group does not belong to the same form type as the form instance."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=["form_instance"]),
            models.Index(fields=["parent"]),
        ]

    def __str__(self):
        return f"{self.group_id} ({self.id})"

class FormAnswer(TimeAuditableMixin, BaseUuidPrimaryKeyModel):
    group_instance = models.ForeignKey(
        FormGroupInstance,
        related_name="answers",
        on_delete=models.CASCADE
    )
    question = models.ForeignKey(FormQuestion, on_delete=models.CASCADE)

    # universal value store
    value = models.JSONField()

    class Meta:
        unique_together = ("group_instance", "question")

    def clean(self):
        # --- 1. Ensure same FormType ---
        if (
            self.question.form_group.form_section.form_type_id
            != self.group_instance.form_instance.form_type_id
        ):
            raise ValidationError(
                "Question does not belong to this form instance."
            )

        # --- 2. Ensure question belongs to the correct group ---
        if self.question.form_group_id != self.group_instance.group_id:
            raise ValidationError(
                "Question does not belong to this group instance."
            )

    def save(self, *args, **kwargs):
        self.full_clean()  # ensure clean() is always enforced
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.question.label} -> {self.value}"


"""
    The Mapping from Instance and Answers into a model data
"""
class FormProcessingConfig(TimeAuditableMixin, BaseItemType, BaseUuidPrimaryKeyModel):
    form_type = models.ForeignKey(FormType, on_delete=models.CASCADE, related_name="mappings")
    config = models.JSONField()