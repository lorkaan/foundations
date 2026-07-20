
# ------ Register Signal Types -------

from base.registry import MultiRegistry, SetRegistry


REGISTERED_SIGNAL_TYPES = SetRegistry()

# ------ Register Handlers for Signals in Code itself (Event Bus) ------

# Note: This is for functionality that Clients are not allowed to edit or needs 
# to happen with little overhead and can not be dynamic. All Dynamic functionality
# needs to be handled by the Action Registry (ActionEngine) so that it can be 
# stored in the database

SIGNAL_REGISTRY = MultiRegistry()
