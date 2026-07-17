
# ------ Register Signal Types -------

REGISTERED_SIGNAL_TYPES = set()

def register_signal_types(signal_list):
    for s in signal_list:
        REGISTERED_SIGNAL_TYPES.add(s)

# ------ Register Handlers for Signals in Code itself (Event Bus) ------

# Note: This is for functionality that Clients are not allowed to edit or needs 
# to happen with little overhead and can not be dynamic. All Dynamic functionality
# needs to be handled by the Action Registry (ActionRunner) so that it can be 
# stored in the database

SIGNAL_REGISTRY = {}

def register_signal_handler(signal_type: str):
    def decorator(fn):
        SIGNAL_REGISTRY.setdefault(signal_type, []).append(fn)
        return fn
    return decorator
