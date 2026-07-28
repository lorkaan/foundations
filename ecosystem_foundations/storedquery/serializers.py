from ecosystem_foundations.users.serializers import UserRoleSerializer, UserSerializer
from rest_framework import serializers
from ecosystem_foundations.base.serializers import ContentTypeField, TimeAuditableSerializerMixin
from ecosystem_foundations.storedquery.models import SavedQuery, SavedQueryPermission
from ecosystem_foundations.users.models import User, UserRole

class SavedQueryPermissionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    role = UserRoleSerializer(read_only=True)

    # -------------------------
    # WRITE (IDs)
    # -------------------------
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.active(),
        source="user",
        write_only=True
    )

    role_id = serializers.PrimaryKeyRelatedField(
        queryset=UserRole.objects.active(),
        source="role",
        write_only=True,
        required=False  # only if your model allows it
    )

    class Meta:
        model = SavedQueryPermission
        fields = [
            "id",
            "role",
            "user",
            "level",
        ]

    def validate(self, data):
        role = data.get("role")
        user = data.get("user")

        # XOR validation (matches DB constraint)
        if bool(role) == bool(user):
            raise serializers.ValidationError(
                "Exactly one of 'role' or 'user' must be provided."
            )

        return data

class SavedQuerySerializer(
    TimeAuditableSerializerMixin,
    serializers.ModelSerializer
):
    # -------------------------
    # ContentType (uses new field)
    # -------------------------
    model = ContentTypeField()

    # -------------------------
    # Owner (read/write split)
    # -------------------------
    owner = UserSerializer(read_only=True)
    owner_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.active(),
        source="owner",
        write_only=True,
        required=False,
        allow_null=True
    )

    # -------------------------
    # Permissions (nested)
    # -------------------------
    permissions = SavedQueryPermissionSerializer(
        many=True,
        required=False
    )

    class Meta:
        model = SavedQuery
        fields = [
            "id",
            "name",
            "description",
            "model",
            "query",
            "owner",
            "owner_id",
            "is_system",
            "permissions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    # -------------------------
    # Validation
    # -------------------------
    def validate(self, data):
        data = super().validate(data)

        owner = data.get("owner")
        is_system = data.get(
            "is_system",
            getattr(self.instance, "is_system", False)
        )

        # Enforce your DB constraint at serializer level
        if is_system and owner is not None:
            raise serializers.ValidationError(
                "System queries cannot have an owner"
            )

        return data
