from rest_framework.routers import DefaultRouter

from .views import (
    SavedQueryPermissionViewSet,
    SavedQueryViewSet
)

router = DefaultRouter()

router.register(r"permissions", SavedQueryPermissionViewSet, basename="query-permission")
router.register(r"", SavedQueryViewSet, basename="query")

urlpatterns = router.urls