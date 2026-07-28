from ecosystem_foundations.base.models import BaseRunModel
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType

class HistoryEventSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"

class KeyConversionSerializer(serializers.ModelSerializer):

    CONVERSION_KEYS = {}

class ContentTypeField(serializers.Field):
    """
    Represent ContentType as "app_label.model"
    """

    def to_representation(self, value):
        return f"{value.app_label}.{value.model}"

    def to_internal_value(self, data):
        try:
            app_label, model = data.split(".")
            return ContentType.objects.get(app_label=app_label, model=model)
        except (ValueError, ContentType.DoesNotExist):
            raise serializers.ValidationError(
                "ContentType must be in format 'app_label.model'"
            )

class GenericTargetField(serializers.Field):
    """
    Handles OptionalGenericUuidTargetMixin / RequiredGenericUuidTargetMixin
    Uses ContentTypeField internally for consistency
    """

    content_type_field = ContentTypeField()

    def to_representation(self, obj):
        if not obj.content_type or not obj.object_id:
            return None

        return {
            "model": self.content_type_field.to_representation(obj.content_type),
            "id": str(obj.object_id),
        }

    def to_internal_value(self, data):
        if data is None:
            return {
                "content_type": None,
                "object_id": None
            }

        try:
            content_type = self.content_type_field.to_internal_value(
                data["model"]
            )
            object_id = data["id"]

            return {
                "content_type": content_type,
                "object_id": object_id
            }

        except KeyError:
            raise serializers.ValidationError(
                "Target must include 'model' and 'id'"
            )

# Mixin Abstract Serializers

"""
    Mixin Serializers
"""

class TimeAuditableSerializerMixin(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        abstract = True

class ActiveSerializerMixin(serializers.ModelSerializer):
    is_active = serializers.BooleanField(required=False)
    deactivated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        abstract = True

    # -------------------------
    # Validation
    # -------------------------
    def validate(self, data):
        instance = getattr(self, "instance", None)

        is_active = data.get(
            "is_active",
            instance.is_active if instance else True
        )

        deactivated_at = (
            instance.deactivated_at if instance else None
        )

        # Defensive validation (model should also enforce this)
        if is_active and deactivated_at is not None:
            raise serializers.ValidationError(
                "Active objects cannot have deactivated_at set"
            )

        return data

    # -------------------------
    # Update (state transitions)
    # -------------------------
    def update(self, instance, validated_data):
        is_active = validated_data.pop("is_active", None)

        # Apply normal field updates first
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Handle lifecycle transitions
        if is_active is not None:
            if is_active and not instance.is_active:
                instance.activate(commit=False)
            elif not is_active and instance.is_active:
                instance.deactivate(commit=False)

        instance.save()
        return instance

    # -------------------------
    # Create (optional handling)
    # -------------------------
    def create(self, validated_data):
        is_active = validated_data.pop("is_active", True)

        instance = super().create(validated_data)

        # Apply lifecycle after creation if needed
        if not is_active:
            instance.deactivate()

        return instance


class CreatedBySerializerMixin(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    created_by_display = serializers.CharField(
        source="created_by.__str__",
        read_only=True
    )

    class Meta:
        abstract = True

class BaseIsSystemSerializerMixin(serializers.ModelSerializer):
    is_system = serializers.BooleanField(read_only=True)

    class Meta:
        abstract = True


class BaseItemTypeSerializerMixin(serializers.ModelSerializer):
    name = serializers.CharField(max_length=100)
    code = serializers.CharField(max_length=100)

    class Meta:
        abstract = True

    # -------------------------
    # Field-level validation
    # -------------------------
    def validate_code(self, value):
        model = self.Meta.model
        qs = model.objects.filter(code=value)

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError("Code must be unique")

        return value

    # -------------------------
    # System protection
    # -------------------------
    def update(self, instance, validated_data):
        if instance.is_system:
            # Prevent changing core identity fields
            if any(field in validated_data for field in ["code", "name"]):
                raise serializers.ValidationError(
                    "System types cannot be modified"
                )

        return super().update(instance, validated_data)

class BaseRunSerializerMixin(
    TimeAuditableSerializerMixin,
    serializers.ModelSerializer
):
    status = serializers.ChoiceField(
        choices=BaseRunModel.RunStatus.choices,
        read_only=True
    )

    class Meta:
        abstract = True