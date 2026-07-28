from rest_framework.routers import DefaultRouter

from .views import (
    UserRoleViewSet,
    UserViewSet,
    UserAssignmentViewSet
)

router = DefaultRouter()

router.register(r"", UserViewSet, basename="user")
router.register(r"roles", UserRoleViewSet, basename="user-role")
router.register(r"assignments", UserAssignmentViewSet, basename="user-assignment")

urlpatterns = router.urls