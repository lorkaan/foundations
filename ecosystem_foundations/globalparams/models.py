from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime
import uuid

from base.models import ActiveMixin, BaseUuidPrimaryKeyModel, TimeAuditableMixin


# ============================
# Base Value (Abstract)
# ============================

class BaseValue(TimeAuditableMixin, BaseUuidPrimaryKeyModel):
    """
    Abstract base for all parameter value types.

    Each GlobalParameter MUST have exactly one value object,
    enforced via OneToOne relationship.
    """

    parameter = models.OneToOneField(
        "GlobalParameter",
        on_delete=models.CASCADE,
        related_name="value_obj",
    )

    class Meta:
        abstract = True

    def get_value(self):
        """
        Return the raw value.
        Override in subclasses for computed/dynamic values.
        """
        return self.value


# ============================
# Concrete Value Types
# ============================

class StringValue(BaseValue):
    value = models.CharField(max_length=255)


class JsonValue(BaseValue):
    value = models.JSONField()


class IntValue(BaseValue):
    value = models.IntegerField()


class FloatValue(BaseValue):
    value = models.FloatField()


class BooleanValue(BaseValue):
    value = models.BooleanField()


class UUIDValue(BaseValue):
    value = models.UUIDField(default=uuid.uuid4)


class DateTimeValue(BaseValue):
    value = models.DateTimeField()


# ============================
# Global Parameter
# ============================

class GlobalParameter(ActiveMixin, TimeAuditableMixin, BaseUuidPrimaryKeyModel):
    """
    Represents a dynamic, admin-configurable parameter.

    Stores metadata and type.
    Actual value is stored in a corresponding BaseValue subclass.
    """

    class Type(models.TextChoices):
        STRING = "S", "String"
        INT = "I", "Integer"
        FLOAT = "F", "Float"
        BOOLEAN = "B", "Boolean"
        UUID = "U", "UUID"
        DATETIME = "D", "Datetime"
        JSON = "J", "JSON"

    TYPE_MAP = {
        Type.STRING: str,
        Type.INT: int,
        Type.FLOAT: float,
        Type.BOOLEAN: bool,
        Type.UUID: uuid.UUID,
        Type.DATETIME: datetime,
        Type.JSON: (dict, list),
    }

    name = models.CharField(
        max_length=255,
        unique=True,
        null=False,
        blank=False
    )

    description = models.TextField(blank=True)

    type = models.CharField(
        max_length=1,
        choices=Type.choices,
        default=Type.STRING,
    )

    # ----------------------------
    # Core Value Access
    # ----------------------------

    def get_value(self):
        """
        Resolve and validate the parameter value.
        """
        value_obj = getattr(self, "value_obj", None)

        if not value_obj:
            return None

        val = value_obj.get_value()

        expected_type = self.TYPE_MAP.get(self.type)

        if expected_type and not isinstance(val, expected_type):
            raise TypeError(
                f"GlobalParameter '{self.name}' expected {expected_type}, got {type(val)}"
            )

        return val

    # ----------------------------
    # Validation
    # ----------------------------

    def clean(self):
        """
        Ensure type consistency between parameter and value object.
        """
        super().clean()

        value_obj = getattr(self, "value_obj", None)

        if value_obj:
            val = value_obj.get_value()
            expected_type = self.TYPE_MAP.get(self.type)

            if expected_type and not isinstance(val, expected_type):
                raise ValidationError(
                    f"Value type mismatch for parameter '{self.name}'"
                )

    # ----------------------------
    # Display
    # ----------------------------

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

