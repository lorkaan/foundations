from typing import Callable, Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ActionRunner:
    """
    Registry and executor for automation actions.
    """

    REGISTRY: Dict[str, dict] = {}

    # -----------------------------
    # REGISTRATION
    # -----------------------------
    @classmethod
    def register(cls, name: str, *, schema: Optional[dict] = None):
        """
        Decorator to register an action handler.

        schema example:
        {
            "required": ["email", "subject"],
            "optional": ["body"]
        }
        """

        def decorator(fn: Callable[[Any, dict, dict], None]):
            if not callable(fn):
                raise TypeError(f"Handler must be callable, got {type(fn)}")

            if name in cls.REGISTRY:
                raise ValueError(f"Action '{name}' is already registered")

            cls.REGISTRY[name] = {
                "handler": fn,
                "schema": schema or {},
            }

            logger.debug(f"Registered automation action: {name}")
            return fn

        return decorator

    # -----------------------------
    # VALIDATION
    # -----------------------------
    @classmethod
    def validate(cls, action):
        action_def = cls.REGISTRY.get(action.type)

        if not action_def:
            raise ValueError(f"Unknown action type: {action.type}")

        schema = action_def.get("schema", {})
        required_fields = schema.get("required", [])

        for field in required_fields:
            if field not in action.config:
                raise ValueError(
                    f"Missing required config field '{field}' for action '{action.type}'"
                )

    # -----------------------------
    # EXECUTION
    # -----------------------------
    @classmethod
    def run(cls, action, results: Any, context: dict):
        action_def = cls.REGISTRY.get(action.type)

        if action_def is None:
            raise ValueError(f"Unknown action type: {action.type}")

        handler = action_def["handler"]

        if not callable(handler):
            raise TypeError(f"Handler for action {action.type} is not callable")

        # Validate BEFORE execution
        cls.validate(action)

        try:
            logger.info(
                f"Running action '{action.type}' "
                f"for trigger {context.get('trigger_id')}"
            )

            handler(results, action.config, context)

        except Exception as e:
            logger.exception(f"Error running action '{action.type}': {e}")
            raise