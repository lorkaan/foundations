from ecosystem_foundations.automation.models import AutomationAction, AutomationActionRun, AutomationRule, AutomationRun, AutomationTrigger, TriggerTypes
from ecosystem_foundations.automation.registry import ACTION_REGISTRY
from ecosystem_foundations.storedquery.models import SavedQuery
from ecosystem_foundations.storedquery.serializers import SavedQuerySerializer
from rest_framework import serializers
from ecosystem_foundations.base.serializers import ActiveSerializerMixin, BaseRunSerializerMixin, TimeAuditableSerializerMixin
from ecosystem_foundations.watchdog.models import SignalItemType

class AutomationRuleSerializer(
    TimeAuditableSerializerMixin,
    serializers.ModelSerializer
):
    query = serializers.PrimaryKeyRelatedField(
        queryset=SavedQuery.objects.all()
    )

    query_detail = SavedQuerySerializer(
        source="query",
        read_only=True
    )

    class Meta:
        model = AutomationRule
        fields = [
            "id",
            "name",
            "query",
            "query_detail",
            "created_at",
            "updated_at",
        ]

class AutomationTriggerSerializer(
    ActiveSerializerMixin,
    TimeAuditableSerializerMixin,
    serializers.ModelSerializer
):
    # -------------------------
    # Relations (WRITE)
    # -------------------------
    signal_type = serializers.PrimaryKeyRelatedField(
        queryset=SignalItemType.objects.all(),
        required=False,
        allow_null=True
    )

    rule = serializers.PrimaryKeyRelatedField(
        queryset=AutomationRule.objects.all(),
        required=False,
        allow_null=True
    )

    # -------------------------
    # Relations (READ)
    # -------------------------
    # Uncomment if you want expanded responses
    # signal_type_detail = SignalItemTypeSerializer(
    #     source="signal_type",
    #     read_only=True
    # )

    # rule_detail = AutomationRuleSerializer(
    #     source="rule",
    #     read_only=True
    # )

    class Meta:
        model = AutomationTrigger
        fields = [
            "id",
            "name",
            "trigger_type",
            "schedule",
            "signal_type",
            # "signal_type_detail",
            "rule",
            # "rule_detail",

            # lifecycle
            "is_active",
            "deactivated_at",

            # audit
            "created_at",
            "updated_at",

            # scheduling (READ ONLY)
            "next_run_at",

            # locking (READ ONLY)
            "is_running",
            "locked_at",
        ]

        read_only_fields = [
            "created_at",
            "updated_at",
            "next_run_at",
            "is_running",
            "locked_at",
        ]

    # -------------------------
    # Validation (shape only)
    # -------------------------
    def validate(self, data):
        data = super().validate(data)

        trigger_type = data.get(
            "trigger_type",
            getattr(self.instance, "trigger_type", None)
        )

        schedule = data.get(
            "schedule",
            getattr(self.instance, "schedule", None)
        )

        signal_type = data.get(
            "signal_type",
            getattr(self.instance, "signal_type", None)
        )

        # ---- SIGNAL trigger ----
        if trigger_type == TriggerTypes.SIGNAL:
            if not signal_type:
                raise serializers.ValidationError(
                    "Signal trigger requires signal_type"
                )

            if schedule:
                raise serializers.ValidationError(
                    "Signal trigger cannot have schedule"
                )

        # ---- TIME trigger ----
        if trigger_type == TriggerTypes.TIME:
            if not schedule:
                raise serializers.ValidationError(
                    "Time trigger requires schedule"
                )

            if signal_type:
                raise serializers.ValidationError(
                    "Time trigger cannot have signal_type"
                )

        return data

class AutomationActionSerializer(
    ActiveSerializerMixin,
    TimeAuditableSerializerMixin,
    serializers.ModelSerializer
):
    # -------------------------
    # Relations (WRITE)
    # -------------------------
    trigger = serializers.PrimaryKeyRelatedField(
        queryset=AutomationTrigger.objects.all(),
        required=False,
        allow_null=True
    )

    # -------------------------
    # Computed / helper fields
    # -------------------------
    action_schema = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AutomationAction
        fields = [
            "id",
            "trigger",
            "type",
            "condition",
            "config",
            "order",

            # lifecycle
            "is_active",
            "deactivated_at",

            # audit
            "created_at",
            "updated_at",

            # helper
            "action_schema",
        ]

        read_only_fields = [
            "created_at",
            "updated_at",
            "action_schema",
        ]

    # -------------------------
    # Validation (shape only)
    # -------------------------
    def validate(self, data):
        data = super().validate(data)

        instance = getattr(self, "instance", None)

        action_type = data.get(
            "type",
            getattr(instance, "type", None)
        )

        config = data.get(
            "config",
            getattr(instance, "config", {})
        )

        trigger = data.get(
            "trigger",
            getattr(instance, "trigger", None)
        )

        is_active = data.get(
            "is_active",
            getattr(instance, "is_active", True)
        )

        # -------------------------
        # Ensure action type exists
        # -------------------------
        action_def = ACTION_REGISTRY.get(action_type)

        if not action_def:
            raise serializers.ValidationError({
                "type": f"Unknown action type: {action_type}"
            })

        # -------------------------
        # Basic config validation (light)
        # -------------------------
        schema = action_def.get("schema", {})
        required_fields = schema.get("required", [])

        for field in required_fields:
            if field not in config:
                raise serializers.ValidationError({
                    "config": f"Missing required field: {field}"
                })

        # -------------------------
        # Active actions must have trigger
        # -------------------------
        if is_active and not trigger:
            raise serializers.ValidationError(
                "Active actions must be attached to a trigger"
            )

        return data

    # -------------------------
    # Helper: expose schema
    # -------------------------
    def get_action_schema(self, obj):
        action_def = ACTION_REGISTRY.get(obj.type)
        if not action_def:
            return None

        return action_def.get("schema", {})

class AutomationRunSerializer(
    BaseRunSerializerMixin,
    serializers.ModelSerializer
):
    trigger = AutomationTriggerSerializer(read_only=True)
    rule = AutomationRuleSerializer(read_only=True)

    class Meta:
        model = AutomationRun
        fields = [
            "id",
            "status",
            "trigger",
            "rule",
            "context",
            "started_at",
            "finished_at",
            "error",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

class AutomationActionRunSerializer(
    BaseRunSerializerMixin,
    serializers.ModelSerializer
):
    run = AutomationRunSerializer(read_only=True)
    action = AutomationActionSerializer(read_only=True)

    class Meta:
        model = AutomationActionRun
        fields = [
            "id",
            "status",
            "run",
            "action",
            "error",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields