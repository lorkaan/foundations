from ..registry import REGISTERED_SIGNAL_TYPES
from ..models import SignalItemType

def sync_signal_types():
    for label in REGISTERED_SIGNAL_TYPES:
        SignalItemType.objects.get_or_create(label=label)