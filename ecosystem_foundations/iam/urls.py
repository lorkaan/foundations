from rest_framework.routers import DefaultRouter

from .views import (
    RoleFieldPermissionViewSet,
    UserFieldPermissionViewSet
)

router = DefaultRouter()

router.register(r"users", UserFieldPermissionViewSet, basename="iam-user-permission")
router.register(r"roles", RoleFieldPermissionViewSet, basename="iam-role-permission")

urlpatterns = router.urls