from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from datetime import timedelta


from .registry import ACTION_REGISTRY
from base.models import ActiveMixin, BaseRunModel, BaseUuidPrimaryKeyModel, TimeAuditableMixin
from watchdog.models import SignalType

# Create your models here.

# ============================================================
# RULES
# ============================================================

class AutomationRule(TimeAuditableMixin, BaseUuidPrimaryKeyModel):
    name = models.CharField(max_length=255)

    query = models.ForeignKey(
        SavedQuery,
        on_delete=models.CASCADE,
        related_name="automation_rules"
    )

# ============================================================
# TRIGGERS
# ============================================================

class TriggerTypes(models.TextChoices):
    SIGNAL = "S", "Signal"
    TIME = "T", "Time"


class AutomationTrigger(ActiveMixin, TimeAuditableMixin, BaseUuidPrimaryKeyModel):

    class Schedule(models.TextChoices):
        HOURLY = "H", "Hourly"
        DAILY = "D", "Daily"
        WEEKLY = "W", "Weekly"
        MONTHLY = "M", "Monthly"
        YEARLY = "Y", "Yearly"

    SCHEDULE_DELTAS = {
        Schedule.HOURLY: timedelta(hours=1),
        Schedule.DAILY: timedelta(days=1),
        Schedule.WEEKLY: timedelta(weeks=1),
        Schedule.MONTHLY: timedelta(days=30),
        Schedule.YEARLY: timedelta(weeks=52),
    }

    schedule = models.CharField(
        max_length=1,
        choices=Schedule.choices,
        null=True,
        blank=True
    )

    trigger_type = models.CharField(
        max_length=1,
        choices=TriggerTypes.choices,
        default=TriggerTypes.TIME
    )

    signal_type = models.ForeignKey(
        SignalType,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    rule = models.ForeignKey(
        AutomationRule,
        on_delete=models.PROTECT,
        related_name="triggers",
        null=True,
        blank=True
    )

    # ✅ scheduling fix (no drift)
    next_run_at = models.DateTimeField(null=True, blank=True)

    # ✅ concurrency control
    is_running = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)

    name = models.CharField(max_length=255, null=True, blank=True)

    # ------------------------
    # VALIDATION
    # ------------------------

    def clean(self):
        if self.trigger_type == TriggerTypes.SIGNAL and not self.signal_type:
            raise ValidationError("Signal trigger requires signal_type")

        if self.trigger_type == TriggerTypes.TIME and not self.schedule:
            raise ValidationError("Schedule trigger requires schedule")

    # ------------------------
    # SCHEDULING
    # ------------------------

    def should_run(self):
        return (
            self.is_active
            and self.next_run_at
            and timezone.now() >= self.next_run_at
        )

    def compute_next_run(self, from_time=None):
        from_time = from_time or timezone.now()
        delta = self.SCHEDULE_DELTAS.get(self.schedule)

        if not delta:
            return None

        return from_time + delta

    # ------------------------
    # LOCKING (critical)
    # ------------------------

    def acquire_lock(self):
        with transaction.atomic():
            trigger = (
                AutomationTrigger.objects
                .select_for_update()
                .get(pk=self.pk)
            )

            if trigger.is_running:
                return False

            trigger.is_running = True
            trigger.locked_at = timezone.now()
            trigger.save(update_fields=["is_running", "locked_at"])

            return True

    def release_lock(self):
        self.is_running = False
        self.locked_at = None
        self.save(update_fields=["is_running", "locked_at"])

    # ------------------------
    # META
    # ------------------------

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(trigger_type=TriggerTypes.SIGNAL, signal_type__isnull=False, schedule__isnull=True)
                    |
                    models.Q(trigger_type=TriggerTypes.TIME, signal_type__isnull=True, schedule__isnull=False)
                ),
                name="%(app_label)s_%(class)s_valid_trigger_configuration"
            ),
            models.UniqueConstraint(
                fields=['name'],
                condition=models.Q(name__isnull=False),
                name="%(app_label)s_%(class)s_unique_non_null_name"
            )
        ]

        indexes = [
            models.Index(fields=["trigger_type", "signal_type"]),
            models.Index(fields=["trigger_type", "schedule"]),
        ]

# ============================================================
# ACTIONS
# ============================================================

class AutomationAction(ActiveMixin, TimeAuditableMixin, BaseUuidPrimaryKeyModel):

    trigger = models.ForeignKey(
        AutomationTrigger,
        on_delete=models.PROTECT,
        related_name="actions",
        null=True,
        blank=True
    )

    condition = models.JSONField(null=True, blank=True)

    type = models.CharField(
        max_length=255,
        help_text="The action type registered in ActionRegistry",
        db_index=True
    )

    config = models.JSONField(default=dict, blank=True)

    order = models.PositiveIntegerField(default=0)

    # ------------------------
    # VALIDATION
    # ------------------------

    def clean(self):
        super().clean()

        if self.is_active and not self.trigger:
            raise ValidationError("Active actions must be attached to a trigger")

        # To Do: Make work with the ActionEngine class in the registry.py file in this app
        action_def = ACTION_REGISTRY.get(self.type)
        if not action_def:
            raise ValidationError(f"Unknown action type: {self.type}")

        # schema validation
        schema = action_def.get("schema", {})
        required_fields = schema.get("required", [])

        for field in required_fields:
            if field not in self.config:
                raise ValidationError(f"Missing config field: {field}")

    class Meta:
        ordering = ["order"]

# ============================================================
# RUN MODELS (AUDIT)
# ============================================================

class AutomationRun(BaseRunModel):

    trigger = models.ForeignKey(
        AutomationTrigger,
        on_delete=models.CASCADE,
        related_name="runs"
    )

    rule = models.ForeignKey(
        AutomationRule,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    context = models.JSONField(default=dict, blank=True)

    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    error = models.TextField(null=True, blank=True)

class AutomationActionRun(BaseRunModel):

    run = models.ForeignKey(
        AutomationRun,
        on_delete=models.CASCADE,
        related_name="action_runs"
    )

    action = models.ForeignKey(
        AutomationAction,
        on_delete=models.CASCADE
    )

    error = models.TextField(null=True, blank=True)
