from django.db import models
import pghistory

from base.models import BaseItemType, BaseUuidPrimaryKeyModel, OptionalGenericUuidTargetMixin

# Create your models here.
class SignalItenType(BaseItemType):
    pass

@pghistory.track()
class Signal(OptionalGenericUuidTargetMixin, BaseUuidPrimaryKeyModel):
    signal_type = models.ForeignKey(SignalItenType, on_delete=models.PROTECT)
    #severity = models.ForeignKey(SignalSeverity, on_delete=models.PROTECT)
    metadata = models.JSONField(default=dict, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    

