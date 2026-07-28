import uuid
from datetime import datetime

from django.core.exceptions import ValidationError

from .models import (
    GlobalParameter,
    StringValue,
    IntValue,
    FloatValue,
    BooleanValue,
    UUIDValue,
    DateTimeValue,
    JsonValue,
)

VALUE_MODEL_MAP = {
    GlobalParameter.Type.STRING: StringValue,
    GlobalParameter.Type.INT: IntValue,
    GlobalParameter.Type.FLOAT: FloatValue,
    GlobalParameter.Type.BOOLEAN: BooleanValue,
    GlobalParameter.Type.UUID: UUIDValue,
    GlobalParameter.Type.DATETIME: DateTimeValue,
    GlobalParameter.Type.JSON: JsonValue,
}


def coerce_value(param_type, raw_value):
    if raw_value in [None, ""]:
        return None

    try:
        if param_type == GlobalParameter.Type.INT:
            return int(raw_value)

        elif param_type == GlobalParameter.Type.FLOAT:
            return float(raw_value)

        elif param_type == GlobalParameter.Type.BOOLEAN:
            val = str(raw_value).lower()
            if val in ["true", "1", "yes"]:
                return True
            elif val in ["false", "0", "no"]:
                return False
            raise ValueError("Invalid boolean")

        elif param_type == GlobalParameter.Type.UUID:
            return uuid.UUID(raw_value)

        elif param_type == GlobalParameter.Type.DATETIME:
            return datetime.fromisoformat(raw_value)

        elif param_type == GlobalParameter.Type.JSON:
            if isinstance(raw_value, (dict, list)):
                return raw_value
            import json
            return json.loads(raw_value)

        elif param_type == GlobalParameter.Type.STRING:
            return str(raw_value)

        raise ValueError("Unsupported type")

    except Exception as e:
        raise ValidationError(f"Invalid value for type {param_type}: {e}")


def set_parameter_value(instance, value):
    value_model = VALUE_MODEL_MAP.get(instance.type)

    if not value_model:
        raise ValidationError("Unsupported parameter type")

    existing = getattr(instance, "value_obj", None)

    # Remove value
    if value is None:
        if existing:
            existing.delete()
        return

    # Update same type
    if existing and isinstance(existing, value_model):
        existing.value = value
        existing.save()
        return

    # Replace value
    if existing:
        existing.delete()

    value_model.objects.create(
        parameter=instance,
        value=value
    )