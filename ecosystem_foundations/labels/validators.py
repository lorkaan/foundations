from django.core.exceptions import ValidationError


def validate_field_path(model, field_path: str):
    """
    Validates Django ORM-style field paths:
        "person__company__name"
    """

    parts = field_path.split("__")
    current_model = model

    for part in parts:
        try:
            field = current_model._meta.get_field(part)
        except Exception:
            raise ValidationError(
                f"Invalid field path '{field_path}' at '{part}'"
            )

        # Follow relations if applicable
        if hasattr(field, "related_model") and field.related_model:
            current_model = field.related_model