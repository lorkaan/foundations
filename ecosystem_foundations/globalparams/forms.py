import json
import uuid
from datetime import datetime

from django import forms
from django.core.exceptions import ValidationError

from .models import (
    GlobalParameter,
    JsonValue,
    StringValue,
    IntValue,
    FloatValue,
    BooleanValue,
    UUIDValue,
    DateTimeValue,
)

# Map parameter type → value model
VALUE_MODEL_MAP = {
    GlobalParameter.Type.STRING: StringValue,
    GlobalParameter.Type.INT: IntValue,
    GlobalParameter.Type.FLOAT: FloatValue,
    GlobalParameter.Type.BOOLEAN: BooleanValue,
    GlobalParameter.Type.UUID: UUIDValue,
    GlobalParameter.Type.DATETIME: DateTimeValue,
    GlobalParameter.Type.JSON: JsonValue,
}


class GlobalParameterAdminForm(forms.ModelForm):
    """
    Admin form that dynamically handles typed parameter values.
    """

    value = forms.CharField(
        required=False,
        widget=forms.Textarea,
        help_text="Enter value matching the selected type",
    )

    class Meta:
        model = GlobalParameter
        fields = ["name", "description", "type", "is_active"]

    # ----------------------------
    # Init
    # ----------------------------

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        instance = kwargs.get("instance")

        if instance:
            value_obj = getattr(instance, "value_obj", None)
            if value_obj:
                self.fields["value"].initial = value_obj.get_value()

    # ----------------------------
    # Validation
    # ----------------------------

    def clean(self):
        cleaned = super().clean()

        param_type = cleaned.get("type")
        raw_value = cleaned.get("value")

        if raw_value in [None, ""]:
            cleaned["value"] = None
            return cleaned

        try:
            if param_type == GlobalParameter.Type.INT:
                cleaned["value"] = int(raw_value)

            elif param_type == GlobalParameter.Type.FLOAT:
                cleaned["value"] = float(raw_value)

            elif param_type == GlobalParameter.Type.BOOLEAN:
                cleaned["value"] = str(raw_value).lower() in ["true", "1", "yes"]

            elif param_type == GlobalParameter.Type.UUID:
                cleaned["value"] = uuid.UUID(raw_value)

            elif param_type == GlobalParameter.Type.DATETIME:
                cleaned["value"] = datetime.fromisoformat(raw_value)

            elif param_type == GlobalParameter.Type.JSON:
                if isinstance(raw_value, (dict, list)):
                    cleaned["value"] = raw_value
                else:
                    cleaned["value"] = json.loads(raw_value)

            else:
                cleaned["value"] = str(raw_value)

        except Exception as e:
            raise ValidationError(f"Invalid value for type {param_type}: {e}")

        return cleaned

    # ----------------------------
    # Save Logic
    # ----------------------------

    def save(self, commit=True):
        instance = super().save(commit)

        value = self.cleaned_data.get("value")
        param_type = self.cleaned_data.get("type")

        value_model = VALUE_MODEL_MAP[param_type]

        existing = getattr(instance, "value_obj", None)

        # ----------------------------
        # Case 1: No value provided → delete existing
        # ----------------------------
        if value is None:
            if existing:
                existing.delete()
            return instance

        # ----------------------------
        # Case 2: Update existing same-type value
        # ----------------------------
        if existing and isinstance(existing, value_model):
            existing.value = value
            existing.save()
            return instance

        # ----------------------------
        # Case 3: Type changed → replace value object
        # ----------------------------
        if existing:
            existing.delete()

        value_model.objects.create(
            parameter=instance,
            value=value,
        )

        return instance
