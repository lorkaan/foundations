from ecosystem_foundations.signals.registry import REGISTERED_SIGNAL_TYPES
from ecosystem_foundations.signals.models import SignalType

def sync_signal_types():
    for label in REGISTERED_SIGNAL_TYPES:
        SignalType.objects.get_or_create(label=label)