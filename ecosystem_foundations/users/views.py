from django.shortcuts import render

from .models import User, UserAssignment, UserRole
from .serializers import UserAssignmentSerializer, UserRoleSerializer, UserSerializer
from rest_framework import viewsets
from ..base.views import ActiveQuerysetMixin, BaseItemTypeQueryViewSetMixin, BaseQueryViewSetMixin, ForeignKeyFilterMixin, GenericTargetQuerysetMixin, TimeAuditableQuerysetMixin


# Create your views here.



class UserQuerysetMixin(BaseQueryViewSetMixin):

    def apply_filtering(self, queryset):
        queryset = super().apply_filtering(queryset)

        params = self.request.query_params

        username = params.get("username")
        email = params.get("email")
        full_name = params.get("full_name")
        role_id = params.get("role_id")

        if username:
            queryset = queryset.filter(
                username__icontains=username
            )

        if email:
            queryset = queryset.filter(
                email__icontains=email
            )

        if full_name:
            queryset = queryset.filter(
                full_name__icontains=full_name
            )

        if role_id:
            queryset = queryset.filter(
                role_id=role_id
            )

        return queryset

class UserAssignmentUserFilterMixin(ForeignKeyFilterMixin):
    fk_field = "user"

class UserRoleViewSet(
    ActiveQuerysetMixin,
    TimeAuditableQuerysetMixin,
    BaseItemTypeQueryViewSetMixin,
    BaseQueryViewSetMixin,
    viewsets.ModelViewSet,
):
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer

class UserViewSet(
    ActiveQuerysetMixin,
    TimeAuditableQuerysetMixin,
    UserQuerysetMixin,
    BaseQueryViewSetMixin,
    viewsets.ModelViewSet,
):
    queryset = User.objects.select_related(
        "role"
    )
    serializer_class = UserSerializer

class UserAssignmentViewSet(
    ActiveQuerysetMixin,
    TimeAuditableQuerysetMixin,
    UserAssignmentUserFilterMixin,
    GenericTargetQuerysetMixin,
    BaseQueryViewSetMixin,
    viewsets.ModelViewSet,
):
    queryset = UserAssignment.objects.select_related(
        "user",
        "content_type",
    )
    serializer_class = UserAssignmentSerializer