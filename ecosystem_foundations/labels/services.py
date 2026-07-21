from functools import lru_cache

from django.contrib.contenttypes.models import ContentType

from .models import ModelFieldLabel


# -----------------------------
# Internal cached lookup
# -----------------------------
@lru_cache(maxsize=1024)
def _get_label(content_type_id: int, field_path: str):
    try:
        return ModelFieldLabel.objects.get(
            content_type_id=content_type_id,
            field_path=field_path
        ).label
    except ModelFieldLabel.DoesNotExist:
        return None


# -----------------------------
# Public API
# -----------------------------
def get_field_label(model, field_path: str, override: dict | None = None) -> str:
    """
    Resolve human-readable label for a model field path.

    Priority:
        1. override dict
        2. DB label
        3. fallback formatting
    """

    # 1. Override (highest priority)
    if override and field_path in override:
        return override[field_path]

    # 2. DB lookup
    content_type = ContentType.objects.get_for_model(model)
    label = _get_label(content_type.id, field_path)

    if label:
        return label

    # 3. Fallback
    return (
        field_path
        .replace("__", " → ")
        .replace("_", " ")
        .title()
    )