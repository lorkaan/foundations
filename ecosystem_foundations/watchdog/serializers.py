from ecosystem_foundations.base.serializers import ActiveSerializerMixin, BaseItemTypeSerializerMixin, TimeAuditableSerializerMixin
from ecosystem_foundations.watchdog.models import Signal, SignalItemType
from rest_framework import serializers

class SignalItemTypeSerializer(
    BaseItemTypeSerializerMixin,
    ActiveSerializerMixin,
    serializers.ModelSerializer
):
    class Meta:
        model = SignalItemType
        fields = [
            "id",
            "name",
            "code",
            "is_active",
            "deactivated_at",
        ]

class SignalSerializer(
    ActiveSerializerMixin,
    TimeAuditableSerializerMixin,  # assuming Signal uses this (pghistory usually implies it)
    serializers.ModelSerializer
):
    # -------------------------
    # Read representation
    # -------------------------
    signal_type = SignalItemTypeSerializer(read_only=True)

    # -------------------------
    # Write input
    # -------------------------
    signal_type_id = serializers.PrimaryKeyRelatedField(
        queryset=SignalItemType.objects.active(),
        source="signal_type",
        write_only=True
    )

    class Meta:
        model = Signal
        fields = [
            "id",
            "is_active",
            "deactivated_at",
            "created_at",
            "updated_at",
            "signal_type",
            "signal_type_id",
            "metadata",
            "processed_at",
        ]

    # -------------------------
    # Extra safety validation
    # -------------------------
    def validate_signal_type(self, value):
        if not value.is_active:
            raise serializers.ValidationError(
                "Signal type must be active"
            )
        return value