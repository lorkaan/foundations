

from watchdog.models import Signal, SignalType


def create_signal(instance, signal_type_label, **kwargs):
    signal_type, _ = SignalType.objects.get_or_create(label=signal_type_label)    # This is core to the system, so it needs to create if it does not exist

    Signal.objects.create(
        signal_type=signal_type,
        content_object=instance,  # 👈 Generic FK target
        metadata=kwargs
    )