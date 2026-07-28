

from ecosystem_foundations.base.serializers import ContentTypeField
from ecosystem_foundations.labels.models import ModelFieldLabel
from ecosystem_foundations.labels.validators import validate_field_path
from rest_framework import serializers

class ModelFieldLabelSerializer(serializers.ModelSerializer):
    # -------------------------
    # ContentType (clean API)
    # -------------------------
    content_type = ContentTypeField()

    class Meta:
        model = ModelFieldLabel
        fields = [
            "id",
            "content_type",
            "field_path",
            "label",
            "description",
            "group",
        ]

    # -------------------------
    # Validation
    # -------------------------
    def validate(self, data):
        data = super().validate(data)

        content_type = data.get("content_type") or getattr(self.instance, "content_type", None)
        field_path = data.get("field_path") or getattr(self.instance, "field_path", None)

        if content_type and field_path:
            model = content_type.model_class()

            if not model:
                raise serializers.ValidationError("Invalid content type")

            # Reuse your model-level validation
            try:
                validate_field_path(model, field_path)
            except Exception as e:
                raise serializers.ValidationError({
                    "field_path": str(e)
                })

            # Enforce uniqueness nicely (instead of raw DB error)
            qs = ModelFieldLabel.objects.filter(
                content_type=content_type,
                field_path=field_path
            )

            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise serializers.ValidationError(
                    "This field_path already exists for the given model"
                )

        return data