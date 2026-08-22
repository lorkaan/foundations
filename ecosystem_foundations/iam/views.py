from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from .models import RoleFieldPermission, UserFieldPermission
from .serializers import LoginSerializer, RoleFieldPermissionSerializer, UserFieldPermissionSerializer
from rest_framework import viewsets
from ..base.views import BaseQueryViewSetMixin, ContentTypeQuerysetMixin, ForeignKeyFilterMixin
from ..users.serializers import UserSerializer

from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            "detail": "CSRF cookie set"
        })

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )

        if user is None:
            return Response(
                {"detail": "Invalid credentials"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        login(request, user)

        return Response({
            "success": True,
            "user": UserSerializer(
                user,
                context={"request": request},
            ).data,
        })

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)

        return Response({
            "success": True
        })


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(
            request.user,
            context={"request": request},
        )

        return Response(serializer.data)

# Create your views here.
class FieldPermissionQuerysetMixin(BaseQueryViewSetMixin):

    def apply_filtering(self, queryset):
        queryset = super().apply_filtering(queryset)

        params = self.request.query_params

        field_name = params.get("field_name")
        permission = params.get("permission")

        if field_name:
            queryset = queryset.filter(field_name=field_name)

        if permission:
            queryset = queryset.filter(permission=permission)

        return queryset

class RoleFilterQuerysetMixin(ForeignKeyFilterMixin):
    fk_field = "role"

class UserFilterQuerysetMixin(ForeignKeyFilterMixin):
    fk_field = "user"

class RoleFieldPermissionViewSet(
    ContentTypeQuerysetMixin,
    RoleFilterQuerysetMixin,
    FieldPermissionQuerysetMixin,
    BaseQueryViewSetMixin,
    viewsets.ModelViewSet,
):
    queryset = RoleFieldPermission.objects.select_related(
        "role",
        "content_type",
    )
    serializer_class = RoleFieldPermissionSerializer

class UserFieldPermissionViewSet(
    ContentTypeQuerysetMixin,
    UserFilterQuerysetMixin,
    FieldPermissionQuerysetMixin,
    BaseQueryViewSetMixin,
    viewsets.ModelViewSet,
):
    queryset = UserFieldPermission.objects.select_related(
        "user",
        "content_type",
    )
    serializer_class = UserFieldPermissionSerializer