from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    RoleFieldPermissionViewSet,
    UserFieldPermissionViewSet,
    CsrfView,
    LoginView,
    LogoutView,
    MeView
)

router = DefaultRouter()

router.register(r"users", UserFieldPermissionViewSet, basename="iam-user-permission")
router.register(r"roles", RoleFieldPermissionViewSet, basename="iam-role-permission")

urlpatterns = [
    path("auth/csrf/", CsrfView.as_view(), name="iam-auth-csrf"),
    path("auth/login/", LoginView.as_view(), name="iam-auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="iam-auth-logout"),
    path("auth/me/", MeView.as_view(), name="iam-auth-me"),
]

urlpatterns += router.urls