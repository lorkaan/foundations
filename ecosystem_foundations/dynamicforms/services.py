from django.core.exceptions import ValidationError
from django.db import models

from ..base.models import BaseItemType

from .registry import VALIDATOR_REGISTRY, DATA_SOURCE_REGISTRY

def validate_answer(question, value):
    schema = question.schema or {}

    if question.required and value in [None, "", []]:
        raise ValidationError("Required field")

    validator = VALIDATOR_REGISTRY.get(question.field_type)

    if not validator:
        raise ValidationError(f"No validator for {question.field_type}")

    validator(question, value, schema)

# =========================================================
# FIELD VALIDATORS
# =========================================================

@VALIDATOR_REGISTRY.register("T")  # TEXT
def validate_text(question, value, schema):
    if not isinstance(value, str):
        raise ValidationError("Must be a string")

    min_length = schema.get("min_length")
    max_length = schema.get("max_length")

    if min_length is not None and len(value) < min_length:
        raise ValidationError("Too short")

    if max_length is not None and len(value) > max_length:
        raise ValidationError("Too long")


# ---------------------------------------------------------

@VALIDATOR_REGISTRY.register("N")  # NUMBER
def validate_number(question, value, schema):
    if not isinstance(value, (int, float)):
        raise ValidationError("Must be a number")

    if "min" in schema and value < schema["min"]:
        raise ValidationError("Value too small")

    if "max" in schema and value > schema["max"]:
        raise ValidationError("Value too large")


# ---------------------------------------------------------

@VALIDATOR_REGISTRY.register("D")  # DATE
def validate_date(question, value, schema):
    # keep simple; you can upgrade to date parsing later
    if not isinstance(value, str):
        raise ValidationError("Must be a date string (ISO format expected)")


# ---------------------------------------------------------

@VALIDATOR_REGISTRY.register("R")  # DATE_RANGE
def validate_date_range(question, value, schema):
    if not isinstance(value, dict):
        raise ValidationError("Must be an object with start/end")

    if "start" not in value or "end" not in value:
        raise ValidationError("Missing start or end")

    # optional future enhancement:
    # compare dates, enforce ordering, etc.


# ---------------------------------------------------------

@VALIDATOR_REGISTRY.register("E")  # ENUM
def validate_enum(question, value, schema):
    choices = [c["value"] for c in schema.get("choices", [])]
    multiple = schema.get("multiple", False)

    if multiple:
        if not isinstance(value, list):
            raise ValidationError("Must be a list")

        for v in value:
            if v not in choices:
                raise ValidationError(f"Invalid choice: {v}")
    else:
        if value not in choices:
            raise ValidationError("Invalid choice")


# ---------------------------------------------------------

def get_dynamic_options(source_name):
    source = DATA_SOURCE_REGISTRY.get(source_name)

    if not source:
        raise ValidationError(f"Unknown data source: {source_name}")

    # -------------------------
    # Case 1: Model registered
    # -------------------------
    if isinstance(source, type) and issubclass(source, BaseItemType):
        qs = source.objects.all()

    # -------------------------
    # Case 2: Callable registered
    # -------------------------
    elif callable(source):
        qs = source()

    else:
        raise ValidationError(f"Invalid data source: {source_name}")

    return [
        {"label": getattr(obj, "name"), "value": getattr(obj, "id")}
        for obj in qs
    ]

@VALIDATOR_REGISTRY.register("S")  # DYNAMIC SELECT
def validate_dynamic(question, value, schema):
    source = schema.get("source")

    if not source:
        raise ValidationError("Missing data source")

    options = get_dynamic_options(source)
    valid_values = [o["value"] for o in options]

    multiple = schema.get("multiple", False)

    if multiple:
        if not isinstance(value, list):
            raise ValidationError("Must be a list")

        for v in value:
            if v["value"] not in valid_values:
                raise ValidationError("Invalid selection")
    else:
        if not isinstance(value, dict):
            raise ValidationError("Must be an object")

        if value["value"] not in valid_values:
            raise ValidationError("Invalid selection")