

import logging

from .registry import ACTION_REGISTRY

logger = logging.getLogger(__name__)

class ActionEngine:

    @classmethod
    def run(cls, action, results, context):
        definition = ACTION_REGISTRY.get(action.type)

        if definition is None:
            raise ValueError(f"Unknown action type: {action.type}")

        definition.validate(action.config)

        logger.info(
            "Running action '%s' for trigger %s",
            action.type,
            context.get("trigger_id"),
        )

        try:
            definition.handler(
                results,
                action.config,
                context,
            )
        except Exception:
            logger.exception(
                "Error running action '%s'",
                action.type,
            )
            raise