from celery import shared_task
from django.utils import timezone
from django.db import OperationalError

from watchdog.models import Signal
from .models import (
    AutomationTrigger,
    AutomationActionRun,
    AutomationRun,
    TriggerTypes,
)

from .runner import ActionEngine

from utils.queryAstHandler import QueryAstHandler
from utils.boolAstHandler import BooleanAstHandler

import logging

logger = logging.getLogger()


# ============================================================
# SIGNAL TRIGGER ENTRYPOINT
# ============================================================

@shared_task
def evaluate_signal(signal_id):
    signal = Signal.objects.get(id=signal_id)

    triggers = AutomationTrigger.objects.filter(
        is_active=True,
        trigger_type=TriggerTypes.SIGNAL,
        signal_type=signal.signal_type
    )

    logger.info(f"Evaluating signal {signal_id}")

    for trigger in triggers:
        run_trigger.delay(trigger.id, signal_id=signal.id)


# ============================================================
# SCHEDULED ENTRYPOINT
# ============================================================

@shared_task
def run_due_triggers():
    now = timezone.now()

    triggers = AutomationTrigger.objects.filter(
        is_active=True,
        trigger_type=TriggerTypes.TIME,
        next_run_at__lte=now
    )

    for trigger in triggers:
        run_trigger.delay(trigger.id)


# ============================================================
# CORE EXECUTION TASK
# ============================================================

@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def run_trigger(self, trigger_id, signal_id=None):
    now = timezone.now()

    try:
        trigger = AutomationTrigger.objects.get(id=trigger_id)

        # ------------------------------
        # LOCK ACQUISITION (centralized)
        # ------------------------------
        if not trigger.acquire_lock():
            logger.info(f"Trigger {trigger_id} already running")
            return

        # ------------------------------
        # QUERY EXECUTION (optional)
        # ------------------------------
        results = None
        if trigger.rule:
            results = QueryAstHandler.run(
                trigger.rule.query.query_def,
                {}  # TODO: param injection
            )

        # ------------------------------
        # CONTEXT
        # ------------------------------
        context = {
            "trigger_id": trigger.id,
            "signal_id": signal_id,
            "task_id": self.request.id,
            "started_at": now,
        }

        # ------------------------------
        # CREATE RUN
        # ------------------------------
        run = AutomationRun.objects.create(
            trigger=trigger,
            rule=trigger.rule,
            context=results or {},
            started_at=now,
            status=AutomationRun.RunStatus.RUNNING,
        )

        logger.info(f"Executing trigger {trigger_id}")

        # ------------------------------
        # ACTION EXECUTION
        # ------------------------------
        for action in trigger.actions.filter(is_active=True).order_by("order"):

            should_run = True

            if action.condition:
                should_run = BooleanAstHandler.run(
                    action.condition,
                    results or {}
                )

            if not should_run:
                continue

            try:
                ActionEngine.run(action, results, context)

                AutomationActionRun.objects.create(
                    run=run,
                    action=action,
                    status=AutomationActionRun.RunStatus.COMPLETED
                )

            except Exception as e:
                logger.exception(f"Action failed: {action.id}")

                AutomationActionRun.objects.create(
                    run=run,
                    action=action,
                    status=AutomationActionRun.RunStatus.FAILED,
                    error=str(e)
                )

                # optional: fail entire run
                raise

        # ------------------------------
        # SUCCESS FINALIZATION
        # ------------------------------
        run.status = AutomationRun.RunStatus.COMPLETED

        if trigger.trigger_type == TriggerTypes.TIME:
            trigger.next_run_at = trigger.compute_next_run()

        run.finished_at = timezone.now()

        run.save(update_fields=["status", "finished_at"])
        trigger.save(update_fields=["next_run_at"])

    except OperationalError as exc:
        raise self.retry(exc=exc)

    except Exception as exc:
        logger.exception(f"Trigger failed: {trigger_id}")

        AutomationRun.objects.filter(trigger_id=trigger_id).update(
            status=AutomationRun.RunStatus.FAILED,
            finished_at=timezone.now(),
            error=str(exc)
        )

        raise self.retry(exc=exc)

    finally:
        # ------------------------------
        # ALWAYS RELEASE LOCK
        # ------------------------------
        try:
            trigger.release_lock()
        except Exception:
            logger.exception(f"Failed to release lock for {trigger_id}")