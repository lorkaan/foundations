from ecosystem_foundations.base.serializers import ActiveSerializerMixin, GenericTargetField, TimeAuditableSerializerMixin
from ecosystem_foundations.users.models import User, UserAssignment, UserRole
from rest_framework import serializers

class UserRoleSerializer(
    ActiveSerializerMixin,
    TimeAuditableSerializerMixin,
    serializers.ModelSerializer
):
    class Meta:
        model = UserRole
        fields = [
            "id",
            "code",
            "name",
            "description",
            "is_active",
            "deactivated_at",
            "created_at",
            "updated_at",
        ]

class UserSerializer(
    ActiveSerializerMixin,
    TimeAuditableSerializerMixin,
    serializers.ModelSerializer
):
    # -------------------------
    # Read
    # -------------------------
    role = UserRoleSerializer(read_only=True)

    # -------------------------
    # Write
    # -------------------------
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=UserRole.objects.all(),
        source="role",
        write_only=True
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "full_name",
            "email",
            "role",
            "role_id",
            "is_active",
            "deactivated_at",
            "is_staff",
            "date_joined",
            "created_at",
            "updated_at",
        ]

    # Optional: enforce role rules
    def validate_role(self, value):
        if value.is_system and not self.context["request"].user.is_staff:
            raise serializers.ValidationError(
                "Only staff can assign system roles"
            )
        return value

class UserAssignmentSerializer(
    ActiveSerializerMixin,
    TimeAuditableSerializerMixin,
    serializers.ModelSerializer
):
    # -------------------------
    # READ
    # -------------------------
    user = UserSerializer(read_only=True)

    # -------------------------
    # WRITE
    # -------------------------
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.active(),
        source="user",
        write_only=True
    )

    # -------------------------
    # Generic Target (KEY PART)
    # -------------------------
    target = GenericTargetField(source="*")

    class Meta:
        model = UserAssignment
        fields = [
            "id",
            "user",
            "user_id",
            "target",
            "created_by",
            "is_active",
            "deactivated_at",
            "created_at",
            "updated_at",
        ]

    # -------------------------
    # Validation
    # -------------------------
    def validate(self, data):
        data = super().validate(data)

        # Handle both create and update cases
        user = data.get("user") or getattr(self.instance, "user", None)
        content_type = data.get("content_type") or getattr(self.instance, "content_type", None)
        object_id = data.get("object_id") or getattr(self.instance, "object_id", None)

        # Only validate if all required pieces exist
        if user and content_type and object_id:
            qs = UserAssignment.objects.filter(
                user=user,
                content_type=content_type,
                object_id=object_id,
                is_active=True
            )

            # 🔥 IMPORTANT: exclude current instance on update
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise serializers.ValidationError(
                    "User is already assigned to this object"
                )

        return data