from .registry import SIGNAL_REGISTRY

def dispatch_signal(signal):
    handlers = SIGNAL_REGISTRY.get(signal.signal_type.label, [])

    for handler in handlers:
        try:
            handler(signal)
        except Exception:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Signal handler failed: {handler}")

    from automation.tasks import evaluate_signal
    evaluate_signal.delay(signal.id)