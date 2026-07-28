from rest_framework.routers import DefaultRouter

from .views import (
    SignalItemTypeViewSet,
    SignalViewSet
)

router = DefaultRouter()

router.register(r"types", SignalItemTypeViewSet, basename="signal-types")
router.register(r"signals", SignalViewSet, basename="signal")

urlpatterns = router.urls