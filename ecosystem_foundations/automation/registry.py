from dataclasses import dataclass
from typing import Callable
from base.registry import SingleRegistry

@dataclass
class ActionDefinition:
    handler: Callable
    schema: dict

    def validate(self, config):
        required = self.schema.get("required", [])

        for field in required:
            if field not in config:
                raise ValueError(
                    f"Missing required config field '{field}'"
                )

class ActionRegistry(SingleRegistry):
    
    def register(self, name, *, schema=None, replace=False):

        def decorator(fn):
            definition = ActionDefinition(
                handler=fn,
                schema=schema or {}
            )

            return super(ActionRegistry, self).register(
                name,
                definition,
                replace=replace,
            )

        return decorator

ACTION_REGISTRY = ActionRegistry()

