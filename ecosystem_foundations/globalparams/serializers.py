from ..base.serializers import ActiveSerializerMixin, TimeAuditableSerializerMixin
from rest_framework import serializers

from .models import GlobalParameter
from .services import coerce_value, set_parameter_value


class GlobalParameterSerializer(
    ActiveSerializerMixin,
    TimeAuditableSerializerMixin,
    serializers.ModelSerializer
):
    value = serializers.JSONField(required=False)

    class Meta:
        model = GlobalParameter
        fields = [
            "id",
            "name",
            "description",
            "type",
            "value",
            "is_active",
            "deactivated_at",
            "created_at",
            "updated_at",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["value"] = instance.get_value()
        return data

    def validate(self, data):
        param_type = data.get("type") or self.instance.type
        value = data.get("value", None)

        if value is not None:
            coerce_value(param_type, value)

        return data

    def create(self, validated_data):
        value = validated_data.pop("value", None)

        instance = GlobalParameter.objects.create(**validated_data)

        coerced = coerce_value(instance.type, value)
        set_parameter_value(instance, coerced)

        return instance

    def update(self, instance, validated_data):
        value = validated_data.pop("value", None)

        for attr, val in validated_data.items():
            setattr(instance, attr, val)

        instance.save()

        if value is not None:
            coerced = coerce_value(instance.type, value)
            set_parameter_value(instance, coerced)

        return instance