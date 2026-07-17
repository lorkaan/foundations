from django.db import models

from base.models import BaseUuidPrimaryKeyModel, OptionalGenericUuidTargetMixin

# Create your models here.
class SignalType(models.Model):
    label = models.CharField(max_length=250, unique=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~Q(label=""),
                name="signal_type_label_not_empty",
            )
        ]

class Signal(OptionalGenericUuidTargetMixin, BaseUuidPrimaryKeyModel):
    signal_type = models.ForeignKey(SignalType, on_delete=models.PROTECT)
    #severity = models.ForeignKey(SignalSeverity, on_delete=models.PROTECT)
    metadata = models.JSONField(default=dict, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    

