from rest_framework.routers import DefaultRouter

from .views import (
    AutomationRuleViewSet,
    AutomationTriggerViewSet,
    AutomationActionViewSet,
    AutomationRunViewSet,
    AutomationActionRunViewSet,
)

router = DefaultRouter()

router.register(r"rules", AutomationRuleViewSet, basename="automation-rule")
router.register(r"triggers", AutomationTriggerViewSet, basename="automation-trigger")
router.register(r"actions", AutomationActionViewSet, basename="automation-action")
router.register(r"runs", AutomationRunViewSet, basename="automation-run")
router.register(r"action-runs", AutomationActionRunViewSet, basename="automation-action-run")

urlpatterns = router.urls