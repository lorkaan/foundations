

from ..base.serializers import ContentTypeField
from .models import RoleFieldPermission, UserFieldPermission
from ..users.models import User, UserRole
from ..users.serializers import UserRoleSerializer, UserSerializer
from rest_framework import serializers

class RoleFieldPermissionSerializer(serializers.ModelSerializer):
    # -------------------------
    # Role (read/write split)
    # -------------------------
    role = UserRoleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=UserRole.objects.active(),
        source="role",
        write_only=True
    )

    # -------------------------
    # ContentType
    # -------------------------
    content_type = ContentTypeField()

    class Meta:
        model = RoleFieldPermission
        fields = [
            "id",
            "role",
            "role_id",
            "content_type",
            "field_name",
            "permission",
        ]

    # -------------------------
    # Validation
    # -------------------------
    def validate(self, data):
        data = super().validate(data)

        role = data.get("role") or getattr(self.instance, "role", None)
        content_type = data.get("content_type") or getattr(self.instance, "content_type", None)
        field_name = data.get("field_name") or getattr(self.instance, "field_name", None)

        # -------------------------
        # Ensure model + field exist
        # -------------------------
        if content_type and field_name:
            model = content_type.model_class()

            if not model:
                raise serializers.ValidationError(
                    "Invalid content type"
                )

            # Optional but HIGHLY recommended
            if not self._field_exists(model, field_name):
                raise serializers.ValidationError({
                    "field_name": f"{field_name} is not a valid field on {model.__name__}"
                })

        # -------------------------
        # Enforce uniqueness nicely
        # -------------------------
        if role and content_type and field_name:
            qs = RoleFieldPermission.objects.filter(
                role=role,
                content_type=content_type,
                field_name=field_name
            )

            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise serializers.ValidationError(
                    "Permission already exists for this role + field"
                )

        return data

    # -------------------------
    # Helpers
    # -------------------------
    def _field_exists(self, model, field_name):
        """
        Supports both direct fields and __ lookups
        """
        parts = field_name.split("__")
        current_model = model

        for part in parts:
            try:
                field = current_model._meta.get_field(part)
            except Exception:
                return False

            # Follow relations if needed
            if hasattr(field, "related_model") and field.related_model:
                current_model = field.related_model
            else:
                # Last field must be a real field
                return True

        return True

class UserFieldPermissionSerializer(serializers.ModelSerializer):
    # -------------------------
    # User (read/write split)
    # -------------------------
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.active(),
        source="user",
        write_only=True
    )

    # -------------------------
    # ContentType
    # -------------------------
    content_type = ContentTypeField()

    class Meta:
        model = UserFieldPermission
        fields = [
            "id",
            "user",
            "user_id",
            "content_type",
            "field_name",
            "permission",
        ]

    # -------------------------
    # Validation
    # -------------------------
    def validate(self, data):
        data = super().validate(data)

        user = data.get("user") or getattr(self.instance, "user", None)
        content_type = data.get("content_type") or getattr(self.instance, "content_type", None)
        field_name = data.get("field_name") or getattr(self.instance, "field_name", None)

        # -------------------------
        # Ensure model + field exist
        # -------------------------
        if content_type and field_name:
            model = content_type.model_class()

            if not model:
                raise serializers.ValidationError(
                    "Invalid content type"
                )

            if not self._field_exists(model, field_name):
                raise serializers.ValidationError({
                    "field_name": f"{field_name} is not a valid field on {model.__name__}"
                })

        # -------------------------
        # Enforce uniqueness nicely
        # -------------------------
        if user and content_type and field_name:
            qs = UserFieldPermission.objects.filter(
                user=user,
                content_type=content_type,
                field_name=field_name
            )

            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise serializers.ValidationError(
                    "Permission already exists for this user + field"
                )

        return data

    # -------------------------
    # Helpers
    # -------------------------
    def _field_exists(self, model, field_name):
        """
        Supports both direct fields and __ lookups
        """
        parts = field_name.split("__")
        current_model = model

        for i, part in enumerate(parts):
            try:
                field = current_model._meta.get_field(part)
            except Exception:
                return False

            # If this is not the last part, it must be a relation
            if i < len(parts) - 1:
                if not hasattr(field, "related_model") or not field.related_model:
                    return False
                current_model = field.related_model
            else:
                # Last part: valid field
                return True

        return True